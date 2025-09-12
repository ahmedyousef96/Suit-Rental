# Copyright (c) 2025, Ahmed Yousef and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, nowdate

@frappe.whitelist()
def get_customer_measurements(customer):
    """
    Fetch measurements from Customer Measurement Doctype
    if reservation_measurements table is empty.
    """
    if not customer:
        frappe.throw(_("Please select a Customer first"))

    # Get latest Customer Measurement for this customer
    cm_doc = frappe.get_all(
        "Customer Measurement",
        filters={"customer": customer},
        fields=["name"],
        order_by="creation desc",
        limit=1
    )

    if not cm_doc:
        frappe.throw(_("No Customer Measurement found for this customer"))

    cm_doc = frappe.get_doc("Customer Measurement", cm_doc[0].name)

    data = [
        {
            "measurement_type": row.measurement_type,
            "value": row.value,
            "uom": row.uom
        }
        for row in cm_doc.measurements
    ]

    # Display success message
    frappe.msgprint(
        msg=_("Measurements for customer {0} fetched successfully.").format(customer),
        title=_("Measurements Fetched"),
        indicator="green"
    )

    return data

@frappe.whitelist()
def check_availability(item_code, branch=None, warehouse=None, start_date=None, end_date=None):
    """
    Returns total stock, reserved quantity, available stock, and last 10 reservations that include this item.
    """
    if not item_code:
        frappe.throw(_("Item Code is required"))
    if not warehouse:
        frappe.throw(_("Warehouse is required"))
    if not start_date or not end_date:
        frappe.throw(_("Start Date and End Date are required"))

    # Total stock in the specified warehouse
    total_stock = frappe.db.get_value("Bin",
                                     {"item_code": item_code, "warehouse": warehouse},
                                     "actual_qty") or 0.0

    # Count reserved items during the specified period
    reserved_qty = frappe.db.sql("""
        SELECT SUM(ri.qty)
        FROM `tabSuit Reservation` sr
        JOIN `tabReservation Item` ri ON ri.parent = sr.name
        WHERE ri.item_code = %s
          AND sr.docstatus = 1
          AND sr.reservation_status NOT IN ('Cancelled', 'Returned')
          AND (
              (sr.reservation_from <= %s AND sr.reservation_to >= %s)
              OR (sr.reservation_from <= %s AND sr.reservation_to >= %s)
              OR (sr.reservation_from >= %s AND sr.reservation_to <= %s)
          )
    """, (item_code, start_date, start_date, end_date, end_date, start_date, end_date))[0][0] or 0

    available_stock = flt(total_stock) - flt(reserved_qty)

    # Last 10 reservations that include this item (most recent)
    last_10_reservations = frappe.db.sql("""
        SELECT sr.name as reservation_id, sr.customer, sr.reservation_from, sr.reservation_to, sr.reservation_status
        FROM `tabSuit Reservation` sr
        JOIN `tabReservation Item` ri ON ri.parent = sr.name
        WHERE ri.item_code = %s
          AND sr.docstatus = 1
          AND sr.reservation_status NOT IN ('Cancelled', 'Returned')
        ORDER BY sr.reservation_from DESC
        LIMIT 10
    """, (item_code,), as_dict=1) or []



    return {
        "total_stock": flt(total_stock),
        "reserved_qty": flt(reserved_qty),
        "available_stock": available_stock,
        "last_10_reservations": last_10_reservations
    }

@frappe.whitelist()
def deliver_reservation(name, delivery_date, mode_of_payment):
    """
    Deliver the reservation: Update status to 'Delivered', create Material Issue Stock Entry,
    create Payment Entry for remaining amount, create Journal Entry using Branch accounts,
    and store Payment Entry in reservation_payments.
    """
    doc = frappe.get_doc("Suit Reservation", name)
    if doc.docstatus != 1:
        frappe.throw(_("Reservation must be Submitted to deliver"))
    if doc.reservation_status != 'Reserved':
        frappe.throw(_("Reservation must be in 'Reserved' status to deliver"))
    if not doc.source_warehouse:
        frappe.throw(_("Source Warehouse is required for delivery"))
    if not doc.reservation_items or len(doc.reservation_items) == 0:
        frappe.throw(_("Reservation Items are required for delivery"))
    if not doc.branch:
        frappe.throw(_("Branch is required for delivery"))
    if not doc.currency:
        frappe.throw(_("Currency is required for delivery"))
    if not doc.company:
        frappe.throw(_("Company is required for delivery"))
    if not delivery_date:
        frappe.throw(_("Delivery Date is required"))
    if not mode_of_payment:
        frappe.throw(_("Mode of Payment is required for delivery"))

    # Get accounts from Branch
    branch = frappe.get_doc("Branch", doc.branch)
    if not branch.custom_receivable_account:
        frappe.throw(_("Receivable Account not defined in Branch"))
    if not branch.custom_income_account:
        frappe.throw(_("Income Account not defined in Branch"))

    # Recalculate total_estimated_rent and outstanding_amount
    total = 0
    for item in doc.reservation_items:
        if not item.item_code:
            frappe.throw(_("Item Code is missing in row {0}").format(item.idx))
        qty = flt(item.qty) or 0
        if qty <= 0:
            frappe.throw(_("Quantity must be greater than 0 in row {0}").format(item.idx))
        rate = flt(item.rate) or 0
        total += qty * rate
    doc.total_estimated_rent = total
    deposit = flt(doc.deposit_amount) or 0
    paid = flt(doc.paid_amount) or 0
    doc.outstanding_amount = total - (deposit + paid)

    # Create Stock Entry for Material Issue
    se = frappe.new_doc("Stock Entry")
    se.stock_entry_type = 'Material Issue'
    se.company = doc.company
    se.posting_date = delivery_date
    se.currency = doc.currency
    for item in doc.reservation_items:
        se.append("items", {
            "item_code": item.item_code,
            "qty": item.qty,
            "uom": item.uom or "Nos",
            "s_warehouse": doc.source_warehouse
        })
    se.insert()
    se.submit()

    # Create Journal Entry for the financial transaction
    if total > 0:
        je = frappe.new_doc("Journal Entry")
        je.posting_date = delivery_date
        je.company = doc.company
        je.voucher_type = "Journal Entry"
        je.reference_type = "Suit Reservation"
        je.reference_name = doc.name

        # Debit Receivable Account
        je.append("accounts", {
            "account": branch.custom_receivable_account,
            "party_type": "Customer",
            "party": doc.customer,
            "debit_in_account_currency": total,
            "credit_in_account_currency": 0
        })

        # Credit Income Account
        je.append("accounts", {
            "account": branch.custom_income_account,
            "debit_in_account_currency": 0,
            "credit_in_account_currency": total
        })

        je.insert()
        je.submit()

        # Create Payment Entry for remaining amount
        remaining_amount = total - deposit
        if remaining_amount > 0:
            pe = frappe.new_doc("Payment Entry")
            pe.payment_type = "Receive"
            pe.party_type = "Customer"
            pe.party = doc.customer
            pe.paid_amount = remaining_amount
            pe.received_amount = remaining_amount
            pe.company = doc.company
            pe.posting_date = nowdate()
            pe.currency = doc.currency
            pe.paid_from = branch.custom_receivable_account
            pe.paid_to = branch.custom_bank_account
            pe.paid_from_account_currency = doc.currency
            pe.paid_to_account_currency = doc.currency
            pe.mode_of_payment = mode_of_payment
            pe.reference_no = doc.name
            pe.reference_date = nowdate()
            pe.insert()
            pe.submit()

            doc.append("reservation_payments", {
                "payment_entry": pe.name
            })
            doc.paid_amount = total  # Full amount paid (deposit + remaining)
        else:
            doc.paid_amount = deposit  # Only deposit was paid

        doc.outstanding_amount = 0  # Reset after payment

    # Update reservation status, delivery date, and stock entry
    doc.reservation_status = 'Delivered'
    doc.actual_delivery_date = delivery_date
    doc.stock_entry_delivery = se.name
    doc.journal_entry = je.name
    doc.save(ignore_permissions=True)

    # Display success message
    frappe.msgprint(
        msg=_("Reservation {0} has been successfully delivered on {1}.").format(name, delivery_date),
        title=_("Delivery Successful"),
        indicator="green"
    )

    return True

@frappe.whitelist()
def return_reservation(name, return_date):
    """
    Return the reservation: Update status to 'Returned' and create Material Receipt Stock Entry.
    """
    doc = frappe.get_doc("Suit Reservation", name)
    if doc.docstatus != 1:
        frappe.throw(_("Reservation must be Submitted to return"))
    if doc.reservation_status != 'Delivered':
        frappe.throw(_("Reservation must be in 'Delivered' status to return"))
    if not doc.source_warehouse:
        frappe.throw(_("Source Warehouse is required for return"))
    if not doc.reservation_items or len(doc.reservation_items) == 0:
        frappe.throw(_("Reservation Items are required for return"))
    if not doc.currency:
        frappe.throw(_("Currency is required for return"))
    if not doc.company:
        frappe.throw(_("Company is required for return"))
    if not return_date:
        frappe.throw(_("Return Date is required"))

    # Create Stock Entry for Material Receipt
    se = frappe.new_doc("Stock Entry")
    se.stock_entry_type = 'Material Receipt'
    se.company = doc.company
    se.posting_date = return_date
    se.currency = doc.currency
    for item in doc.reservation_items:
        if not item.item_code:
            frappe.throw(_("Item Code is missing in row {0}").format(item.idx))
        qty = flt(item.qty) or 0
        if qty <= 0:
            frappe.throw(_("Quantity must be greater than 0 in row {0}").format(item.idx))
        se.append("items", {
            "item_code": item.item_code,
            "qty": item.qty,
            "uom": item.uom or "Nos",
            "t_warehouse": doc.source_warehouse
        })
    se.insert()
    se.submit()

    # Update reservation status, return date, and stock entry
    doc.reservation_status = 'Returned'
    doc.actual_return_date = return_date
    doc.stock_entry_return = se.name
    doc.save(ignore_permissions=True)

    # Display success message
    frappe.msgprint(
        msg=_("Reservation {0} has been successfully returned on {1}.").format(name, return_date),
        title=_("Return Successful"),
        indicator="green"
    )

    return True