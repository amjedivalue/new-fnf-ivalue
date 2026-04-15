import frappe
# Get Full and Final Settings (Single Doctype)





def get_fnf_settings():
    print("Return Full and Final Settings")
    return frappe.get_single("Full and Final Settings")
