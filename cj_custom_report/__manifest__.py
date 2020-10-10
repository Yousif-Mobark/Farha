{
    'name': 'Magal Maintenance Management',
    'version': '1.0',
    'author': 'Osman Alrasheed',
    'category': 'Employees',
    'description': """
This module created to manage maintence services provid by Magal 

	""",
 'depends': ['base','fleet','maintenance','stock','account','hr','sale','point_of_sale'],
    'data': [

        'data/data.xml',
        # 'security/ir.model.access.csv',
        'wizard/report_wizard.xml',
        'report/pos_report.xml',
        # 'views/maintenance.xml',
        # 'views/custody_clearace.xml',
        # 'views/custody_request.xml',
        # 'views/manufacturing.xml',
        # 'views/contract.xml',



    ],
    'application': True,
    'installable': True,
    'auto_install': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
