{
    'name': 'Bandoo School Purchase',
    'version': '18.0.1.1.0',
    'summary': 'Compenso ore insegnante: ordine d\'acquisto dalle ore registrate',
    'category': 'Purchases',
    'depends': [
        'bandoo_school',
        'purchase',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/res_config_settings_views.xml',
        'wizards/teacher_hours_bill_views.xml',
    ],
    'author': 'Marco De Paoli',
    'maintainer': 'Marco De Paoli',
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
