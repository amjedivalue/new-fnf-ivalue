import frappe
from frappe.utils import flt, get_first_day, getdate

from new_ivalue_fnf.api import date_utils


# =========================================
# أدوات مساعدة للإجازات الشخصية
# =========================================

def get_personal_leave_start_date(end_date):
    # إرجاع أول يوم في الشهر الخاص بتاريخ النهاية
    return get_first_day(getdate(end_date))


def convert_leave_hours_to_days(hours):
    # تحويل ساعات الإجازة إلى أيام
    # تم اعتماد 8 ساعات = يوم واحد
    return flt(flt(hours) / 8, 2)


def add_days_to_leave_type_balance(leave_days_by_type, leave_type, days):
    # إضافة عدد الأيام إلى نوع الإجازة داخل القاموس
    if leave_type not in leave_days_by_type:
        leave_days_by_type[leave_type] = 0.0

    leave_days_by_type[leave_type] = flt(leave_days_by_type[leave_type] + days, 2)


def get_personal_leave_days_by_type(employee: str, end_date) -> dict:
    # هذه الدالة تجمع الإجازات الشخصية خلال الشهر
    # ثم ترجع عدد الأيام لكل نوع إجازة

    month_start = get_personal_leave_start_date(end_date)

    personal_leaves = frappe.get_all(
        "Personal Leave",
        filters={
            "employee": employee,
            "date": ["between", [month_start, end_date]],
            "docstatus": 1,
        },
        fields=[
            "leave_type",
            "hours",
        ],
    )

    leave_days_by_type = {}

    for row in personal_leaves:
        leave_type = row.get("leave_type")

        if not leave_type:
            continue

        hours = row.get("hours")
        days = convert_leave_hours_to_days(hours)

        add_days_to_leave_type_balance(
            leave_days_by_type,
            leave_type,
            days
        )

    return leave_days_by_type


# =========================================
# أدوات مساعدة للإجازات المرحلة
# =========================================

def get_carry_forward_leave_types():
    # جلب جميع أنواع الإجازات المسموح بترحيلها بشكل دينمك
    return frappe.get_all(
        "Leave Type",
        filters={
            "is_carry_forward": 1,
        },
        pluck="name",
    )


def get_latest_leave_allocation(employee, leave_type, end_date):
    # جلب آخر Leave Allocation معتمد للموظف ولنفس نوع الإجازة
    allocations = frappe.get_all(
        "Leave Allocation",
        filters={
            "employee": employee,
            "leave_type": leave_type,
            "docstatus": 1,
            "from_date": ("<=", end_date),
        },
        fields=[
            "name",
            "from_date",
            "to_date",
            "total_leaves_allocated",
            "extra_days",
        ],
        order_by="from_date desc, to_date desc, modified desc",
        limit=1,
    )

    if not allocations:
        return None

    return allocations[0]


def calculate_allocated_leave_days(allocation_row):
    # حساب إجمالي الإجازات المستحقة من التخصيص مع الأيام الإضافية
    total_leaves_allocated = flt(allocation_row.get("total_leaves_allocated"))
    extra_days = flt(allocation_row.get("extra_days"))

    return flt(total_leaves_allocated + extra_days, 2)


def get_approved_leave_applications(employee, leave_type, allocation_start_date, end_date):
    # جلب طلبات الإجازة المعتمدة التي تتقاطع مع فترة التخصيص
    return frappe.get_all(
        "Leave Application",
        filters={
            "employee": employee,
            "leave_type": leave_type,
            "docstatus": 1,
            "status": "Approved",
            "from_date": ("<=", end_date),
            "to_date": (">=", allocation_start_date),
        },
        fields=[
            "from_date",
            "to_date",
            "total_leave_days",
        ],
    )


def calculate_taken_days_from_leave_applications(leave_applications, allocation_start_date, end_date):
    # حساب الأيام المأخوذة من طلبات الإجازة
    # ويتم احتساب فقط الجزء المتقاطع مع فترة التخصيص

    taken_days = 0.0

    for leave_application in leave_applications:
        application_start_date = leave_application.get("from_date")
        application_end_date = leave_application.get("to_date")
        application_total_days = flt(leave_application.get("total_leave_days"))

        overlap_days = date_utils.overlap_inclusive_days(
            application_start_date,
            application_end_date,
            allocation_start_date,
            end_date
        )

        total_application_days = date_utils.inclusive_days(
            application_start_date,
            application_end_date
        )

        if total_application_days <= 0:
            continue

        proportional_taken_days = application_total_days * (
            flt(overlap_days) / flt(total_application_days)
        )

        taken_days = taken_days + flt(proportional_taken_days)

    return flt(taken_days, 2)


def calculate_total_taken_days(leave_type, leave_applications_taken_days, personal_leave_days_by_type):
    # حساب إجمالي الأيام المأخوذة من:
    # 1- طلبات الإجازة
    # 2- الإجازات الشخصية

    personal_leave_days = flt(personal_leave_days_by_type.get(leave_type, 0))
    total_taken_days = flt(leave_applications_taken_days + personal_leave_days, 2)

    return total_taken_days


def create_carry_forward_leave_row(leave_type, earned_days, taken_days, balance_days, allocation_reference):
    # إنشاء سطر خاص بالإجازات المرحلة بشكل موحد
    return {
        "leave_type": leave_type,
        "earned": flt(earned_days, 2),
        "taken": flt(taken_days, 2),
        "balance": flt(balance_days, 2),
        "allocation_ref": allocation_reference,
    }


# =========================================
# الدالة الرئيسية لحساب الإجازات المرحلة
# =========================================

def compute_carry_forward_leave_rows(employee: str, start_date, end_date) -> list[dict]:
    # هذه الدالة تبني جدول الإجازات المرحلة للموظف
    # وتحسب لكل نوع:
    # - المستحق
    # - المأخوذ
    # - الرصيد المتبقي

    rows = []

    personal_leave_days_by_type = get_personal_leave_days_by_type(
        employee,
        end_date
    )

    carry_forward_leave_types = get_carry_forward_leave_types()

    for leave_type in carry_forward_leave_types:
        latest_allocation = get_latest_leave_allocation(
            employee,
            leave_type,
            end_date
        )

        if not latest_allocation:
            continue

        allocation_reference = latest_allocation.get("name")
        allocation_start_date = latest_allocation.get("from_date")
        earned_days = calculate_allocated_leave_days(latest_allocation)

        approved_leave_applications = get_approved_leave_applications(
            employee,
            leave_type,
            allocation_start_date,
            end_date
        )

        leave_applications_taken_days = calculate_taken_days_from_leave_applications(
            approved_leave_applications,
            allocation_start_date,
            end_date
        )

        total_taken_days = calculate_total_taken_days(
            leave_type,
            leave_applications_taken_days,
            personal_leave_days_by_type
        )

        balance_days = flt(earned_days - total_taken_days, 2)

        if balance_days <= 0:
            continue

        leave_row = create_carry_forward_leave_row(
            leave_type=leave_type,
            earned_days=earned_days,
            taken_days=total_taken_days,
            balance_days=balance_days,
            allocation_reference=allocation_reference,
        )

        rows.append(leave_row)

    return rows