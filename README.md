# IF3141 Sistem Informasi - Odoo Setup

## Introduction

Odoo merupakan *Enterprise Resource Planning System* yang mampu melakukan implementasi modul modul kustom untuk menyelesaikan permasalahan proses bisnis pada suatu perusahaan.

Odoo memberikan opsi *on-premise solution* sehingga developer dapat melakukan implementasi kustom modul pada local environment.

Repository ini diperuntukkan untuk Tugas Besar IF3141 Sistem Informasi. Untuk memulai silakan melakukan fork dan membuat repository private untuk workspace setiap kelompok.


## Pre-requisites
Odoo diimplementasikan dengan Python environment dan database PostgreSQL. Repository ini sudah membungkus service aplikasi dan database melalui Docker.

Sebelum memulai, pastikan dependency berikut sudah terpasang:

1. Docker Desktop
	- Download: https://www.docker.com/products/docker-desktop/
2. Python 3.11
	- Digunakan untuk virtual environment (venv) pada proses development modul

## Struktur Direktori

- `/config`
	- Untuk menyimpan konfigurasi Odoo
- `/custom_addons`
	- Tempat pengerjaan modul kustom
- `/dump`
	- Database dump yang dapat diakses scripts untuk proses import/export
- `/scripts`
	- Untuk melakukan database migration
- `docker-compose.yml`
	- Orchestration service Odoo dan PostgreSQL

## Step-by-step Installation

1. Jalankan service Odoo dan PostgreSQL:

	```bash
	docker compose up -d
	```

2. Buka aplikasi pada browser:
	- http://localhost:8069

3. Login menggunakan kredensial default:
	- Username: `admin`
	- Password: `admin`

4. Aktifkan mode developer:
	- Masuk ke **Settings**
	- Nyalakan **Developer Mode / Developer Access**

5. Buat Python virtual environment pada workspace:

	```bash
	python3.11 -m venv .venv
	source .venv/bin/activate
	pip install --upgrade pip
	pip install -r requirements.txt
	```

6. Implementasikan modul pada folder:
	- `custom_addons/`

7. Setelah implementasi modul selesai, lakukan update daftar aplikasi:
	- Masuk ke menu **Apps**
	- Pilih **Update Apps List**

8. Jika melakukan perubahan terhadap isi modul (modifying database), jangan lupa lakukan langkah database migration dengan mengikuti step di heading bawah ini.

## Routes Aplikasi Tripma Sign

Base URL lokal:

```text
http://localhost:8069
```

| Method | Route | Auth | Keterangan |
| --- | --- | --- | --- |
| `GET` | `/tripma/order` | Public | Redirect ke mockup form order statis |
| `GET` | `/tripma/admin/external-order` | User, Admin Penjualan | Form input pesanan eksternal dari WhatsApp/langsung/telepon |
| `POST` | `/tripma/admin/external-order/submit` | User, Admin Penjualan | Registrasi pesanan eksternal ke database utama dan antrian produksi |
| `GET` | `/tripma/admin/external-order/success/<order_id>` | User, Admin Penjualan | Halaman sukses setelah nomor order resmi diterbitkan |
| `GET` | `/tripma/production` | User, Admin Penjualan atau Staf Produksi | Dashboard antrian dan status produksi |
| `GET` | `/tripma/production/update/<order_id>` | User, Admin Penjualan atau Staf Produksi | Form update status produksi untuk order tertentu |
| `POST` | `/tripma/production/update/submit` | User, Admin Penjualan atau Staf Produksi | Submit perubahan status produksi |
| `GET` | `/tripma/track` | Public | Halaman pencarian tracking order |
| `GET` | `/tripma/track/<order_name>` | Public | Detail tracking berdasarkan nomor order |

Catatan akses:

- Fitur input pesanan eksternal membutuhkan grup Odoo **Tripma Sign / Admin Penjualan**.
- Dashboard produksi dapat diakses oleh **Admin Penjualan** atau **Staf Produksi**.
- Setelah perubahan modul, lakukan **Apps > Update Apps List > Upgrade TripmaStore** agar route, field, dan view baru aktif.

## Database Migration

Odoo menggunakan local database pada implementasinya. Maka dari itu dibutuhkan migration system yang dapat dilakukan melakukan **dump db** atau **import db**. Sebelum melakukan migration jangan lupa untuk selalu mematikan service odoo & databasenya dengan menjalankan :

```bash 
docker compose down
```

Apabila terdapat perubahan pada database dan perubahan tersebut ingin diteruskan ke anggota tim lain, lakukan export database terlebih dahulu menggunakan script pada folder `scripts`.

- macOS/Linux:

  ```bash
  ./scripts/export_db.sh
  ```

- Windows:

  ```bat
  scripts\export_db.cmd
  ```

Untuk melanjutkan pengerjaan dari hasil perubahan database rekan tim, lakukan import database terlebih dahulu :

- macOS/Linux:

  ```bash
  ./scripts/import_db.sh
  ```

- Windows:

  ```bat
  scripts\import_db.cmd
  ```
