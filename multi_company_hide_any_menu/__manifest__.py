{
    'name': 'Multi Company Hide Any Menu For Any User',
    'version': '0.1',
    'author': 'FreelancerApps',
    'category': 'Tools',
    'depends': ['base'],
    'summary': 'Multi Company Hide Any Menu For Any User hide invisible any menu hide invisible any hide invisible menu hide any invisible hide any menu invisible hide any hide menu invisible hide menu any invisible hide menu invisible any hide any invisible menu any hide invisible hide menu hide any report hide report hide any field hide field Generic Security Restriction generic_security_restriction restrict menu show_hide_menu hide menu hide field hide report Restrict User Menus web_restrict_user_menu hide user menus user_menu_restrictions restrict_menu_access User Menu Restriction Security for Menu generate barcode product auto Restrict Read Only User Hide Any Menu Restrict User Menus multi level approve three level approve Tripple Approve Purchase Tripple Approval Project Checklist Task Checklist website document attachment product attachment',
    'description': """
Multi Company Hide / Invisible Any Menu sub-menu from any user even if user is administrator.
=============================================================================================
If you want to hide unwanted menu, sub-menu for particular user depend on selected company for that user then just install this app.

Suppose User want to hide Sales App in Company A but should be visible in Company B,
Purchase App visible in Company A but should be hidden in Company B.
So user can avoid selling or buying in a wrong company.
There are too many such type of scenario in such situation this app is very useful

Go to setting --> Users --> Users --> Hide Specific Menu Page --> Select any Menu, Sub menu that you want ot hide for this user. --> Just save and refresh page and enjoy !

Key features:
--------------
* Easy To Use.
* Hide Any Menu, Sub-Menu.
* Setting Can Applied For Administrator Too.
* Company Wise Configuration.
* Same Menu Can Accessible From One Company But Hide In Another Company.
* Set Access Right, So Only Specific User Will Change/Set Hide Menu Setting.

<Search Keyword for internal user only>
---------------------------------------
hide invisible any menu hide invisible any hide invisible menu hide any invisible hide any menu invisible hide any hide menu invisible hide menu any invisible hide menu invisible any hide any invisible menu any hide invisible hide menu
""",
    'data': [
        'security/multi_company_menu_hide_security.xml',
        'security/ir.model.access.csv',
        'views/company_view.xml',
        'wizard/wiz_fill_user_hide_menu.xml'
    ],
    'images': ['static/description/multi_company_hide_any_menu_banner.png'],
    'live_test_url': 'https://youtu.be/hov0m73bOMA',
    'price': 12.99,
    'currency': 'USD',
    'license': 'OPL-1',
    'installable': True,
    'auto_install': False,
}
