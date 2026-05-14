from odoo import http
from odoo.http import request

class TripmaBaseController(http.Controller):

    def is_admin(self):
        user = request.env.user
        return (
            user.has_group('Tripma-Sign.group_tripma_admin')
            or user.has_group('base.group_system')
            or user.has_group('base.group_erp_manager')
        )

    def is_production_staff(self):
        return (
            request.env.user.has_group(
                'Tripma-Sign.group_tripma_production_staff'
            )
            or self.is_admin()
        )

    def is_customer(self):
        return request.env.user.has_group(
            'Tripma-Sign.group_tripma_customer'
        )

    def redirect_unauthorized(self):
        return request.redirect('/tripma/akses-ditolak')