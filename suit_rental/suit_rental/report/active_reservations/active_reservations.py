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
		conditions.append("%(date)s = reservation_date")
		params["date"] = date
	if branch:
		conditions.append("branch = %(branch)s")
		params["branch"] = branch

	# Only active reservations
	conditions.append("reservation_status = 'Reserved'")

	condition_str = " AND ".join(conditions)

	data = frappe.db.sql(
		f"""
        SELECT
            name,
            customer_name,
            mobile_number,
            reservation_date,
            reservation_from,
            reservation_to,
            reservation_status,
            total_estimated_rent,
            deposit_amount,
            branch
        FROM `tabSuit Reservation`
        WHERE {condition_str}
        ORDER BY reservation_from
    """,
		params,
		as_dict=True,
	)

	columns = [
		{"label": _("Branch"), "fieldname": "branch", "fieldtype": "Link", "options": "Branch", "width": 180},
		{
			"label": _("Reservation"),
			"fieldname": "name",
			"fieldtype": "Link",
			"options": "Suit Reservation",
			"width": 180,
		},
		{"label": _("Customer Name"), "fieldname": "customer_name", "fieldtype": "Data", "width": 200},
		{"label": _("Customer Mobile"), "fieldname": "mobile_number", "fieldtype": "Data", "width": 180},
		{"label": _("Reservation Date"), "fieldname": "reservation_date", "fieldtype": "Date", "width": 150},
		{
			"label": _("Total Value"),
			"fieldname": "total_estimated_rent",
			"fieldtype": "Currency",
			"width": 140,
		},
		{"label": _("Deposit Amount"), "fieldname": "deposit_amount", "fieldtype": "Currency", "width": 140},
	]

	return columns, data
