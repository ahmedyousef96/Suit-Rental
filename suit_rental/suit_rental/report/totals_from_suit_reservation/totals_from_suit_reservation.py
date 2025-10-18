import frappe
from frappe import _


def execute(filters=None):
	filters = filters or {}
	columns = get_columns()
	data = get_data(filters)

	chart = get_chart(data)

	return columns, data, None, chart


def get_columns():
	return [
		{"label": _("Branch"), "fieldname": "branch", "fieldtype": "Link", "options": "Branch", "width": 180},
		{
			"label": _("Total Sales"),
			"fieldname": "total_sales",
			"fieldtype": "Currency",
			"width": 160,
			"options": "currency",
		},
		{
			"label": _("Deposit Amount"),
			"fieldname": "deposit_amount_total",
			"fieldtype": "Currency",
			"width": 160,
			"options": "currency",
		},
		{
			"label": _("Outstanding Amount"),
			"fieldname": "outstanding_total",
			"fieldtype": "Currency",
			"width": 160,
			"options": "currency",
		},
		{
			"label": _("Count of Transactions"),
			"fieldname": "transaction_count",
			"fieldtype": "Int",
			"width": 180,
		},
	]


def get_data(filters):
	conditions = ["docstatus = 1"]

	if filters.get("from_date"):
		conditions.append("reservation_date >= %(from_date)s")
	if filters.get("to_date"):
		conditions.append("reservation_date <= %(to_date)s")
	if filters.get("branch"):
		conditions.append("branch = %(branch)s")

	condition_str = " AND ".join(conditions)

	query = f"""
        SELECT
            branch,
            SUM(COALESCE(total_estimated_rent, 0)) AS total_sales,
            SUM(COALESCE(deposit_amount, 0)) AS deposit_amount_total,
            SUM(COALESCE(outstanding_amount, 0)) AS outstanding_total,
            COUNT(*) AS transaction_count
        FROM `tabSuit Reservation`
        WHERE {condition_str}
        GROUP BY branch
        ORDER BY SUM(COALESCE(total_estimated_rent, 0)) DESC
    """

	return frappe.db.sql(query, filters, as_dict=True)


def get_chart(data):
	if not data:
		return None

	labels = [d["branch"] for d in data]
	sales = [d["total_sales"] for d in data]

	return {
		"data": {"labels": labels, "datasets": [{"name": _("Total Sales"), "values": sales}]},
		"type": "pie",
		"colors": ["#5E64FF", "#FFB822", "#36B37E", "#F66D44", "#A3A0FB"],
	}
