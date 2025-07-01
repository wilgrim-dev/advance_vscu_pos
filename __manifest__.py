# -*- coding: utf-8 -*-

{
    'name': "KRA POS eTIMS VSCU Integration",

    'summary': """
        Kra electronically signs pos receipts.""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Wilson Ndirangu",
    'website': "https://odoo.co.ke",

    'category': 'Extra Tools',
    'version': '17.0.0.1.0',

    # any module necessary for this one to work correctly
    'depends': ['point_of_sale'],
    'external_dependencies': {'python': ['qrcode']},
    'license': 'LGPL-3',
    'data': [
        'views/pos.xml',
        'views/pos_config.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [ 
            'advance_vscu_pos/static/src/**/*',
        ],       
    },
    'application': False,
    'auto_install': True
}
