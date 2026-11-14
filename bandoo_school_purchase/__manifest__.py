{
    'name': 'Bandoo School Purchase',
    'version': '18.0.2.0.0',
    'summary': 'Consuntivo insegnante: ordine ore insegnante dalle rendicontazioni, prodotto ore per tipo di lezione dal corso',
    'category': 'Purchases',
    'depends': [
        'bandoo_school',
        'purchase',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/project_project_views.xml',
        'wizards/teacher_hours_bill_views.xml',
    ],
    'author': 'Marco De Paoli',
    'maintainer': 'Marco De Paoli',
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
