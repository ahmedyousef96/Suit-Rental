# Copyright (c) 2025, Ahmed Yousef and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, nowdate, get_datetime, now_datetime


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
        limit=1,
    )

    if not cm_doc:
        frappe.throw(_("No Customer Measurement found for this customer"))

    cm_doc = frappe.get_doc("Customer Measurement", cm_doc[0].name)

    data = [
        {"measurement_type": row.measurement_type, "value": row.value, "uom": row.uom}
        for row in cm_doc.measurements
    ]

    # Display success message
    frappe.msgprint(
        msg=_("Measurements for customer {0} fetched successfully.").format(customer),
        title=_("Measurements Fetched"),
        indicator="green",
    )

    return data


@frappe.whitelist()
def check_availability(
    item_code, branch=None, warehouse=None, start_date=None, end_date=None
):
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
    total_stock = (
        frappe.db.get_value(
            "Bin", {"item_code": item_code, "warehouse": warehouse}, "actual_qty"
        )
        or 0.0
    )

    # Count reserved items during the specified period
    reserved_qty = (
        frappe.db.sql(
            """
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
    """,
            (
                item_code,
                start_date,
                start_date,
                end_date,
                end_date,
                start_date,
                end_date,
            ),
        )[0][0]
        or 0
    )

    available_stock = flt(total_stock) - flt(reserved_qty)

    # Last 10 reservations that include this item (most recent)
    last_10_reservations = (
        frappe.db.sql(
            """
        SELECT sr.name as reservation_id, sr.customer, sr.reservation_from, sr.reservation_to, sr.reservation_status
        FROM `tabSuit Reservation` sr
        JOIN `tabReservation Item` ri ON ri.parent = sr.name
        WHERE ri.item_code = %s
          AND sr.docstatus = 1
          AND sr.reservation_status NOT IN ('Cancelled', 'Returned')
        ORDER BY sr.reservation_from DESC
        LIMIT 10
    """,
            (item_code,),
            as_dict=1,
        )
        or []
    )

    return {
        "total_stock": flt(total_stock),
        "reserved_qty": flt(reserved_qty),
        "available_stock": available_stock,
        "last_10_reservations": last_10_reservations,
    }

# Deliver Items
@frappe.whitelist()
def deliver_reservation(name, delivery_date, mode_of_payment):

    doc = frappe.get_doc("Suit Reservation", name)

    # -----------------------------
    # Basic Validations
    # -----------------------------
    if doc.docstatus != 1:
        frappe.throw(_("Reservation must be Submitted to deliver"))

    if doc.reservation_status != "Reserved":
        frappe.throw(_("Reservation must be in 'Reserved' status to deliver"))

    if not doc.source_warehouse:
        frappe.throw(_("Source Warehouse is required for delivery"))

    if not doc.reservation_items:
        frappe.throw(_("Reservation Items are required for delivery"))

    if not doc.company:
        frappe.throw(_("Company is required for delivery"))

    if not doc.currency:
        frappe.throw(_("Currency is required for delivery"))

    if not delivery_date:
        frappe.throw(_("Delivery Date is required for delivery"))

    delivery_dt = get_datetime(delivery_date)
    delivery_date_only = delivery_dt.date()
    delivery_time_only = delivery_dt.time()

    reservation_dt = get_datetime(doc.reservation_date)

    if delivery_dt <= reservation_dt:
        frappe.throw(_("Delivery date & time must be after reservation date & time"))

    if not mode_of_payment:
        frappe.throw(_("Mode of Payment is required for delivery"))

    if not doc.customer_stock_warehouse:
        frappe.throw(_("Customer Stock Warehouse must be set before delivery"))

    if not doc.branch:
        frappe.throw(_("Branch is required for delivery"))

    # -----------------------------
    # Load Branch & Posting Settings
    # -----------------------------
    branch = frappe.get_doc("Branch", doc.branch)

    income_posting_type = (branch.custom_post_income_as or "Journal Entry").strip()
    si_status = (branch.custom_sales_invoice_status or "Submit").strip()
    je_status = (branch.custom_journal_entry_status or "Submit").strip()

    # -----------------------------
    # Resolve Mode of Payment Account
    # -----------------------------
    mop_account = frappe.db.get_value(
        "Mode of Payment Account",
        {"parent": mode_of_payment, "company": doc.company},
        "default_account",
    )

    if not mop_account:
        frappe.throw(
            _("No account found for Mode of Payment: {0}").format(mode_of_payment)
        )

    # -----------------------------
    # Validate Items + Calculate Rent
    # -----------------------------
    total_rent = 0

    for item in doc.reservation_items:
        if not item.item_code:
            frappe.throw(_("Item Code is missing in row {0}").format(item.idx))

        if flt(item.qty) != 1:
            frappe.throw(_("Quantity must be 1 in row {0}.").format(item.idx))

        if item.has_serial_no and not item.serial_no:
            frappe.throw(
                _("Serial No is required for item {0} in row {1}").format(
                    item.item_code, item.idx
                )
            )

        if item.has_batch_no and not item.batch_no:
            frappe.throw(
                _("Batch No is required for item {0} in row {1}").format(
                    item.item_code, item.idx
                )
            )

        total_rent += flt(item.rate)

    deposit_paid = flt(doc.deposit_amount)
    already_paid = flt(doc.paid_amount)
    doc.total_estimated_rent = total_rent
    doc.outstanding_amount = total_rent - (deposit_paid + already_paid)

    # -----------------------------
    # STOCK TRANSFER (Branch -> Customer Stock)
    # -----------------------------
    se = frappe.new_doc("Stock Entry")
    se.stock_entry_type = "Material Transfer"
    se.company = doc.company
    se.posting_date = delivery_date_only
    se.posting_time = delivery_time_only
    se.set_posting_time = 1

    for item in doc.reservation_items:
        row = {
            "item_code": item.item_code,
            "qty": 1,
            "uom": item.uom or "Nos",
            "s_warehouse": doc.source_warehouse,
            "t_warehouse": doc.customer_stock_warehouse,
            "use_serial_batch_fields": 1,
        }

        if item.serial_no:
            row["serial_no"] = item.serial_no
        if item.batch_no:
            row["batch_no"] = item.batch_no

        se.append("items", row)

    se.flags.ignore_mandatory = True
    se.insert()
    se.submit()

    for item in doc.reservation_items:
        item.is_delivered = 1

    # Track Stock Entry in child table
    doc.append(
        "reservation_stock_entries",
        {
            "stock_entry": se.name,
            "entry_type": "Delivery",
            "posting_date": delivery_dt,
            "remark": "Stock moved to customer stock warehouse",
        },
    )
    

    # -----------------------------
    # SECURITY PAYMENT
    # -----------------------------
    security_amount = flt(doc.security_amount)
    force_collect_security = bool(doc.force_collect_security_amount)

    if force_collect_security and security_amount <= 0:
        frappe.throw(_("Security Amount is required when forced."))

    if force_collect_security and security_amount > 0:
        pe_sec = frappe.new_doc("Payment Entry")
        pe_sec.payment_type = "Receive"
        pe_sec.party_type = "Customer"
        pe_sec.party = doc.customer
        pe_sec.company = doc.company
        pe_sec.posting_date = delivery_date_only
        pe_sec.currency = doc.currency
        pe_sec.paid_to = mop_account
        pe_sec.mode_of_payment = mode_of_payment
        pe_sec.paid_amount = security_amount
        pe_sec.received_amount = security_amount
        pe_sec.reference_no = doc.name
        pe_sec.reference_date = delivery_date_only
        
        pe_sec.flags.ignore_mandatory = True

        pe_sec.insert()
        pe_sec.submit()

        doc.append(
            "reservation_payments",
            {
                "payment_entry": pe_sec.name,
                "payment_mode": mode_of_payment,
                "amount": security_amount,
                "description": "Security Payment",
                "type": "Receive",
            },
        )

    # -----------------------------
    # RENT INCOME POSTING
    # -----------------------------
    rent_invoice_doc = None

    # Journal Entry Method
    if income_posting_type == "Journal Entry":
        je = frappe.new_doc("Journal Entry")
        je.company = doc.company
        je.posting_date = delivery_date_only
        je.voucher_type = "Journal Entry"
        je.user_remark = "Suit Reservation"
        je.cheque_no = doc.name

        je.append(
            "accounts",
            {
                "account": branch.custom_receivable_account,
                "party_type": "Customer",
                "party": doc.customer,
                "debit_in_account_currency": total_rent,
            },
        )

        je.append(
            "accounts",
            {
                "account": branch.custom_income_account,
                "credit_in_account_currency": total_rent,
            },
        )

        je.flags.ignore_mandatory = True
        je.insert()

        if je_status == "Submit":
            je.submit()

        doc.append(
            "reservation_journal_entry",
            {
                "journal_entry": je.name,
                "date": delivery_dt,
                "purpose": "Rent",
                "amount": total_rent,
            },
        )

    # Sales Invoice Method
    else:
        if not branch.custom_rent_invoice_item:
            frappe.throw(_("Rent Invoice Item must be defined in Branch"))

        si = frappe.new_doc("Sales Invoice")
        si.customer = doc.customer
        si.company = doc.company
        si.posting_date = delivery_date_only
        si.posting_time = delivery_time_only
        si.due_date = delivery_date_only
        si.currency = doc.currency
        si.ignore_pricing_rule = 1
        si.set_posting_time = 1

        si.append(
            "items",
            {
                "item_code": branch.custom_rent_invoice_item,
                "qty": 1,
                "rate": total_rent,
            },
        )

        si.flags.ignore_mandatory = True
        si.insert()  # draft first

        # Add Deposit Payment as advance (if exists)
        for pay in doc.reservation_payments:
            if pay.description == "Deposit Payment" and pay.payment_entry:
                pe_remarks = (
                    frappe.db.get_value("Payment Entry", pay.payment_entry, "remarks")
                    or ""
                )
                pe_paid_amount = flt(
                    frappe.db.get_value(
                        "Payment Entry", pay.payment_entry, "paid_amount"
                    )
                    or 0
                )

                if pe_paid_amount:
                    si.append(
                        "advances",
                        {
                            "reference_type": "Payment Entry",
                            "reference_name": pay.payment_entry,
                            "advance_amount": pe_paid_amount,
                            "allocated_amount": pe_paid_amount,
                            "remarks": pe_remarks,
                            "difference_posting_date": si.posting_date,
                        },
                    )

        si.save()
        rent_invoice_doc = si

    # -----------------------------
    # REMAINING RENT PAYMENT
    # -----------------------------
    remaining_rent = total_rent - deposit_paid

    if remaining_rent > 0:
        pe_rent = frappe.new_doc("Payment Entry")
        pe_rent.payment_type = "Receive"
        pe_rent.party_type = "Customer"
        pe_rent.party = doc.customer
        pe_rent.company = doc.company
        pe_rent.posting_date = delivery_date_only
        pe_rent.currency = doc.currency
        pe_rent.mode_of_payment = mode_of_payment
        pe_rent.paid_to = mop_account
        pe_rent.paid_amount = remaining_rent
        pe_rent.received_amount = remaining_rent
        pe_rent.reference_no = doc.name
        pe_rent.reference_date = delivery_date_only
        
        pe_rent.flags.ignore_mandatory = True

        pe_rent.insert()
        pe_rent.submit()

        doc.append(
            "reservation_payments",
            {
                "payment_entry": pe_rent.name,
                "payment_mode": mode_of_payment,
                "amount": remaining_rent,
                "description": "Remaining Rent Payment",
                "type": "Receive",
            },
        )

        # If we used Sales Invoice, add Remaining Rent as advance too
        if rent_invoice_doc:
            pe_remarks = pe_rent.remarks or ""
            rent_invoice_doc.append(
                "advances",
                {
                    "reference_type": "Payment Entry",
                    "reference_name": pe_rent.name,
                    "advance_amount": remaining_rent,
                    "allocated_amount": remaining_rent,
                    "remarks": pe_remarks,
                    "difference_posting_date": rent_invoice_doc.posting_date,
                },
            )
            rent_invoice_doc.save()

        doc.paid_amount = total_rent
    else:
        doc.paid_amount = deposit_paid

    doc.outstanding_amount = 0

    # -----------------------------
    # FINALIZE SALES INVOICE (if used)
    # -----------------------------
    if rent_invoice_doc:
        if si_status == "Submit":
            rent_invoice_doc.submit()

        doc.append(
            "reservation_sales_invoice",
            {
                "sales_invoice": rent_invoice_doc.name,
                "date": delivery_dt,
                "purpose": "Rent",
                "amount": total_rent,
            },
        )

    # -----------------------------
    # FINAL UPDATE
    # -----------------------------
    doc.reservation_status = "Delivered"
    doc.actual_delivery_date = delivery_dt

    doc.save(ignore_permissions=True)

    frappe.msgprint(
        msg=_("Reservation {0} has been successfully delivered.").format(name),
        title=_("Delivery Successful"),
        indicator="green",
    )

    return True


## Return API


@frappe.whitelist()
def return_reservation(name, actual_return_datetime):

    doc = frappe.get_doc("Suit Reservation", name)

    # -----------------------------
    # Load Branch & Posting Settings
    # -----------------------------
    branch = frappe.get_doc("Branch", doc.branch)

    income_posting_type = (branch.custom_post_income_as or "Journal Entry").strip()
    si_status = (branch.custom_sales_invoice_status or "Submit").strip()
    je_status = (branch.custom_journal_entry_status or "Submit").strip()

    # -------------------------------------------------
    # BASIC VALIDATIONS
    # -------------------------------------------------
    if doc.docstatus != 1:
        frappe.throw(_("Reservation must be Submitted"))

    if doc.reservation_status != "Delivered":
        frappe.throw(_("Reservation must be in Delivered status"))

    if not actual_return_datetime:
        frappe.throw(_("Return Date & Time is required"))

    if not doc.actual_delivery_date:
        frappe.throw(_("Delivery Date & Time is missing"))

    return_dt = get_datetime(actual_return_datetime)
    delivery_dt = get_datetime(doc.actual_delivery_date)

    if return_dt <= delivery_dt:
        frappe.throw(_("Return date & time must be after delivery date & time"))

    if not doc.reservation_items:
        frappe.throw(_("No reservation items found"))

    # -------------------------------------------------
    # VALIDATE ITEMS
    # -------------------------------------------------
    total_penalty = 0
    penalty_items = []

    for item in doc.reservation_items:

        if not item.return_status:
            frappe.throw(_("Return Status is required for all items"))

        if not item.return_type:
            frappe.throw(_("Return Type is missing in row {0}").format(item.idx))

        penalty_amount = flt(item.penalty_amount)

        if item.return_type in ("Damage", "Lost") and penalty_amount > 0:
            total_penalty += penalty_amount
            penalty_items.append(item)

    # -------------------------------------------------
    # STOCK ENTRIES
    # -------------------------------------------------
    # 1) GOOD - Transfer back to Branch Store
    # 2) DAMAGE - Transfer to Damage Warehouse
    # 3) LOST - Material Issue from Customer Stock

    for item in doc.reservation_items:

        # -------- GOOD --------
        if item.return_type == "Good":

            se = frappe.new_doc("Stock Entry")
            se.stock_entry_type = "Material Transfer"
            se.company = doc.company
            se.posting_date = return_dt.date()
            se.posting_time = return_dt.time()
            se.set_posting_time = 1

            se.append(
                "items",
                {
                    "item_code": item.item_code,
                    "qty": 1,
                    "uom": item.uom or "Nos",
                    "s_warehouse": doc.customer_stock_warehouse,
                    "t_warehouse": doc.source_warehouse,
                    "use_serial_batch_fields": 1,
                    "serial_no": item.serial_no or "",
                    "batch_no": item.batch_no or "",
                },
            )

            se.flags.ignore_mandatory = True
            se.insert()
            se.submit()

            doc.append(
                "reservation_stock_entries",
                {
                    "stock_entry": se.name,
                    "entry_type": "Return - Good",
                    "posting_date": return_dt,
                    "remark": "Returned to branch warehouse",
                },
            )

        # -------- DAMAGE --------
        elif item.return_type == "Damage":

            status = frappe.get_doc("Suit Return Status", item.return_status)

            se = frappe.new_doc("Stock Entry")
            se.stock_entry_type = "Material Transfer"
            se.company = doc.company
            se.posting_date = return_dt.date()
            se.posting_time = return_dt.time()
            se.set_posting_time = 1

            se.append(
                "items",
                {
                    "item_code": item.item_code,
                    "qty": 1,
                    "uom": item.uom or "Nos",
                    "s_warehouse": doc.customer_stock_warehouse,
                    "t_warehouse": status.damage_warehouse,
                    "use_serial_batch_fields": 1,
                    "serial_no": item.serial_no or "",
                    "batch_no": item.batch_no or "",
                },
            )

            se.flags.ignore_mandatory = True
            se.insert()
            se.submit()

            doc.append(
                "reservation_stock_entries",
                {
                    "stock_entry": se.name,
                    "entry_type": "Return - Damage",
                    "posting_date": return_dt,
                    "remark": "Moved to damage warehouse",
                },
            )

        # -------- LOST --------
        elif item.return_type == "Lost":

            se = frappe.new_doc("Stock Entry")
            se.stock_entry_type = "Material Issue"
            se.company = doc.company
            se.posting_date = return_dt.date()
            se.posting_time = return_dt.time()
            se.set_posting_time = 1

            se.append(
                "items",
                {
                    "item_code": item.item_code,
                    "qty": 1,
                    "uom": item.uom or "Nos",
                    "s_warehouse": doc.customer_stock_warehouse,
                    "use_serial_batch_fields": 1,
                    "serial_no": item.serial_no or "",
                    "batch_no": item.batch_no or "",
                },
            )

            se.flags.ignore_mandatory = True
            se.insert()
            se.submit()

            doc.append(
                "reservation_stock_entries",
                {
                    "stock_entry": se.name,
                    "entry_type": "Return - Lost",
                    "posting_date": return_dt,
                    "remark": "Item lost by customer",
                },
            )

    for item in doc.reservation_items:
        item.is_returned = 1

    # -------------------------------------------------
    # PENALTY ACCOUNTING (ONLY IF > 0)
    # -------------------------------------------------
    if total_penalty > 0:

        # -------- JOURNAL ENTRY --------
        if income_posting_type == "Journal Entry":
            je = frappe.new_doc("Journal Entry")
            je.company = doc.company
            je.posting_date = return_dt.date()
            je.posting_time = return_dt.time()
            je.set_posting_time = 1
            je.voucher_type = "Journal Entry"
            je.user_remark = "Suit Return Penalty"
            je.cheque_no = doc.name

            je.append(
                "accounts",
                {
                    "account": branch.custom_receivable_account,
                    "party_type": "Customer",
                    "party": doc.customer,
                    "debit_in_account_currency": total_penalty,
                },
            )

            je.append(
                "accounts",
                {
                    "account": branch.custom_income_account,
                    "credit_in_account_currency": total_penalty,
                },
            )

            je.flags.ignore_mandatory = True
            je.insert()

            if je_status == "Submit":
                je.submit()

            doc.append(
                "reservation_journal_entry",
                {
                    "journal_entry": je.name,
                    "date": return_dt,
                    "purpose": "Return Penalty",
                    "amount": total_penalty,
                },
            )

        # -------- SALES INVOICE --------
        else:

            si = frappe.new_doc("Sales Invoice")
            si.customer = doc.customer
            si.company = doc.company
            si.posting_date = return_dt.date()
            si.posting_time = return_dt.time()
            si.set_posting_time = 1
            si.ignore_pricing_rule = 1
            si.currency = doc.currency

            for item in penalty_items:
                status = frappe.get_doc("Suit Return Status", item.return_status)

                si.append(
                    "items",
                    {
                        "item_code": status.income_item,
                        "qty": 1,
                        "rate": item.penalty_amount,
                    },
                )

            si.flags.ignore_mandatory = True
            si.insert()

            if si_status == "Submit":
                si.submit()

            doc.append(
                "reservation_sales_invoice",
                {
                    "sales_invoice": si.name,
                    "date": return_dt,
                    "purpose": "Return Penalty",
                    "amount": total_penalty,
                },
            )

    # -------------------------------------------------
    # FINAL UPDATE
    # -------------------------------------------------
    doc.reservation_status = "Returned"
    doc.actual_return_date = return_dt

    doc.save(ignore_permissions=True)

    frappe.msgprint(
        _("Reservation {0} has been successfully returned").format(doc.name),
        indicator="green",
    )

    return True
