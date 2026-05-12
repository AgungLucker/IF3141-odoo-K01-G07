from odoo import fields, models


class TripmaUsers(models.Model):
    _inherit = 'res.users'

    tripma_role = fields.Selection(
        selection=[
            ('admin', 'Admin Penjualan'),
            ('production_staff', 'Staf Produksi'),
        ],
        string='Tripma Role',
        default=False,
    )
