import frappe
from frappe.utils import getdate, flt, nowdate

from . import employee_data
from . import service_time
from . import receivables
from . import payables
from . import leaves
from . import salary
from . import additional_salary
from . import gratuity

# =========================================
# أدوات مساعدة عامة
# =========================================

def set_transaction_date(doc, method=None):
    # تعيين تاريخ الحركة تلقائياً إذا كان الحقل فارغ
    if not doc.transaction_date:
        doc.transaction_date = nowdate()


<<<<<<< Updated upstream
def has_only_default_placeholder_rows(doc) -> bool:
    placeholder_payables = {"Gratuity", "Expense Claim", "Bonus", "Leave Encashment"}
    placeholder_receivables = {"Employee Advance"}
=======
def get_placeholder_payable_components():
    # إرجاع أسماء السطور الافتراضية الخاصة بالمستحقات
    return {
        "Gratuity",
        "Expense Claim",
        "Bonus",
        "Leave Encashment",
    }


def get_placeholder_receivable_components():
    # إرجاع أسماء السطور الافتراضية الخاصة بالمطلوبات على الموظف
    return {
        "Employee Advance",
        "Loan",
    }


def row_is_placeholder(row, allowed_components):
    # التحقق هل السطر الحالي مجرد سطر افتراضي فارغ
    component = row.get("component")
    reference_document = row.get("reference_document")
    amount = flt(row.get("amount"))

    if component not in allowed_components:
        return False
>>>>>>> Stashed changes

    if reference_document:
        return False

    if amount != 0:
        return False

    return True


def all_rows_are_placeholder(rows, allowed_components):
    # التحقق هل كل السطور الموجودة عبارة عن placeholder فقط
    if not rows:
        return True

    for row in rows:
        if not row_is_placeholder(row, allowed_components):
            return False

    return True


def has_only_default_placeholder_rows(doc) -> bool:
    # التحقق هل المستند يحتوي فقط على السطور الافتراضية الابتدائية
    payables_rows = doc.get("payables") or []
    receivables_rows = doc.get("receivables") or []

    if not payables_rows and not receivables_rows:
        return False

    placeholder_payables = get_placeholder_payable_components()
    placeholder_receivables = get_placeholder_receivable_components()

    payables_are_placeholder = all_rows_are_placeholder(
        payables_rows,
        placeholder_payables
    )

    receivables_are_placeholder = all_rows_are_placeholder(
        receivables_rows,
        placeholder_receivables
    )

    if payables_are_placeholder and receivables_are_placeholder:
        return True

    return False


def should_rebuild_fnf(doc) -> bool:
    # تحديد هل يجب إعادة بناء البيانات داخل مستند المخالصة
    if doc.docstatus != 0:
        return False

    if not doc.employee:
        return False

    if not doc.relieving_date:
        return False

    old_doc = doc.get_doc_before_save()

    # أول حفظ للمستند
    if not old_doc:
        return True

    # إذا كانت السطور الحالية مجرد سطور افتراضية
    if has_only_default_placeholder_rows(doc):
        return True

    # إذا تغير الموظف
    if old_doc.employee != doc.employee:
        return True

    # إذا تغير تاريخ آخر يوم عمل
    if str(old_doc.relieving_date) != str(doc.relieving_date):
        return True

    return False


def get_final_date(relieving_date, employee_snapshot):
    # إرجاع تاريخ آخر يوم عمل من القيمة المرسلة أو من الموظف
    final_date = getdate(relieving_date or employee_snapshot.get("relieving_date"))

    if not final_date:
        frappe.throw("Relieving Date is required.")

    return final_date


def get_join_date(employee_snapshot):
    # إرجاع تاريخ مباشرة الموظف مع التحقق من وجوده
    join_date = employee_snapshot.get("date_of_joining")

    if not join_date:
        frappe.throw("Employee Date of Joining is missing.")

    return join_date


def get_letter_head(company):
    # جلب الترويسة الافتراضية الخاصة بالشركة
    return frappe.db.get_value(
        "Company",
        company,
        "default_letter_head"
    )


def get_currency(employee_snapshot, salary_data):
    # تحديد العملة بشكل دينمك من بيانات الراتب ثم من الشركة
    currency = salary_data.get("currency")

    if currency:
        return currency

    company = employee_snapshot.get("company")
    currency = employee_data.fetch_company_currency(company)

    if currency:
        return currency

    frappe.throw(
        "Salary Currency is missing in Salary Structure Assignment, Salary Structure, and Company."
    )


def calculate_leaves_balance(leave_rows):
    # جمع رصيد الإجازات القابل للتسوية
    total_balance = 0.0

    for row in leave_rows:
        total_balance = total_balance + flt(row.get("balance"))

    return total_balance


def build_salary_summary(salary_info):
    # تجهيز ملخص الراتب بالشكل المطلوب للواجهة
    breakdown = salary_info.get("breakdown") or {}

    return {
        "basic_salary": flt(breakdown.get("basic"), 2),
        "housing": flt(breakdown.get("housing"), 2),
        "transportation": flt(breakdown.get("traveling"), 2),
        "other_allowance": flt(breakdown.get("other"), 2),
        "monthly_gross_salary": flt(breakdown.get("monthly_total"), 2),
        "daily_rate": flt(salary_info.get("daily_rate"), 6),
        "worked_days": flt(salary_info.get("worked_days"), 1),
        "prorated_amount": flt(salary_info.get("amount"), 2),
    }


def build_service_summary(service_data):
    # تجهيز ملخص مدة الخدمة
    return {
        "years": service_data.get("years", 0),
        "months": service_data.get("months", 0),
        "days": service_data.get("days", 0),
        "total_years": service_data.get("total_years", 0),
    }


def build_totals_summary(total_payables, total_receivables, total_assets_cost):
    # تجهيز الإجماليات النهائية
    return {
        "total_payable_amount": flt(total_payables, 2),
        "total_receivable_amount": flt(total_receivables, 2),
        "total_asset_recovery_cost": flt(total_assets_cost, 2),
    }


def set_field_value_if_exists(doc, fieldname, value):
    # تعبئة الحقل فقط إذا كان موجوداً داخل الدوكتايب
    if hasattr(doc, fieldname):
        setattr(doc, fieldname, value)


def clear_child_tables(doc):
    # مسح الجداول قبل إعادة تعبئتها
    doc.set("payables", [])
    doc.set("receivables", [])
    doc.set("assets_allocated", [])

    if hasattr(doc, "custom_carry_forward_leaves"):
        doc.set("custom_carry_forward_leaves", [])


def build_financial_row_for_doc(row):
    # تجهيز سطر جدول المستحقات أو المطلوبات قبل إضافته للمستند
    return {
        "component": row.get("component"),
        "reference_document_type": row.get("reference_document_type"),
        "reference_document": row.get("reference_document"),
        "account": row.get("account"),
        "amount": row.get("amount"),
        "status": row.get("status") or "Settled",
        "custom_number_of_days": row.get("custom_number_of_days"),
    }


def append_financial_rows(doc, table_name, rows):
    # إضافة السطور المالية للمستند مع تجاهل السطور التي قيمتها صفر أو أقل
    for row in rows:
        amount = flt(row.get("amount"))

        if amount <= 0:
            continue

        prepared_row = build_financial_row_for_doc(row)
        doc.append(table_name, prepared_row)


def append_carry_forward_leave_rows(doc, leave_rows):
    # إضافة جدول الإجازات المرحلة إذا كان الجدول موجوداً
    if not hasattr(doc, "custom_carry_forward_leaves"):
        return

    for row in leave_rows:
        doc.append("custom_carry_forward_leaves", {
            "leave_type": row.get("leave_type"),
            "earned": row.get("earned"),
            "taken": row.get("taken"),
            "balance": row.get("balance"),
            "allocation_ref": row.get("allocation_ref"),
        })


def set_standard_employee_fields(doc, employee_snapshot):
    # تعبئة الحقول الأساسية الخاصة بالموظف
    set_field_value_if_exists(doc, "employee_name", employee_snapshot.get("employee_name"))
    set_field_value_if_exists(doc, "company", employee_snapshot.get("company"))
    set_field_value_if_exists(doc, "department", employee_snapshot.get("department"))
    set_field_value_if_exists(doc, "designation", employee_snapshot.get("designation"))
    set_field_value_if_exists(doc, "date_of_joining", employee_snapshot.get("date_of_joining"))


def set_custom_summary_fields(doc, data, salary_data):
    # تعبئة الحقول المخصصة الخاصة بملخص الراتب والعملة والترويسة
    set_field_value_if_exists(doc, "custom_company_currency", data.get("company_currency"))
    set_field_value_if_exists(doc, "custom_letter_head", data.get("letter_head"))
    set_field_value_if_exists(doc, "custom_basic_salary", salary_data.get("basic_salary", 0))
    set_field_value_if_exists(doc, "custom_housing", salary_data.get("housing", 0))
    set_field_value_if_exists(doc, "custom_transportation", salary_data.get("transportation", 0))
    set_field_value_if_exists(doc, "custom_other_allowances", salary_data.get("other_allowance", 0))
    set_field_value_if_exists(doc, "custom_monthly_gross_salary", salary_data.get("monthly_gross_salary", 0))
    set_field_value_if_exists(doc, "custom_work_days", data.get("relieving_month_days", 0))
    set_field_value_if_exists(doc, "custom_leaves_balanced", data.get("leaves_balanced", 0))
    set_field_value_if_exists(doc, "custom_leaves_amount", data.get("leaves_amount", 0))


def set_service_fields(doc, service_data):
    # تعبئة الحقول الخاصة بمدة خدمة الموظف
    set_field_value_if_exists(doc, "custom_service_years", service_data.get("years", 0))
    set_field_value_if_exists(doc, "custom_service_month", service_data.get("months", 0))
    set_field_value_if_exists(doc, "custom_service_days", service_data.get("days", 0))
    set_field_value_if_exists(doc, "custom_total_of_years", service_data.get("total_years", 0))


def set_total_fields(doc, totals_data):
    # تعبئة الحقول النهائية الخاصة بالإجماليات
    set_field_value_if_exists(
        doc,
        "total_payable_amount",
        totals_data.get("total_payable_amount", 0)
    )
    set_field_value_if_exists(
        doc,
        "total_receivable_amount",
        totals_data.get("total_receivable_amount", 0)
    )
    set_field_value_if_exists(
        doc,
        "total_asset_recovery_cost",
        totals_data.get("total_asset_recovery_cost", 0)
    )


def force_rows_status_to_settled(rows):
    # فرض حالة جميع السطور على Settled
    for row in rows or []:
        row.status = "Settled"


# =========================================
# الواجهة البرمجية الرئيسية
# =========================================

@frappe.whitelist()
def get_full_and_final_data(employee: str, relieving_date=None):
    # هذه الدالة الرئيسية ترجع كل بيانات المخالصة الجاهزة للعرض أو التعبئة
    employee_snapshot = employee_data.fetch_employee_snapshot(employee)

    if not employee_snapshot:
        frappe.throw("Employee not found.")

    company = employee_snapshot.get("company")
    letter_head = get_letter_head(company)
    join_date = get_join_date(employee_snapshot)
    final_date = get_final_date(relieving_date, employee_snapshot)

    salary_info = salary.compute_last_month_prorated_salary(
        employee,
        join_date,
        final_date
    )

<<<<<<< Updated upstream
    currency = salary_info.get("currency")
    if not currency:
        currency = employee_data.fetch_company_currency(emp.get("company"))

    if not currency:
        frappe.throw("Salary Currency is missing in Salary Structure Assignment and Company.")

    payable_account = employee_data.fetch_company_payable_account(emp.get("company"))
=======
    currency = get_currency(employee_snapshot, salary_info)
    payable_account = employee_data.fetch_company_payable_account(company)

    leave_rows = leaves.compute_carry_forward_leave_rows(
        employee,
        join_date,
        final_date
    )
>>>>>>> Stashed changes

    service_data = service_time.compute_service_period(join_date, final_date)
    

    payables_rows, total_payables = payables.build_payables_rows(
        salary_info,
        leave_rows,
        payable_account
    )
    

    expense_claim_rows, total_expense_claims = payables.build_payables_from_expense_claims(
        employee,
        payable_account
    )
  
    

    for row in expense_claim_rows:
        payables_rows.append(row)

    total_payables = total_payables + total_expense_claims

    receivables_rows, total_receivables = receivables.build_receivables_from_employee_advances(
        employee
    )
    # =========================================
    # GRATUITY (ERPNext)
    # =========================================

    gratuity_doc = gratuity.create_gratuity_document(
    employee,
    payable_account=payable_account
)

    if gratuity_doc:
        gratuity_row = gratuity.build_payable_row_from_gratuity_doc(gratuity_doc)

    if gratuity_row:
        payables_rows.append(gratuity_row)
        total_payables = total_payables + gratuity_doc.amount
 
  

    # =========================================
    # Additional Salary
    # =========================================

    additional_payables, additional_receivables, add_pay_total, add_rec_total = additional_salary.build_rows_from_additional_salary(
        employee,
        final_date,
        payable_account
    )

    for row in additional_payables:
        payables_rows.append(row)

    total_payables = total_payables + add_pay_total

    for row in additional_receivables:
        receivables_rows.append(row)

    total_receivables = total_receivables + add_rec_total

    # حالياً لا يوجد احتساب للأصول
    assets_rows = []
    total_assets_cost = 0.0

    leaves_balance = calculate_leaves_balance(leave_rows)
    leave_amount = flt(leaves_balance * salary_info.get("daily_rate"), 2)

    salary_summary = build_salary_summary(salary_info)
    service_summary = build_service_summary(service_data)
    totals_summary = build_totals_summary(
        total_payables,
        total_receivables,
        total_assets_cost
    )
    
    return {
        "ok": True,
        "company_currency": currency,
        "letter_head": letter_head,
        "employee": employee_snapshot,
        "salary": salary_summary,
        "relieving_month_days": flt(salary_info.get("worked_days")),
        "service": service_summary,
        "payables": payables_rows,
        "receivables": receivables_rows,
        "assets_allocated": assets_rows,
        "carry_forward_leaves": leave_rows,
        "totals": totals_summary,
        "leaves_balanced": flt(leaves_balance, 2),
        "leaves_amount": flt(leave_amount, 2),
    }


# =========================================
# تعبئة مستند المخالصة
# =========================================

def populate_full_and_final_doc(doc, method=None):
    # تعبئة مستند المخالصة تلقائياً عند الإنشاء أو التعديل إذا تحقق شرط إعادة البناء
    if not should_rebuild_fnf(doc):
        return

    data = get_full_and_final_data(
        employee=doc.employee,
        relieving_date=doc.relieving_date
    )

    if not data:
        return

    if not data.get("ok"):
        return

    employee_snapshot = data.get("employee") or {}
    salary_data = data.get("salary") or {}
    service_data = data.get("service") or {}
    totals_data = data.get("totals") or {}

    set_standard_employee_fields(doc, employee_snapshot)
    set_custom_summary_fields(doc, data, salary_data)
    set_service_fields(doc, service_data)

    clear_child_tables(doc)

    append_financial_rows(doc, "payables", data.get("payables") or [])
    append_financial_rows(doc, "receivables", data.get("receivables") or [])
    append_carry_forward_leave_rows(doc, data.get("carry_forward_leaves") or [])

<<<<<<< Updated upstream
    if hasattr(doc, "custom_service_days"):
        doc.custom_service_days = service_data.get("days", 0)

    if hasattr(doc, "custom_total_of_years"):
        doc.custom_total_of_years = service_data.get("total_years", 0)

    # clear tables
    doc.set("payables", [])
    doc.set("receivables", [])
    doc.set("assets_allocated", [])

    if hasattr(doc, "custom_carry_forward_leaves"):
        doc.set("custom_carry_forward_leaves", [])

    # fill payables
    for row in data.get("payables") or []:
        doc.append("payables", {
            "component": row.get("component"),
            "reference_document_type": row.get("reference_document_type"),
            "reference_document": row.get("reference_document"),
            "account": row.get("account"),
            "amount": row.get("amount"),
            "status": row.get("status") or "Settled",
            "custom_number_of_days": (
                row.get("custom_number_of_days")
                or row.get("days")
                or row.get("day_count")
                or 0
            ),
        })

    # fill receivables
    for row in data.get("receivables") or []:
        doc.append("receivables", {
            "component": row.get("component"),
            "reference_document_type": row.get("reference_document_type"),
            "reference_document": row.get("reference_document"),
            "account": row.get("account"),
            "amount": row.get("amount"),
            "status": row.get("status") or "Settled",
            "custom_number_of_days": (
                row.get("custom_number_of_days")
                or row.get("days")
                or row.get("day_count")
                or 0
            ),
        })

    # carry forward leaves
    if hasattr(doc, "custom_carry_forward_leaves"):
        for row in data.get("carry_forward_leaves") or []:
            doc.append("custom_carry_forward_leaves", {
                "leave_type": row.get("leave_type"),
                "earned": row.get("earned"),
                "taken": row.get("taken"),
                "balance": row.get("balance"),
                "allocation_ref": row.get("allocation_ref"),
            })

    # totals
    if hasattr(doc, "total_payable_amount"):
        doc.total_payable_amount = totals_data.get("total_payable_amount", 0)

    if hasattr(doc, "total_receivable_amount"):
        doc.total_receivable_amount = totals_data.get("total_receivable_amount", 0)

    if hasattr(doc, "total_asset_recovery_cost"):
        doc.total_asset_recovery_cost = totals_data.get("total_asset_recovery_cost", 0)

    # force status
    for row in doc.payables or []:
        row.status = "Settled"
=======
    set_total_fields(doc, totals_data)
>>>>>>> Stashed changes

    force_rows_status_to_settled(doc.payables)
    force_rows_status_to_settled(doc.receivables)