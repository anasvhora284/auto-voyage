# -*- coding: utf-8 -*-
from odoo import http, _
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.exceptions import AccessError, MissingError
from odoo.osv.expression import OR
import logging

class vehicleControllers(CustomerPortal):
    _logger = logging.getLogger(__name__)

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
        values.update(self._get_frontend_layout_values())
        
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
        values.update(self._get_frontend_layout_values())
        
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
            'fuel_type': kw.get('fuel_type', 'petrol'),
            'transmission': kw.get('transmission', 'manual'),
            'mileage': kw.get('mileage', ''),
            'insurance_number': kw.get('insurance_number', ''),
            'insurance_provider': kw.get('insurance_provider', ''),
            'insurance_expiry': kw.get('insurance_expiry', ''),
            'registration_expiry': kw.get('registration_expiry', ''),
        })
        values.update(self._get_frontend_layout_values())
        
        return request.render("auto_voyage.portal_create_vehicle", values)

    @http.route(['/my/vehicle/create'], type='http', auth="user", website=True)
    def portal_create_vehicle_process(self, **kw):
        """Process vehicle creation form"""
        values = self._prepare_portal_layout_values()
        values.update({
            'page_name': 'create_vehicle',
            'error': {},
            'error_message': [],
            'success': False,
        })
        
        # Validate required fields
        required_fields = ['make', 'model', 'year', 'license_plate']
        error = {}
        error_message = []
        
        for field in required_fields:
            if not kw.get(field):
                error[field] = 'missing'
                error_message.append(_('Please fill in all required fields.'))
        
        # Validate year
        if kw.get('year') and not kw.get('year', '').isdigit():
            error['year'] = 'error'
            error_message.append(_('Year must be a number.'))
        
        # If there are errors, return to form with values
        if error:
            values.update({
                'error': error,
                'error_message': error_message,
            })
            # Pass form values back to form
            for field in kw:
                values[field] = kw.get(field)
            values.update(self._get_frontend_layout_values())
            return request.render("auto_voyage.portal_create_vehicle", values)
        
        try:
            # Prepare vehicle values
            vehicle_values = {
                'partner_id': request.env.user.partner_id.id,
                'name': f"{kw.get('make')} {kw.get('model')} ({kw.get('year')})",
                'make': kw.get('make'),
                'model': kw.get('model'),
                'year': int(kw.get('year')),
                'license_plate': kw.get('license_plate'),
                'state': 'active',
            }
            
            # Add optional fields if present
            optional_fields = [
                'color', 'vin', 'fuel_type', 'transmission', 'mileage',
                'insurance_number', 'insurance_provider', 'insurance_expiry',
                'registration_expiry'
            ]
            
            for field in optional_fields:
                if kw.get(field):
                    if field == 'mileage':
                        vehicle_values[field] = float(kw.get(field))
                    elif field in ['insurance_expiry', 'registration_expiry']:
                        if kw.get(field):
                            vehicle_values[field] = kw.get(field)
                    else:
                        vehicle_values[field] = kw.get(field)
            
            # Create vehicle with proper error handling
            try:
                vehicle = request.env['auto.voyage.vehicle'].sudo().create(vehicle_values)
                # Commit the transaction
                request.env.cr.commit()
                # Redirect to the new vehicle's detail page
                return request.redirect(f'/my/vehicle/{vehicle.id}')
            except Exception as e:
                # Rollback the transaction
                request.env.cr.rollback()
                # Handle specific field errors dynamically
                if 'duplicate key value violates unique constraint' in str(e):
                    # Extract the field name from the error message
                    field_name = str(e).split('Key ')[1].split(' ')[0]  # Extracting the field name from the error message
                    field_name = field_name.replace('_', ' ').replace('(', '').replace(')', '').split('=')
                    field_value = field_name[1]
                    field_name = field_name[0]
                    print(field_name, "------------------------------------")
                    error_message.append(_(f'The value for the field "{field_name}" with "{field_value}" already exists. Please use a different one.'))
                else:
                    error_message.append(_("An error occurred creating a vehicle check details!"))
                values.update({
                    'error': True,
                    'error_message': error_message,
                })
                # Pass form values back to form
                for field in kw:
                    values[field] = kw.get(field)
                values.update(self._get_frontend_layout_values())
                return request.render("auto_voyage.portal_create_vehicle", values)
            
        except Exception as e:
            # Rollback the transaction
            request.env.cr.rollback()
            error_message.append(_("An unexpected error occurred: %s", str(e)))
            values.update({
                'error': error,
                'error_message': error_message,
            })
            # Pass form values back to form
            for field in kw:
                values[field] = kw.get(field)
            values.update(self._get_frontend_layout_values())
            return request.render("auto_voyage.portal_create_vehicle", values)

    @http.route(['/my/vehicle/edit/<int:vehicle_id>'], type='http', auth="user", website=True)
    def portal_edit_vehicle(self, vehicle_id, **kw):
        try:
            vehicle_sudo = self._document_check_access('auto.voyage.vehicle', vehicle_id)
        except (AccessError, MissingError):
            return request.redirect('/my/vehicles')
            
        values = self._prepare_portal_layout_values()
        values.update({
            'vehicle': vehicle_sudo,
            'page_name': 'edit_vehicle',
            'error': {},
            'error_message': [],
            'success': False,
        })
        
        # If form was submitted, process the update
        if kw:
            error = {}
            error_message = []
            
            # Required fields
            required_fields = ['make', 'model', 'year', 'license_plate']
            for field in required_fields:
                if not kw.get(field):
                    error[field] = 'missing'
                    error_message.append(_('Please fill in all required fields.'))
            
            # Validate year
            if kw.get('year') and not kw.get('year', '').isdigit():
                error['year'] = 'error'
                error_message.append(_('Year must be a number.'))
            
            # Report errors
            if error:
                values.update({
                    'error': error,
                    'error_message': error_message,
                    'success': False,
                })
                # Pass form values back to form
                for field in kw:
                    values[field] = kw.get(field)
                values.update(self._get_frontend_layout_values())
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
                    vehicle_values['mileage'] = float(kw.get('mileage'))
                if kw.get('insurance_number'):
                    vehicle_values['insurance_number'] = kw.get('insurance_number')
                if kw.get('insurance_provider'):
                    vehicle_values['insurance_provider'] = kw.get('insurance_provider')
                if kw.get('insurance_expiry'):
                    vehicle_values['insurance_expiry'] = kw.get('insurance_expiry')
                if kw.get('registration_expiry'):
                    vehicle_values['registration_expiry'] = kw.get('registration_expiry')
                
                vehicle_sudo.sudo().write(vehicle_values)
                
                # On successful update, redirect to the vehicles page
                return request.redirect('/my/vehicles')
                
            except Exception as e:
                error_message.append(_("An error occurred: %s", str(e)))
                values.update({
                    'error': error,
                    'error_message': error_message,
                    'success': False,
                })
                # Pass form values back to form
                for field in kw:
                    values[field] = kw.get(field)
                values.update(self._get_frontend_layout_values())
                return request.render("auto_voyage.portal_edit_vehicle", values)
        
        # Populate with vehicle values if no form submission
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
        
        values.update(self._get_frontend_layout_values())
        return request.render("auto_voyage.portal_edit_vehicle", values)