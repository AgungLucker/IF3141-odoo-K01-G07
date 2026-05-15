# Tripma Sign - Sistem Informasi Odoo

## Identitas Kelompok
- Nama Kelompok: G07
- Nomor Kelas: K01
- Anggota Kelompok:
  - Anggota 1: 13523013	 Nathaniel Jonathan Rusli
  - Anggota 2: 13523021  Muhammad Raihan Nazhim Oktana
  - Anggota 3: 13523023  Muhammad Aufa Farabi
  - Anggota 4: 13523043  Najwa Kahani Fatima
  - Anggota 5: 13523061  Darrel Adinarya Sunanda


## Nama Sistem dan Perusahaan
- Nama Sistem: E-Commerce Mandiri Tripma Sign
- Nama Perusahaan: Tripma Sign

## Deskripsi Sistem
E-Commerce Mandiri Tripma Sign adalah sistem informasi berbasis Odoo yang dirancang untuk mendukung proses pemesanan, produksi, dan pelacakan produk signagea. Sistem ini mengintegrasikan fungsi front-end untuk pelanggan, kontrol pesanan internal untuk admin penjualan, dan dashboard produksi untuk staf produksi sehingga proses bisnis menjadi lebih terstruktur dan mudah dilacak.

Sistem ini menyediakan modul kustom Odoo yang memungkinkan pembuatan pesanan eksternal dari admin, pengelolaan katalog produk, pembaruan status produksi, serta pelacakan nomor order. Dengan memanfaatkan modul kustom `Tripma-Sign`, perusahaan dapat mengelola antrian produksi dan komunikasi internal tanpa harus menggunakan sistem manual berbasis spreadsheet.

## Cara Menjalankan Sistem
1. Pastikan Docker dan Docker Compose terpasang di mesin.
2. Buka terminal pada folder proyek `IF3141-odoo-K01-G07`.
3. Jalankan layanan Odoo dan PostgreSQL:

   ```bash
   docker compose up -d
   ```

   *Expected result:* layanan Odoo aktif dan dapat diakses di `http://localhost:8069`.
   
   *Screenshot placeholder:*
   <img width="593" height="111" alt="image" src="https://github.com/user-attachments/assets/52e31474-c637-4632-b358-48675cad1e3f" />


5. Akses aplikasi Odoo melalui browser:
   - `http://localhost:8069`

   *Expected result:* halaman login Odoo tampil.
   
   *Screenshot placeholder:*
   <img width="500" height="205" alt="image" src="https://github.com/user-attachments/assets/c26a0ee5-7764-4e50-a919-f8facfb59bbe" />


7. Untuk akses admin, login dengan akun admin default:
   - Username: `admin`
   - Password: `admin`

   *Expected result:* masuk ke dashboard backend Odoo.
   
   *Screenshot placeholder:*
   <img width="540" height="202" alt="image" src="https://github.com/user-attachments/assets/887bdf69-6282-4a52-b66d-205f517c3edb" />


9. Untuk menjalankan ulang atau mematikan layanan setelah selesai:

   ```bash
   docker compose down
   ```

   *Expected result:* layanan Odoo dan PostgreSQL berhenti.
   
   *Screenshot placeholder:* <img width="596" height="89" alt="image" src="https://github.com/user-attachments/assets/d1f1ee4e-cf5d-4503-9ad3-814756963429" />

   

## Credensial Role
- Admin Odoo (Superuser):
  - Username: `admin`
  - Password: `admin`

- Admin Penjualan / Tripma Sign Admin:
  - Username: `admin` (atau akun Odoo yang terdaftar dengan grup `Tripma Sign / Admin Penjualan`)
  - Password: `admin`

- Staf Produksi:
  - Username: `staf` (akun Odoo dengan grup `Tripma Sign / Staf Produksi`)
  - Password: `123`

- Pelanggan / User Publik:
  - Register akun sebagai customer, lalu logi.
  - Untuk akun pelanggan terdaftar, gunakan akun Odoo dengan grup pelanggan di instalasi Odoo.

## Kesimpulan dan Saran
Sistem Tripma Sign memberikan solusi manajemen pemesanan dan produksi untuk usaha signage dengan menghadirkan alur kerja yang lebih terstruktur. Penggunaan platform Odoo memungkinkan integrasi antara penginputan pesanan, pengelolaan katalog, dan pelacakan produksi dalam satu ekosistem.

Saran: lengkapi modul dengan fungsi notifikasi pelanggan dan laporan produksi otomatis agar admin penjualan dan staf produksi dapat memantau status order secara real time dan mengurangi risiko keterlambatan pengiriman. Jika memungkinkan, tambahkan integrasi dengan WhatsApp API untuk penerimaan pesanan eksternal yang lebih efektif.
