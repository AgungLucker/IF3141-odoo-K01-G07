import base64

from odoo import http
from odoo.http import request

from .base_controller import TripmaBaseController


class TripmaCustomerController(TripmaBaseController):
    @http.route("/tripma/catalog", type="http", auth="public", website=True)
    def catalog(self, **kw):
        """
        FR-01: Menampilkan katalog produk signage.
        """
        products = (
            request.env["tripma.product"].sudo().search([("is_active", "=", True)])
        )
        return self._render_tripma(
            "Tripma-Sign.tripma_catalog_page", {"products": products}
        )

    @http.route("/tripma/order/form", type="http", auth="user", website=True)
    def order_form(self, **kw):
        """
        FR-01: Menampilkan formulir pemesanan mandiri, memanfaatkan pengecekan role terpusat.
        """
        if self._get_current_user_role() != "customer":
            return request.redirect("/tripma/akses-ditolak")

        product_id = kw.get("product_id")
        try:
            product = (
                request.env["tripma.product"].sudo().browse(int(product_id))
                if product_id and product_id.isdigit()
                else False
            )
        except (ValueError, TypeError):
            product = False

        return self._render_tripma(
            "Tripma-Sign.tripma_order_form_template",
            {"customer": request.env.user.partner_id, "selected_product": product},
        )

    @http.route(
        "/tripma/order/submit",
        type="http",
        auth="user",
        methods=["POST"],
        website=True,
        csrf=True,
    )
    def order_submit(self, **post):
        """
        FR-01: Memproses input pesanan dan file desain secara terpusat.
        Otomatis menghitung billing_total berdasarkan produk dan spek.
        """
        if self._get_current_user_role() != "customer":
            return request.redirect("/tripma/akses-ditolak")

        product_specs = post.get("product_specs")
        product_id = post.get("product_id")
        try:
            quantity = int(post.get("quantity", 1))
            width = float(post.get("width_cm", 0))
            height = float(post.get("height_cm", 0))
        except (ValueError, TypeError):
            return request.redirect(
                "/tripma/order/form?error=Jumlah dan ukuran harus berupa angka"
            )

        shipping_address = post.get("shipping_address")
        design_file = request.httprequest.files.get("design_file")

        if not product_specs:
            return request.redirect(
                "/tripma/order/form?error=Spesifikasi produk wajib diisi"
            )

        if not shipping_address:
            return request.redirect(
                "/tripma/order/form?error=Alamat pengiriman wajib diisi"
            )

        # Automated Pricing Logic
        billing_total = 0.0
        if product_id:
            product = request.env["tripma.product"].sudo().browse(int(product_id))
            if product.exists():
                if product.price_type == "unit":
                    billing_total = product.base_price * quantity
                elif product.price_type == "area":
                    # Area in square meters (width * height / 10000)
                    area = (width * height) / 10000.0
                    billing_total = product.base_price * area * quantity

        file_data = False
        if design_file and design_file.filename:
            file_data = base64.b64encode(design_file.read())

        new_order = (
            request.env["tripma.order"]
            .sudo()
            .create(
                {
                    "customer_id": request.env.user.partner_id.id,
                    "product_id": int(product_id) if product_id else False,
                    "product_specs": product_specs,
                    "quantity": quantity,
                    "width_cm": width,
                    "height_cm": height,
                    "design_file": file_data,
                    "shipping_address": shipping_address,
                    "billing_total": billing_total,
                    "source_channel": "website",
                    "state": "draft",
                }
            )
        )
        new_order.action_issue_invoice()
        return request.redirect(f"/tripma/order/success/{new_order.id}")

    @http.route(
        "/tripma/order/success/<int:order_id>", type="http", auth="user", website=True
    )
    def order_success(self, order_id, **kw):
        """
        FR-01: Menampilkan rincian invoice dan nomor order setelah submit.
        """
        order = request.env["tripma.order"].sudo().browse(order_id)
        if (not order.exists()) or (
            order.customer_id.id != request.env.user.partner_id.id
        ):
            return request.redirect("/tripma/track")
        else:
            return self._render_tripma(
                "Tripma-Sign.tripma_order_success_template",
                {"order": order, "invoice": order.invoice_ids[:1]},
            )

    @http.route("/tripma/customer/dashboard", auth="user", website=True)
    def customer_dashboard(self, **kw):
        """
        FR-04: Dashboard utama pelanggan untuk melihat daftar pesanan.
        """
        if self._get_current_user_role() != "customer":
            return request.redirect("/tripma/akses-ditolak")
        else:
            orders = request.env["tripma.order"].search(
                [("customer_id", "=", request.env.user.partner_id.id)]
            )
            return self._render_tripma(
                "Tripma-Sign.customer_dashboard_template", {"orders": orders}
            )

    @http.route(
        "/tripma/invoice/<int:invoice_id>", type="http", auth="user", website=True
    )
    def customer_invoice(self, invoice_id, **kw):
        """
        FR-01 / UC-04: Menampilkan rincian invoice untuk dibayar.
        """
        if self._get_current_user_role() != "customer":
            return request.redirect("/tripma/akses-ditolak")

        invoice = request.env["tripma.invoice"].sudo().browse(invoice_id)
        if (
            not invoice.exists()
            or invoice.order_id.customer_id.id != request.env.user.partner_id.id
        ):
            return request.redirect("/tripma/customer/dashboard")

        return self._render_tripma(
            "Tripma-Sign.tripma_invoice_page",
            {"invoice": invoice, "order": invoice.order_id},
        )

    @http.route(
        "/tripma/invoice/pay/<int:invoice_id>",
        type="http",
        auth="user",
        methods=["POST"],
        website=True,
        csrf=True,
    )
    def customer_pay_invoice(self, invoice_id, **kw):
        """
        Simulasi pembayaran invoice oleh pelanggan.
        """
        if self._get_current_user_role() != "customer":
            return request.redirect("/tripma/akses-ditolak")

        invoice = request.env["tripma.invoice"].sudo().browse(invoice_id)
        if (
            invoice.exists()
            and invoice.order_id.customer_id.id == request.env.user.partner_id.id
        ):
            # Simulasi pembayaran lunas dan update state order
            invoice.sudo().write({"payment_status": "paid"})
            if invoice.order_id.state == "waiting_payment":
                invoice.order_id.sudo().action_validate_payment()

        return request.redirect(f"/tripma/invoice/{invoice_id}")
