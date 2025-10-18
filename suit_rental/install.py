import frappe
from frappe import _


def after_sync():
	"""Hook to run after app installation or sync"""
	create_suit_rental_roles()


def create_suit_rental_roles():
	create_suit_manager_role()
	create_suit_user_role()


def create_suit_manager_role():
	if frappe.db.exists("Role", "Suit Rental Manager"):
		frappe.db.set_value("Role", "Suit Rental Manager", "desk_access", 1)
		frappe.msgprint(_("Role 'Suit Rental Manager' already exists. Ensured desk access."))
	else:
		role = frappe.new_doc("Role")
		role.role_name = "Suit Rental Manager"
		role.desk_access = 1
		role.save()
		frappe.msgprint(_("Created Role: Suit Rental Manager"))


def create_suit_user_role():
	if frappe.db.exists("Role", "Suit Rental User"):
		frappe.db.set_value("Role", "Suit Rental User", "desk_access", 1)
		frappe.msgprint(_("Role 'Suit Rental User' already exists. Ensured desk access."))
	else:
		role = frappe.new_doc("Role")
		role.role_name = "Suit Rental User"
		role.desk_access = 1
		role.save()
		frappe.msgprint(_("Created Role: Suit Rental User"))
