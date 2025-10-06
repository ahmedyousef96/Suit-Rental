import frappe
from frappe.utils import getdate

def execute(filters=None):
    if not filters:
        filters = {}

    date = getdate(filters.get("date"))
    branch_filter = filters.get("branch")

    data = []

    if branch_filter:
        branches = [{"name": branch_filter}]
    else:
        branches = frappe.get_all("Branch", fields=["name"])

    for b in branches:
        branch_name = b["name"]

        # Deliveries Due
        deliveries_due = frappe.db.count("Suit Reservation", {
            "branch": branch_name,
            "reservation_from": date,
            "docstatus": 1
        }, cache=False)

        delivered = frappe.db.count("Suit Reservation", {
            "branch": branch_name,
            "reservation_from": date,
            "reservation_status": "Delivered",
            "docstatus": 1
        }, cache=False)

        deliveries_pending = deliveries_due - delivered

        # Returns Due
        returns_due = frappe.db.count("Suit Reservation", {
            "branch": branch_name,
            "reservation_to": date,
            "docstatus": 1
        }, cache=False)

        returned = frappe.db.count("Suit Reservation", {
            "branch": branch_name,
            "reservation_to": date,
            "reservation_status": "Returned",
            "docstatus": 1
        }, cache=False)

        returns_pending = returns_due - returned

        # Active Reservations
        reserved = frappe.db.sql("""
            SELECT COUNT(*) FROM `tabSuit Reservation`
            WHERE branch = %s
            AND reservation_status = 'Reserved'
            AND %s BETWEEN reservation_from AND reservation_to
            AND docstatus = 1
        """, (branch_name, date))[0][0]

        # ? Make counts clickable links
        deliveries_link = f"<a href='/app/query-report/Deliveries%20Pending?date={date}&branch={branch_name}' target='_blank'>{deliveries_pending}</a>"
        returns_link = f"<a href='/app/query-report/Returns%20Pending?date={date}&branch={branch_name}' target='_blank'>{returns_pending}</a>"
        active_link = f"<a href='/app/query-report/Active%20Reservations?date={date}&branch={branch_name}' target='_blank'>{reserved}</a>"

        data.append({
            "branch": branch_name,
            "deliveries_pending": deliveries_link,
            "returns_pending": returns_link,
            "reserved": active_link
        })

    columns = [
        {"label": "Branch", "fieldname": "branch", "fieldtype": "Data", "width": 150},
        {"label": "Deliveries Pending", "fieldname": "deliveries_pending", "fieldtype": "Data", "width": 150},
        {"label": "Returns Pending", "fieldname": "returns_pending", "fieldtype": "Data", "width": 150},
        {"label": "Active Reservations", "fieldname": "reserved", "fieldtype": "Data", "width": 150},
    ]

    return columns, data
