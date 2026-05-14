from odoo import http
from odoo.exceptions import AccessDenied
from odoo.http import request

from .base_controller import TripmaBaseController


class TripmaAuthController(TripmaBaseController):
    # FR-04: LOGIN CUSTOM & ROUTING
    @http.route("/tripma/login", type="http", auth="public", website=True, csrf=False)
    def login_page(self, **kw):
        """
        Halaman Login khusus Aplikasi Bisnis Tripma Sign.
        """
        # Jika sudah login, lempar sesuai role-nya
        if request.session.uid:
            role = self._get_current_user_role()
            if role == "unknown":
                return request.redirect("/web/session/logout?redirect=/tripma/login")
            return self._redirect_by_role()

        values = {
            "error": kw.get("error"),
            "message": kw.get("message"),
            "login": kw.get("login", ""),
        }

        # Handle POST request (Submit Login)
        if request.httprequest.method == "POST":
            login = kw.get("login")
            password = kw.get("password")
            try:
                # Coba autentikasi menggunakan engine Odoo
                uid = request.session.authenticate(request.session.db, login, password)
                if uid:
                    user = request.env["res.users"].sudo().browse(uid)

                    # Auto Assign if admin
                    if user.has_group("base.group_system") or user.has_group(
                        "base.group_erp_manager"
                    ):
                        tripma_admin_group = request.env.ref(
                            "Tripma-Sign.group_tripma_admin"
                        )

                        # Add group if not already assigned
                        if tripma_admin_group not in user.groups_id:
                            user.write({"groups_id": [(4, tripma_admin_group.id)]})

                    # Sukses login, arahkan ke dasbor yang sesuai
                    return self._redirect_by_role()
            except AccessDenied:
                values["error"] = "Email/Username atau Kata Sandi salah."
            except Exception as e:
                values["error"] = f"Terjadi kesalahan sistem: {str(e)}"

        return self._render_tripma("Tripma-Sign.tripma_login_page", values)

    @http.route("/tripma/register", type="http", auth="public", website=True)
    def register_page(self, **kw):
        """
        Halaman Pendaftaran Akun Pelanggan (Terpisah dari bawaan Odoo).
        """
        if request.session.uid:
            return self._redirect_by_role()

        values = {
            "error": kw.get("error"),
            "name": kw.get("name", ""),
            "login": kw.get("login", ""),
            "phone": kw.get("phone", ""),
            "address": kw.get("address", ""),
        }
        return self._render_tripma("Tripma-Sign.tripma_register_page", values)

    @http.route(
        "/tripma/register/submit",
        type="http",
        auth="public",
        methods=["POST"],
        website=True,
        csrf=True,
    )
    def register_submit(self, **kw):
        """
        Memproses pendaftaran dan otomatis memasukkan user ke group Customer.
        """
        name = kw.get("name")
        login = kw.get("login")
        password = kw.get("password")
        confirm_password = kw.get("confirm_password")
        phone = kw.get("phone")
        address = kw.get("address")

        if not name or not login or not password or not address:
            return request.redirect(
                f"/tripma/register?error=Semua kolom bertanda bintang wajib diisi&name={name}&login={login}&phone={phone}&address={address}"
            )

        if password != confirm_password:
            return request.redirect(
                f"/tripma/register?error=Konfirmasi kata sandi tidak cocok&name={name}&login={login}&phone={phone}&address={address}"
            )

        # Cek apakah username/email sudah dipakai
        existing = (
            request.env["res.users"].sudo().search([("login", "=", login)], limit=1)
        )
        if existing:
            return request.redirect(
                f"/tripma/register?error=Email/Username sudah terdaftar, silakan login&name={name}&login={login}&phone={phone}&address={address}"
            )

        try:
            customer_group = request.env.ref("Tripma-Sign.group_tripma_customer")
            portal_group = request.env.ref(
                "base.group_portal", raise_if_not_found=False
            )

            groups_to_add = [customer_group.id]
            if portal_group:
                groups_to_add.append(portal_group.id)

            # Buat akun baru secara aman menggunakan sudo
            user = (
                request.env["res.users"]
                .sudo()
                .with_context(no_reset_password=True)
                .create(
                    {"name": name, "login": login, "groups_id": [(6, 0, groups_to_add)]}
                )
            )

            # Explicitly write password and mark as Tripma customer
            user.sudo().write({"password": password})
            partner_vals = {
                "is_tripma_customer": True,
                "email": login,
                "street": address,
            }
            if phone:
                partner_vals["phone"] = phone
            user.partner_id.sudo().write(partner_vals)

            # Commit the transaction so the new user is visible to the authenticate cursor
            request.env.cr.commit()

            # Autentikasi dengan database yang tepat
            db = request.session.db or request.env.cr.dbname
            request.session.authenticate(db, login, password)
            return request.redirect("/tripma/customer/dashboard")

        except Exception as e:
            return request.redirect(
                f"/tripma/register?error=Gagal mendaftar: {str(e)}&name={name}&login={login}&phone={phone}"
            )

    @http.route("/", type="http", auth="public", website=True)
    def root_redirect(self, **kw):
        """
        Root URL handler — Show Landing Page
        """
        return self._render_tripma("Tripma-Sign.tripma_landing_page")

    # @http.route('/web', type='http', auth='public', website=True)
    # def web_redirect(self, **kw):
    #     """
    #     Override /web route to redirect to Tripma:
    #     - If authenticated as admin/system: allow access to Odoo backend
    #     - Otherwise: redirect to Tripma dashboard or login
    #     """
    #     if not request.session.uid:
    #         return request.redirect('/tripma/login')

    #     # Check if user has admin/system access
    #     user = request.env.user
    #     if user.has_group('base.group_system') or user.has_group('base.group_erp_manager'):
    #         # Allow admin users to access Odoo backend
    #         return request.redirect('/web/home')

    #     # For non-admin users, redirect to their appropriate dashboard
    #     return self._redirect_by_role()

    # @http.route('/web', type='http', auth='public', website=True)
    # def web_redirect(self, **kw):
    #     if not request.session.uid:
    #         return request.redirect('/tripma/login')

    #     return self._redirect_by_role()

    @http.route("/web/login", type="http", auth="public", website=True)
    def web_login_redirect(self, **kw):
        """
        Override /web/login to redirect to Tripma login instead.
        This intercepts Odoo's default login page and sends users to our custom login.
        """
        if request.session.uid:
            # Already logged in, redirect based on group
            return self._redirect_by_role()

        # Not logged in, go to Tripma login page
        return request.redirect("/tripma/login")

    # ----- Helpers -----
    # def _get_current_user_role(self):
    #     """FR-04: Kembalikan role string user yang sedang login."""
    #     user = request.env.user
    #     if user.has_group('Tripma-Sign.group_tripma_admin'):
    #         return 'admin'
    #     if user.has_group('Tripma-Sign.group_tripma_production_staff'):
    #         return 'production_staff'
    #     if user.has_group('Tripma-Sign.group_tripma_customer'):
    #         return 'customer'
    #     return 'unknown'

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

    def _redirect_by_role(self):
        """
        FR-04: Routing otomatis setelah login — kirim user ke dashboard
        yang sesuai dengan perannya.
          Admin Penjualan → /tripma/admin/dashboard
          Staf Produksi   → /tripma/production  (milik FR-03 Nathan)
          Pelanggan       → /tripma/customer/dashboard
        """
        role = self._get_current_user_role()
        if role == "admin":
            return request.redirect("/tripma/admin/dashboard")
        if role == "production_staff":
            return request.redirect("/tripma/production")
        if role == "customer":
            return request.redirect("/tripma/customer/dashboard")
        return request.redirect("/web/login")

    def _redirect_unauthorized(self):
        """FR-04: Redirect ke halaman akses ditolak."""
        return request.redirect("/tripma/akses-ditolak")

    # ----- Halaman Akses Ditolak -----
    @http.route("/tripma/akses-ditolak", auth="public", website=True)
    def akses_ditolak(self, **kw):
        """
        FR-04: Halaman yang muncul saat user mencoba akses route tanpa izin.
        Menampilkan tombol kembali ke dashboard yang sesuai perannya.
        """
        return self._render_tripma("Tripma-Sign.page_akses_ditolak")

    # ----- API JSON: Cek Role (untuk frontend JS) -----
    @http.route("/tripma/api/my-role", auth="user", type="json", methods=["GET"])
    def api_get_my_role(self, **kw):
        """
        FR-04: Endpoint JSON — kembalikan role user yang sedang login.
        Digunakan mockup HTML / frontend untuk conditional rendering
        elemen UI berbasis peran (tanpa reload halaman).
        """
        user = request.env.user
        return {
            "uid": user.id,
            "name": user.name,
            "role": self._get_current_user_role(),
            "is_admin": user.has_group("Tripma-Sign.group_tripma_admin"),
            "is_production_staff": user.has_group(
                "Tripma-Sign.group_tripma_production_staff"
            ),
            "is_customer": user.has_group("Tripma-Sign.group_tripma_customer"),
        }
