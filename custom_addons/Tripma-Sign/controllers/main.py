import datetime
from odoo import http
from odoo.http import request

STAGE_LABELS = {
    'waiting':  'Menunggu Antrian',
    'cutting':  'Pemapasan / Cutting',
    'printing': 'Printing / Produksi',
    'assembly': 'Pemasangan / Assembly',
    'finishing': 'Finishing / QC',
    'ready':    'Siap Dikirim',
}

ALL_STAGES = [
    ('waiting',   '📥', 'Menunggu Antrian',      'Belum mulai dikerjakan'),
    ('cutting',   '✂️', 'Persiapan / Cutting',   'Sedang dipotong / disiapkan'),
    ('printing',  '🖨️', 'Printing / Produksi',   'Sedang dicetak / diproduksi'),
    ('assembly',  '🔧', 'Pemasangan / Assembly',  'Tahap perakitan komponen'),
    ('finishing', '✨', 'Finishing / QC',         'Quality check & finishing'),
    ('ready',     '📦', 'Siap Dikirim',           'Pesanan selesai, siap pickup'),
]


class TripmaUI(http.Controller):
    @http.route('/tripma/order', auth='public', website=True)
    def mockup_order(self, **kw):
        return request.redirect('/Tripma-Sign/static/mockup/03_form_order.html')


class TripmaProductionController(http.Controller):

    def _check_production_staff(self):
        return request.env.user.has_group('Tripma-Sign.group_tripma_production_staff')

    def _compute_progress(self, order):
        state = order.state
        stage = order.current_production_stage
        if state == 'done':
            return 100, 4
        if state == 'in_production' and stage == 'ready':
            return 80, 3
        if state in ('in_queue', 'in_production'):
            return 55, 2
        if state == 'waiting_payment':
            return 25, 1
        return 0, 0

    @http.route('/tripma/production', auth='user', website=True)
    def production_dashboard(self, **kw):
        if not self._check_production_staff():
            return request.redirect('/odoo')
        Order = request.env['tripma.order']
        today = datetime.date.today()
        antrian_orders = Order.search([('state', '=', 'in_queue')])
        in_progress_orders = Order.search([
            ('state', '=', 'in_production'),
            ('current_production_stage', 'in', ('cutting', 'printing', 'assembly')),
        ])
        finishing_orders = Order.search([
            ('state', '=', 'in_production'),
            ('current_production_stage', '=', 'finishing'),
        ])
        siap_kirim_orders = Order.search([
            ('state', '=', 'in_production'),
            ('current_production_stage', '=', 'ready'),
        ])
        deadline_threshold = today + datetime.timedelta(days=2)
        near_deadline = Order.search([
            ('state', 'in', ['in_queue', 'in_production']),
            ('order_date', '<=', deadline_threshold),
            ('order_date', '>=', today),
        ])
        return request.render('Tripma-Sign.production_dashboard', {
            'antrian_orders':     antrian_orders,
            'in_progress_orders': in_progress_orders,
            'finishing_orders':   finishing_orders,
            'siap_kirim_orders':  siap_kirim_orders,
            'queue_count':        len(antrian_orders),
            'production_count':   len(in_progress_orders) + len(finishing_orders),
            'ready_count':        len(siap_kirim_orders),
            'near_deadline_count': len(near_deadline),
            'today':              today,
            'STAGE_LABELS':       STAGE_LABELS,
        })

    @http.route('/tripma/production/update/<int:order_id>', auth='user', website=True)
    def update_status_form(self, order_id, **kw):
        if not self._check_production_staff():
            return request.redirect('/odoo')
        order = request.env['tripma.order'].browse(order_id)
        if not order.exists():
            return request.redirect('/tripma/production')
        history = order.production_status_ids.sorted('update_time', reverse=True)
        pending_orders = request.env['tripma.order'].search([
            ('state', 'in', ['in_queue', 'in_production']),
            ('id', '!=', order_id),
        ], limit=10)
        return request.render('Tripma-Sign.update_status', {
            'order':          order,
            'history':        history,
            'pending_orders': pending_orders,
            'all_stages':     ALL_STAGES,
            'STAGE_LABELS':   STAGE_LABELS,
        })

    @http.route('/tripma/production/update/submit', auth='user', methods=['POST'], website=True, csrf=True)
    def submit_status_update(self, **post):
        if not self._check_production_staff():
            return request.redirect('/odoo')
        order_id = int(post.get('order_id', 0))
        stage_name = post.get('stage_name', '').strip()
        note = post.get('note', '').strip()
        valid_stages = ['waiting', 'cutting', 'printing', 'assembly', 'finishing', 'ready']
        if not order_id or stage_name not in valid_stages:
            return request.redirect('/tripma/production')
        order = request.env['tripma.order'].browse(order_id)
        if not order.exists():
            return request.redirect('/tripma/production')
        request.env['tripma.production.status'].create({
            'order_id':   order_id,
            'stage_name': stage_name,
            'note':       note or False,
            'updated_by': request.env.user.id,
        })
        if stage_name in ('cutting', 'printing', 'assembly', 'finishing'):
            if order.state == 'in_queue':
                order.sudo().action_start_production()
        elif stage_name == 'ready':
            if order.state == 'in_production':
                order.sudo().action_complete()
        return request.redirect('/tripma/production/update/%d' % order_id)

    @http.route('/tripma/track', auth='public', website=True)
    def track_order_search(self, q='', **kw):
        if q:
            return request.redirect('/tripma/track/%s' % q.strip())
        orders = []
        if request.env.user and not request.env.user._is_public():
            orders = request.env['tripma.order'].search(
                [('customer_id', '=', request.env.user.partner_id.id)])
        return request.render('Tripma-Sign.track_order', {
            'order':        False,
            'orders':       orders,
            'query':        q,
            'order_name':   '',
            'progress_pct': 0,
            'active_step':  0,
        })

    @http.route('/tripma/track/<string:order_name>', auth='public', website=True)
    def track_order_detail(self, order_name, **kw):
        order = request.env['tripma.order'].sudo().search(
            [('name', '=', order_name)], limit=1)
        progress_pct, active_step = self._compute_progress(order) if order else (0, 0)
        return request.render('Tripma-Sign.track_order', {
            'order':        order or False,
            'orders':       [],
            'query':        order_name,
            'order_name':   order_name,
            'progress_pct': progress_pct,
            'active_step':  active_step,
        })
