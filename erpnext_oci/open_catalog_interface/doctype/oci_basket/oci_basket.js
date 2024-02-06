// Copyright (c) 2021, Asprotec AG and contributors
// For license information, please see license.txt

frappe.ui.form.on('OCI Basket', {
    refresh: function(frm) {
        // render basket List
        if(frm.fields_dict['display']) {
            $(frm.fields_dict['display'].wrapper)
                .html(frappe.render_template("oci_basket",
                    frm.doc.__onload));
        
            frappe.call({
                method: 'erpnext_oci.open_catalog_interface.utils.get_basket_data',
                args: {"cdn": frm.doc},
                callback: function(r) {
                    if (r.message != 'Error') {
                        show_table(r.message);
                        frm.set_df_property("display","hidden",false);
                    } else {
                        console.log("fehler beim parsen");
                        frappe.show_alert( r.message );
                    }
                }
            });
        }
        frm.add_custom_button(__("Erstelle fehlende Artikel"), function() {
            if (localStorage.getItem("all_items_exist") != 1) {
                frappe.call({
                    method: 'erpnext_oci.open_catalog_interface.utils.create_items',
                    args: {"cdn": frm.doc},
                    callback: function(r) {
                        frappe.show_alert( r.message );
                        cur_frm.reload_doc();
                    }
                });
            } else {
                frappe.msgprint("Alle Artikel existieren bereits im ERP.");
            }
        });
    }
});


function show_table(data) {
    var all_items_exist = 1;
    var output = [];
    // create header
    output.push('<thead>');
    output.push('<tr>');
    for(var i = 0; i < data["fields"].length ;i++){
        output.push(`<th>${data["fields"][i].title}</td>`);
    }
    output.push('<th>ERP</th>');
    output.push('</tr>');
    output.push('</thead>');
    // create lines
    output.push('<tbody>');
    for(var i = 0; i < data.values.length ;i++){
        output.push('<tr>');
        for(var z = 0; z < data.fields.length ;z++){
            output.push(`<td>${data.values[i][data.fields[z].title]}</td>`);
        }
        if (data.values[i]['exist']) {
            output.push(`<td><a href="/desk#Form/Item/${data.values[i]['exist']}">&#9989;</a></td>`);
        } else {
            output.push('<td>&#10060; </td>');
            all_items_exist = 0;
        }
        output.push('</tr>');
    }
    output.push('<tr>');
    output.push('</tbody>');
    document.getElementById('table_body').innerHTML = document.getElementById('table_body').innerHTML + output.join('');
    localStorage.setItem("all_items_exist", all_items_exist);
}
