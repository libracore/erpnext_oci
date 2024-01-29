frappe.pages['oci-partners'].on_page_load = function(wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'OCI Partners',
        single_column: true
    });

    frappe.oci_partners.make(page);
    frappe.oci_partners.run();
    frappe.oci_partners.show_data();
}

frappe.oci_partners = {
    start: 0,
    make: function(page) {
            var me = frappe.oci_partners;
            me.page = page;
            me.body = $('<div></div>').appendTo(me.page.main);
            var data = "";
            $(frappe.render_template('oci_partners', data)).appendTo(me.body);
    },
    run: function() {
    },
    show_data: function(){
        frappe.call({
            method: 'erpnext_oci.open_catalog_interface.page.oci_partners.oci_partners.get_partner_form_datas',
            args: {},
            callback: function(r) {
                show_table(r.message);
            }
        });
    }
}

function show_table(data) {
    var output = [];
    for(var i = 0; i < data.length; i++){
        output.push('<tr>');
        output.push('<td>' + data[i].name + '</td>');
        var parameters = "";
        for(var j = 0; j < data[i].parameter.length; j++){
            parameters = parameters + '<input type="hidden" name="' + data[i].parameter[j][0] + '" value="' + data[i].parameter[j][1] + '">';
        }
        output.push('<td><form action="' + data[i].url + '" method="' + data[i].type + '" target="_blank">' + parameters +'<input type="hidden" name="HOOK_URL" value="' + location.protocol + '//' + location.hostname + '/api/method/erpnext_oci.open_catalog_interface.utils.create_hock_page"><input type="submit" value="Gehe zu Webshop"></form></td>');
        output.push('</tr>');
    }

    document.getElementById('table_body').innerHTML = document.getElementById('table_body').innerHTML + output.join('');

}
