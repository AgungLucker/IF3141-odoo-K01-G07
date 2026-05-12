from odoo import http
from odoo.http import request

class TripmaUI(http.Controller):
    @http.route('/tripma/order', auth='public', website=True)
    def mockup_order(self, **kw):
        # Redirect ke file HTML statis kita!
        return request.redirect('/Tripma-Sign/static/mockup/03_form_order.html')