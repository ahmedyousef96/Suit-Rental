import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, nowdate


class SuitReservation(Document):
	def before_submit(self):
		"""Set reservation_status and create Payment Entry for deposit if applicable."""
		self.reservation_status = "Reserved"

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

			# Load Branch
			branch = frappe.get_doc("Branch", self.branch)
			if not branch.custom_receivable_account:
				frappe.throw(_("Receivable Account not defined in Branch"))

			# Resolve Mode of Payment Account
			mop_account = frappe.db.get_value(
				"Mode of Payment Account",
				{"parent": self.mode_of_payment, "company": self.company},
				"default_account",
			)
			if not mop_account:
				frappe.throw(_("No account configured in Mode of Payment: {0}").format(self.mode_of_payment))

			# Create Payment Entry (Deposit)
			pe = frappe.new_doc("Payment Entry")
			pe.payment_type = "Receive"
			pe.party_type = "Customer"
			pe.party = self.customer
			pe.company = self.company
			pe.posting_date = nowdate()
			pe.currency = self.currency

			pe.paid_from = branch.custom_receivable_account
			pe.paid_to = mop_account
			pe.paid_from_account_currency = self.currency
			pe.paid_to_account_currency = self.currency

			pe.mode_of_payment = self.mode_of_payment
			pe.reference_no = self.name
			pe.reference_date = nowdate()

			pe.paid_amount = self.deposit_amount
			pe.received_amount = self.deposit_amount

			pe.flags.ignore_mandatory = True
			pe.insert()
			pe.submit()

			self.append(
				"reservation_payments",
				{
					"payment_entry": pe.name,
					"description": "Deposit Payment",
					"payment_mode": pe.mode_of_payment,
					"amount": pe.paid_amount,
					"type": "Receive",
				},
			)

			self.paid_amount = self.deposit_amount
			self.outstanding_amount = flt(self.total_estimated_rent) - flt(self.deposit_amount)

		frappe.msgprint(
			msg=_("Reservation {0} has been successfully submitted with status '{1}'.").format(
				self.name, self.reservation_status
			),
			title=_("Submission Successful"),
			indicator="green",
		)

	def cancel_related_records(self):
		"""Cancel Stock Entries, Payment Entries, Journal Entries, and Sales Invoices."""

		# Cancel Delivery Stock Entry
		if self.stock_entry_delivery:
			se_delivery = frappe.get_doc("Stock Entry", self.stock_entry_delivery)
			if se_delivery.docstatus == 1:
				se_delivery.cancel()

		# Cancel Return Stock Entry
		if self.stock_entry_return:
			se_return = frappe.get_doc("Stock Entry", self.stock_entry_return)
			if se_return.docstatus == 1:
				se_return.cancel()

		# Cancel Payment Entries
		if self.reservation_payments:
			for row in self.reservation_payments:
				if row.payment_entry:
					pe = frappe.get_doc("Payment Entry", row.payment_entry)
					if pe.docstatus == 1:
						pe.cancel()

		# Cancel Journal Entries (child table)
		if hasattr(self, "reservation_journal_entry"):
			for row in self.reservation_journal_entry:
				if row.journal_entry:
					je = frappe.get_doc("Journal Entry", row.journal_entry)
					if je.docstatus == 1:
						je.cancel()

		# Cancel legacy single journal entry field
		if self.journal_entry:
			je = frappe.get_doc("Journal Entry", self.journal_entry)
			if je.docstatus == 1:
				je.cancel()

		# Cancel Sales Invoices (child table)
		if hasattr(self, "reservation_sales_invoice"):
			for row in self.reservation_sales_invoice:
				if row.sales_invoice:
					si = frappe.get_doc("Sales Invoice", row.sales_invoice)
					if si.docstatus == 1:
						si.cancel()

	def before_cancel(self):
		"""Update reservation status before cancel."""
		self.reservation_status = "Cancelled"

		frappe.msgprint(
			msg=_("Reservation {0} has been successfully cancelled.").format(self.name),
			title=_("Cancellation Successful"),
			indicator="red",
		)

	def on_cancel(self):
		"""Cancel all related financial and stock documents."""
		self.cancel_related_records()
