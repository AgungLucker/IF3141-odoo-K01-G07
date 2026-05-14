import datetime
import odoo
import base64
from odoo import http
from odoo.http import request
from odoo.exceptions import AccessDenied

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
    # Dummy route untuk integrasi selanjutnya, saat ini dihapus agar tidak redirect ke mockup.
    pass

class TripmaOrderController(http.Controller) :
    @http.route('/tripma/order/form' , type = 'http' , auth = 'user' , website = True)
    def order_form(self , **kw) :
        """
        FR-01: Menampilkan formulir pemesanan mandiri (FR-01)
        Hanya pelanggan yang bisa mengakses halaman ini, staf produksi dan admin
        akan diarahkan ke halaman akses ditolak.
        """
        if (not request.env.user.has_group('Tripma-Sign.group_tripma_customer')) :
            return request.redirect('/tripma/akses-ditolak')
        else :
            return request.render('Tripma-Sign.tripma_order_form_template' , {
                'customer': request.env.user.partner_id
            })

    @http.route('/tripma/order/submit' , type = 'http' , auth = 'user' , methods = ['POST'] , website = True , csrf = True)
    def order_submit(self , **post) :
        """
        FR-01: Memproses input pesanan dan file desain (FR-01)
        Hanya pelanggan yang bisa submit pesanan, staf produksi dan admin
        akan diarahkan ke halaman akses ditolak.
        """
        user = request.env.user
        product_specs = post.get('product_specs')
        design_file = post.get('design_file')
        if (not product_specs) :
            return request.redirect('/tripma/order/form?error=Spesifikasi produk wajib diisi')
        else :
            file_data = False
            if (design_file) :
                file_data = base64.b64encode(design_file.read())
            new_order = request.env['tripma.order'].sudo().create({
                'customer_id' : user.partner_id.id,
                'product_specs' : product_specs,
                'design_file' : file_data,
                'source_channel' : 'website',
                'state' : 'draft'
            })
            new_order.action_issue_invoice()
            return request.redirect(f'/tripma/order/success/{new_order.id}')

    @http.route('/tripma/order/success/<int:order_id>' , type = 'http' , auth = 'user' , website = True)
    def order_success(self , order_id , **kw) :
        """
        FR-01: Menampilkan rincian nomor order dan invoice setelah berhasil.
        Hanya pelanggan yang bisa mengakses halaman ini, staf produksi dan admin
        akan diarahkan ke halaman akses ditolak.
        """
        order = request.env['tripma.order'].sudo().browse(order_id)
        if ((not order.exists()) or (order.customer_id.id != request.env.user.partner_id.id)) :
            return request.redirect('/tripma/track')
        else :
            return request.render('Tripma-Sign.tripma_order_success_template' , {
                'order' : order,
                'invoice' : order.invoice_ids[:1]
            })

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


# =============================================================================
# FR-04: Sistem mampu membatasi hak akses data sesuai tingkat otoritas
# Tujuan : Membatasi akses data sensitif sesuai peran jabatan (OW-01 / OW-04)
# Operasi: Validasi hak akses pengguna (has_group) per route
# Output : Redirect ke dashboard yang sesuai, atau halaman akses ditolak
# =============================================================================

class TripmaAuthController(http.Controller):

    # ----- Helpers -----

    def _get_current_user_role(self):
        """FR-04: Kembalikan role string user yang sedang login."""
        user = request.env.user
        if user.has_group('Tripma-Sign.group_tripma_admin'):
            return 'admin'
        if user.has_group('Tripma-Sign.group_tripma_production_staff'):
            return 'production_staff'
        if user.has_group('Tripma-Sign.group_tripma_customer'):
            return 'customer'
        return 'unknown'

    def _redirect_by_role(self):
        """
        FR-04: Routing otomatis setelah login — kirim user ke dashboard
        yang sesuai dengan perannya.
          Admin Penjualan → /tripma/admin/dashboard
          Staf Produksi   → /tripma/production  (milik FR-03 Nathan)
          Pelanggan       → /tripma/pelanggan/pesanan
        """
        role = self._get_current_user_role()
        if role == 'admin':
            return request.redirect('/tripma/admin/dashboard')
        if role == 'production_staff':
            return request.redirect('/tripma/production')
        if role == 'customer':
            return request.redirect('/tripma/pelanggan/pesanan')
        return request.redirect('/web/login')
    def _redirect_unauthorized(self):
        """FR-04: Redirect ke halaman akses ditolak."""
        return request.redirect('/tripma/akses-ditolak')

    # =========================================================================
    # FR-04: LOGIN CUSTOM & ROUTING
    # =========================================================================

    @http.route('/tripma/login', type='http', auth='public', website=True)
    def login_page(self, **kw):
        """
        Halaman Login khusus Aplikasi Bisnis Tripma Sign.
        """
        # Jika sudah login, lempar sesuai role-nya
        if request.session.uid:
            role = self._get_current_user_role()
            if role == 'unknown':
                return request.redirect('/web/session/logout?redirect=/tripma/login')
            return self._redirect_by_role()

        values = {
            'error': kw.get('error'),
            'message': kw.get('message'),
            'login': kw.get('login', '')
        }

        # Handle POST request (Submit Login)
        if request.httprequest.method == 'POST':
            login = kw.get('login')
            password = kw.get('password')
            try:
                # Coba autentikasi menggunakan engine Odoo
                uid = request.session.authenticate(request.session.db, login, password)
                if uid:
                    # Sukses login, arahkan ke dasbor yang sesuai
                    return self._redirect_by_role()
            except AccessDenied:
                values['error'] = "Email/Username atau Kata Sandi salah."
            except Exception as e:
                values['error'] = f"Terjadi kesalahan sistem: {str(e)}"

        return request.render('Tripma-Sign.tripma_login_page', values)

    @http.route('/tripma/register', type='http', auth='public', website=True)
    def register_page(self, **kw):
        """
        Halaman Pendaftaran Akun Pelanggan (Terpisah dari bawaan Odoo).
        """
        if request.session.uid:
            return self._redirect_by_role()
            
        values = {
            'error': kw.get('error'),
            'name': kw.get('name', ''),
            'login': kw.get('login', ''),
            'phone': kw.get('phone', '')
        }
        return request.render('Tripma-Sign.tripma_register_page', values)

    @http.route('/tripma/register/submit', type='http', auth='public', methods=['POST'], website=True, csrf=True)
    def register_submit(self, **kw):
        """
        Memproses pendaftaran dan otomatis memasukkan user ke group Customer.
        """
        name = kw.get('name')
        login = kw.get('login')
        password = kw.get('password')
        confirm_password = kw.get('confirm_password')
        phone = kw.get('phone')

        if not name or not login or not password:
            return request.redirect(f'/tripma/register?error=Semua kolom bertanda bintang wajib diisi&name={name}&login={login}&phone={phone}')
        
        if password != confirm_password:
            return request.redirect(f'/tripma/register?error=Konfirmasi kata sandi tidak cocok&name={name}&login={login}&phone={phone}')

        # Cek apakah username/email sudah dipakai
        existing = request.env['res.users'].sudo().search([('login', '=', login)], limit=1)
        if existing:
            return request.redirect(f'/tripma/register?error=Email/Username sudah terdaftar, silakan login&name={name}&login={login}&phone={phone}')

        try:
            customer_group = request.env.ref('Tripma-Sign.group_tripma_customer')
            portal_group = request.env.ref('base.group_portal', raise_if_not_found=False)
            
            groups_to_add = [customer_group.id]
            if portal_group:
                groups_to_add.append(portal_group.id)
                
            # Buat akun baru secara aman menggunakan sudo
            user = request.env['res.users'].sudo().create({
                'name': name,
                'login': login,
                'password': password,
                'groups_id': [(6, 0, groups_to_add)]
            })
            
            if phone:
                user.partner_id.sudo().write({'phone': phone})
            
            # Otomatis login menggunakan sesi yang baru dibuat
            request.session.authenticate(request.session.db, login, password)
            return request.redirect('/tripma/pelanggan/pesanan')
            
        except Exception as e:
            return request.redirect(f'/tripma/register?error=Gagal mendaftar: {str(e)}&name={name}&login={login}&phone={phone}')

    def _redirect_by_role(self):
        """
        Fungsi helper untuk melempar user ke halaman yang tepat sesuai rolenya.
        """
        role = self._get_current_user_role()
        if role == 'admin':
            return request.redirect('/tripma/admin/dashboard')
        if role == 'production_staff':
            return request.redirect('/tripma/production')
        if role == 'customer':
            return request.redirect('/tripma/pelanggan/pesanan')
        return request.redirect('/web/login')

    # ----- Dashboard Admin Penjualan -----

    @http.route('/tripma/admin/dashboard', auth='user', website=True)
    def admin_dashboard(self, **kw):
        """
        FR-04: Dashboard Admin Penjualan.
        Hanya group_tripma_admin yang diizinkan masuk.
        Semua data pesanan ditampilkan (dijaga record rule di ir.rule.xml).
        """
        if not request.env.user.has_group('Tripma-Sign.group_tripma_admin'):
            return self._redirect_unauthorized()

        Order = request.env['tripma.order']
        values = {
            'user_role':       'admin',
            'user_name':       request.env.user.name,
            'total_orders':    Order.search_count([]),
            'draft_count':     Order.search_count([('state', '=', 'draft')]),
            'waiting_count':   Order.search_count([('state', '=', 'waiting_payment')]),
            'queue_count':     Order.search_count([('state', '=', 'in_queue')]),
            'prod_count':      Order.search_count([('state', '=', 'in_production')]),
            'done_count':      Order.search_count([('state', '=', 'done')]),
        }
        # Render ke QWeb template admin_dashboard
        return request.render('Tripma-Sign.admin_dashboard', values)

    @http.route('/tripma/admin/pesanan', auth='user', website=True)
    def admin_pesanan(self, **kw):
        """FR-04: Halaman input pesanan eksternal — Admin only."""
        if not request.env.user.has_group('Tripma-Sign.group_tripma_admin'):
            return self._redirect_unauthorized()
        # (Template QWeb sebenarnya akan dikerjakan di FR-02)
        return request.render('Tripma-Sign.admin_dashboard', {
            'user_role': 'admin', 'user_name': request.env.user.name, 
            'total_orders': 0, 'draft_count': 0, 'waiting_count': 0, 
            'queue_count': 0, 'prod_count': 0, 'done_count': 0
        })

    # ----- Dashboard Pelanggan -----

    @http.route('/tripma/pelanggan/pesanan', auth='user', website=True)
    def customer_pesanan(self, **kw):
        """
        FR-04: Halaman lacak pesanan untuk pelanggan.
        Record rule di ir.rule.xml memastikan hanya pesanan milik sendiri
        yang bisa diakses di level database — controller ini hanya routing.
        """
        if not request.env.user.has_group('Tripma-Sign.group_tripma_customer'):
            return request.redirect('/web')
        return request.redirect('/tripma/track')

    @http.route('/tripma/pelanggan/invoice', auth='user', website=True)
    def customer_invoice(self, **kw):
        """FR-04: Halaman invoice pelanggan — Customer only."""
        if not request.env.user.has_group('Tripma-Sign.group_tripma_customer'):
            return request.redirect('/web')
        # (Template QWeb sebenarnya dikerjakan di FR lain)
        return request.render('website.404')

    # ----- Halaman Akses Ditolak -----

    @http.route('/tripma/akses-ditolak', auth='public', website=True)
    def akses_ditolak(self, **kw):
        """
        FR-04: Halaman yang muncul saat user mencoba akses route tanpa izin.
        Menampilkan tombol kembali ke dashboard yang sesuai perannya.
        """
        public_user_id = request.env.ref('base.public_user').id
        is_logged_in = request.env.user.id != public_user_id
        role = self._get_current_user_role() if is_logged_in else 'unknown'
        return request.render('Tripma-Sign.page_akses_ditolak', {
            'user_role':    role,
            'is_logged_in': is_logged_in,
        })

    # ----- API JSON: Cek Role (untuk frontend JS) -----

    @http.route('/tripma/api/my-role', auth='user', type='json', methods=['GET'])
    def api_get_my_role(self, **kw):
        """
        FR-04: Endpoint JSON — kembalikan role user yang sedang login.
        Digunakan mockup HTML / frontend untuk conditional rendering
        elemen UI berbasis peran (tanpa reload halaman).
        """
        user = request.env.user
        return {
            'uid':                user.id,
            'name':               user.name,
            'role':               self._get_current_user_role(),
            'is_admin':           user.has_group('Tripma-Sign.group_tripma_admin'),
            'is_production_staff': user.has_group('Tripma-Sign.group_tripma_production_staff'),
            'is_customer':        user.has_group('Tripma-Sign.group_tripma_customer'),
        }