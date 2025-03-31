# -*- coding: utf-8 -*-
from odoo import http, fields, _
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.exceptions import AccessError, MissingError, ValidationError
from odoo.osv.expression import OR
from collections import OrderedDict
import json
import logging
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)

class serviceControllers(CustomerPortal):
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
        values.update(self._get_frontend_layout_values())
        
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
        values.update(self._get_frontend_layout_values())
        
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
        
        # Get today's date
        today = fields.Date.today()
        
        # Get today's requests
        today_domain = [
            ('provider_id', '=', provider.id),
            ('scheduled_date', '>=', today),
            ('scheduled_date', '<', today + timedelta(days=1)),
            ('state', 'in', ['scheduled', 'in_progress'])
        ]
        today_requests = ServiceRequest.search(today_domain, order='scheduled_date asc')
        
        values.update({
            'date': date_begin,
            'provider': provider,
            'service_requests': service_requests,
            'today_requests': today_requests,
            'page_name': 'provider_service',
            'pager': pager,
            'default_url': '/my/provider-services',
            'searchbar_sortings': searchbar_sortings,
            'searchbar_filters': searchbar_filters,
            'sortby': sortby,
            'filterby': filterby,
            'today': today,
        })
        values.update(self._get_frontend_layout_values())
        
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
        values.update(self._get_frontend_layout_values())
        
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
