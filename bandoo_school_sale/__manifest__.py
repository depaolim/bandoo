{
    'name': 'Bandoo School Sale',
    'version': '18.0.1.0.0',
    'summary': 'Iscrizioni a corsi, rette e conguaglio per la scuola di musica',
    'category': 'Sales',
    'depends': [
        'bandoo_school',
        'sale_management',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/product_data.xml',
        'views/project_project_views.xml',
        'views/res_partner_views.xml',
        'views/sale_order_views.xml',
        'views/enrollment_settlement_views.xml',
    ],
    'author': 'Marco De Paoli',
    'maintainer': 'Marco De Paoli',
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
