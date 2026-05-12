from odoo import api, fields, models


class TripmaOrder(models.Model):
    _name = 'tripma.order'
    _description = 'Tripma Order'
    _order = 'order_date desc, name desc'

    name = fields.Char(string='Order Number', required=True, copy=False, readonly=True, default='New')
    order_date = fields.Date(string='Order Date', required=True, default=fields.Date.today)
    product_specs = fields.Text(string='Product Specifications')
    design_file = fields.Binary(string='Design File', attachment=True)
    billing_total = fields.Monetary(string='Billing Total', currency_field='currency_id')
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id,
        required=True,
    )
    source_channel = fields.Selection(
        selection=[
            ('website', 'Website'),
            ('whatsapp', 'WhatsApp'),
            ('offline', 'Offline / Walk-in'),
        ],
        string='Source Channel',
        required=True,
        default='website',
    )
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('waiting_payment', 'Menunggu Pembayaran'),
            ('in_queue', 'Antri Produksi'),
            ('in_production', 'Proses Produksi'),
            ('done', 'Selesai Produksi'),
        ],
        string='Status',
        required=True,
        default='draft',
    )
    customer_id = fields.Many2one('res.partner', string='Customer', required=True, ondelete='restrict')
    managed_by = fields.Many2one(
        'res.users',
        string='Managed By',
        help='Admin who input this order (external/offline orders)',
    )
    input_date = fields.Datetime(string='Input Date')

    invoice_ids = fields.One2many('tripma.invoice', 'order_id', string='Invoices')
    production_status_ids = fields.One2many('tripma.production.status', 'order_id', string='Production History')
    current_production_stage = fields.Selection(
        selection=[
            ('waiting', 'Menunggu Antrian'),
            ('cutting', 'Pemapasan / Cutting'),
            ('printing', 'Printing / Produksi'),
            ('assembly', 'Pemasangan / Assembly'),
            ('finishing', 'Finishing / QC'),
            ('ready', 'Siap Kirim'),
        ],
        string='Current Production Stage',
        compute='_compute_current_production_stage',
        store=True,
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('tripma.order') or 'New'
        return super().create(vals_list)

    @api.depends('production_status_ids.stage_name', 'production_status_ids.update_time')
    def _compute_current_production_stage(self):
        for order in self:
            latest = order.production_status_ids.sorted('update_time', reverse=True)
            order.current_production_stage = latest[0].stage_name if latest else False

    def action_issue_invoice(self):
        """STD: draft -> waiting_payment. Creates invoice."""
        for order in self:
            if order.state == 'draft':
                self.env['tripma.invoice'].create({'order_id': order.id})
                order.state = 'waiting_payment'

    def action_validate_payment(self):
        """STD: waiting_payment -> in_queue."""
        for order in self:
            if order.state == 'waiting_payment':
                order.invoice_ids.filtered(
                    lambda i: i.payment_status == 'unpaid'
                ).write({'payment_status': 'paid'})
                order.state = 'in_queue'

    def action_start_production(self):
        """STD: in_queue -> in_production."""
        for order in self:
            if order.state == 'in_queue':
                order.state = 'in_production'

    def action_complete(self):
        """STD: in_production -> done."""
        for order in self:
            if order.state == 'in_production':
                order.state = 'done'

    def get_order_summary(self):
        self.ensure_one()
        return {
            'name': self.name,
            'customer': self.customer_id.name,
            'state': self.state,
            'billing_total': self.billing_total,
            'current_stage': self.current_production_stage,
        }
