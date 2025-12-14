import frappe
from frappe import _


def create_suit_rental_roles():
	create_suit_manager_role()
	create_suit_user_role()


def create_suit_manager_role():
	if frappe.db.exists("Role", "Suit Rental Manager"):
		frappe.db.set_value("Role", "Suit Rental Manager", "desk_access", 1)
	else:
		role = frappe.new_doc("Role")
		role.role_name = "Suit Rental Manager"
		role.desk_access = 1
		role.insert(ignore_permissions=True)


def create_suit_user_role():
	if frappe.db.exists("Role", "Suit Rental User"):
		frappe.db.set_value("Role", "Suit Rental User", "desk_access", 1)
	else:
		role = frappe.new_doc("Role")
		role.role_name = "Suit Rental User"
		role.desk_access = 1
		role.insert(ignore_permissions=True)
