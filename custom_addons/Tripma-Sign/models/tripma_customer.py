from odoo import api , fields , models

class TripmaCustomer(models.Model) :
    _inherit = 'res.partner'

    is_tripma_customer = fields.Boolean(
        string = 'Is Tripma Customer', 
        default = False,
        help = "Centang jika partner ini adalah pelanggan layanan signage."
    )

    tripma_order_ids = fields.One2many(
        'tripma.order', 
        'customer_id', 
        string = 'Pesanan Tripma'
    )

    tripma_order_count = fields.Integer(
        string = 'Jumlah Pesanan', 
        compute = '_compute_tripma_order_count'
    )

    @api.depends('tripma_order_ids')
    def _compute_tripma_order_count(self) :
        for (partner) in (self) :
            partner.tripma_order_count = len(partner.tripma_order_ids)

    def action_view_tripma_orders(self) :
        self.ensure_one()
        return {
            'name' : 'Pesanan Pelanggan',
            'type' : 'ir.actions.act_window',
            'res_model' : 'tripma.order',
            'view_mode' : 'tree,form',
            'domain' : [('customer_id' , '=' , self.id)],
            'context' : {'default_customer_id' : self.id}
        }