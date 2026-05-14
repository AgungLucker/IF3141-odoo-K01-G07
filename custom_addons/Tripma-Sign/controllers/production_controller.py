from .base_controller import TripmaBaseController
from .utils import STAGE_LABELS, ALL_STAGES
from odoo.http import request
from odoo import http
import datetime

class TripmaProductionController(TripmaBaseController):

    @http.route('/tripma/production', auth='user', website=True)
    def production_dashboard(self, **kw):
        if not self.is_admin() and not self.is_production_staff():
            return request.redirect('/odoo')
        Order = request.env['tripma.order']
        today = datetime.date.today()
        antrian_orders = Order.search([('state', '=', 'in_queue')])
        in_progress_orders = Order.search([
            ('state', '=', 'in_production'),
            '|',
            ('current_production_stage', '=', False),
            ('current_production_stage', 'in', ['waiting', 'cutting', 'printing', 'assembly']),
        ])
        finishing_orders = Order.search([
            ('state', '=', 'in_production'),
            ('current_production_stage', '=', 'finishing'),
        ])
        siap_kirim_orders = Order.search([
            '|',
            ('current_production_stage', '=', 'ready'),
            ('state', '=', 'done'),
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
        if not self.is_admin() and not self.is_production_staff():
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
        if not self.is_admin() and not self.is_production_staff():
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
        request.env['tripma.production.status'].sudo().create({
            'order_id':   order_id,
            'stage_name': stage_name,
            'note':       note or False,
            'updated_by': request.env.user.id,
        })
        if stage_name in ('cutting', 'printing', 'assembly', 'finishing', 'ready'):
            if order.state == 'in_queue':
                order.sudo().action_start_production()
        return request.redirect('/tripma/production/update/%d' % order_id)