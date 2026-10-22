import re

from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    lines = env["sale.order.line"].search(
        [("pack_parent_line_id", "!=", False), ("name", "=like", "> %")]
    )
    for line in lines:
        name = re.sub(r"^(> )+", "", line.name)
        display_name = line.product_id.with_context(
            lang=line.order_id._get_lang()
        ).display_name
        if not name.startswith(display_name):
            continue
        name = name[len(display_name) :].lstrip("\n")
        cr.execute(
            "UPDATE sale_order_line SET name = %s WHERE id = %s", (name, line.id)
        )
