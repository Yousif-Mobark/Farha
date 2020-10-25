{
    'name': 'Magal Maintenance Management',
    'version': '1.0',
    'author': 'Osman Alrasheed',
    'category': 'Employees',
    'description': """
This module created to manage maintence services provid by Magal 

	""",
 'depends': ['base','maintenance','stock','account','hr','sale'],
    'data': [

        'security/ir.model.access.csv',
        'views/maintenance.xml',
        'views/custody_clearace.xml',
        'views/custody_request.xml',
        'views/manufacturing.xml',
        'views/contract.xml'


    ],
    'application': True,
    'installable': True,
    'auto_install': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
