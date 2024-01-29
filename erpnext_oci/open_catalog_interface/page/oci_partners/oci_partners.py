import frappe
from frappe import throw, _

@frappe.whitelist()
def get_partner_form_datas():
    form_datas = []
    partners = frappe.get_all("OCI Partners")
    for _partner in partners:
        partner = frappe.get_doc("OCI Partners", _partner.name)
        partner_form = {
            'name': partner.name,
            'type': partner.type,
            'url': partner.url,
            'parameter': []
        }
        for url_parameter in partner.url_parameter:
            partner_form['parameter'].append([url_parameter.parameter, url_parameter.value])
        form_datas.append(partner_form)
    return form_datas



