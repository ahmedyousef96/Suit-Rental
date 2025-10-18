frappe.ui.form.on("Suit Reservation", {
	refresh(frm) {
		// Add button to fetch customer measurements only if docstatus is 0 (Draft)
		if (frm.doc.docstatus === 0) {
			frm.add_custom_button(__("Get Customer Measurement"), function () {
				if (!frm.doc.customer) {
					frappe.msgprint(__("Please select a Customer first"));
					return;
				}

				// Show loading spinner
				frappe.dom.freeze(__("Fetching measurements..."));
				frappe.call({
					method: "suit_rental.api.get_customer_measurements",
					args: {
						customer: frm.doc.customer,
					},
					callback: function (r) {
						if (r.message) {
							// Clear the reservation_measurements table before adding new rows
							frm.clear_table("reservation_measurements");
							r.message.forEach((row) => {
								let child = frm.add_child("reservation_measurements");
								child.measurement_type = row.measurement_type;
								child.value = row.value;
								child.uom = row.uom;
							});
							frm.refresh_field("reservation_measurements");
							frappe.msgprint(__("Measurements fetched successfully"));
						}
					},
					error: function (err) {
						frappe.msgprint({
							title: __("Missing Data"),
							message:
								__('<a href="/app/customer-measurement/new?customer=') +
								encodeURIComponent(frm.doc.customer) +
								__('">Click here to add measurements.</a>'),
							indicator: "red",
						});
					},
					always: function () {
						frappe.dom.unfreeze();
					},
				});
			});
		}

		// Add Deliver button if docstatus is 1 (Submitted) and reservation_status is 'Reserved'
		if (frm.doc.docstatus === 1 && frm.doc.reservation_status === "Reserved") {
			frm.add_custom_button(__("Deliver"), function () {
				let dialog = new frappe.ui.Dialog({
					title: __("Deliver Reservation"),
					fields: [
						{
							label: __("Delivery Date"),
							fieldname: "delivery_date",
							fieldtype: "Date",
							default: frappe.datetime.now_date(),
							reqd: 1,
						},
						{
							label: __("Mode of Payment"),
							fieldname: "mode_of_payment",
							fieldtype: "Link",
							options: "Mode of Payment",
							default: frm.doc.mode_of_payment,
							reqd: 1,
						},
					],
					primary_action_label: __("Deliver"),
					primary_action(values) {
						frappe.call({
							method: "suit_rental.api.deliver_reservation",
							args: {
								name: frm.doc.name,
								delivery_date: values.delivery_date,
								mode_of_payment: values.mode_of_payment,
							},
							callback: function (r) {
								if (r.message) {
									frm.reload_doc();
									frappe.msgprint(__("Reservation delivered successfully"));
								}
							},
						});
						dialog.hide();
					},
				});
				dialog.show();
			});
		}

		// Add Return button if docstatus is 1 (Submitted) and reservation_status is 'Delivered'
		if (frm.doc.docstatus === 1 && frm.doc.reservation_status === "Delivered") {
			frm.add_custom_button(__("Return"), function () {
				let dialog = new frappe.ui.Dialog({
					title: __("Return Reservation"),
					fields: [
						{
							label: __("Return Date"),
							fieldname: "return_date",
							fieldtype: "Date",
							default: frappe.datetime.now_date(),
							reqd: 1,
						},
					],
					primary_action_label: __("Return"),
					primary_action(values) {
						frappe.call({
							method: "suit_rental.api.return_reservation",
							args: {
								name: frm.doc.name,
								return_date: values.return_date,
							},
							callback: function (r) {
								if (r.message) {
									frm.reload_doc();
									frappe.msgprint(__("Reservation returned successfully"));
								}
							},
						});
						dialog.hide();
					},
				});
				dialog.show();
			});
		}

		// Auto-set sales_person from session user
		if (!frm.doc.sales_person) {
			frm.set_value("sales_person", frappe.session.user);
		}
	},

	deposit_amount(frm) {
		// Validate deposit_amount is not greater than total_estimated_rent
		if (
			frm.doc.deposit_amount &&
			frm.doc.total_estimated_rent &&
			frm.doc.deposit_amount > frm.doc.total_estimated_rent
		) {
			frappe.msgprint({
				title: __("Invalid Deposit"),
				message: __("Deposit Amount cannot be greater than Total Estimated Rent."),
				indicator: "red",
			});
			frm.set_value("deposit_amount", 0);
		}
		debounced_update_total_estimated(frm);
	},

	event_date(frm) {
		if (frm.doc.event_date) {
			const today = frappe.datetime.now_date();
			if (frappe.datetime.get_diff(frm.doc.event_date, today) < 0) {
				frappe.msgprint(__("Event date should be in the future"));
				//frm.set_value("event_date", null);
				//return;
			}
			frm.set_value("reservation_from", frappe.datetime.add_days(frm.doc.event_date, -1));
			frm.set_value("reservation_to", frappe.datetime.add_days(frm.doc.event_date, 1));
		}
	},

	reservation_to(frm) {
		if (frm.doc.reservation_from && frm.doc.reservation_to) {
			if (frappe.datetime.get_diff(frm.doc.reservation_to, frm.doc.reservation_from) < 0) {
				frappe.msgprint(__("Reservation To date cannot be before Reservation From date"));
				frm.set_value("reservation_to", null);
			}
		}
	},
});

frappe.ui.form.on("Reservation Item", {
	item_code(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		// Validate no duplicate item_code in reservation_items
		if (row.item_code) {
			const duplicate = frm.doc.reservation_items.some(
				(item, idx) => item.item_code === row.item_code && item.name !== row.name
			);
			if (duplicate) {
				frappe.msgprint({
					title: __("Duplicate Item"),
					message: __(
						"Item Code {0} is already added. Please select a different item.",
						[row.item_code]
					),
					indicator: "red",
				});
				frappe.model.set_value(cdt, cdn, "item_code", "");
				frm.refresh_field("reservation_items");
				return;
			}
		}
		debounced_update_total_estimated(frm);
	},

	qty(frm, cdt, cdn) {
		debounced_update_total_estimated(frm);
	},

	rate(frm, cdt, cdn) {
		debounced_update_total_estimated(frm);
	},

	check_availability(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		if (!row) return;

		if (
			!frm.doc.branch ||
			!frm.doc.reservation_from ||
			!frm.doc.reservation_to ||
			!frm.doc.source_warehouse
		) {
			frappe.show_alert({
				message: __(
					"Select Branch, Reserve From, Reserve To, and Source Warehouse first."
				),
				indicator: "orange",
			});
			return;
		}
		check_item_balance(frm, row);
	},

	reservation_items_remove(frm, cdt, cdn) {
		debounced_update_total_estimated(frm);
	},
});

// ---- Helpers ----
function check_item_balance(frm, row) {
	if (!row.item_code) {
		frappe.show_alert({ message: __("Select an item first"), indicator: "orange" });
		return;
	}

	frappe.dom.freeze(__("Checking availability..."));
	frappe.call({
		method: "suit_rental.api.check_availability",
		args: {
			item_code: row.item_code,
			branch: frm.doc.branch,
			warehouse: frm.doc.source_warehouse,
			start_date: frm.doc.reservation_from,
			end_date: frm.doc.reservation_to,
		},
		callback: function (r) {
			if (!r || !r.message) {
				frappe.show_alert({
					message: __("No response from availability API"),
					indicator: "red",
				});
				return;
			}

			const m = r.message;
			frm.refresh_field("reservation_items");

			frappe.msgprint({
				title: __("Availability"),
				message: build_availability_html(m),
				indicator: m.available_stock > 0 ? "green" : "red",
			});
		},
		error: function (err) {
			// Use the error message directly or fallback to a default
			let error_message = err.message || __("Unknown error");
			frappe.msgprint({
				title: __("Error"),
				message: __("Failed to check availability: ") + error_message,
				indicator: "red",
			});
		},
		always: function () {
			frappe.dom.unfreeze();
		},
	});
}

function build_availability_html(m) {
	let html = `<div>
        <p><b>${__("Total stock in Sales Warehouse")}:</b> ${m.total_stock}</p>
        <p><b>${__("Reserved Quantity")}:</b> ${m.reserved_qty}</p>
        <p><b>${__("Available Stock")}:</b> ${m.available_stock}</p>
        <h5>${__("Last 10 reservations")}</h5>`;
	if (!m.last_10_reservations || m.last_10_reservations.length === 0) {
		html += `<p>${__("No recent reservations found.")}</p>`;
	} else {
		html += `<div style="max-height:240px; overflow:auto;">
            <table class="table table-bordered" style="width:100%;border-collapse:collapse;">
              <thead><tr>
                <th>${__("Customer")}</th>
                <th>${__("From")}</th>
                <th>${__("To")}</th>
                <th>${__("Status")}</th>
              </tr></thead>
              <tbody>`;
		m.last_10_reservations.forEach(function (x) {
			html += `<tr>
                <td>${x.customer || ""}</td>
                <td>${x.reservation_from || ""}</td>
                <td>${x.reservation_to || ""}</td>
                <td>${__(x.reservation_status) || ""}</td>
            </tr>`;
		});
		html += `</tbody></table>`;
	}
	html += `</div></div>`;
	return html;
}

const debounced_update_total_estimated = frappe.utils.debounce((frm) => {
	let total = 0;
	(frm.doc.reservation_items || []).forEach((row) => {
		const qty = flt(row.qty) || 0;
		const rate = flt(row.rate) || 0;
		total += qty * rate;
	});

	frm.set_value("total_estimated_rent", total);
	let deposit = flt(frm.doc.deposit_amount) || 0;
	let paid = flt(frm.doc.paid_amount) || 0;
	frm.set_value("outstanding_amount", total - (deposit + paid));
}, 300);

function update_total_estimated(frm) {
	debounced_update_total_estimated(frm);
}
