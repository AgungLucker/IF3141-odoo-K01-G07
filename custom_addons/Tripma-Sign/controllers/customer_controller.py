from .base_controller import TripmaBaseController
from odoo.http import request
from odoo import http

class TripmaCustomerController(TripmaBaseController):
    # ----- Dashboard Pelanggan -----
    @http.route('/tripma/pelanggan/pesanan', auth='user', website=True)
    def customer_pesanan(self, **kw):
        """
        FR-04: Halaman lacak pesanan untuk pelanggan.
        Record rule di ir.rule.xml memastikan hanya pesanan milik sendiri
        yang bisa diakses di level database — controller ini hanya routing.
        """
        if not request.env.user.has_group('Tripma-Sign.group_tripma_customer'):
            return request.redirect('/web')
        return request.redirect('/tripma/track')

    @http.route('/tripma/pelanggan/invoice', auth='user', website=True)
    def customer_invoice(self, **kw):
        """FR-04: Halaman invoice pelanggan — Customer only."""
        if not request.env.user.has_group('Tripma-Sign.group_tripma_customer'):
            return request.redirect('/web')
        # (Template QWeb sebenarnya dikerjakan di FR lain)
        return request.render('website.404')