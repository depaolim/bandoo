{
    'name': 'Bandoo School Sale',
    'version': '18.0.2.0.0',
    'summary': 'Iscrizioni a corsi, rette e consuntivo allievo per la scuola di musica',
    'category': 'Sales',
    'depends': [
        'bandoo_school',
        'sale_management',
        'sale_project',
        # Esplicito e non incidentale: `sale_timesheet` crea il corso
        # individuale e ne scrive il monte ore, e il nostro override, che lo
        # riscrive dalle lezioni previste, deve girare dopo il suo.
        'sale_timesheet',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/uom_data.xml',
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
