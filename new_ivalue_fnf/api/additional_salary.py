import frappe
from frappe.utils import flt


# =========================================
# أدوات مساعدة
# =========================================

def get_additional_salary_records(employee, end_date):
    # جلب كل Additional Salary الخاصة بالموظف حتى تاريخ معين

    records = frappe.get_all(
        "Additional Salary",
        filters={
            "employee": employee,
            "docstatus": 1,
            "payroll_date": ["<=", end_date],
        },
        fields=[
            "name",
            "salary_component",
            "amount",
            "payroll_date",
        ],
        order_by="payroll_date desc"
    )

    return records


def get_salary_component_type(component_name):
    # تحديد نوع Salary Component (Earning أو Deduction)

    if not component_name:
        return None

    component_type = frappe.get_value(
        "Salary Component",
        component_name,
        "type"
    )

    return component_type


def create_additional_salary_row(component, document_name, account, amount):
    # إنشاء سطر موحد للاستخدام داخل الجداول

    return {
        "component": component,
        "reference_document_type": "Additional Salary",
        "reference_document": document_name,
        "account": account,
        "amount": flt(amount),
        "status": "Settled",
        "custom_number_of_days": 0,
    }


# =========================================
# الدالة الرئيسية
# =========================================

def build_rows_from_additional_salary(employee, end_date, account):
    # هذه الدالة:
    # - تجلب Additional Salary
    # - تفرق بين Earning و Deduction
    # - ترجع سطور payables و receivables

    payables_rows = []
    receivables_rows = []

    total_payables = 0.0
    total_receivables = 0.0

    records = get_additional_salary_records(employee, end_date)

    for record in records:

        component = record.get("salary_component")
        amount = flt(record.get("amount"))
        document_name = record.get("name")

        if not component:
            continue

        if not document_name:
            continue

        if amount <= 0:
            continue

        component_type = get_salary_component_type(component)

        # =========================================
        # إذا Earning → Payables
        # =========================================
        if component_type == "Earning":

            row = create_additional_salary_row(
                component,
                document_name,
                account,
                amount
            )

            payables_rows.append(row)
            total_payables = total_payables + amount

        # =========================================
        # إذا Deduction → Receivables
        # =========================================
        if component_type == "Deduction":

            row = create_additional_salary_row(
                component,
                document_name,
                account,
                amount
            )

            receivables_rows.append(row)
            total_receivables = total_receivables + amount

    return (
        payables_rows,
        receivables_rows,
        flt(total_payables, 2),
        flt(total_receivables, 2)
    )