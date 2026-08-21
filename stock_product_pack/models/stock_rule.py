# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, models


class StockRule(models.Model):
    _inherit = "stock.rule"

    @api.model
    def run(self, procurements, raise_user_error=True):
        """If 'run' is called on a pack product storable with
        'dont_create_move' active, we remove the procurement with this
        product pack, regardless of its pack display type (detailed or
        non detailed).
        """
        procurements = [
            procurement
            for procurement in procurements
            if not (
                procurement.product_id
                and procurement.product_id.pack_ok
                and procurement.product_id.dont_create_move
            )
        ]
        return super().run(procurements, raise_user_error=raise_user_error)
