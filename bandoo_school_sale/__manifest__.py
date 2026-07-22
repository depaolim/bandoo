{
    'name': 'Bandoo School Sale',
    'version': '18.0.1.0.0',
    'summary': 'Iscrizioni a corsi, rette e conguaglio per la scuola di musica',
    'category': 'Sales',
    'depends': [
        'bandoo_school',
        'sale_management',
        'sale_project',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/product_template_views.xml',
        'views/sale_order_views.xml',
        'views/enrollment_settlement_views.xml',
    ],
    'author': 'Marco De Paoli',
    'maintainer': 'Marco De Paoli',
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
