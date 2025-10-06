frappe.listview_settings['Suit Reservation'] = {
    add_fields: ["reservation_status"],
    has_indicator_for_draft: 1, // Optional: Show draft indicator if applicable
    get_indicator: function(doc) {
        // Define indicator based on reservation_status
        if (doc.reservation_status) {
            switch (doc.reservation_status) {
                case "Reserved":
                    return [__("Reserved"), "orange", "reservation_status,=,Reserved"];
                case "Delivered":
                    return [__("Delivered"), "green", "reservation_status,=,Delivered"];
                case "Returned":
                    return [__("Returned"), "blue", "reservation_status,=,Returned"];
                case "Cancelled":
                    return [__("Cancelled"), "red", "reservation_status,=,Cancelled"];
                default:
                    return [__(doc.reservation_status || "Unknown"), "gray", "reservation_status,=,Unknown"];
            }
        }
        return [__("No Status"), "gray", "reservation_status,=,No Status"];
    }
};