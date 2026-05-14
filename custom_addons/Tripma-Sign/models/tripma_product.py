from odoo import fields, models


class TripmaProduct(models.Model):
    _name = "tripma.product"
    _description = "Tripma Sign Product Catalog"
    _order = "sequence, id"

    name = fields.Char(string="Product Name", required=True)
    sequence = fields.Integer(default=10)
    category = fields.Selection(
        [
            ("neon", "Neon Sign"),
            ("acrylic", "Acrylic Sign"),
            ("banner", "Banner & Spanduk"),
            ("stiker", "Stiker & Cutting"),
            ("papan", "Papan Nama"),
            ("custom", "Custom / Lainnya"),
        ],
        string="Category",
        required=True,
        default="custom",
    )

    description = fields.Text(string="Description")
    icon = fields.Char(
        string="Icon/Emoji", help="Emoji or simple icon to represent the product"
    )
    image = fields.Binary(string="Product Image")

    base_price = fields.Float(string="Base Price", required=True, default=0.0)
    price_type = fields.Selection(
        [
            ("unit", "Per Unit"),
            ("area", "Per m² (Area)"),
        ],
        string="Price Type",
        required=True,
        default="unit",
    )

    is_active = fields.Boolean(string="Active in Catalog", default=True)
