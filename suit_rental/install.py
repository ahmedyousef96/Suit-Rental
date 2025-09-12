import frappe


#def after_install():
    """
    Hook to run after the app is installed.
    Sets default website settings.    
    """
    create_tatweer_theme()
    set_website_settings_defaults()
    


def after_sync():

    create_suit_rental_roles()


def create_suit_rental_roles():

    create_suit_manager_role()
    create_suit_user_role()
    


def create_suit_manager_role():

    if frappe.db.exists("Role", "Suit Rental Manager"):
        frappe.db.set_value("Role", "Suit Rental Manager", "desk_access", 1)
        frappe.msgprint("Role 'Suit Rental Manager' already exists. Ensured desk access.")
    else:
        role = frappe.get_doc(
            {
                "doctype": "Role",
                "role_name": "Suit Rental Manager",
                "home_page": "",  # Optional: specify a home page for the role
                "desk_access": 1,
            }
        )
        role.save()
        frappe.msgprint("Suit Rental Manager' created successfully.")


def create_suit_user_role():

    if frappe.db.exists("Role", "Suit Rental User"):
        frappe.db.set_value("Role", "Suit Rental User", "desk_access", 1)
        frappe.msgprint("Role 'Suit Rental User' already exists. Ensured desk access.")
    else:
        role = frappe.new_doc("Role")
        role.update(
            {
                "role_name": "Suit Rental User",
                "home_page": "",  # Optional: specify a home page for the role
                "desk_access": 1,
            }
        )
        role.save()
        frappe.msgprint("Role 'Suit Rental User' created successfully.")
        
        

def create_tatweer_theme():
    if not frappe.db.exists("Website Theme", "Tatweer Theme"):
        doc = frappe.get_doc({
            "doctype": "Website Theme",
            "theme_name": "Tatweer Theme",
            # You can add custom CSS/JS here if needed, e.g.:
            # "custom_css": ".my-custom-class { color: red; }",
            # "custom_js": "console.log('Theme loaded');"
        })
        doc.insert(ignore_permissions=True) # Use insert for new doc
        frappe.msgprint("Website Theme 'Tatweer Theme' created.")
    else:
        frappe.msgprint("Website Theme 'Tatweer Theme' already exists.")


def set_website_settings_defaults():
    """
    Sets default values for the Website Settings DocType,
    including logos, app name, home page, redirects, and top bar items.
    """
    try:
        # Get the single Website Settings DocType
        # 'Website Settings' is the standard Frappe DocType.
        website_settings = frappe.get_single("Website Settings")

        # Set image fields
        # Use the correct relative path for your SVG logo from the public directory
        website_settings.app_logo = "/assets/tatweer_uni/images/tatweer_uni_logo.svg"
        website_settings.banner_image = "/assets/tatweer_uni/images/tatweer_uni_logo.svg"
        website_settings.favicon = "/assets/tatweer_uni/images/tatweer_uni_logo.svg"
        website_settings.footer_logo = "/assets/tatweer_uni/images/tatweer_uni_logo.svg"
        website_settings.splash_image = "/assets/tatweer_uni/images/tatweer_uni_logo.svg"

        # Set other website properties
        website_settings.app_name = "Tatweer"
        website_settings.title_prefix = "Tatweer Ed"
        website_settings.home_page = "ed-home"
        website_settings.show_footer_on_login = 1
        website_settings.hide_login = 0
        website_settings.navbar_search = 0
        website_settings.show_language_picker = 1
        website_settings.hide_footer_signup = 1
        website_settings.website_theme = "Tatweer Theme"  # Ensure this theme exists
        website_settings.navbar_template = "Standard Navbar"
        website_settings.footer_template = "Tatweer Footer"  # Ensure this footer template exists
        website_settings.footer_powered = "Revamp Consulting"
        website_settings.copyright = "Revamp Consulting"

        # Clear existing route redirects and add new ones
        website_settings.route_redirects = []
        redirect_entries = [
            {
                "source": "/pending-actions/list",
                "target": "/pending-actions-list"
            },
            {
                "source": "/university-admission/list",
                "target": "/university-admission-list"
            }
        ]
        for entry in redirect_entries:
            website_settings.append("route_redirects", entry)

        # Clear existing top bar items and add new ones
        website_settings.top_bar_items = []
        top_bar_items_entries = [
            {
                "label": "Home Page",
                "url": "/ed-home"
            },
            {
                "label": "Admissions"
            },
            {
                "label": "Apply",
                "parent_label": "Admissions",
                "url": "/university-admission/new"
            },
            {
                "label": "Admission Status",
                "parent_label": "Admissions",
                "url": "/university-admission-list"
            },
            {
                "label": "Pending Actions",
                "parent_label": "Admissions",
                "url": "/pending-actions-list"
            }
        ]
        for entry in top_bar_items_entries:
            website_settings.append("top_bar_items", entry)

        # Save the changes to the Website Settings DocType
        # ignore_permissions=True is often needed for hooks to bypass permission checks
        website_settings.save(ignore_permissions=True)

        # Commit the changes to the database
        frappe.db.commit()

        frappe.msgprint("Website Settings defaults set successfully for Tatweer Uni app.")

    except Exception as e:
        # Log any errors that occur during the process
        frappe.log_error(frappe.get_traceback(), "Error setting Website Settings defaults")
        frappe.msgprint(f"Failed to set Website Settings defaults: {e}")