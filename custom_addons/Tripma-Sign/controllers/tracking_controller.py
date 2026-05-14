from odoo import http
from odoo.http import request

from .base_controller import TripmaBaseController


class TripmaTrackController(TripmaBaseController):
    def _compute_progress(self, order):
        state = order.state
        stage = order.current_production_stage
        if state == "done":
            return 100, 4
        if state == "in_production" and stage == "ready":
            return 80, 3
        if state in ("in_queue", "in_production"):
            return 55, 2
        if state == "waiting_payment":
            return 25, 1
        return 0, 0

    @http.route("/tripma/track", auth="public", website=True)
    def track_order_search(self, q="", **kw):
        if q:
            return request.redirect("/tripma/track/%s" % q.strip())
        orders = []
        if request.env.user and not request.env.user._is_public():
            orders = request.env["tripma.order"].search(
                [("customer_id", "=", request.env.user.partner_id.id)]
            )
        return self._render_tripma(
            "Tripma-Sign.track_order_page",
            {
                "order": False,
                "orders": orders,
                "query": q,
                "order_name": "",
                "progress_pct": 0,
                "active_step": 0,
            },
        )

    @http.route("/tripma/track/<string:order_name>", auth="public", website=True)
    def track_order_detail(self, order_name, **kw):
        order = (
            request.env["tripma.order"]
            .sudo()
            .search([("name", "=", order_name)], limit=1)
        )
        progress_pct, active_step = self._compute_progress(order) if order else (0, 0)
        return self._render_tripma(
            "Tripma-Sign.track_order_page",
            {
                "order": order or False,
                "orders": [],
                "query": order_name,
                "order_name": order_name,
                "progress_pct": progress_pct,
                "active_step": active_step,
            },
        )
