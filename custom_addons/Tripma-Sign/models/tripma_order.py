from odoo import api, fields, models


class TripmaOrder(models.Model):
    _name = "tripma.order"
    _description = "Tripma Order"
    _order = "order_date desc, name desc"

    name = fields.Char(
        string="Order Number", required=True, copy=False, readonly=True, default="New"
    )
    order_date = fields.Date(
        string="Order Date", required=True, default=fields.Date.today
    )
    product_specs = fields.Text(string="Product Specifications")
    design_file = fields.Binary(string="Design File", attachment=True)
    billing_total = fields.Monetary(
        string="Billing Total", currency_field="currency_id"
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
        required=True,
    )
    source_channel = fields.Selection(
        selection=[
            ("website", "Website"),
            ("whatsapp", "WhatsApp"),
            ("offline", "Offline / Walk-in"),
            ("phone", "Telepon"),
        ],
        string="Source Channel",
        required=True,
        default="website",
    )
    external_reference = fields.Char(string="External Reference")
    external_notes = fields.Text(string="External Channel Notes")
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("waiting_payment", "Menunggu Pembayaran"),
            ("in_queue", "Antri Produksi"),
            ("in_production", "Proses Produksi"),
            ("done", "Selesai Produksi"),
        ],
        string="Status",
        required=True,
        default="draft",
    )
    customer_id = fields.Many2one(
        "res.partner", string="Customer", required=True, ondelete="restrict"
    )
    managed_by = fields.Many2one(
        "res.users",
        string="Managed By",
        help="Admin who input this order (external/offline orders)",
    )
    input_date = fields.Datetime(string="Input Date")

    product_id = fields.Many2one("tripma.product", string="Selected Product")
    quantity = fields.Integer(string="Quantity", default=1)
    width_cm = fields.Float(string="Width (cm)")
    height_cm = fields.Float(string="Height (cm)")
    shipping_address = fields.Text(string="Shipping Address")

    invoice_ids = fields.One2many("tripma.invoice", "order_id", string="Invoices")
    production_status_ids = fields.One2many(
        "tripma.production.status", "order_id", string="Production History"
    )
    current_production_stage = fields.Selection(
        selection=[
            ("waiting", "Menunggu Antrian"),
            ("cutting", "Pemapasan / Cutting"),
            ("printing", "Printing / Produksi"),
            ("assembly", "Pemasangan / Assembly"),
            ("finishing", "Finishing / QC"),
            ("ready", "Siap Kirim"),
        ],
        string="Current Production Stage",
        compute="_compute_current_production_stage",
        store=True,
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "New") == "New":
                vals["name"] = (
                    self.env["ir.sequence"].next_by_code("tripma.order") or "New"
                )
        return super().create(vals_list)

    @api.depends(
        "production_status_ids.stage_name", "production_status_ids.update_time"
    )
    def _compute_current_production_stage(self):
        for order in self:
            latest = order.production_status_ids.sorted("update_time", reverse=True)
            order.current_production_stage = latest[0].stage_name if latest else False

    def action_issue_invoice(self):
        """STD: draft -> waiting_payment. Creates invoice."""
        for order in self:
            if order.state == "draft":
                self.env["tripma.invoice"].create({"order_id": order.id})
                order.state = "waiting_payment"

    def action_validate_payment(self):
        """STD: waiting_payment -> in_queue."""
        for order in self:
            if order.state == "waiting_payment":
                order.invoice_ids.filtered(
                    lambda i: i.payment_status == "unpaid"
                ).write({"payment_status": "paid"})
                order.state = "in_queue"

    def action_start_production(self):
        """STD: in_queue -> in_production."""
        for order in self:
            if order.state == "in_queue":
                order.state = "in_production"

    def action_complete(self):
        """STD: in_production -> done."""
        for order in self:
            if order.state == "in_production":
                order.state = "done"

    @api.model
    def create_external_order(self, vals):
        """Create a centralized external order and put it in the production queue."""
        partner = self._find_or_create_external_customer(vals)
        order = self.create(
            {
                "customer_id": partner.id,
                "order_date": vals.get("order_date") or fields.Date.today(),
                "product_specs": self._build_external_product_specs(vals),
                "design_file": vals.get("design_file") or False,
                "billing_total": vals.get("billing_total") or 0.0,
                "source_channel": vals.get("source_channel") or "whatsapp",
                "state": "in_queue",
                "managed_by": self.env.user.id,
                "input_date": fields.Datetime.now(),
                "external_reference": vals.get("external_reference") or False,
                "external_notes": vals.get("external_notes") or False,
            }
        )
        self.env["tripma.production.status"].create(
            {
                "order_id": order.id,
                "stage_name": "waiting",
                "updated_by": self.env.user.id,
                "note": "Pesanan eksternal didaftarkan oleh admin dan masuk antrian produksi.",
            }
        )
        return order

    @api.model
    def _find_or_create_external_customer(self, vals):
        Partner = self.env["res.partner"].sudo()
        phone = (vals.get("customer_phone") or "").strip()
        email = (vals.get("customer_email") or "").strip()
        name = (vals.get("customer_name") or vals.get("company_name") or "").strip()
        domain = []
        if phone:
            domain = ["|", ("phone", "=", phone), ("mobile", "=", phone)]
        elif email:
            domain = [("email", "=", email)]
        partner = Partner.search(domain, limit=1) if domain else Partner.browse()
        if partner:
            update_vals = {"is_tripma_customer": True}
            if vals.get("customer_address") and not partner.street:
                update_vals["street"] = vals["customer_address"]
            if email and not partner.email:
                update_vals["email"] = email
            partner.write(update_vals)
            return partner
        return Partner.create(
            {
                "name": name,
                "phone": phone or False,
                "mobile": phone or False,
                "email": email or False,
                "street": vals.get("customer_address") or False,
                "is_tripma_customer": True,
            }
        )

    @api.model
    def _build_external_product_specs(self, vals):
        parts = []
        for label, key in [
            ("Usaha/instansi", "company_name"),
            ("Produk", "product_name"),
            ("Bahan", "material"),
            ("Ukuran", "size"),
            ("Jumlah", "quantity"),
            ("Target selesai", "target_date"),
            ("Instruksi", "special_instructions"),
        ]:
            value = vals.get(key)
            if value:
                suffix = " unit" if key == "quantity" else ""
                parts.append("%s: %s%s" % (label, value, suffix))
        return "\n".join(parts)

    def get_order_summary(self):
        self.ensure_one()
        return {
            "name": self.name,
            "customer": self.customer_id.name,
            "state": self.state,
            "billing_total": self.billing_total,
            "current_stage": self.current_production_stage,
        }
