
# Copyright (c) 2019-2021, libracore and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, json
from datetime import date
from frappe import _
from urllib.parse import unquote
from frappe.utils import cint

@frappe.whitelist()
def create_hock_page():
    try:
        main_data = None
        main_data_json_dump = None
        data = frappe.form_dict
        if '~CALLER' in data.keys():
            main_data = data
            main_data_json_dump = json.dumps(json.loads(str(data).replace("\"","").replace("'","\"")))
        else:
            '''
                workaround:
                get manually the application/x-www-form-urlencoded body content from the request object and convert it to json
            '''
            # decode to utf-8 and url unquote application/x-www-form-urlencoded body content
            request_data = unquote(frappe.local.request.get_data().decode("utf-8"))
            json_data, json_string = json_converter(request_data)
        
            if '~CALLER' in json_data:
                special_encoding_definition = frappe.db.get_value("OCI Partners", json_data["~CALLER"], 'encoding')
                if special_encoding_definition:
                    request_data = unquote(frappe.local.request.get_data().decode(special_encoding_definition))
                    json_data, json_string = json_converter(request_data)
                whitespace_replacement = frappe.db.get_value("OCI Partners", json_data["~CALLER"], 'whitespace_replacement')
                main_data = json_data
                main_data_json_dump = json_string.replace(whitespace_replacement, " ") if whitespace_replacement else json_string
            elif 'NEW_ITEM-MATNR[1]' in json_data:
                # wago fallback lösung (bad!)
                special_encoding_definition = frappe.db.get_value("OCI Partners", 'Wago', 'encoding')
                if special_encoding_definition:
                    request_data = unquote(frappe.local.request.get_data().decode(special_encoding_definition))
                    json_data, json_string = json_converter(request_data)
                whitespace_replacement = frappe.db.get_value("OCI Partners", 'Wago', 'whitespace_replacement')
                json_data['~CALLER'] = 'Wago'
                main_data = json_data
                main_data_json_dump = json_string.replace(whitespace_replacement, " ") if whitespace_replacement else json_string
        
        if not main_data:
            frappe.local.response["type"] = "redirect"
            frappe.local.response["location"] = "/desk#"
            return
        
        basket = frappe.get_doc({
                    "doctype": "OCI Basket",
                    "oci_partner" : main_data['~CALLER'],
                    "date" : date.today(),
                    "data" : main_data_json_dump
                })
        basket.insert(ignore_permissions=True)
        frappe.db.commit()
        frappe.local.response["type"] = "redirect"
        frappe.local.response["location"] = "/desk#List/OCI%20Basket/List"
    except Exception as err:
        frappe.log_error("{0}".format(err), 'OCI Failed: create_hock_page')

def json_converter(request_data):
    # convert to json 
    request_data_list = request_data.split("&")
    request_data_list = [item.split('=') if '=' in item else (item, '') for item in request_data_list]
    json_data = {key.upper(): value for key, value in request_data_list}
    json_string = json.dumps(json_data, indent=2)
    return json_data, json_string



@frappe.whitelist()
def get_basket_data(cdn):
    doc = json.loads(cdn)
    partner = frappe.get_doc("OCI Partners", doc["oci_partner"])
    fields = []
    item_code = ""
    # create fields for display and header
    for value in partner.fields:
        if(value.show_in_table):
            fields.append(value)
        if(value.fieldtype == "Item-Field" and value.fieldname == "item_code"):
            item_code = value.returnfield

    data = json.loads(doc['data'])
    i = 0 
    values = []
    while True:
        if (fields[0].returnfield.replace("%",str(i+1))) not in data:
            break
        
        details = {}
        # add field infromations
        for z in range(len(fields)):
            details[fields[z].title] = ""
            
            if (fields[z].returnfield.replace("%",str(i+1)))in data:
                details[fields[z].title] = data[fields[z].returnfield.replace("%",str(i+1))]
        # check item exist
        exist = True
        if item_code != "" and ((item_code.replace("%",str(i+1))) in data):
            exist = frappe.db.exists("Item", data[item_code.replace("%",str(i+1))])
            if not exist:
                exist = check_manufactur_number(data[item_code.replace("%",str(i+1))])
        details["exist"] = exist

        # check stock maintenance
        stock_item_function = """
                cur_frm.trigger("chek_stock_items");
        """
        details['stock_check'] = """ data-item-code='{0}' data-check-stock='check' onclick='{1}'""".format(data[item_code.replace("%",str(i+1))], stock_item_function)
        if exist:
            if cint(frappe.db.get_value("Item", exist, 'is_stock_item')) == 1:
                details['stock_check'] = ' checked onclick="return false;"'
            else:
                details['stock_check'] = ' onclick="return false;"'

        values.append(details)
        i = i+1

    response = {}
    response["fields"] = fields
    response["values"] = values

    return response

@frappe.whitelist()
def get_basket_items(basket):
    oci_basket = frappe.get_doc("OCI Basket", basket)
    partner = frappe.get_doc("OCI Partners", oci_basket.oci_partner)

    basket_quantity = ""
    item_code = ""
    basket_uom = ""

    for value in partner.fields:
        if(value.fieldtype == "Basket-Quantity"):
            basket_quantity = value.returnfield
        if(value.fieldtype == "Item-Field" and value.fieldname == "item_code"):
            item_code = value.returnfield
        if(value.fieldtype == "Item-UOM"):
            basket_uom = value.returnfield

    data = json.loads(oci_basket.data)
    result = []
    i = 0
    while True:
        if (item_code.replace("%",str(i+1))) not in data:
            break
        
        item_codename = None
        item_quantity = None
        item_uom = None
        #parse data
        if item_code != "" and ((item_code.replace("%",str(i+1))) in data):
            item_codename = frappe.db.exists("Item", data[item_code.replace("%",str(i+1))])
            if not item_codename:
                item_codename = check_manufactur_number(data[item_code.replace("%",str(i+1))])
        if basket_quantity != "" and ((basket_quantity.replace("%",str(i+1))) in data) and item_codename:
            item_quantity = data[basket_quantity.replace("%",str(i+1))] or 1
            item_uom = data[basket_uom.replace("%",str(i+1))] or None

        if item_codename and item_quantity:
            result.append({"item_code" : item_codename, "quantity" : item_quantity, "uom": item_uom})
        i = i+1
    frappe.db.set_value("OCI Basket", basket, 'purchase_order', 1)
    return {
        'items': result,
        'supplier': partner.supplier
    }


@frappe.whitelist()
def create_items(cdn, stock_items):
    doc = json.loads(cdn)
    stock_items = stock_items.split(",")
    partner = frappe.get_doc("OCI Partners",doc["oci_partner"])
    supplier = partner.supplier
    own_item_code = cint(partner.use_own_item_code)
    itemfields = []
    pricefields = []
    price_units = []
    uomfields = []
    item_code = ""
    result = []
    # fiend fields
    for value in partner.fields:
        if(value.fieldtype == "Item-Field" and value.fieldname != "item_code" and value.fieldname):
            itemfields.append(value)
        if(value.fieldtype == "Item-Price"):
            pricefields.append(value)
        if(value.fieldtype == "Price-Unit"):
            price_units.append(value)
        if(value.fieldtype == "Item-UOM"):
            uomfields.append(value)
        if(value.fieldtype == "Item-Field" and value.fieldname == "item_code"):
            item_code = value.returnfield


    data = json.loads(doc['data'])

    i = 0 
    while True:
        if (itemfields[0].returnfield.replace("%",str(i+1))) not in data:
            break
        
        item_codename = ""
        #parse data
        exist = True
        if item_code != "" and ((item_code.replace("%",str(i+1))) in data):
            item_codename = data[item_code.replace("%",str(i+1))]
            exist = frappe.db.exists("Item",item_codename)
        
        if not exist:
            exist = check_manufactur_number(item_codename)
        
        if exist:
            i = i+1
            continue

        itemdata = {}
        # add field infromations
        for z in range(len(itemfields)):
            itemdata[itemfields[z].fieldname] = itemfields[z].default
            if (itemfields[z].returnfield.replace("%",str(i+1)))in data:
                if int(itemfields[z].max_length) > 0:
                    itemdata[itemfields[z].fieldname] = str(data[itemfields[z].returnfield.replace("%",str(i+1))])[:int(itemfields[z].max_length)]
                else:
                    itemdata[itemfields[z].fieldname] = data[itemfields[z].returnfield.replace("%",str(i+1))]

        # add uom infromations
        uomdata = {}
        for z in range(len(uomfields)):
            uomdata[uomfields[z].fieldname] = uomfields[z].default
            if (uomfields[z].returnfield.replace("%",str(i+1)))in data:
                if frappe.db.exists("UOM", data[uomfields[z].returnfield.replace("%",str(i+1))]):
                    uomdata[uomfields[z].fieldname] = data[uomfields[z].returnfield.replace("%",str(i+1))]

        # add price infromations
        pricedata = [len(pricefields)]
        for z in range(len(pricefields)):
            pricedata[z] = {}
            pricedata[z]['field'] = [pricefields[z].fieldname]
            if (pricefields[z].pricelist != None):
                pricedata[z]['pricelist'] = pricefields[z].pricelist
            if (pricefields[z].returnfield.replace("%",str(i+1)))in data:
                price_unit_factor = 1
                for zz in range(len(price_units)):
                    if (price_units[zz].returnfield.replace("%",str(i+1)))in data:
                        price_unit_factor = int(data[price_units[zz].returnfield.replace("%",str(i+1))]) or 1
                pricedata[z]['price'] = float(data[pricefields[z].returnfield.replace("%",str(i+1))]) / price_unit_factor


        result.append(create_item(item_codename, itemdata, uomdata, pricedata, supplier, item_codename, partner.item_defaults, own_item_code, stock_items))
        i = i+1	

    return "Items added: <br/>" + "<br/>".join(result)

def create_item(item_codename, itemdata, uomdata, pricedata, supplier, supplier_part_no, defaults, own_item_code, stock_items):
    docdata = {}
    docdata["doctype"] = "Item"
    if own_item_code != 1:
        docdata["item_code"] = item_codename
    docdata["show_in_website"] = 0
    docdata["is_sales_item"] = 1
    docdata["is_purchase_item"] = 1
    if supplier_part_no in stock_items:
        docdata["is_stock_item"] = 1
    else:
        docdata["is_stock_item"] = 0
    for key,field in itemdata.items():
        docdata[key] = field
    for key,field in uomdata.items():
        docdata[key] = field
    docdata["item_defaults"] = defaults
    docdata["supplier_items"] = [{
                                "supplier" : supplier,
                                "supplier_part_no" : supplier_part_no
                                }]

    new_item = frappe.get_doc(docdata)
    new_item.insert()

    for price in pricedata:
        item_price = frappe.get_doc({
            "doctype": "Item Price",
            "price_list": price["pricelist"],
            "item_code": new_item.item_code,
            "price_list_rate": price["price"],
            "supplier": supplier
        }).insert()

    return item_codename

def check_manufactur_number(item_code):
    item = frappe.db.sql("""
                         SELECT `parent`
                         FROM `tabItem Supplier`
                         WHERE `supplier_part_no` = '{0}'
                         """.format(item_code), as_dict=True)
    if len(item) > 0:
        return item[0].parent
    else:
        return None
