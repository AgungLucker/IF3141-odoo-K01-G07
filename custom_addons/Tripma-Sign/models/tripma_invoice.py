from odoo import api, fields, models


class TripmaInvoice(models.Model):
    _name = 'tripma.invoice'
    _description = 'Tripma Invoice'
    _order = 'issue_date desc, name desc'

    name = fields.Char(string='Invoice Number', required=True, copy=False, readonly=True, default='New')
    issue_date = fields.Date(string='Issue Date', required=True, default=fields.Date.today)
    payment_status = fields.Selection(
        selection=[
            ('unpaid', 'Belum Dibayar'),
            ('paid', 'Lunas'),
            ('cancelled', 'Dibatalkan'),
        ],
        string='Payment Status',
        required=True,
        default='unpaid',
    )
    order_id = fields.Many2one('tripma.order', string='Order', required=True, ondelete='cascade')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('tripma.invoice') or 'New'
        return super().create(vals_list)

    def update_payment_status(self, new_status):
        self.write({'payment_status': new_status})
