import frappe
from frappe.permissions import add_permission, update_permission_property


def test_additive_permissions():
	doctype = "Warehouse"
	role = "Suit Rental User"
	permlevel = 0

	# 1. Add role to doctype (safe, additive)
	add_permission(doctype, role, permlevel)

	# 2. Grant read permission only
	update_permission_property(doctype, role, permlevel, "read", 1)

	print(f"Added READ permission for {role} on {doctype}")
