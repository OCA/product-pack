# Copyright 2019 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = "product.template"

    pack_type = fields.Selection(
        [("detailed", "Detailed"), ("non_detailed", "Non Detailed")],
        "Pack Type",
        help="On sale orders or purchase orders:\n"
        "* Detailed: Display components individually in the sale order.\n"
        "* Non Detailed: Do not display components individually in the"
        " sale order.",
    )
    pack_component_price = fields.Selection(
        [
            ("detailed", "Detailed per component"),
            ("totalized", "Totalized in main product"),
            ("ignored", "Ignored"),
        ],
        "Pack component price",
        help="On sale orders or purchase orders:\n"
        "* Detailed per component: Detail lines with prices.\n"
        "* Totalized in main product: Detail lines merging "
        "lines prices on pack (don't show component prices).\n"
        "* Ignored: Use product pack price (ignore detail line prices).",
    )
    pack_ok = fields.Boolean(
        "Is Pack?",
        help="Is a Product Pack?",
    )
    pack_line_ids = fields.One2many(
        related="product_variant_ids.pack_line_ids",
    )
    used_in_pack_line_ids = fields.One2many(
        related="product_variant_ids.used_in_pack_line_ids",
        readonly=True,
    )
    pack_modifiable = fields.Boolean(
        help="If you check this field yo will be able to edit "
        "sale/purchase order line relate to its component",
    )

    @api.onchange("pack_type", "pack_component_price")
    def onchange_pack_type(self):
        products = self.filtered(
            lambda x: x.pack_modifiable
            and (x.pack_type != "detailed" or x.pack_component_price != "detailed")
        )
        for rec in products:
            rec.pack_modifiable = False

    @api.constrains("company_id", "product_variant_ids")
    def _check_pack_line_company(self):
        """Check packs are related to packs of same company."""
        for rec in self:
            for line in rec.pack_line_ids:
                if (
                    line.product_id.company_id and rec.company_id
                ) and line.product_id.company_id != rec.company_id:
                    raise ValidationError(
                        _(
                            "Pack lines products company must be the same as the "
                            "parent product company"
                        )
                    )
            for line in rec.used_in_pack_line_ids:
                if (
                    line.product_id.company_id and rec.company_id
                ) and line.parent_product_id.company_id != rec.company_id:
                    raise ValidationError(
                        _(
                            "Pack lines products company must be the same as the "
                            "parent product company"
                        )
                    )

    def write(self, vals):
        """We remove from product.product to avoid error."""
        _vals = vals.copy()
        if vals.get("pack_line_ids", False):
            self.product_variant_ids.write({"pack_line_ids": vals.get("pack_line_ids")})
            _vals.pop("pack_line_ids")
        return super().write(_vals)
