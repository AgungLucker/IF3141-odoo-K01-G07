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
        if (not self.is_customer()) :
            return request.redirect('/tripma/akses-ditolak')
        else :
            return request.render('Tripma-Sign.tripma_order_form_template' , {'customer' : request.env.user.partner_id})

    @http.route('/tripma/order/submit' , type = 'http' , auth = 'user' , methods = ['POST'] , website = True , csrf = True)
    def order_submit(self , **post) :
        """
        FR-01: Memproses input pesanan dan file desain secara terpusat.
        """
        if (not self.is_customer()) :
            return request.redirect('/tripma/akses-ditolak')
        else :
            # Update customer profile if changed
            partner = request.env.user.partner_id
            update_vals = {}
            if post.get('cust_name') and post.get('cust_name') != partner.name:
                update_vals['name'] = post.get('cust_name')
            if post.get('cust_email') and post.get('cust_email') != partner.email:
                update_vals['email'] = post.get('cust_email')
            if post.get('cust_phone'):
                phone = post.get('cust_phone')
                if phone != partner.phone and phone != partner.mobile:
                    update_vals['phone'] = phone
            if post.get('cust_address') and post.get('cust_address') != partner.street:
                update_vals['street'] = post.get('cust_address')
            if update_vals:
                partner.sudo().write(update_vals)

            # Build product specs string
            parts = []
            if post.get('material'): parts.append(f"Bahan: {post.get('material')}")
            if post.get('size'): parts.append(f"Ukuran: {post.get('size')}")
            if post.get('quantity'): parts.append(f"Jumlah: {post.get('quantity')} unit")
            if post.get('special_instructions'): parts.append(f"Catatan: {post.get('special_instructions')}")
            
            product_specs = '\n'.join(parts)
            design_file = post.get('design_file')
            
            if not product_specs:
                return request.redirect('/tripma/order/form?error=Spesifikasi produk wajib diisi')
            else:
                file_data = False
                if design_file:
                    file_data = base64.b64encode(design_file.read())
                new_order = request.env['tripma.order'].sudo().create({
                    'customer_id': partner.id,
                    'product_specs': product_specs,
                    'design_file': file_data,
                    'source_channel': 'website',
                    'state': 'draft'
                })
                new_order.action_issue_invoice()
                return request.redirect(f'/tripma/order/success/{new_order.id}')

    @http.route('/tripma/order/invoice/<int:order_id>', type='http', auth='user', website=True)
    def invoice_view(self, order_id, **kw):
        """
        Menampilkan halaman invoice yang sudah di-redesign.
        """
        if not self.is_customer():
            return request.redirect('/tripma/akses-ditolak')
            
        order = request.env['tripma.order'].sudo().browse(order_id)
        if not order.exists() or order.customer_id.id != request.env.user.partner_id.id:
            return request.redirect('/tripma/track')
            
        invoice = order.invoice_ids[:1] if order.invoice_ids else False
        if not invoice:
            return request.redirect('/tripma/track')
            
        return request.render('Tripma-Sign.customer_invoice_page', {'invoice': invoice})

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

    @http.route('/tripma/order/confirm_payment', type='http', auth='user', methods=['POST'], website=True, csrf=True)
    def confirm_payment(self, **post):
        """
        Dummy endpoint untuk simulasi konfirmasi pembayaran.
        """
        if not self.is_customer():
            return request.redirect('/tripma/akses-ditolak')
            
        order_id = post.get('order_id')
        if order_id:
            order = request.env['tripma.order'].sudo().browse(int(order_id))
            if order.exists() and order.customer_id.id == request.env.user.partner_id.id:
                if order.state == 'waiting_payment':
                    order.action_validate_payment()
                return request.redirect(f'/tripma/track/{order.name}')
        return request.redirect('/tripma/track')

    @http.route('/tripma/customer/dashboard' , auth = 'user' , website = True)
    def customer_dashboard(self , **kw) :
        """
        FR-04: Dashboard utama pelanggan untuk melihat daftar pesanan.
        """
        if (not self.is_customer()) :
            return request.redirect('/tripma/akses-ditolak')
        else :
            return request.redirect('/tripma/track')