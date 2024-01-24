from __future__ import unicode_literals
from frappe import _

def get_data():
    return [
        {
            "label": _("OCI Interface"),
            "icon": "fa fa-money",
            "items": [
                {
                    "type": "page",
                    "name": "oci-partners",
                    "label": _("OCI Partner"),
                    "description": _("OCI Partner")
                },
                {
                    "type": "doctype",
                    "name": "OCI Basket",
                    "label": _("OCI Basket"),
                    "description": _("OCI Basket")
                }
            ]
        },
        {
            "label": _("Configuration"),
            "icon": "a fa-money",
            "items": [
                {
                    "type": "doctype",
                    "name": "OCI Partners",
                    "label": _("OCI Partner"),
                    "description": _("OCI Partner")
                },
                {
                    "type": "page",
                    "name": "oci-hook-page",
                    "label": _("OCI Hook Page"),
                    "description": _("OCI Hook Page")
                }
            ]
        }
    ]
