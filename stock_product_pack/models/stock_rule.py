# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, models


class ProcurementGroup(models.Model):
    _inherit = "procurement.group"

    def is_pack_dont_create_move(self, product):
        return (
            product
            and product.pack_ok
            and product.dont_create_move
            and product.pack_type == "detailed"
        )

    @api.model
    def run(self, procurements, raise_user_error=True):
        """If 'run' is called on a pack product storable.
        we remove the procurement with this product pack.
        """
        for procurement in procurements:
            if self.is_pack_dont_create_move(procurement.product_id):
                procurements.remove(procurement)

        return super().run(procurements, raise_user_error=raise_user_error)
