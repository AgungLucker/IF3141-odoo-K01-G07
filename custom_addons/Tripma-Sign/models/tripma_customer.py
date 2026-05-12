from odoo import fields, models


class TripmaCustomer(models.Model):
    _inherit = 'res.partner'

    is_tripma_customer = fields.Boolean(string='Is Tripma Customer', default=False)
