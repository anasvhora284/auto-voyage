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
    
    # Vehicles
    @http.route(['/my/vehicles', '/my/vehicles/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_vehicles(self, page=1, date_begin=None, date_end=None, sortby=None, search=None, search_in='all', **kw):
        """Display user's vehicles"""
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        Vehicle = request.env['auto.voyage.vehicle']
        
        domain = [('partner_id', '=', partner.id)]
        
        # Search
        searchbar_inputs = {
            'make': {'input': 'make', 'label': _('Search in Make')},
            'model': {'input': 'model', 'label': _('Search in Model')},
            'license_plate': {'input': 'license_plate', 'label': _('Search in License Plate')},
            'all': {'input': 'all', 'label': _('Search in All')},
        }
        
        # Search conditions
        if search and search_in:
            search_domain = []
            if search_in in ('make', 'all'):
                search_domain = OR([search_domain, [('make', 'ilike', search)]])
            if search_in in ('model', 'all'):
                search_domain = OR([search_domain, [('model', 'ilike', search)]])
            if search_in in ('license_plate', 'all'):
                search_domain = OR([search_domain, [('license_plate', 'ilike', search)]])
            domain += search_domain
        
        searchbar_sortings = {
            'date': {'label': _('Newest'), 'order': 'create_date desc'},
            'make': {'label': _('Make'), 'order': 'make'},
            'model': {'label': _('Model'), 'order': 'model'},
            'year': {'label': _('Year'), 'order': 'year desc'},
        }
        
        # Default sort by date
        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']
        
        # Count for pager
        vehicle_count = Vehicle.search_count(domain)
        
        # Pager
        pager = portal_pager(
            url="/my/vehicles",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby, 'search_in': search_in, 'search': search},
            total=vehicle_count,
            page=page,
            step=self._items_per_page
        )
        
        # Content according to pager and archive selected
        vehicles = Vehicle.search(domain, order=order, limit=self._items_per_page, offset=pager['offset'])
        
        values.update({
            'date': date_begin,
            'vehicles': vehicles,
            'page_name': 'vehicle',
            'pager': pager,
            'default_url': '/my/vehicles',
            'searchbar_sortings': searchbar_sortings,
            'searchbar_inputs': searchbar_inputs,
            'sortby': sortby,
            'search_in': search_in,
            'search': search,
        })
        return request.render("auto_voyage.portal_my_vehicles", values)
    
    @http.route(['/my/vehicle/<int:vehicle_id>'], type='http', auth="user", website=True)
    def portal_my_vehicle_detail(self, vehicle_id, **kw):
        """Display vehicle details"""
        try:
            vehicle_sudo = self._document_check_access('auto.voyage.vehicle', vehicle_id)
        except (AccessError, MissingError):
            return request.redirect('/my')
            
        values = self._prepare_portal_layout_values()
        values.update({
            'vehicle': vehicle_sudo,
            'page_name': 'vehicle',
        })
        return request.render("auto_voyage.portal_my_vehicle_detail", values)

    @http.route('/my/vehicle/new', type='http', auth="user", website=True)
    def portal_create_vehicle(self, **kw):
        """Display vehicle creation form"""
        values = self._prepare_portal_layout_values()
        values.update({
            'page_name': 'create_vehicle',
            'error': {},
            'error_message': [],
            'success': False,
            # Default values
            'make': kw.get('make', ''),
            'model': kw.get('model', ''),
            'year': kw.get('year', ''),
            'license_plate': kw.get('license_plate', ''),
            'color': kw.get('color', ''),
            'vin': kw.get('vin', ''),
            'fuel_type': kw.get('fuel_type', 'gasoline'),
            'transmission': kw.get('transmission', 'automatic'),
            'mileage': kw.get('mileage', ''),
            'insurance_number': kw.get('insurance_number', ''),
            'insurance_provider': kw.get('insurance_provider', ''),
            'insurance_expiry': kw.get('insurance_expiry', ''),
            'registration_expiry': kw.get('registration_expiry', ''),
        })
        return request.render("auto_voyage.portal_create_vehicle", values)

    @http.route(['/my/vehicle/create'], type='http', auth="user", website=True)
    def portal_create_vehicle_process(self, **kw):
        error = {}
        error_message = []
        
        # Required fields
        required_fields = ['make', 'model', 'year', 'license_plate']
        for field in required_fields:
            if not kw.get(field):
                error[field] = 'missing'
        
        # Validate year
        if kw.get('year') and not kw.get('year', '').isdigit():
            error['year'] = 'error'
            error_message.append(_('Year must be a number.'))
        
        # Report errors
        if error:
            values = {
                'error': error,
                'error_message': error_message,
                'success': False,
            }
            
            # Pass form values back to form
            for field in kw:
                values[field] = kw.get(field)
            
            return request.render("auto_voyage.portal_create_vehicle", values)
        
        # Process data
        try:
            # Create vehicle
            vehicle_values = {
                'partner_id': request.env.user.partner_id.id,
                'name': f"{kw.get('make')} {kw.get('model')} ({kw.get('year')})",
                'make': kw.get('make'),
                'model': kw.get('model'),
                'year': int(kw.get('year')),
                'license_plate': kw.get('license_plate'),
                'state': 'active',
            }
            
            # Optional fields
            if kw.get('color'):
                vehicle_values['color'] = kw.get('color')
            if kw.get('vin'):
                vehicle_values['vin'] = kw.get('vin')
            if kw.get('fuel_type'):
                vehicle_values['fuel_type'] = kw.get('fuel_type')
            if kw.get('transmission'):
                vehicle_values['transmission'] = kw.get('transmission')
            if kw.get('mileage'):
                vehicle_values['mileage'] = int(kw.get('mileage'))
            if kw.get('insurance_number'):
                vehicle_values['insurance_number'] = kw.get('insurance_number')
            if kw.get('insurance_provider'):
                vehicle_values['insurance_provider'] = kw.get('insurance_provider')
            if kw.get('insurance_expiry'):
                vehicle_values['insurance_expiry'] = kw.get('insurance_expiry')
            if kw.get('registration_expiry'):
                vehicle_values['registration_expiry'] = kw.get('registration_expiry')
            
            vehicle = request.env['auto.voyage.vehicle'].sudo().create(vehicle_values)
            
            values = {
                'success': True,
                'page_name': 'create_vehicle',
            }
            
            return request.render("auto_voyage.portal_create_vehicle", values)
            
        except Exception as e:
            error_message.append(_("An error occurred: %s", str(e)))
            values = {
                'error': error,
                'error_message': error_message,
                'success': False,
            }
            
            # Pass form values back to form
            for field in kw:
                values[field] = kw.get(field)
            
            return request.render("auto_voyage.portal_create_vehicle", values)

    @http.route(['/my/vehicle/edit/<int:vehicle_id>'], type='http', auth="user", website=True)
    def portal_edit_vehicle(self, vehicle_id, **kw):
        try:
            vehicle_sudo = self._document_check_access('auto.voyage.vehicle', vehicle_id)
        except (AccessError, MissingError):
            return request.redirect('/my/vehicles')
        
        values = {
            'vehicle': vehicle_sudo,
            'page_name': 'edit_vehicle',
            'error': {},
            'success': False,
        }
        
        # If form was submitted with errors, populate fields with submitted values
        if kw:
            for field in ['make', 'model', 'year', 'license_plate', 'color', 'vin', 'fuel_type', 
                         'transmission', 'mileage', 'insurance_number', 'insurance_provider', 
                         'insurance_expiry', 'registration_expiry']:
                if field in kw:
                    values[field] = kw.get(field)
        # Otherwise populate with vehicle values
        else:
            values.update({
                'make': vehicle_sudo.make,
                'model': vehicle_sudo.model,
                'year': vehicle_sudo.year,
                'license_plate': vehicle_sudo.license_plate,
                'color': vehicle_sudo.color,
                'vin': vehicle_sudo.vin,
                'fuel_type': vehicle_sudo.fuel_type,
                'transmission': vehicle_sudo.transmission,
                'mileage': vehicle_sudo.mileage,
                'insurance_number': vehicle_sudo.insurance_number,
                'insurance_provider': vehicle_sudo.insurance_provider,
                'insurance_expiry': vehicle_sudo.insurance_expiry,
                'registration_expiry': vehicle_sudo.registration_expiry,
            })
        
        return request.render("auto_voyage.portal_edit_vehicle", values)

    @http.route(['/my/vehicle/update/<int:vehicle_id>'], type='http', auth="user", website=True)
    def portal_update_vehicle_process(self, vehicle_id, **kw):
        try:
            vehicle_sudo = self._document_check_access('auto.voyage.vehicle', vehicle_id)
        except (AccessError, MissingError):
            return request.redirect('/my/vehicles')
        
        error = {}
        error_message = []
        
        # Required fields
        required_fields = ['make', 'model', 'year', 'license_plate']
        for field in required_fields:
            if not kw.get(field):
                error[field] = 'missing'
        
        # Validate year
        if kw.get('year') and not kw.get('year', '').isdigit():
            error['year'] = 'error'
            error_message.append(_('Year must be a number.'))
        
        # Report errors
        if error:
            values = {
                'vehicle': vehicle_sudo,
                'error': error,
                'error_message': error_message,
                'success': False,
            }
            
            # Pass form values back to form
            for field in kw:
                values[field] = kw.get(field)
            
            return request.render("auto_voyage.portal_edit_vehicle", values)
        
        # Process data
        try:
            # Update vehicle
            vehicle_values = {
                'name': f"{kw.get('make')} {kw.get('model')} ({kw.get('year')})",
                'make': kw.get('make'),
                'model': kw.get('model'),
                'year': int(kw.get('year')),
                'license_plate': kw.get('license_plate'),
            }
            
            # Optional fields
            if kw.get('color'):
                vehicle_values['color'] = kw.get('color')
            if kw.get('vin'):
                vehicle_values['vin'] = kw.get('vin')
            if kw.get('fuel_type'):
                vehicle_values['fuel_type'] = kw.get('fuel_type')
            if kw.get('transmission'):
                vehicle_values['transmission'] = kw.get('transmission')
            if kw.get('mileage'):
                vehicle_values['mileage'] = int(kw.get('mileage'))
            if kw.get('insurance_number'):
                vehicle_values['insurance_number'] = kw.get('insurance_number')
            if kw.get('insurance_provider'):
                vehicle_values['insurance_provider'] = kw.get('insurance_provider')
            if kw.get('insurance_expiry'):
                vehicle_values['insurance_expiry'] = kw.get('insurance_expiry')
            if kw.get('registration_expiry'):
                vehicle_values['registration_expiry'] = kw.get('registration_expiry')
            
            vehicle_sudo.write(vehicle_values)
            
            values = {
                'vehicle': vehicle_sudo,
                'success': True,
                'page_name': 'edit_vehicle',
            }
            
            return request.render("auto_voyage.portal_edit_vehicle", values)
            
        except Exception as e:
            error_message.append(_("An error occurred: %s", str(e)))
            values = {
                'vehicle': vehicle_sudo,
                'error': error,
                'error_message': error_message,
                'success': False,
            }
            
            # Pass form values back to form
            for field in kw:
                values[field] = kw.get(field)
            
            return request.render("auto_voyage.portal_edit_vehicle", values)
    
    # Service Requests
    @http.route(['/my/service-requests', '/my/service-requests/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_service_requests(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, **kw):
        """Display user's service requests"""
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        ServiceRequest = request.env['auto.voyage.service.request']
        
        domain = [('partner_id', '=', partner.id)]
        
        searchbar_sortings = {
            'date': {'label': _('Scheduled Date'), 'order': 'scheduled_date desc'},
            'name': {'label': _('Reference'), 'order': 'name'},
            'state': {'label': _('Status'), 'order': 'state'},
        }
        
        searchbar_filters = {
            'all': {'label': _('All'), 'domain': []},
            'draft': {'label': _('Draft'), 'domain': [('state', '=', 'draft')]},
            'confirmed': {'label': _('Confirmed'), 'domain': [('state', '=', 'confirmed')]},
            'scheduled': {'label': _('Scheduled'), 'domain': [('state', '=', 'scheduled')]},
            'in_progress': {'label': _('In Progress'), 'domain': [('state', '=', 'in_progress')]},
            'completed': {'label': _('Completed'), 'domain': [('state', '=', 'completed')]},
            'cancelled': {'label': _('Cancelled'), 'domain': [('state', '=', 'cancelled')]},
        }
        
        # Default sort by date
        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']
        
        # Default filter by all
        if not filterby:
            filterby = 'all'
        domain += searchbar_filters[filterby]['domain']
        
        # Count for pager
        service_count = ServiceRequest.search_count(domain)
        
        # Pager
        pager = portal_pager(
            url="/my/service-requests",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby, 'filterby': filterby},
            total=service_count,
            page=page,
            step=self._items_per_page
        )
        
        # Content according to pager and archive selected
        service_requests = ServiceRequest.search(domain, order=order, limit=self._items_per_page, offset=pager['offset'])
        
        values.update({
            'date': date_begin,
            'service_requests': service_requests,
            'page_name': 'service_request',
            'pager': pager,
            'default_url': '/my/service-requests',
            'searchbar_sortings': searchbar_sortings,
            'searchbar_filters': searchbar_filters,
            'sortby': sortby,
            'filterby': filterby,
        })
        return request.render("auto_voyage.portal_my_service_requests", values)
    
    @http.route(['/my/service-request/<int:service_request_id>'], type='http', auth="user", website=True)
    def portal_my_service_request_detail(self, service_request_id, **kw):
        """Display service request details"""
        try:
            service_request_sudo = self._document_check_access('auto.voyage.service.request', service_request_id)
        except (AccessError, MissingError):
            return request.redirect('/my')
            
        values = self._prepare_portal_layout_values()
        values.update({
            'service_request': service_request_sudo,
            'page_name': 'service_request',
        })
        return request.render("auto_voyage.portal_my_service_request_detail_view", values)
    
    # Service Provider Portal
    @http.route(['/my/provider-services', '/my/provider-services/page/<int:page>'], type='http', auth="user", website=True)
    def portal_provider_services(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        
        # Check if user is a service provider
        provider = request.env['auto.voyage.service.provider'].sudo().search([('partner_id', '=', partner.id)], limit=1)
        if not provider:
            return request.redirect('/my')
            
        ServiceRequest = request.env['auto.voyage.service.request']
        
        domain = [('provider_id', '=', provider.id)]
        
        searchbar_sortings = {
            'date': {'label': _('Scheduled Date'), 'order': 'scheduled_date desc'},
            'name': {'label': _('Reference'), 'order': 'name'},
            'state': {'label': _('Status'), 'order': 'state'},
        }
        
        searchbar_filters = {
            'all': {'label': _('All'), 'domain': []},
            'scheduled': {'label': _('Scheduled'), 'domain': [('state', '=', 'scheduled')]},
            'in_progress': {'label': _('In Progress'), 'domain': [('state', '=', 'in_progress')]},
            'completed': {'label': _('Completed'), 'domain': [('state', '=', 'completed')]},
        }
        
        # Default sort by date
        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']
        
        # Default filter by all
        if not filterby:
            filterby = 'all'
        domain += searchbar_filters[filterby]['domain']
        
        # Count for pager
        service_count = ServiceRequest.search_count(domain)
        
        # Pager
        pager = portal_pager(
            url="/my/provider-services",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby, 'filterby': filterby},
            total=service_count,
            page=page,
            step=self._items_per_page
        )
        
        # Content according to pager and archive selected
        service_requests = ServiceRequest.search(domain, order=order, limit=self._items_per_page, offset=pager['offset'])
        
        values.update({
            'date': date_begin,
            'provider': provider,
            'service_requests': service_requests,
            'page_name': 'provider_service',
            'pager': pager,
            'default_url': '/my/provider-services',
            'searchbar_sortings': searchbar_sortings,
            'searchbar_filters': searchbar_filters,
            'sortby': sortby,
            'filterby': filterby,
        })
        return request.render("auto_voyage.portal_provider_services", values)
    
    @http.route(['/my/provider-service/<int:service_request_id>'], type='http', auth="user", website=True)
    def portal_provider_service_detail(self, service_request_id, **kw):
        try:
            service_request_sudo = self._document_check_access('auto.voyage.service.request', service_request_id)
        except (AccessError, MissingError):
            return request.redirect('/my')
            
        # Check if user is the service provider
        provider = request.env['auto.voyage.service.provider'].sudo().search([('partner_id', '=', request.env.user.partner_id.id)], limit=1)
        if not provider or service_request_sudo.provider_id != provider:
            return request.redirect('/my')
            
        values = self._prepare_portal_layout_values()
        values.update({
            'service_request': service_request_sudo,
            'page_name': 'provider_service',
        })
        return request.render("auto_voyage.portal_provider_service_detail", values)
    
    @http.route(['/my/provider-service/<int:service_request_id>/update_status'], type='http', auth="user", website=True)
    def provider_update_service_status(self, service_request_id, new_status, **kw):
        try:
            service_request_sudo = self._document_check_access('auto.voyage.service.request', service_request_id)
        except (AccessError, MissingError):
            return request.redirect('/my')
            
        # Check if user is the service provider
        provider = request.env['auto.voyage.service.provider'].sudo().search([('partner_id', '=', request.env.user.partner_id.id)], limit=1)
        if not provider or service_request_sudo.provider_id != provider:
            return request.redirect('/my')
            
        # Validate status transition
        valid_transitions = {
            'scheduled': ['in_progress', 'cancelled'],
            'in_progress': ['completed', 'cancelled'],
        }
        
        if service_request_sudo.state not in valid_transitions or new_status not in valid_transitions[service_request_sudo.state]:
            return request.redirect('/my/provider-services')
            
        # Update status
        service_request_sudo.write({'state': new_status})
        
        return request.redirect('/my/provider-service/%s' % service_request_id)


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

