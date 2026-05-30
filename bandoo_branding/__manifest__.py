{
    'name': 'Bandoo Branding',
    'version': '18.0.1.0.0',
    'summary': 'Custom branding for the Bandoo login page',
    'category': 'Technical',
    'depends': ['web'],
    'data': [
        'views/login_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'bandoo_branding/static/img/logo.png',
        ],
    },
    'author': 'Marco De Paoli',
    'support': 'depaolim@gmail.com',
    'maintainer': 'Marco De Paoli',
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
