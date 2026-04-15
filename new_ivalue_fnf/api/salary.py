from frappe import _
import frappe
from frappe.utils import flt, getdate

from new_ivalue_fnf.api import date_utils


# =========================================
# أدوات مساعدة لبيانات الراتب
# =========================================

def get_empty_salary_breakdown():
    # إرجاع هيكل افتراضي فارغ لتفاصيل الراتب
    return {
        "basic": 0,
        "housing": 0,
        "traveling": 0,
        "other": 0,
        "monthly_total": 0,
    }


def get_assignment_field_value(assignment, fieldname, default_value=0):
    # جلب قيمة حقل من Salary Structure Assignment مع قيمة افتراضية إذا لم يكن موجوداً
    if not assignment:
        return default_value

    return getattr(assignment, fieldname, default_value)


def get_traveling_allowance_value(assignment):
    # جلب بدل المواصلات بشكل دينمك
    # يدعم أكثر من اسم حقل لتجنب الهارد كود قدر الإمكان
    possible_field_names = [
        "custom_travelling",
        "custom_traveling",
    ]

    for fieldname in possible_field_names:
        value = flt(get_assignment_field_value(assignment, fieldname, 0))

        if value:
            return value

    return 0


def calculate_monthly_total(basic, housing, traveling, other):
    # حساب إجمالي الراتب الشهري
    return flt(basic + housing + traveling + other)


def get_salary_period_start_date(join_date, relieving_date):
    # تحديد بداية فترة الاستحقاق داخل شهر آخر يوم عمل
    period_start_date = date_utils.month_first_day(relieving_date)

    if join_date:
        joining_date = getdate(join_date)

        if joining_date > period_start_date:
            period_start_date = joining_date

    return period_start_date


def calculate_daily_rate(monthly_total):
    # حساب الأجر اليومي
    # حالياً المعادلة المعتمدة هي القسمة على 30
    return flt(monthly_total / 30, 2)


def calculate_prorated_salary_amount(monthly_total, worked_days, month_days, daily_rate):
    # حساب المبلغ المستحق:
    # إذا عمل الشهر كامل يأخذ الراتب كامل
    # وإذا لم يكمل الشهر يتم احتسابها بشكل نسبي
    if worked_days >= month_days:
        return flt(monthly_total, 2)

    return flt(worked_days * daily_rate, 2)


# =========================================
# جلب آخر Salary Structure Assignment
# =========================================

def fetch_latest_salary_assignment(employee: str, as_of_date):
    # جلب آخر Salary Structure Assignment معتمد للموظف حتى تاريخ محدد
    assignment_name = frappe.db.get_value(
        "Salary Structure Assignment",
        {
            "employee": employee,
            "docstatus": 1,
            "from_date": ("<=", as_of_date),
        },
        "name",
        order_by="from_date desc",
    )

    if not assignment_name:
        return None

    return frappe.get_doc("Salary Structure Assignment", assignment_name)


# =========================================
# جلب العملة
# =========================================

def get_salary_assignment_currency(assignment):
    # جلب العملة من Salary Structure Assignment
    # وإذا لم تكن موجودة يتم الرجوع إلى Salary Structure
    if not assignment:
        return None

    assignment_currency = getattr(assignment, "currency", None)

    if assignment_currency:
        return assignment_currency

    salary_structure = getattr(assignment, "salary_structure", None)

    if not salary_structure:
        return None

    structure_currency = frappe.db.get_value(
        "Salary Structure",
        salary_structure,
        "currency"
    )

    if structure_currency:
        return structure_currency

    return None


# =========================================
# بناء تفاصيل الراتب
# =========================================

def build_salary_breakdown(assignment) -> dict:
    # بناء تفاصيل الراتب من مكونات Salary Structure Assignment
    if not assignment:
        return get_empty_salary_breakdown()

    basic_salary = flt(get_assignment_field_value(assignment, "base", 0))
    housing_allowance = flt(get_assignment_field_value(assignment, "custom_housing", 0))
    traveling_allowance = flt(get_traveling_allowance_value(assignment))
    other_allowance = flt(get_assignment_field_value(assignment, "custom_other_allowance", 0))

    monthly_total = calculate_monthly_total(
        basic_salary,
        housing_allowance,
        traveling_allowance,
        other_allowance
    )

    return {
        "basic": basic_salary,
        "housing": housing_allowance,
        "traveling": traveling_allowance,
        "other": other_allowance,
        "monthly_total": monthly_total,
    }


# =========================================
# الدالة الرئيسية لحساب راتب آخر شهر
# =========================================

def compute_last_month_prorated_salary(employee: str, join_date, relieving_date) -> dict:
    # هذه الدالة تحسب راتب آخر شهر بشكل نسبي حسب عدد الأيام المستحقة
    assignment = fetch_latest_salary_assignment(employee, relieving_date)

    if not assignment:
        frappe.throw(
            _("No Salary Structure Assignment found for this employee. Please go to Salary Structure Assignment and create one.")
        )

    breakdown = build_salary_breakdown(assignment)
    monthly_total = flt(breakdown.get("monthly_total"))
    currency = get_salary_assignment_currency(assignment)

    period_start_date = get_salary_period_start_date(join_date, relieving_date)
    month_days = date_utils.days_in_month(relieving_date)
    worked_days = date_utils.inclusive_days(period_start_date, relieving_date)
    daily_rate = calculate_daily_rate(monthly_total)

    amount = calculate_prorated_salary_amount(
        monthly_total,
        worked_days,
        month_days,
        daily_rate
    )

    return {
        "assignment_name": assignment.name,
        "currency": currency,
        "worked_days": flt(worked_days, 2),
        "daily_rate": flt(daily_rate, 2),
        "amount": flt(amount, 2),
        "breakdown": breakdown,
    }
