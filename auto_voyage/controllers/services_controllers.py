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

class AutoVoyageServicesController(http.Controller):
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
    def portal_my_service_requests(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, search=None, search_in='all', **kw):
        """Display service requests for the current user"""
        values = self._prepare_portal_layout_values()
        ServiceRequest = request.env['auto.voyage.service.request']
        
        # Get domain from access control method
        domain = ServiceRequest._search_service_requests_by_access()
        
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
            'page_name': 'service_requests',
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
    def portal_service_request_detail(self, service_request_id, **kw):
        """Display service request details"""
        ServiceRequest = request.env['auto.voyage.service.request']
        
        # Get domain from access control method
        domain = ServiceRequest._search_service_requests_by_access()
        domain.append(('id', '=', service_request_id))
        
        # Check if the user has access to this specific service request
        service_request = ServiceRequest.search(domain, limit=1)
        if not service_request:
            return request.redirect('/my/service-requests')
        
        values = self._prepare_portal_layout_values()
        values.update({
            'service_request': service_request,
            'page_name': 'service_request',
            'user': request.env.user,
            'env': request.env,
        })
        values.update(self._get_frontend_layout_values())
        
        return request.render("auto_voyage.portal_my_service_request_detail_view", values)
    
    @http.route(['/my/services/<int:service_id>/rate'], type='http', auth="user", website=True)
    def portal_service_rating(self, service_id, **kw):
        """Service rating page"""
        service = request.env['auto.voyage.service.request'].sudo().browse(service_id)
        if not service.exists() or service.partner_id.id != request.env.user.partner_id.id:
            return request.redirect('/my')
            
        values = self._prepare_portal_layout_values()
        values.update({
            'service': service,
            'page_name': 'service_rating',
        })
        return request.render("auto_voyage.portal_service_rating", values)
