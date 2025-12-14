import frappe

from suit_rental.setup.roles import create_suit_rental_roles
from suit_rental.setup.permissions import setup_suit_rental_permissions


def after_install():
	create_suit_rental_roles()
	#setup_suit_rental_permissions()


#def after_sync():
#	setup_suit_rental_permissions()


def before_uninstall():
	delete_custom_fields()


def delete_custom_fields():
	fields = [
		"custom_address",
		"custom_manager_name",
		"custom_column_break_jl8ov",
		"custom_section_break_bo9yy",
		"custom_default_warehouse",
		"custom_column_break_iw550",
		"custom_receivable_account",
		"custom_income_account",
		"custom_income_settings",
		"custom_post_income_as",
		"custom_column_break_gzbye",
		"custom_rent_invoice_item",
		"custom_sales_invoice_status",
		"custom_journal_entry_status",
		"custom_sales_invoice_item_mapping",
		"custom_customer_stock_warehouse",
		"custom_company",
		"custom_is_rental_item",
		"custom_rental_price",
		"custom_suit_rental_configuration",
		"custom_column_break_gwzji",
		"custom_lost_penalty_amount",
		"custom_damage_penalty_amount" "work_environment",
	]

	for field in fields:
		frappe.db.delete("Custom Field", {"fieldname": field})