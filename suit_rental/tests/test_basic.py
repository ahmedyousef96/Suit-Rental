import frappe

def test_basic_app_loading():
    """Simple test to confirm the app loads correctly."""
    assert frappe.get_app_path('suit_rental') is not None
