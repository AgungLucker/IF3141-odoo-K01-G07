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

def parse_money(value):
    if not value:
        return 0.0
    normalized = str(value).replace('.', '').replace(',', '.').strip()
    try:
        return float(normalized)
    except ValueError:
        return 0.0