# -*- coding: utf-8 -*-

{
    'name': "KRA POS eTIMS Integration",

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
    'depends': ['point_of_sale', 'ke_etims_tax_pos'],
    'external_dependencies': {'python': ['qrcode']},
    'license': 'LGPL-3',
    'data': [
        # 'views/company.xml',
    ],
    'application': False,
    'auto_install': True
}
