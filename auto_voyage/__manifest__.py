# -*- coding: utf-8 -*-
{
    'name': "Auto Voyage",

    'summary': "Complete Vehicle Service Management System",

    'description': """
Auto Voyage is a comprehensive vehicle service management system that helps:
- Manage vehicles and their service history
- Handle service providers and their schedules
- Manage service requests and bookings
- Digital contract management
- Rating and review system
- Complete service lifecycle management
    """,

    'author': "Anas Vhora",
    'website': "https://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Services/Vehicle',
    'version': '18.0.1.0.0',
    'sequence': -100,

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'mail',
        'portal',
        'product',
        'calendar',
        'web',
        'account',
        'account_payment',
    ],

    # always loaded
    'data': [
        # Security
        'security/auto_voyage_security.xml',
        'security/ir.model.access.csv',
        
        # Data
        'data/sequence_data.xml',
        'data/service_data.xml',
        
        # Views - Menu first, then other views
        'views/menu_views.xml',  # Base menu structure should be loaded first
        'views/vehicle_views.xml',
        'views/service_views.xml',
        'views/service_provider_views.xml',
        'views/service_request_views.xml',
        'views/contract_views.xml',
        'views/discussion_views.xml',
        'views/rating_views.xml',
        'views/dashboard_views.xml',
        
        # Wizards
        'wizard/assign_service_views.xml',
        
        # Reports
        'report/service_report.xml',
        'report/contract_report.xml',
    ],

    'demo': [
        'demo/demo.xml',
    ],
    
    'application': True,
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}

