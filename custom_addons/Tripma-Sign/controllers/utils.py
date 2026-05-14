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
    # Jika ada titik dan koma, asumsikan titik adalah ribuan dan koma adalah desimal (format ID/EU)
    # Jika hanya ada koma, ganti jadi titik
    # Jika hanya ada titik, biarkan (format US/Standard)
    val_str = str(value).strip()
    if '.' in val_str and ',' in val_str:
        # Format 1.000,50 -> 1000.50
        normalized = val_str.replace('.', '').replace(',', '.')
    elif ',' in val_str:
        # Format 1000,50 -> 1000.50
        normalized = val_str.replace(',', '.')
    else:
        # Format 1000.50 -> 1000.50
        normalized = val_str
    
    try:
        return float(normalized)
    except ValueError:
        return 0.0