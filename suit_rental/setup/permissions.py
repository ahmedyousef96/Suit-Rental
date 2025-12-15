# suit_rental/setup/permissions.py
# Copyright (c) 2025
# Safe permission handling for Suit Rental app
# Compatible with Frappe Cloud & Marketplace

import frappe


# ----------------------------------------------------
# Internal helper
# ----------------------------------------------------

def ensure_role_permission(doctype: str, role: str, perms: dict):

    # ----------------------------------
    # 1) Check if Custom DocPerm exists
    # ----------------------------------
    has_custom = frappe.db.exists("Custom DocPerm", {"parent": doctype})

    # ----------------------------------
    # 2) If no Custom  copy ALL DocPerm
    # ----------------------------------
    if not has_custom:
        standard_perms = frappe.get_all(
            "DocPerm",
            filters={"parent": doctype},
            fields=[
                "role",
                "permlevel",
                "if_owner",
                "select",
                "read",
                "write",
                "create",
                "delete",
                "submit",
                "cancel",
                "amend",
                "report",
                "export",
                "import",
                "share",
                "print",
                "email",
            ],
            order_by="idx",
        )

        for perm in standard_perms:
            doc = frappe.new_doc("Custom DocPerm")
            doc.parent = doctype
            doc.parenttype = "DocType"
            doc.parentfield = "permissions"

            for key, value in perm.items():
                if hasattr(doc, key):
                    setattr(doc, key, value)

            doc.insert(ignore_permissions=True)

    # ----------------------------------
    # 3) Check if role already exists
    # ----------------------------------
    existing_roles = set(
        frappe.get_all(
            "Custom DocPerm",
            filters={"parent": doctype},
            pluck="role",
        )
    )

    if role in existing_roles:
        return

    # ----------------------------------
    # 4) Add new role permission
    # ----------------------------------
    doc = frappe.new_doc("Custom DocPerm")
    doc.parent = doctype
    doc.parenttype = "DocType"
    doc.parentfield = "permissions"
    doc.role = role
    doc.permlevel = 0

    # Select is very important for Link fields
    if hasattr(doc, "select"):
        doc.select = 1

    for key, value in perms.items():
        if hasattr(doc, key):
            setattr(doc, key, value)

    doc.insert(ignore_permissions=True)

    # ----------------------------------
    # 5) Clear cache
    # ----------------------------------
    frappe.clear_cache(doctype=doctype)
    if hasattr(frappe.permissions, "clear_doctype_cache"):
        frappe.permissions.clear_doctype_cache(doctype)


# ----------------------------------------------------
# Public setup function
# ----------------------------------------------------

def setup_suit_rental_permissions():

    CONFIG = {
        # -----------------------
        # Master Data
        # -----------------------
        "Item": {
            "user": {"read": 1},
            "manager": {"read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "export": 1},
        },
        "Item Group": {
            "user": {"read": 1},
            "manager": {"read": 1, "write": 1, "create": 1, "delete": 1},
        },
        "Item Price": {
            "user": {"read": 1},
            "manager": {"read": 1, "write": 1, "create": 1, "delete": 1},
        },
        "Brand": {
            "user": {"read": 1},
            "manager": {"read": 1, "write": 1, "create": 1, "delete": 1},
        },
        "UOM": {
            "user": {"read": 1},
            "manager": {"read": 1, "write": 1, "create": 1, "delete": 1},
        },

        # -----------------------
        # Stock
        # -----------------------
        "Warehouse": {
            "user": {"read": 1},
            "manager": {"read": 1, "write": 1, "create": 1, "delete": 1},
        },
        "Warehouse Type": {
            "user": {"read": 1},
            "manager": {"read": 1, "write": 1, "create": 1, "delete": 1},
        },
        "Stock Entry": {
            "user": {
                "read": 1, "write": 1, "create": 1,
                "submit": 1, "cancel": 1, "amend": 1
            },
            "manager": {
                "read": 1, "write": 1, "create": 1, "delete": 1,
                "submit": 1, "cancel": 1, "amend": 1
            },
        },

        # -----------------------
        # Buying
        # -----------------------
        "Supplier": {
            "user": {"read": 1},
            "manager": {"read": 1, "write": 1, "create": 1, "delete": 1},
        },
        "Supplier Group": {
            "user": {"read": 1},
            "manager": {"read": 1, "write": 1, "create": 1, "delete": 1},
        },
        "Purchase Invoice": {
            "user": {
                "read": 1, "write": 1, "create": 1,
                "submit": 1, "cancel": 1, "amend": 1
            },
            "manager": {
                "read": 1, "write": 1, "create": 1, "delete": 1,
                "submit": 1, "cancel": 1, "amend": 1
            },
        },
        "Purchase Receipt": {
            "user": {
                "read": 1, "write": 1, "create": 1,
                "submit": 1, "cancel": 1, "amend": 1
            },
            "manager": {
                "read": 1, "write": 1, "create": 1, "delete": 1,
                "submit": 1, "cancel": 1, "amend": 1
            },
        },

        # -----------------------
        # Selling / Accounting
        # -----------------------
        "Customer": {
            "user": {"read": 1, "write": 1},
            "manager": {"read": 1, "write": 1, "create": 1, "delete": 1},
        },
        "Account": {
            "user": {"read": 1},
            "manager": {"read": 1, "write": 1},
        },
        "Company": {
            "user": {"read": 1, "report": 1},
            "manager": {"read": 1, "report": 1},
        },
        "Mode of Payment": {
            "user": {"read": 1},
            "manager": {"read": 1, "write": 1},
        },
        "Journal Entry": {
            "user": {
                "read": 1, "write": 1, "create": 1,
                "submit": 1, "cancel": 1, "amend": 1
            },
            "manager": {
                "read": 1, "write": 1, "create": 1, "delete": 1,
                "submit": 1, "cancel": 1, "amend": 1
            },
        },
        "Payment Entry": {
            "user": {
                "read": 1, "write": 1, "create": 1,
                "submit": 1, "cancel": 1, "amend": 1
            },
            "manager": {
                "read": 1, "write": 1, "create": 1, "delete": 1,
                "submit": 1, "cancel": 1, "amend": 1
            },
        },
    }

    for doctype, roles in CONFIG.items():
        if "user" in roles:
            ensure_role_permission(doctype, "Suit Rental User", roles["user"])
        if "manager" in roles:
            ensure_role_permission(doctype, "Suit Rental Manager", roles["manager"])
