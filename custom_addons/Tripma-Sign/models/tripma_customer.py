from odoo import api, fields, models


class TripmaCustomer(models.Model):
    _inherit = "res.partner"

    is_tripma_customer = fields.Boolean(string="Is Tripma Customer", default=False)
    has_user_account = fields.Boolean(
        string="Has User Account",
        compute="_compute_has_user_account",
        store=True,
        help="Check if this partner is linked to a system user account.",
    )

    @api.depends("user_ids")
    def _compute_has_user_account(self):
        for partner in self:
            partner.has_user_account = bool(partner.user_ids)
