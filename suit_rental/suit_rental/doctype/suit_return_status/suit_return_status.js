frappe.ui.form.on("Suit Return Status", {
    refresh(frm) {

        let help_html = `
            <table class="table table-bordered" style="background-color: var(--scrollbar-track-color);">
                <tr>
                    <td>
                        <h4><i class="fa fa-info-circle"></i> {{ __("Return Status Rules") }}</h4>
                        <ul>
                            <li>{{ __("Each Return Status defines how the system handles returned rental items.") }}</li>
                            <li>{{ __("System behavior depends on the selected Type: Good, Damage, or Lost.") }}</li>
                            <li>{{ __("Penalty amounts come from the Item doctype (Lost Penalty / Damage Penalty).") }}</li>
                            <li>{{ __("Stock movement is handled automatically based on the Type logic.") }}</li>
                        </ul>
                    </td>
                </tr>

                <tr>
                    <td>
                        <h4><i class="fa fa-check-circle"></i> {{ __("GOOD Return") }}</h4>
                        <ul>
                            <li>{{ __("No penalty is applied.") }}</li>
                            <li>{{ __("Item is transferred back from Customer Stock Warehouse to Branch Warehouse.") }}</li>
                            <li>{{ __("No income posting is created.") }}</li>
                        </ul>
                    </td>
                </tr>

                <tr>
                    <td>
                        <h4><i class="fa fa-exclamation-circle"></i> {{ __("DAMAGE Return") }}</h4>
                        <ul>
                            <li>{{ __("Penalty equals the Damage Penalty Amount defined in the Item.") }}</li>
                            <li>{{ __("Stock is transferred back to Branch (item returned but damaged).") }}</li>
                            <li>{{ __("Income is posted according to Post Income As setting in Branch:") }}
                                <ul>
                                    <li>{{ __("Journal Entry - credit income account.") }}</li>
                                    <li>{{ __("Sales Invoice - create service invoice for penalty.") }}</li>
                                </ul>
                            </li>
                        </ul>
                    </td>
                </tr>

                <tr>
                    <td>
                        <h4><i class="fa fa-times-circle"></i> {{ __("LOST Return") }}</h4>
                        <ul>
                            <li>{{ __("Penalty equals the Lost Penalty Amount defined in the Item.") }}</li>
                            <li>{{ __("Item is removed permanently via Material Issue.") }}</li>
                            <li>{{ __("Income posting follows Branch settings (JE or Invoice).") }}</li>
                        </ul>
                    </td>
                </tr>

                <tr>
                    <td>
                        <h4><i class="fa fa-lightbulb-o"></i> {{ __("Notes") }}</h4>
                        <ul>
                            <li>{{ __("Partial return is not allowed. All rental items must be processed together.") }}</li>
                            <li>{{ __("Penalty can be optionally overridden if Allow Edit Penalty is enabled.") }}</li>
                            <li>{{ __("This configuration is Branch-based. Each Branch can define its own rules.") }}</li>
                        </ul>
                    </td>
                </tr>
            </table>
        `;

        frm.set_df_property("return_rule_help", "options", help_html);
    }
});
