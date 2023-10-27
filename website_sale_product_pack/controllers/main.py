from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale

class WebsiteSale(WebsiteSale):

    def shop(self, page=0, category=None, search='', min_price=0.0, max_price=0.0, ppg=False, **post):
        request.update_context(whole_pack_price=True)
        return super().shop(page=page, category=category, search=search, min_price=min_price, max_price=max_price, ppg=ppg, **post)
