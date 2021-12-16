# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ProductPackType(models.Model):

    _name = "product.pack.type"
    _description = "Product Pack Type"

    name = fields.Char()
    description = fields.Text()
    color = fields.Integer()
    active = fields.Boolean(default=True)

    product_pack_ids = fields.One2many(
        comodel_name="product.template",
        inverse_name="pack_type_id",
        domain=[("pack_ok", "=", True)],
        help="These are the pack products of this type",
    )
    product_pack_count = fields.Integer(compute="_compute_product_pack_count")

    def _compute_product_pack_count(self):
        for pack_type in self:
            pack_type.product_pack_count = len(pack_type.product_pack_ids)

    def _get_default_pack_action_context(self):
        return {
            "default_pack_type_id": self.id,
            "default_pack_ok": 1,
        }

    def action_product_pack_view(self):
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "product_pack.action_product_pack"
        )
        if len(self) == 1:
            action["context"] = self._get_default_pack_action_context()
        action["domain"] = [("pack_type_id", "in", self.ids)]
        return action
