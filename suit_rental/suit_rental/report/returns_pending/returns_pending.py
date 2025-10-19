import frappe
from frappe import _


def execute(filters=None):
	if not filters:
		filters = {}

	date = filters.get("date")
	branch = filters.get("branch")

	conditions = ["docstatus = 1"]
	params = {}

	if date:
		conditions.append("reservation_to = %(date)s")
		params["date"] = date
	if branch:
		conditions.append("branch = %(branch)s")
		params["branch"] = branch

	# Exclude already returned
	conditions.append("reservation_status != 'Returned'")

	condition_str = " AND ".join(conditions)

	data = frappe.db.sql(
		f"""
        SELECT
            name,
            customer_name,
            reservation_from,
            reservation_to,
            reservation_status,
            branch
        FROM `tabSuit Reservation`
        WHERE {condition_str}
        ORDER BY reservation_to
    """,
		params,
		as_dict=True,
	)

	columns = [
		{
			"label": _("Reservation"),
			"fieldname": "name",
			"fieldtype": "Link",
			"options": "Suit Reservation",
			"width": 150,
		},
		{"label": _("Customer"), "fieldname": "customer_name", "fieldtype": "Data", "width": 180},
		{"label": _("From"), "fieldname": "reservation_from", "fieldtype": "Date", "width": 120},
		{"label": _("To"), "fieldname": "reservation_to", "fieldtype": "Date", "width": 120},
		{"label": _("Status"), "fieldname": "reservation_status", "fieldtype": "Data", "width": 120},
		{"label": _("Branch"), "fieldname": "branch", "fieldtype": "Link", "options": "Branch", "width": 150},
	]

	return columns, data
