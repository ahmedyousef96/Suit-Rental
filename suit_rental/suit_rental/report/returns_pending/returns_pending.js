frappe.query_reports["Returns Pending"] = {
    "filters": [
        {
            "fieldname": "date",
            "label": __("Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.get_today()
        },
        {
            "fieldname": "branch",
            "label": __("Branch"),
            "fieldtype": "Link",
            "options": "Branch"
        }
    ]
};
