{
    'name': "TripmaStore",
    'summary': "Website E-commerce Tripma Sign",
    'author': "Kelompok 07 - K01",
    'category': 'Uncategorized',
    'version': '1.0',
    'depends': ['base', 'website'], 
    'data': [
        'security/tripma_groups.xml',
        'security/ir.model.access.csv',
        'data/tripma_sequences.xml',
        'views/templates.xml',
        'views/menus.xml',
    ],
    'application': True,
}