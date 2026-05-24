import frappe


def execute():
    fnf_names = frappe.get_all(
        "Full and Final Statement",
        filters={
            "docstatus": 0,
        },
        pluck="name",
        order_by="creation asc",
    )

    updated_count = 0
    skipped_count = 0
    failed_count = 0

    for docname in fnf_names:
        try:
            doc = frappe.get_doc("Full and Final Statement", docname)

            if not doc.employee:
                skipped_count += 1
                print(
                    "Skipped Full and Final Statement {0}: Employee is missing.".format(
                        docname
                    )
                )
                continue

            if not doc.relieving_date:
                skipped_count += 1
                print(
                    "Skipped Full and Final Statement {0}: Relieving Date is missing.".format(
                        docname
                    )
                )
                continue

            # Saving triggers validate hook and rebuilds FNF rows.
            doc.save(ignore_permissions=True)

            gratuity_account = None

            for row in doc.payables or []:
                if (
                    row.reference_document_type == "Employee"
                    and row.component != "Article 77 Compensation"
                    and row.account
                ):
                    gratuity_account = row.account
                    break

            if gratuity_account:
                changed = False

                for row in doc.payables or []:
                    if row.component == "Article 77 Compensation":
                        if row.account != gratuity_account:
                            row.account = gratuity_account
                            changed = True

                if changed:
                    doc.save(ignore_permissions=True)

            updated_count += 1

            print(
                "Full and Final Statement {0} has been updated successfully.".format(
                    docname
                )
            )

        except Exception:
            failed_count += 1

            frappe.log_error(
                title="Draft FNF Rebuild Failed - {0}".format(docname),
                message=frappe.get_traceback(),
            )

            print(
                "Failed to update Full and Final Statement {0}. Check Error Log.".format(
                    docname
                )
            )

    print(
        "Draft Full and Final Statement update completed. Updated: {0}, Skipped: {1}, Failed: {2}.".format(
            updated_count,
            skipped_count,
            failed_count,
        )
    )