
frappe.ui.form.on("Full and Final Statement", {
  onload(frm) {
    if (!frm.doc.transaction_date) {
      frm.set_value("transaction_date", frappe.datetime.get_today());
    }

    clear_placeholder_rows(frm);
  },

  refresh(frm) {
    clear_placeholder_rows(frm);
  
    // =========================================================
    // زر مباشر لفتح الاعدادات
    // =========================================================

    var button = frm.add_custom_button(
      "Settings",
      function() {
        frappe.set_route("Form", "Full and Final Settings");
      }
    );

<<<<<<< Updated upstream
  employee(frm) {
=======
   
    button.prepend('<i class="fa fa-cog"></i> ');

  
  
  },
employee(frm) {
  if (!frm.doc.employee) {
    clear_employee_related_data(frm);
    return;
  }

  clear_placeholder_rows(frm);

  setTimeout(() => {
>>>>>>> Stashed changes
    clear_placeholder_rows(frm);
  },

  relieving_date(frm) {
    clear_placeholder_rows(frm);
  },

  validate(frm) {
    clear_placeholder_rows(frm);
  }
});

function clear_placeholder_rows(frm) {
  const payablePlaceholders = new Set([
    "Gratuity",
    "Expense Claim",
    "Bonus",
    "Leave Encashment"
  ]);

<<<<<<< Updated upstream
  const receivablePlaceholders = new Set([
    "Employee Advance"
  ]);

=======
// Full and Final button
function clear_placeholder_rows(frm) {
>>>>>>> Stashed changes
  frm.doc.payables = (frm.doc.payables || []).filter((row) => {
    const isPlaceholder =
      payablePlaceholders.has(row.component) &&
      !row.reference_document &&
      Number(row.amount || 0) === 0;

    return !isPlaceholder;
  });

  frm.doc.receivables = (frm.doc.receivables || []).filter((row) => {
    const isPlaceholder =
      receivablePlaceholders.has(row.component) &&
      !row.reference_document &&
      Number(row.amount || 0) === 0;

    return !isPlaceholder;
  });

  frm.refresh_field("payables");
  frm.refresh_field("receivables");
}

function add_settings_button(frm) {

}