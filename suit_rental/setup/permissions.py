import frappe


PERMISSIONS = [
	# -------------------------
	# Item
	# -------------------------
	{"parent": "Item", "role": "Suit Rental User", "read": 1, "export": 1},
	{
		"parent": "Item",
		"role": "Suit Rental Manager",
		"read": 1,
		"write": 1,
		"create": 1,
		"delete": 1,
		"print": 1,
		"report": 1,
		"export": 1,
		"import": 1,
	},

	# -------------------------
	# Branch
	# -------------------------
	{"parent": "Branch", "role": "Suit Rental User", "read": 1, "export": 1},
	{
		"parent": "Branch",
		"role": "Suit Rental Manager",
		"read": 1,
		"write": 1,
		"create": 1,
		"delete": 1,
		"print": 1,
		"report": 1,
		"export": 1,
		"import": 1,
	},

	# -------------------------
	# Warehouse
	# -------------------------
	{"parent": "Warehouse", "role": "Suit Rental User", "read": 1, "export": 1},
	{
		"parent": "Warehouse",
		"role": "Suit Rental Manager",
		"read": 1,
		"write": 1,
		"create": 1,
		"delete": 1,
		"print": 1,
		"report": 1,
		"export": 1,
	},

	# -------------------------
	# Stock Entry
	# -------------------------
	{
		"parent": "Stock Entry",
		"role": "Suit Rental User",
		"read": 1,
		"write": 1,
		"create": 1,
		"delete": 1,
		"submit": 1,
		"cancel": 1,
		"amend": 1,
		"print": 1,
		"report": 1,
		"export": 1,
	},
	{
		"parent": "Stock Entry",
		"role": "Suit Rental Manager",
		"read": 1,
		"write": 1,
		"create": 1,
		"delete": 1,
		"submit": 1,
		"cancel": 1,
		"amend": 1,
		"print": 1,
		"report": 1,
		"export": 1,
	},

	# -------------------------
	# Payment Entry
	# -------------------------
	{
		"parent": "Payment Entry",
		"role": "Suit Rental User",
		"read": 1,
		"write": 1,
		"create": 1,
		"delete": 1,
		"submit": 1,
		"cancel": 1,
		"print": 1,
		"report": 1,
		"export": 1,
	},
	{
		"parent": "Payment Entry",
		"role": "Suit Rental Manager",
		"read": 1,
		"write": 1,
		"create": 1,
		"delete": 1,
		"submit": 1,
		"cancel": 1,
		"print": 1,
		"report": 1,
		"export": 1,
	},

	# -------------------------
	# Journal Entry
	# -------------------------
	{
		"parent": "Journal Entry",
		"role": "Suit Rental User",
		"read": 1,
		"write": 1,
		"create": 1,
		"delete": 1,
		"submit": 1,
		"cancel": 1,
		"print": 1,
		"report": 1,
		"export": 1,
	},
	{
		"parent": "Journal Entry",
		"role": "Suit Rental Manager",
		"read": 1,
		"write": 1,
		"create": 1,
		"delete": 1,
		"submit": 1,
		"cancel": 1,
		"print": 1,
		"report": 1,
		"export": 1,
	},
]


def setup_suit_rental_permissions():

	for perm in PERMISSIONS:
		if frappe.db.exists(
			"Custom DocPerm",
			{
				"parent": perm["parent"],
				"role": perm["role"],
				"permlevel": 0,
			},
		):
			continue

		doc = frappe.get_doc(
			{
				"doctype": "Custom DocPerm",
				"parent": perm["parent"],
				"role": perm["role"],
				"permlevel": 0,
				**{k: v for k, v in perm.items() if k not in ("parent", "role")},
			}
		)
		doc.insert(ignore_permissions=True)
