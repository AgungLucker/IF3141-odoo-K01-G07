from odoo import http
from odoo.http import request


class TripmaBaseController(http.Controller):
    def _get_current_user_role(self):
        user = request.env.user
        if (
            user.has_group("Tripma-Sign.group_tripma_admin")
            or user.has_group("base.group_system")
            or user.has_group("base.group_erp_manager")
        ):
            return "admin"
        if user.has_group("Tripma-Sign.group_tripma_production_staff"):
            return "production_staff"
        if user.has_group("Tripma-Sign.group_tripma_customer"):
            return "customer"
        return "unknown"

    def _render_tripma(self, template, values=None):
        """Helper to render templates with consistent context (role, name, etc)."""
        if values is None:
            values = {}

        is_logged_in = request.session.uid is not None
        role = self._get_current_user_role() if is_logged_in else "public"

        # Ensure we don't overwrite if specifically passed
        ctx = {
            "user_role": role,
            "user_name": request.env.user.name if is_logged_in else "",
            "is_logged_in": is_logged_in,
        }
        ctx.update(values)
        return request.render(template, ctx)

    def is_admin(self):
        user = request.env.user
        return (
            user.has_group("Tripma-Sign.group_tripma_admin")
            or user.has_group("base.group_system")
            or user.has_group("base.group_erp_manager")
        )

    def is_production_staff(self):
        return (
            request.env.user.has_group("Tripma-Sign.group_tripma_production_staff")
            or self.is_admin()
        )

    def is_customer(self):
        return request.env.user.has_group("Tripma-Sign.group_tripma_customer")

    def redirect_unauthorized(self):
        return request.redirect("/tripma/akses-ditolak")
