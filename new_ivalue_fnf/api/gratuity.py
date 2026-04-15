# =========================================
# GRATUITY
# =========================================

import frappe
from frappe.utils import nowdate


# =========================================
# أدوات مساعدة
# =========================================

def get_employee_doc(employee):
    # جلب مستند الموظف
    if not employee:
        return None

    return frappe.get_cached_doc("Employee", employee)


def get_company_country(company):
    # جلب دولة الشركة
    if not company:
        return None

    return frappe.db.get_value("Company", company, "country")


def get_default_gratuity_rule():
    # جلب أول قاعدة مكافأة متاحة
    return frappe.db.get_value("Gratuity Rule", {}, "name")


# =========================================
# التحقق من الأهلية
# =========================================

def is_employee_eligible(employee):
    # التحقق من أهلية الموظف للمكافأة
    employee_doc = get_employee_doc(employee)

    if not employee_doc:
        return False

    if not employee_doc.company:
        return False

    if employee_doc.employment_type != "Permanent":
        return False

    company_country = get_company_country(employee_doc.company)

    if company_country != "Saudi Arabia":
        return False

    return True


# =========================================
# إنشاء مستند المكافأة
# =========================================

def create_gratuity_document(employee, full_and_final=None, payable_account=None):
    if not is_employee_eligible(employee):
        return None

    employee_doc = get_employee_doc(employee)
    gratuity_rule = get_default_gratuity_rule()

    if not gratuity_rule:
        frappe.throw("No Gratuity Rule found.")

    # 🔥 جلب حساب المصروف (اختياري)
    expense_account = frappe.db.get_value(
        "Company",
        employee_doc.company,
        "default_expense_account"
    )

    gratuity_doc = frappe.get_doc({
        "doctype": "Gratuity",
        "employee": employee,
        "company": employee_doc.company,
        "gratuity_rule": gratuity_rule,
        "posting_date": nowdate(),

        "payable_account": payable_account,
        "expense_account": expense_account,

        "custom_full_and_final_statement": full_and_final,
    })

    gratuity_doc.insert(ignore_permissions=True)

    return gratuity_doc
# =========================================
# تجهيز سطر المستحقات
# =========================================

def build_payable_row_from_gratuity_doc(gratuity_doc):
    # تحويل مستند المكافأة إلى سطر داخل Payables
    if not gratuity_doc:
        return None

    return {
        "component": "Gratuity",
        "reference_document_type": "Gratuity",
        "reference_document": gratuity_doc.name,
        "account": gratuity_doc.payable_account,
        "amount": gratuity_doc.amount,
        "status": "Settled",
        "custom_number_of_days": 0,
    }