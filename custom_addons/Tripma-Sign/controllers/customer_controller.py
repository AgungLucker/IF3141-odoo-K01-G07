import base64
from odoo import http
from odoo.http import request
from .base_controller import TripmaBaseController

class TripmaCustomerController(TripmaBaseController) :
    @http.route('/tripma/order/form' , type = 'http' , auth = 'user' , website = True)
    def order_form(self , **kw) :
        """
        FR-01: Menampilkan formulir pemesanan mandiri, memanfaatkan pengecekan role terpusat.
        """
        if (self._get_current_user_role() != 'customer') :
            return request.redirect('/tripma/akses-ditolak')
        else :
            return request.render('Tripma-Sign.tripma_order_form_template' , {'customer' : request.env.user.partner_id})

    @http.route('/tripma/order/submit' , type = 'http' , auth = 'user' , methods = ['POST'] , website = True , csrf = True)
    def order_submit(self , **post) :
        """
        FR-01: Memproses input pesanan dan file desain secara terpusat.
        """
        if (self._get_current_user_role() != 'customer') :
            return request.redirect('/tripma/akses-ditolak')
        else :
            product_specs = post.get('product_specs')
            design_file = post.get('design_file')
            if (not product_specs) :
                return request.redirect('/tripma/order/form?error=Spesifikasi produk wajib diisi')
            else :
                file_data = False
                if (design_file) :
                    file_data = base64.b64encode(design_file.read())
                new_order = request.env['tripma.order'].sudo().create({
                    'customer_id' : request.env.user.partner_id.id,
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
        FR-01: Menampilkan rincian invoice dan nomor order setelah submit.
        """
        order = request.env['tripma.order'].sudo().browse(order_id)
        if ((not order.exists()) or (order.customer_id.id != request.env.user.partner_id.id)) :
            return request.redirect('/tripma/track')
        else :
            return request.render('Tripma-Sign.tripma_order_success_template' , {'order' : order , 'invoice' : order.invoice_ids[:1]})

    @http.route('/tripma/customer/dashboard' , auth = 'user' , website = True)
    def customer_dashboard(self , **kw) :
        """
        FR-04: Dashboard utama pelanggan untuk melihat daftar pesanan.
        """
        if (self._get_current_user_role() != 'customer') :
            return request.redirect('/tripma/akses-ditolak')
        else :
            orders = request.env['tripma.order'].search([('customer_id' , '=' , request.env.user.partner_id.id)])
            return request.render('Tripma-Sign.customer_dashboard_template' , {'orders': orders})