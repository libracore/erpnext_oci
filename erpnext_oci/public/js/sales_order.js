frappe.ui.form.on('Sales Order', {
    refresh(frm) {
        if (frm.doc.docstatus == 0) {
            frm.add_custom_button(__("OCI Import"), function() {
                oci_import(frm);
            });
        }
    }
});

function oci_import(frm) {
    var d = new frappe.ui.Dialog({
        'fields': [
            {'fieldname': 'oci_basket', 'fieldtype': 'Link', 'label': __('OCI Basket'), 'options': 'OCI Basket', 'reqd': 1,
            'get_query': function() { return { filters: {'purchase_order': ['!=', 1] } } }
        }
        ],
        primary_action: function() {
            d.hide();
            var values = d.get_values();
            frappe.call({
                method: 'erpnext_oci.open_catalog_interface.utils.get_basket_items',
                args: {
                    basket: values.oci_basket
                },
                "callback": function(response) {
                    var tbl = frm.doc.items || [];
                    var i = tbl.length;
                    while (i--)
                    {
                        cur_frm.get_field("items").grid.grid_rows[i].remove();
                    }
                    cur_frm.refresh_field('items');
                    for (var i = 0; i < response.message.items.length; i++) {
                        var child = cur_frm.add_child('items');
                        frappe.model.set_value(child.doctype, child.name, 'item_code', response.message.items[i].item_code);
                        frappe.model.set_value(child.doctype, child.name, 'qty', response.message.items[i].quantity);
                        frappe.model.set_value(child.doctype, child.name, 'uom', response.message.items[i].uom);
                    }
                    cur_frm.refresh_field('items');
                }
            });
        },
        primary_action_label: __('OK'),
        title: __('OCI Import')
    });
    d.show();
}