# Copyright 2019 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, api, models
from odoo.exceptions import ValidationError


class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.constrains("pack_line_ids")
    def check_website_published(self):
        for rec in self.filtered("is_published"):
            unpublished = rec.pack_line_ids.mapped("product_id").filtered(
                lambda x: not x.is_published
            )
            if unpublished:
                raise ValidationError(
                    _(
                        "You can't add unpublished products (%(unpublished_products)s) to"
                        "a published pack (%(pack_name)s)"
                    )
                    % {
                        "unpublished_products": ", ".join(unpublished.mapped("name")),
                        "pack_name": rec.name,
                    }
                )
