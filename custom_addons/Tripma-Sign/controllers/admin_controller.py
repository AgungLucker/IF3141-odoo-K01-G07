import base64
import csv
import io

from odoo import fields, http
from odoo.http import request

from .base_controller import TripmaBaseController
from .utils import parse_money


class TripmaAdminController(TripmaBaseController):
    def _check_sales_admin(self):
        user = request.env.user
        return (
            user.has_group("Tripma-Sign.group_tripma_admin")
            or user.has_group("base.group_system")
            or user.has_group("base.group_erp_manager")
        )

    def _external_order_context(self, created_order=False, errors=None, values=None):
        recent_orders = request.env["tripma.order"].search(
            [
                ("source_channel", "in", ["whatsapp", "offline", "phone"]),
            ],
            order="input_date desc, order_date desc",
            limit=5,
        )
        return {
            "created_order": created_order,
            "errors": errors or [],
            "values": values or {},
            "recent_orders": recent_orders,
            "channels": [
                ("whatsapp", "WhatsApp"),
                ("offline", "Langsung / Walk-in"),
                ("phone", "Telepon"),
            ],
        }

    @http.route("/tripma/admin/external-order", auth="user", website=True)
    def external_order_form(self, **kw):
        if not self._check_sales_admin():
            return request.redirect("/odoo")
        return self._render_tripma(
            "Tripma-Sign.external_order_form",
            self._external_order_context(),
        )

    @http.route(
        "/tripma/admin/external-order/success/<int:order_id>", auth="user", website=True
    )
    def external_order_success(self, order_id, **kw):
        if not self._check_sales_admin():
            return request.redirect("/odoo")
        order = request.env["tripma.order"].browse(order_id)
        if not order.exists():
            return request.redirect("/tripma/admin/external-order")
        return self._render_tripma(
            "Tripma-Sign.external_order_form",
            self._external_order_context(created_order=order),
        )

    @http.route(
        "/tripma/admin/external-order/submit",
        auth="user",
        methods=["POST"],
        website=True,
        csrf=True,
    )
    def submit_external_order(self, **post):
        if not self._check_sales_admin():
            return request.redirect("/odoo")
        required_fields = [
            "customer_name",
            "customer_phone",
            "customer_address",
            "product_name",
        ]
        errors = [
            "Field %s wajib diisi." % field.replace("_", " ")
            for field in required_fields
            if not (post.get(field) or "").strip()
        ]
        channel = (post.get("source_channel") or "").strip()
        if channel not in ["whatsapp", "offline", "phone"]:
            errors.append("Kanal pesanan tidak valid.")
        if errors:
            return self._render_tripma(
                "Tripma-Sign.external_order_form",
                self._external_order_context(errors=errors, values=post),
            )

        width = (post.get("width_cm") or "").strip()
        height = (post.get("height_cm") or "").strip()
        size = "%s x %s cm" % (width, height) if width or height else ""
        uploaded_file = request.httprequest.files.get("design_file")
        design_file = False
        if uploaded_file and uploaded_file.filename:
            design_file = base64.b64encode(uploaded_file.read())

        order = request.env["tripma.order"].create_external_order(
            {
                "source_channel": channel,
                "customer_name": (post.get("customer_name") or "").strip(),
                "customer_phone": (post.get("customer_phone") or "").strip(),
                "customer_email": (post.get("customer_email") or "").strip(),
                "company_name": (post.get("company_name") or "").strip(),
                "customer_address": (post.get("customer_address") or "").strip(),
                "product_name": (post.get("product_name") or "").strip(),
                "material": (post.get("material") or "").strip(),
                "size": size,
                "quantity": (post.get("quantity") or "1").strip(),
                "special_instructions": (
                    post.get("special_instructions") or ""
                ).strip(),
                "billing_total": parse_money(post.get("billing_total")),
                "order_date": post.get("order_date") or fields.Date.today(),
                "target_date": post.get("target_date") or "",
                "external_reference": (post.get("external_reference") or "").strip(),
                "external_notes": (post.get("external_notes") or "").strip(),
                "design_file": design_file,
            }
        )
        return request.redirect("/tripma/admin/external-order/success/%d" % order.id)

    # ----- Dashboard Admin Penjualan -----
    @http.route("/tripma/admin/dashboard", auth="user", website=True)
    def admin_dashboard(self, **kw):
        """
        FR-04: Dashboard Admin Penjualan.
        Hanya group_tripma_admin yang diizinkan masuk.
        Semua data pesanan ditampilkan (dijaga record rule di ir.rule.xml).
        """
        if not self._check_sales_admin():
            return self._redirect_unauthorized()

        Order = request.env["tripma.order"]
        values = {
            "total_orders": Order.search_count([]),
            "draft_count": Order.search_count([("state", "=", "draft")]),
            "waiting_count": Order.search_count([("state", "=", "waiting_payment")]),
            "queue_count": Order.search_count([("state", "=", "in_queue")]),
            "prod_count": Order.search_count(
                [
                    ("state", "=", "in_production"),
                    ("current_production_stage", "!=", "ready"),
                ]
            ),
            "done_count": Order.search_count(
                ["|", ("state", "=", "done"), ("current_production_stage", "=", "ready")]
            ),
            "recent_orders": Order.search([], order="create_date desc", limit=5),
            "recent_activities": Order.search(
                [("source_channel", "in", ["whatsapp", "offline", "phone"])],
                order="create_date desc",
                limit=3,
            ),
        }
        # Render ke QWeb template admin_dashboard
        return self._render_tripma("Tripma-Sign.admin_dashboard", values)

    @http.route("/tripma/admin/semua-pesanan", auth="user", website=True)
    def admin_semua_pesanan(self, **kw):
        """Halaman Semua Pesanan Kustom (Frontend)"""
        if not self._check_sales_admin():
            return self._redirect_unauthorized()

        Order = request.env["tripma.order"]
        all_orders = Order.search([], order="order_date desc, create_date desc")

        values = {
            "all_orders": all_orders,
        }
        return self._render_tripma("Tripma-Sign.admin_all_orders", values)

    @http.route("/tripma/admin/semua-pesanan/export", auth="user", website=True)
    def admin_export_pesanan(self, **kw):
        """Fungsi Export CSV untuk Semua Pesanan"""
        if not self._check_sales_admin():
            return self._redirect_unauthorized()

        Order = request.env["tripma.order"]
        orders = Order.search([], order="order_date desc, create_date desc")

        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow(
            [
                "No. Order",
                "Tanggal",
                "Pelanggan",
                "Produk",
                "Channel",
                "Status",
                "Total",
            ]
        )

        # Rows
        for order in orders:
            product_str = (
                order.product_specs.split("\n")[0]
                if order.product_specs and "\n" in order.product_specs
                else (order.product_specs or "-")
            )
            writer.writerow(
                [
                    order.name,
                    order.order_date.strftime("%Y-%m-%d") if order.order_date else "-",
                    order.customer_id.name or "-",
                    product_str,
                    order.source_channel,
                    order.state,
                    order.billing_total,
                ]
            )

        # Prepare Response
        response = request.make_response(
            output.getvalue(),
            headers=[
                ("Content-Type", "text/csv"),
                (
                    "Content-Disposition",
                    'attachment; filename="Semua_Pesanan_Tripma.csv"',
                ),
            ],
        )
        return response
