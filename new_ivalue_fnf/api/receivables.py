import frappe
from frappe.utils import flt

from . import employee_data


# =========================================
# أدوات مساعدة
# =========================================

def get_employee_company(employee):
    # جلب الشركة المرتبطة بالموظف مع التحقق من وجود الموظف
    employee_snapshot = employee_data.fetch_employee_snapshot(employee)

    if not employee_snapshot:
        frappe.throw("Employee not found.")

    return employee_snapshot.get("company")


def get_employee_advance_account(company):
    # جلب حساب السلف الافتراضي من الشركة بشكل دينمك
    return frappe.get_value("Company", company, "default_employee_advance_account")


def calculate_employee_advance_outstanding(advance_row):
    # حساب المبلغ المتبقي على سلفة الموظف بعد خصم المدفوع والمطالب به
    advance_amount = flt(advance_row.get("advance_amount"))
    paid_amount = flt(advance_row.get("paid_amount"))
    claimed_amount = flt(advance_row.get("claimed_amount"))

    outstanding_amount = advance_amount - paid_amount - claimed_amount

    return flt(outstanding_amount, 2)


def create_employee_advance_receivable_row(advance_name, account, outstanding_amount):
    # إنشاء سطر المطلوبات الخاص بسلفة الموظف
    return {
        "component": "Employee Advance",
        "reference_document_type": "Employee Advance",
        "reference_document": advance_name,
        "account": account,
        "amount": flt(outstanding_amount),
        "status": "Settled",
        "custom_number_of_days": 0,
    }


def get_submitted_employee_advances(employee):
    # جلب كل سلف الموظف المعتمدة من النظام
    return frappe.get_all(
        "Employee Advance",
        filters={
            "employee": employee,
            "docstatus": 1,
        },
        fields=[
            "name",
            "purpose",
            "advance_amount",
            "paid_amount",
            "claimed_amount",
            "status",
        ],
        order_by="posting_date desc",
    )


# =========================================
# بناء المطلوبات من سلف الموظف
# =========================================

def build_receivables_from_employee_advances(employee: str):
    # هذه الدالة تقوم بجلب سلف الموظف
    # ثم تحسب المبلغ المتبقي وتحوّله إلى سطور داخل جدول المطلوبات

    rows = []
    total_amount = 0.0

    company = get_employee_company(employee)
    account = get_employee_advance_account(company)
    employee_advances = get_submitted_employee_advances(employee)

    for advance_row in employee_advances:
        advance_name = advance_row.get("name")

        if not advance_name:
            continue

        outstanding_amount = calculate_employee_advance_outstanding(advance_row)

        if outstanding_amount <= 0:
            continue

<<<<<<< Updated upstream
        rows.append({
            "component": "Employee Advance",
            "reference_document_type": "Employee Advance",
            "reference_document": adv.name,
            "account": account,
            "amount": outstanding,
            "status": "Settled",
            "custom_number_of_days": 0,
        })
        total += outstanding

    return rows, flt(total, 2)  
=======
        receivable_row = create_employee_advance_receivable_row(
            advance_name=advance_name,
            account=account,
            outstanding_amount=outstanding_amount,
        )

        rows.append(receivable_row)
        total_amount = total_amount + outstanding_amount

    return rows, flt(total_amount, 2)
>>>>>>> Stashed changes
