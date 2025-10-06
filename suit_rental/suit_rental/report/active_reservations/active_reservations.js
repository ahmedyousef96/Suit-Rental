frappe.query_reports["Active Reservations"] = {
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
