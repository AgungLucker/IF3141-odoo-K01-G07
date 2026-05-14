# This script can be run using:
# docker-compose exec web odoo shell -d <your_db_name> < scripts/seed_products.py

# In Odoo shell, 'env' is already available.
products = [
    {
        'name': 'Neon Sign Custom',
        'category': 'neon',
        'description': 'Lampu neon custom untuk dekorasi ruangan, logo toko, atau hiasan dinding dengan berbagai pilihan warna.',
        'base_price': 150000.0,
        'price_type': 'unit',
        'icon': '💡',
        'is_active': True,
    },
    {
        'name': 'Acrylic Sign & Plakat',
        'category': 'acrylic',
        'description': 'Plakat atau papan informasi berbahan acrylic berkualitas tinggi dengan potongan laser yang presisi.',
        'base_price': 200000.0,
        'price_type': 'area',
        'icon': '🖼️',
        'is_active': True,
    },
    {
        'name': 'Banner High Res (Outdoor/Indoor)',
        'category': 'banner',
        'description': 'Cetak banner atau spanduk dengan tinta tahan lama dan resolusi tinggi untuk kebutuhan promosi.',
        'base_price': 25000.0,
        'price_type': 'area',
        'icon': '🚩',
        'is_active': True,
    },
    {
        'name': 'Stiker Vinyl & Cutting',
        'category': 'stiker',
        'description': 'Stiker berbahan vinyl tahan air dan cuaca, cocok untuk label produk atau dekorasi kendaraan.',
        'base_price': 50000.0,
        'price_type': 'area',
        'icon': '🏷️',
        'is_active': True,
    },
    {
        'name': 'Papan Nama Toko (Galvanis)',
        'category': 'papan',
        'description': 'Papan nama toko kokoh dari bahan galvanis atau stainless dengan finishing cat berkualitas.',
        'base_price': 750000.0,
        'price_type': 'unit',
        'icon': '🏪',
        'is_active': True,
    },
    {
        'name': 'Huruf Timbul LED',
        'category': 'custom',
        'description': 'Huruf timbul dengan lampu LED di dalamnya untuk kesan mewah dan profesional pada fasad bangunan.',
        'base_price': 350000.0,
        'price_type': 'unit',
        'icon': '🔠',
        'is_active': True,
    }
]

for product_vals in products:
    if not env['tripma.product'].search([('name', '=', product_vals['name'])], limit=1):
        env['tripma.product'].create(product_vals)
        print(f"Created product: {product_vals['name']}")
    else:
        print(f"Product already exists: {product_vals['name']}")

env.cr.commit()
