{
    'name': 'Bandoo School Sale',
    'version': '18.0.1.6.0',
    'summary': 'Iscrizioni a corsi, rette e consuntivo allievo per la scuola di musica',
    'category': 'Sales',
    'depends': [
        'bandoo_school',
        'sale_management',
        'sale_project',
        # Esplicito e non incidentale: `sale_timesheet` riscrive
        # `allocated_hours` sul progetto generato, e senza questa dipendenza il
        # nostro override girerebbe *prima* del suo e verrebbe sovrascritto.
        'sale_timesheet',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/export_lists.xml',
        'views/product_template_views.xml',
        'views/project_project_views.xml',
        'views/sale_order_views.xml',
        'views/sale_order_line_views.xml',
        'views/enrollment_settlement_views.xml',
    ],
    'author': 'Marco De Paoli',
    'maintainer': 'Marco De Paoli',
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
