import frappe
from frappe.utils import flt


# =========================================
# أدوات مساعدة
# =========================================

def create_payable_row(
    component,
    reference_document_type,
    reference_document,
    account,
    amount,
    status,
    number_of_days
):
    # إنشاء سطر مستحقات بشكل موحد لتقليل التكرار
    return {
        "component": component,
        "reference_document_type": reference_document_type,
        "reference_document": reference_document,
        "account": account,
        "amount": amount,
        "status": status,
        "custom_number_of_days": number_of_days,
    }


def is_positive_amount(value):
    # التحقق أن القيمة أكبر من صفر
    amount = flt(value)

    if amount > 0:
        return True

    return False


# =========================================
# بناء سطور المستحقات من الراتب والإجازات
# =========================================

def build_payables_rows(salary_info, leave_rows, payable_account):
    # هذه الدالة تقوم ببناء جميع سطور المستحقات:
    # - راتب الأيام
    # - بدل الإجازات المرحلة

    rows = []
    total_amount = 0.0

    salary_amount = flt(salary_info.get("amount"))
    worked_days = flt(salary_info.get("worked_days"), 2)

    # =========================================
    # سطر راتب الأيام
    # =========================================
    if is_positive_amount(salary_amount):
        salary_row = create_payable_row(
            component="Salary days",
            reference_document_type="Salary Structure Assignment",
            reference_document=salary_info.get("assignment_name"),
            account=payable_account,
            amount=salary_amount,
            status="Settled",
            number_of_days=flt(worked_days, 2),
        )

        rows.append(salary_row)
        total_amount = total_amount + salary_amount

    # =========================================
    # سطور الإجازات
    # =========================================
    daily_rate = flt(salary_info.get("daily_rate"))

    for leave_row in leave_rows:
        leave_days = flt(leave_row.get("balance"), 2)
        leave_amount = flt(leave_days * daily_rate, 2)

        if leave_days <= 0:
            continue

        if leave_amount <= 0:
            continue

        leave_payable_row = create_payable_row(
            component=leave_row.get("leave_type"),
            reference_document_type="Leave Allocation",
            reference_document=leave_row.get("allocation_ref"),
            account=payable_account,
            amount=leave_amount,
            status="Settled",
            number_of_days=flt(leave_days, 2),
        )

        rows.append(leave_payable_row)
        total_amount = total_amount + leave_amount

    return rows, flt(total_amount, 2)


# =========================================
# بناء سطور المستحقات من Expense Claim
# =========================================

def build_payables_from_expense_claims(employee: str, account: str | None = None):
    # هذه الدالة تقوم بجلب المطالبات (Expense Claim)
    # وتحويلها إلى سطور مستحقات داخل المخالصة

    rows = []
    total_amount = 0.0

    claims = frappe.get_all(
        "Expense Claim",
        filters={
            "employee": employee,
            "docstatus": 1,
            "status": ["!=", "Paid"],
        },
        fields=[
            "name",
            "total_sanctioned_amount",
            "status",
        ],
        order_by="modified desc",
    )

    for claim in claims:
        amount = flt(claim.get("total_sanctioned_amount"))

        if not is_positive_amount(amount):
            continue

        expense_row = create_payable_row(
            component="Expense Claim",
            reference_document_type="Expense Claim",
            reference_document=claim.get("name"),
            account=account,
            amount=amount,
            status=claim.get("status") or "Unsettled",
            number_of_days=0,
        )

        rows.append(expense_row)
        total_amount = total_amount + amount

    return rows, flt(total_amount, 2)