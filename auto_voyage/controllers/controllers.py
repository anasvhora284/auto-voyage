# -*- coding: utf-8 -*-
from odoo import http, fields, _
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.exceptions import AccessError, MissingError, ValidationError
from odoo.osv.expression import OR
from collections import OrderedDict
import json
import logging

_logger = logging.getLogger(__name__)

# Define service categories with icons
SERVICE_CATEGORIES = {
    'maintenance': {'name': 'Maintenance', 'icon': 'wrench', 'description': 'Regular vehicle maintenance services'},
    'repair': {'name': 'Repair', 'icon': 'tools', 'description': 'Vehicle repair and restoration services'},
    'inspection': {'name': 'Inspection', 'icon': 'clipboard-check', 'description': 'Comprehensive vehicle inspection services'},
    'cleaning': {'name': 'Cleaning', 'icon': 'spray-can', 'description': 'Vehicle cleaning and detailing services'},
    'custom': {'name': 'Custom Service', 'icon': 'cog', 'description': 'Customized vehicle services'}
}

class AutoVoyagePortal(CustomerPortal):
    """Portal Controller for Auto Voyage"""

    def _get_frontend_layout_values(self):
        """Helper method to prepare frontend layout values"""
        # Get frontend languages
        frontend_languages = request.env['res.lang'].sudo()._get_frontend()
        current_lang = frontend_languages[request.env.lang]
        
        # Prepare frontend layout values
        return {
            'frontend_languages': frontend_languages,
            'frontend_language': current_lang,
            'frontend_language_code': request.env.lang,
            'frontend_language_name': current_lang.name,
            'frontend_language_direction': current_lang.direction,
            'frontend_language_rtl': current_lang.direction == 'rtl',
            'is_portal': True,
            'no_breadcrumbs': False,
            'breadcrumbs_searchbar': False,
            'is_frontend_multilang': bool(len(frontend_languages) > 1),
            'lang': request.env.lang,
            'user_id': request.env.user,
            'res_company': request.env.company,
            'request': request,
        }

    def _prepare_home_portal_values(self, counters):
        """Prepare values for portal home page"""
        values = super()._prepare_home_portal_values(counters)
        
        partner = request.env.user.partner_id
        
        if 'vehicle_count' in counters:
            vehicle_count = request.env['auto.voyage.vehicle'].search_count([
                ('partner_id', '=', partner.id)
            ])
            values['vehicle_count'] = vehicle_count
            
        if 'service_request_count' in counters:
            service_request_count = request.env['auto.voyage.service.request'].search_count([
                ('partner_id', '=', partner.id)
            ])
            values['service_request_count'] = service_request_count
            
        if 'contract_count' in counters:
            contract_count = request.env['auto.voyage.contract'].search_count([
                ('partner_id', '=', partner.id)
            ])
            values['contract_count'] = contract_count
            
        if 'rating_count' in counters:
            rating_count = request.env['auto.voyage.rating'].search_count([
                ('partner_id', '=', partner.id)
            ])
            values['rating_count'] = rating_count
            
        if 'discussion_count' in counters:
            discussion_count = request.env['auto.voyage.discussion'].search_count([
                ('partner_id', '=', partner.id)
            ])
            values['discussion_count'] = discussion_count
            
        return values

class AutoVoyageWebsite(http.Controller):
    """Website Controller for Auto Voyage"""

    @http.route('/', type='http', auth="public", website=True)
    def index(self, **kw):
        """Website homepage"""
        return request.render("auto_voyage.homepage", {
            'services': request.env['auto.voyage.service'].search([]),
            'providers': request.env['auto.voyage.service.provider'].search([]),
            'categories': SERVICE_CATEGORIES
        })
    
    @http.route('/services', type='http', auth="public", website=True)
    def services(self, **kw):
        """Services page"""
        # Get all services
        services = request.env['auto.voyage.service'].search([])
        currency_id = request.env['res.currency'].search([], limit=1)
        
        # Group services by category
        services_by_category = {}
        for service in services:
            if service.category not in services_by_category:
                services_by_category[service.category] = []
            services_by_category[service.category].append(service)
        
        return request.render("auto_voyage.services_page", {
            'services': services,
            'currency_id': currency_id,
            'services_by_category': services_by_category,
            'categories': SERVICE_CATEGORIES
        })
    
    @http.route('/about', type='http', auth="public", website=True)
    def about(self, **kw):
        """About page"""
        return request.render("auto_voyage.about_page", {})
    
    @http.route('/contact', type='http', auth="public", website=True)
    def contact(self, **kw):
        """Contact page"""
        return request.render("auto_voyage.contact_page", {})
    
    @http.route('/booking', type='http', auth="user", website=True)
    def booking(self, **kw):
        """Booking page"""
        return request.render("auto_voyage.booking_page", {
            'vehicles': request.env['auto.voyage.vehicle'].search([('partner_id', '=', request.env.user.partner_id.id)]),
            'services': request.env['auto.voyage.service'].search([]),
            'providers': request.env['auto.voyage.service.provider'].search([]),
            'categories': SERVICE_CATEGORIES
        })
    
    @http.route('/booking/submit', type='http', auth="user", website=True, methods=['POST'])
    def booking_submit(self, **post):
        """Handle booking form submission"""
        # Convert the scheduled_date from ISO format to the expected format
        scheduled_date = post.get('scheduled_date')
        if scheduled_date:
            # Convert the ISO format to the required format
            scheduled_date = scheduled_date.replace("T", " ")  # Replace 'T' with a space

        service_request = request.env['auto.voyage.service.request'].sudo().create({
            'partner_id': request.env.user.partner_id.id,
            'vehicle_id': int(post.get('vehicle_id')),
            'service_id': int(post.get('service_id')),
            'scheduled_date': scheduled_date,  # Use the converted date
            'description': post.get('description'),
            'state': 'draft',
        })
        return request.redirect('/my/service-request/%s' % service_request.id)
    
    @http.route('/service-providers', type='http', auth="public", website=True)
    def service_providers(self, **kw):
        """Service providers page"""
        return request.render("auto_voyage.providers_page", {
            'providers': request.env['auto.voyage.service.provider'].search([]),
            'ratings': request.env['auto.voyage.rating'].search([('state', '=', 'published')])
        })

