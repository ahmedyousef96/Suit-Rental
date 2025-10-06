// Copyright (c) 2025, Ahmed Yousef and contributors
// For license information, please see license.txt

frappe.query_reports["Totals from Suit Reservation"] = {
    "filters": [
        {
            "fieldname": "from_date",
            "label": __("From Date"),
            "fieldtype": "Date",
            "reqd": 1,
            "default": frappe.datetime.get_today(),
            "on_change": function(query_report) {
                validate_dates(query_report);
                query_report.refresh();
            }
        },
        {
            "fieldname": "to_date",
            "label": __("To Date"),
            "fieldtype": "Date",
            "reqd": 1,
            "default": frappe.datetime.get_today(),
            "on_change": function(query_report) {
                validate_dates(query_report);
                query_report.refresh();
            }
        },
        {
            "fieldname": "branch",
            "label": __("Branch"),
            "fieldtype": "Link",
            "options": "Branch",
            "reqd": 0,
            "on_change": function(query_report) {
                query_report.refresh();
            }
        }
    ],

    onload: function(report) {
        // Add quick range buttons
        report.page.add_inner_button(__("Today"), function() {
            set_date_range("today");
            report.refresh();
        });

        report.page.add_inner_button(__("This Week"), function() {
            set_date_range("week");
            report.refresh();
        });

        report.page.add_inner_button(__("This Month"), function() {
            set_date_range("month");
            report.refresh();
        });
    }
};

function validate_dates(query_report) {
    let from_date = frappe.query_report.get_filter_value("from_date");
    let to_date = frappe.query_report.get_filter_value("to_date");

    if (from_date && to_date && from_date > to_date) {
        frappe.msgprint({
            title: __("Invalid Date Range"),
            message: __("From Date cannot be greater than To Date."),
            indicator: "red"
        });
        frappe.query_report.set_filter_value("to_date", "");
    }
}

function set_date_range(option) {
    let today = frappe.datetime.get_today();

    if (option === "month") {
        let month_start = frappe.datetime.month_start(today);
        frappe.query_report.set_filter_value("from_date", month_start);
        frappe.query_report.set_filter_value("to_date", today);
    }
    else if (option === "week") {
        let week_start = frappe.datetime.add_days(today, -frappe.datetime.week_start(today));
        frappe.query_report.set_filter_value("from_date", week_start);
        frappe.query_report.set_filter_value("to_date", today);
    }
    else if (option === "month") {
        let month_start = frappe.datetime.month_start(today);
        frappe.query_report.set_filter_value("from_date", month_start);
        frappe.query_report.set_filter_value("to_date", today);
    }
}
