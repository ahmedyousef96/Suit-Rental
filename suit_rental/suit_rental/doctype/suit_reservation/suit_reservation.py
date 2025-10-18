# Copyright (c) 2025, Ahmed Yousef and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, nowdate

class SuitReservation(Document):
    def before_submit(self):
        """Set reservation_status and create Payment Entry for deposit if applicable."""
        self.reservation_status = 'Reserved'
        if self.deposit_amount and self.deposit_amount > 0:
            if not self.mode_of_payment:
                frappe.throw(_("Mode of Payment is required for deposit payment"))
            if not self.company:
                frappe.throw(_("Company is required for deposit payment"))
            if not self.currency:
                frappe.throw(_("Currency is required for deposit payment"))
            if not self.customer:
                frappe.throw(_("Customer is required for deposit payment"))
            if not self.branch:
                frappe.throw(_("Branch is required for deposit payment"))

            # Get accounts from Branch
            branch = frappe.get_doc("Branch", self.branch)
            if not branch.custom_receivable_account:
                frappe.throw(_("Receivable Account not defined in Branch"))
            if not branch.custom_bank_account:
                frappe.throw(_("Bank Account not defined in Branch"))

            # Create Payment Entry for deposit
            pe = frappe.new_doc("Payment Entry")
            pe.payment_type = "Receive"
            pe.party_type = "Customer"
            pe.party = self.customer
            pe.paid_amount = self.deposit_amount
            pe.received_amount = self.deposit_amount
            pe.company = self.company
            pe.posting_date = nowdate()
            pe.currency = self.currency
            pe.paid_from = branch.custom_receivable_account
            pe.paid_to = branch.custom_bank_account
            pe.paid_from_account_currency = self.currency
            pe.paid_to_account_currency = self.currency
            pe.mode_of_payment = self.mode_of_payment
            pe.reference_no = self.name
            pe.reference_date = nowdate()
            pe.insert()
            pe.submit()

           
            self.append("reservation_payments", {
                "payment_entry": pe.name
            })
            self.paid_amount = self.deposit_amount
            self.outstanding_amount = flt(self.total_estimated_rent) - flt(self.deposit_amount)
           

            # Save the document to persist reservation_payments
            #self.save(ignore_permissions=True)

        # Display confirmation message
        frappe.msgprint(
            msg=_("Reservation {0} has been successfully submitted with status '{1}'.").format(self.name, self.reservation_status),
            title=_("Submission Successful"),
            indicator="green"
        )

    def cancel_related_records(self):
        """
        Cancel related Stock Entries, Payment Entries, and Journal Entry when Suit Reservation is canceled.
        """
        #frappe.log_error(f"Before cancel: reservation_payments for {self.name}: {self.reservation_payments}")

        # Cancel Stock Entry for delivery
        if self.stock_entry_delivery:
            se_delivery = frappe.get_doc("Stock Entry", self.stock_entry_delivery)
            if se_delivery.docstatus == 1:
                se_delivery.cancel()

        # Cancel Stock Entry for return
        if self.stock_entry_return:
            se_return = frappe.get_doc("Stock Entry", self.stock_entry_return)
            if se_return.docstatus == 1:
                se_return.cancel()

        # Cancel Payment Entries
        if self.reservation_payments:
            for payment in self.reservation_payments:
                if payment.payment_entry:
                    pe = frappe.get_doc("Payment Entry", payment.payment_entry)
                    if pe.docstatus == 1:
                        pe.cancel()

        # Cancel Journal Entry
        if self.journal_entry:
            je = frappe.get_doc("Journal Entry", self.journal_entry)
            if je.docstatus == 1:
                je.cancel()

        #frappe.log_error(f"After cancel: reservation_payments for {self.name}: {self.reservation_payments}")

    def before_cancel(self):
        """
        Hook to update reservation status before Suit Reservation is canceled.
        """
        self.reservation_status = 'Cancelled'
        # Display confirmation message
        frappe.msgprint(
            msg=_("Reservation {0} has been successfully cancelled.").format(self.name),
            title=_("Cancellation Successful"),
            indicator="red"
        )

    def on_cancel(self):
        """
        Hook to handle cancellation of related records after Suit Reservation is canceled.
        """
        self.cancel_related_records()
        