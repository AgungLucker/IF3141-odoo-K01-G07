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
        'security/ir.rule.xml',          # FR-04: Record-level security per role

        # Data
        'data/tripma_sequences.xml',

        # Views
        'views/templates.xml',
        'views/admin_layout_templates.xml',
        'views/admin_templates.xml',
        'views/production_templates.xml',
        'views/external_order_templates.xml',
        'views/menus.xml',
    ],
    'application': True,
}
