{
    "name": "TripmaStore",
    "summary": "Website E-commerce Tripma Sign",
    "author": "Kelompok 07 - K01",
    "category": "Uncategorized",
    "version": "1.0",
    "depends": ["base", "web"],
    "data": [
        "security/tripma_groups.xml",
        "security/ir.model.access.csv",
        "security/ir.rule.xml",  # FR-04: Record-level security per role
        # Pages
        "views/pages/landing.xml",
        # Data
        "data/tripma_sequences.xml",
        "data/demo_users.xml",
        # Menus
        "views/menus.xml",
        # Layouts
        "views/layouts/main_layout.xml",
        "views/layouts/components/navbar.xml",
        "views/layouts/components/alerts.xml",
        "views/layouts/components/admin_sidebar.xml",
        "views/layouts/admin_layout.xml",
        "views/layouts/customer_layout.xml",
        # Auth Pages
        "views/pages/auth/login.xml",
        "views/pages/auth/register.xml",
        "views/pages/auth/access_denied.xml",
        # Admin Pages
        "views/pages/admin/dashboard.xml",
        "views/pages/admin/external_order.xml",
        "views/pages/admin/all_orders.xml",
        "views/pages/admin/catalog_views.xml",
        "views/pages/admin/backend_views.xml",
        "views/pages/admin/production.xml",
        # Customer Pages
        "views/pages/customer/tracking.xml",
        "views/pages/customer/invoice.xml",
        "views/pages/customer/catalog.xml",
        "views/customer_templates.xml",
    ],
    "post_init_hook": "post_init_hook",
    "application": True,
}
