from odoo import api, fields, models


class TripmaProductionStatus(models.Model):
    _name = 'tripma.production.status'
    _description = 'Tripma Production Status Log'
    _order = 'update_time desc'

    name = fields.Char(string='Reference', required=True, copy=False, readonly=True, default='New')
    stage_name = fields.Selection(
        selection=[
            ('waiting', 'Menunggu Antrian'),
            ('cutting', 'Pemapasan / Cutting'),
            ('printing', 'Printing / Produksi'),
            ('assembly', 'Pemasangan / Assembly'),
            ('finishing', 'Finishing / QC'),
            ('ready', 'Siap Kirim'),
        ],
        string='Stage',
        required=True,
    )
    update_time = fields.Datetime(string='Update Time', required=True, default=fields.Datetime.now)
    order_id = fields.Many2one('tripma.order', string='Order', required=True, ondelete='cascade')
    updated_by = fields.Many2one('res.users', string='Updated By', default=lambda self: self.env.user)
    note = fields.Text(string='Notes')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('tripma.production.status') or 'New'
        return super().create(vals_list)

    def get_latest_status(self):
        self.ensure_one()
        return self.order_id.production_status_ids.sorted('update_time', reverse=True)[:1]
