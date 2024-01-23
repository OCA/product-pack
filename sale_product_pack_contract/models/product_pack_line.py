# Copyright 2023 Foodles (http://www.foodles.co).
# @author Pierre Verkest <pierreverkest84@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import _, api, models
from odoo.exceptions import UserError


class ProductPack(models.Model):
    _inherit = "product.pack.line"

    @api.constrains(
        "parent_product_id",
        "product_id",
    )
    def _check_contract_component(self):
        for pack_product, pack_lines in self.group_recordset_by(
            lambda pack_line: pack_line.parent_product_id
        ):
            if (
                pack_product.pack_type != "detailed"
                or pack_product.pack_component_price != "detailed"
            ):
                component_contract_products = pack_lines.filtered(
                    lambda line: line.product_id.is_contract
                )
                if component_contract_products.exists():
                    raise UserError(
                        _(
                            "This pack '%s' contains components %r that are marked "
                            "to be contract products. At the moment contract component "
                            "support only on detailed pack type and detailed "
                            "component price pack."
                        )
                        % (
                            pack_product.name,
                            component_contract_products.mapped("product_id.name"),
                        )
                    )
