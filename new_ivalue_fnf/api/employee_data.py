# # =========================================
# # MASTER DATA
# # =========================================

# import frappe


# # =========================================
# # أدوات مساعدة عامة
# # =========================================

# def get_single_value(doctype, name, fieldname):
#     # جلب قيمة واحدة من قاعدة البيانات
#     if not doctype:
#         return None

#     if not name:
#         return None

#     if not fieldname:
#         return None

#     return frappe.db.get_value(doctype, name, fieldname)


# def get_cached_document(doctype, name):
#     # جلب المستند من الكاش لتحسين الأداء
#     if not doctype:
#         return None

#     if not name:
#         return None

#     return frappe.get_cached_doc(doctype, name)


# def get_first_available_field_value(doc, fieldnames):
#     # البحث عن أول حقل يحتوي على قيمة ضمن قائمة حقول
#     if not doc:
#         return None

#     for fieldname in fieldnames:
#         if hasattr(doc, fieldname):
#             value = getattr(doc, fieldname)

#             if value:
#                 return value

#     return None


# # =========================================
# # بيانات الموظف
# # =========================================

# def fetch_employee_snapshot(employee_id: str) -> dict:
#     # جلب بيانات الموظف الأساسية لاستخدامها في الحسابات
#     employee_data = frappe.db.get_value(
#         "Employee",
#         employee_id,
#         [
#             "name",
#             "employee_name",
#             "company",
#             "department",
#             "designation",
#             "date_of_joining",
#             "relieving_date",
#             "employment_type",
            
#         ],
#         as_dict=True,
#     )

#     if not employee_data:
#         return {}

#     return employee_data


# def fetch_employee_salary_currency(employee: str) -> str | None:
#     # جلب عملة راتب الموظف
#     if not employee:
#         return None

#     return get_single_value(
#         "Employee",
#         employee,
#         "salary_currency"
#     )


# # =========================================
# # بيانات الشركة
# # =========================================

# def fetch_company_currency(company: str) -> str | None:
#     # جلب العملة الافتراضية للشركة
#     if not company:
#         return None

#     return get_single_value(
#         "Company",
#         company,
#         "default_currency"
#     )


# def fetch_company_payable_account(company: str) -> str | None:
#     # جلب حساب المستحقات الخاص بالشركة بشكل دينمك
#     if not company:
#         return None

#     company_doc = get_cached_document("Company", company)

#     if not company_doc:
#         return None

#     candidate_fields = [
#         "default_payroll_payable_account",
#         "payroll_payable_account",
#         "default_payable_account",
#     ]

#     payable_account = get_first_available_field_value(
#         company_doc,
#         candidate_fields
#     )

#     return payable_account
# =========================================
# MASTER DATA
# =========================================

import frappe


# =========================================
# أدوات مساعدة عامة
# =========================================

def get_single_value(doctype, name, fieldname):
    # جلب قيمة واحدة من قاعدة البيانات
    if not doctype:
        return None

    if not name:
        return None

    if not fieldname:
        return None

    return frappe.db.get_value(doctype, name, fieldname)


def get_cached_document(doctype, name):
    # جلب المستند من الكاش لتحسين الأداء
    if not doctype:
        return None

    if not name:
        return None

    return frappe.get_cached_doc(doctype, name)


def get_first_available_field_value(doc, fieldnames):
    # البحث عن أول حقل يحتوي على قيمة ضمن قائمة حقول
    if not doc:
        return None

    for fieldname in fieldnames:
        if hasattr(doc, fieldname):
            value = getattr(doc, fieldname)

            if value:
                return value

    return None


# =========================================
# بيانات الموظف
# =========================================

def fetch_employee_snapshot(employee_id: str) -> dict:
    # جلب بيانات الموظف الأساسية لاستخدامها في الحسابات
    employee_data = frappe.db.get_value(
        "Employee",
        employee_id,
        [
            "name",
            "employee_name",
            "company",
            "department",
            "designation",
            "date_of_joining",
            "relieving_date",
            "employment_type",
        ],
        as_dict=True,
    )

    if not employee_data:
        return {}

    return employee_data


def fetch_employee_salary_currency(employee: str) -> str | None:
    # جلب عملة راتب الموظف
    if not employee:
        return None

    return get_single_value(
        "Employee",
        employee,
        "salary_currency"
    )


# =========================================
# بيانات الشركة
# =========================================

def fetch_company_currency(company: str) -> str | None:
    # جلب العملة الافتراضية للشركة
    if not company:
        return None

    return get_single_value(
        "Company",
        company,
        "default_currency"
    )


def fetch_company_country(company: str) -> str | None:
    # جلب دولة الشركة
    if not company:
        return None

    return get_single_value(
        "Company",
        company,
        "country"
    )


def fetch_company_payable_account(company: str) -> str | None:
    # جلب حساب المستحقات الخاص بالشركة بشكل دينمك
    if not company:
        return None

    company_doc = get_cached_document("Company", company)

    if not company_doc:
        return None

    candidate_fields = [
        "default_payroll_payable_account",
        "payroll_payable_account",
        "default_payable_account",
    ]

    payable_account = get_first_available_field_value(
        company_doc,
        candidate_fields
    )

    return payable_account