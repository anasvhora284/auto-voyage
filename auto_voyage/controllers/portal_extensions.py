# -*- coding: utf-8 -*-
from odoo import http, fields, _
from odoo.http import request
from odoo.exceptions import AccessError, MissingError, ValidationError
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.osv.expression import OR
from datetime import datetime, timedelta
from .controllers import AutoVoyagePortal
import base64

class AutoVoyagePortalExtensions(AutoVoyagePortal):
    """Extended Portal Controller for Auto Voyage"""
    
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
    
    # Contracts
    @http.route(['/my/contracts', '/my/contracts/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_contracts(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, **kw):
        """Display user's contracts"""
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        Contract = request.env['auto.voyage.contract']
        
        domain = [('partner_id', '=', partner.id)]
        
        # Date filters
        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]
            
        # Default sort by date
        if not sortby:
            sortby = 'date'
            
        # Sorting options
        searchbar_sortings = {
            'date': {'label': _('Newest'), 'order': 'create_date desc'},
            'name': {'label': _('Reference'), 'order': 'name'},
            'start_date': {'label': _('Start Date'), 'order': 'start_date desc'},
        }
        
        # Filter options
        searchbar_filters = {
            'all': {'label': _('All'), 'domain': []},
            'active': {'label': _('Active'), 'domain': [('state', '=', 'active')]},
            'draft': {'label': _('Draft'), 'domain': [('state', '=', 'draft')]},
            'expired': {'label': _('Expired'), 'domain': [('state', '=', 'expired')]},
        }
        
        # Default filter
        if not filterby:
            filterby = 'all'
        domain += searchbar_filters[filterby]['domain']
        
        # Count for pager
        contract_count = Contract.search_count(domain)
        
        # Pager
        pager = portal_pager(
            url="/my/contracts",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby, 'filterby': filterby},
            total=contract_count,
            page=page,
            step=self._items_per_page
        )
        
        # Content
        contracts = Contract.search(domain, order=searchbar_sortings[sortby]['order'], limit=self._items_per_page, offset=pager['offset'])
        
        values.update({
            'date': date_begin,
            'contracts': contracts,
            'page_name': 'contracts',
            'pager': pager,
            'default_url': '/my/contracts',
            'searchbar_sortings': searchbar_sortings,
            'searchbar_filters': searchbar_filters,
            'sortby': sortby,
            'filterby': filterby,
        })
        values.update(self._get_frontend_layout_values())
        
        return request.render("auto_voyage.portal_my_contracts", values)
    
    @http.route(['/my/contracts/<int:contract_id>'], type='http', auth="user", website=True)
    def portal_contract_page(self, contract_id, **kw):
        """Display contract details"""
        try:
            contract_sudo = self._document_check_access('auto.voyage.contract', contract_id)
        except (AccessError, MissingError):
            return request.redirect('/my/contracts')
            
        values = self._prepare_portal_layout_values()
        values.update({
            'contract': contract_sudo,
            'page_name': 'contract',
        })
        values.update(self._get_frontend_layout_values())
        
        return request.render("auto_voyage.portal_contract_page", values)
    
    @http.route(['/my/contracts/<int:contract_id>/accept'], type='http', auth="user", website=True)
    def portal_contract_accept(self, contract_id, **kw):
        """Accept contract"""
        try:
            contract_sudo = self._document_check_access('auto.voyage.contract', contract_id)
        except (AccessError, MissingError):
            return request.redirect('/my/contracts')
            
        if contract_sudo.state == 'draft':
            contract_sudo.write({'state': 'active'})
            
        return request.redirect('/my/contracts/%s' % contract_id)
    
    @http.route(['/my/contracts/<int:contract_id>/reject'], type='http', auth="user", website=True)
    def portal_contract_reject(self, contract_id, **kw):
        """Reject contract"""
        try:
            contract_sudo = self._document_check_access('auto.voyage.contract', contract_id)
        except (AccessError, MissingError):
            return request.redirect('/my/contracts')
            
        if contract_sudo.state == 'draft':
            contract_sudo.write({'state': 'cancelled'})
            
        return request.redirect('/my/contracts/%s' % contract_id)
    
    # Discussions
    @http.route(['/my/discussions', '/my/discussions/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_discussions(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, **kw):
        """Display user's discussions"""
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        Discussion = request.env['auto.voyage.discussion']
        
        domain = [('partner_id', '=', partner.id)]
        
        # Date filters
        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]
            
        # Default sort by date
        if not sortby:
            sortby = 'date'
            
        # Sorting options
        searchbar_sortings = {
            'date': {'label': _('Newest'), 'order': 'create_date desc'},
            'name': {'label': _('Subject'), 'order': 'name'},
        }
        
        # Filter options
        searchbar_filters = {
            'all': {'label': _('All'), 'domain': []},
            'open': {'label': _('Open'), 'domain': [('state', '=', 'open')]},
            'closed': {'label': _('Closed'), 'domain': [('state', '=', 'closed')]},
        }
        
        # Default filter
        if not filterby:
            filterby = 'all'
        domain += searchbar_filters[filterby]['domain']
        
        # Count for pager
        discussion_count = Discussion.search_count(domain)
        
        # Pager
        pager = portal_pager(
            url="/my/discussions",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby, 'filterby': filterby},
            total=discussion_count,
            page=page,
            step=self._items_per_page
        )
        
        # Content
        discussions = Discussion.search(domain, order=searchbar_sortings[sortby]['order'], limit=self._items_per_page, offset=pager['offset'])
        
        values.update({
            'date': date_begin,
            'discussions': discussions,
            'page_name': 'discussions',
            'pager': pager,
            'default_url': '/my/discussions',
            'searchbar_sortings': searchbar_sortings,
            'searchbar_filters': searchbar_filters,
            'sortby': sortby,
            'filterby': filterby,
        })
        values.update(self._get_frontend_layout_values())
        
        return request.render("auto_voyage.portal_my_discussions", values)
    
    @http.route(['/my/discussions/<int:discussion_id>'], type='http', auth="user", website=True)
    def portal_discussion_page(self, discussion_id, **kw):
        """Display discussion details"""
        try:
            discussion_sudo = self._document_check_access('auto.voyage.discussion', discussion_id)
        except (AccessError, MissingError):
            return request.redirect('/my/discussions')
            
        values = self._prepare_portal_layout_values()
        values.update({
            'discussion': discussion_sudo,
            'page_name': 'discussion',
        })
        values.update(self._get_frontend_layout_values())
        
        return request.render("auto_voyage.portal_discussion_page", values)
    
    @http.route(['/my/discussions/post'], type='http', auth="user", website=True, methods=['POST'])
    def portal_discussion_post(self, **kw):
        """Post a message to a discussion"""
        discussion_id = int(kw.get('discussion_id', 0))
        message = kw.get('message', '')
        attachment = kw.get('attachment', None)
        
        if not discussion_id or not message:
            return request.redirect('/my/discussions')
            
        try:
            discussion_sudo = self._document_check_access('auto.voyage.discussion', discussion_id)
        except (AccessError, MissingError):
            return request.redirect('/my/discussions')
            
        if discussion_sudo.state not in ['new', 'in_progress', 'waiting']:
            return request.redirect('/my/discussions/%s' % discussion_id)
            
        # Determine the author - if user is customer, use customer partner_id
        # If user is internal, use the service provider's partner_id
        author_id = request.env.user.partner_id.id
        
        # Create message
        message_values = {
            'body': message,
            'message_type': 'comment',
            'subtype_xmlid': 'mail.mt_comment',
            'author_id': author_id,
        }
        
        # Handle attachment if any
        attachment_ids = []
        if attachment and attachment.filename:
            try:
                # Read the file content
                file_content = attachment.read()
                if file_content:
                    # Create the attachment
                    attachment_data = {
                        'name': attachment.filename,
                        'datas': base64.b64encode(file_content),
                        'res_model': 'auto.voyage.discussion',
                        'res_id': discussion_id,
                    }
                    new_attachment = request.env['ir.attachment'].sudo().create(attachment_data)
                    attachment_ids.append(new_attachment.id)
                    message_values['attachment_ids'] = [(6, 0, attachment_ids)]
            except Exception as e:
                # Log the error but don't fail the whole operation
                _logger.error(f"Error processing attachment: {str(e)}")
        
        # Post the message with attachment if any
        discussion_sudo.with_context(mail_create_nosubscribe=True).message_post(**message_values)
            
        return request.redirect('/my/discussions/%s' % discussion_id)
    
    @http.route(['/my/discussions/<int:discussion_id>/close'], type='http', auth="user", website=True)
    def portal_discussion_close(self, discussion_id, **kw):
        """Close a discussion"""
        try:
            discussion_sudo = self._document_check_access('auto.voyage.discussion', discussion_id)
        except (AccessError, MissingError):
            return request.redirect('/my/discussions')
            
        # Only the creator can close the discussion
        if discussion_sudo.create_uid.id == request.env.user.id and discussion_sudo.state == 'open':
            discussion_sudo.write({'state': 'closed'})
            
        return request.redirect('/my/discussions/%s' % discussion_id)
    
    # Ratings
    @http.route(['/my/ratings', '/my/ratings/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_ratings(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, **kw):
        """Display user's ratings"""
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        Rating = request.env['auto.voyage.rating']
        
        domain = [('partner_id', '=', partner.id)]
        
        # Date filters
        if date_begin and date_end:
            domain += [('rating_date', '>=', date_begin), ('rating_date', '<=', date_end)]
            
        # Default sort by date
        if not sortby:
            sortby = 'date'
            
        # Sorting options
        searchbar_sortings = {
            'date': {'label': _('Newest'), 'order': 'rating_date desc'},
            'rating': {'label': _('Highest Rating'), 'order': 'overall_rating desc'},
            'name': {'label': _('Reference'), 'order': 'name'},
        }
        
        # Filter options
        searchbar_filters = {
            'all': {'label': _('All'), 'domain': []},
            'published': {'label': _('Published'), 'domain': [('state', '=', 'published')]},
            'submitted': {'label': _('Submitted'), 'domain': [('state', '=', 'submitted')]},
            'draft': {'label': _('Draft'), 'domain': [('state', '=', 'draft')]},
        }
        
        # Default filter
        if not filterby:
            filterby = 'all'
        domain += searchbar_filters[filterby]['domain']
        
        # Count for pager
        rating_count = Rating.search_count(domain)
        
        # Pager
        pager = portal_pager(
            url="/my/ratings",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby, 'filterby': filterby},
            total=rating_count,
            page=page,
            step=self._items_per_page
        )
        
        # Content
        ratings = Rating.search(domain, order=searchbar_sortings[sortby]['order'], limit=self._items_per_page, offset=pager['offset'])
        
        values.update({
            'date': date_begin,
            'ratings': ratings,
            'page_name': 'ratings',
            'pager': pager,
            'default_url': '/my/ratings',
            'searchbar_sortings': searchbar_sortings,
            'searchbar_filters': searchbar_filters,
            'sortby': sortby,
            'filterby': filterby,
        })
        values.update(self._get_frontend_layout_values())
        
        return request.render("auto_voyage.portal_my_ratings", values)
    
    @http.route(['/my/ratings/<int:rating_id>'], type='http', auth="user", website=True)
    def portal_rating_page(self, rating_id, **kw):
        """Display rating details"""
        try:
            rating_sudo = self._document_check_access('auto.voyage.rating', rating_id)
        except (AccessError, MissingError):
            return request.redirect('/my/ratings')
            
        # Check if rating can be edited (within 7 days and not published)
        can_edit = (fields.Datetime.now() - rating_sudo.create_date).days <= 7 and rating_sudo.state != 'published'
            
        values = self._prepare_portal_layout_values()
        values.update({
            'rating': rating_sudo,
            'page_name': 'rating',
            'can_edit': can_edit,
        })
        values.update(self._get_frontend_layout_values())
        
        return request.render("auto_voyage.portal_rating_page", values)
    
    @http.route(['/my/ratings/<int:rating_id>/edit'], type='http', auth="user", website=True)
    def portal_rating_edit(self, rating_id, **kw):
        """Display rating edit form"""
        try:
            rating_sudo = self._document_check_access('auto.voyage.rating', rating_id)
            if rating_sudo.partner_id != request.env.user.partner_id:
                return request.redirect('/my/ratings')
        except (AccessError, MissingError):
            return request.redirect('/my/ratings')
            
        values = self._prepare_portal_layout_values()
        values.update({
            'rating': rating_sudo,
            'page_name': 'rating_edit',
            'service_quality': rating_sudo.service_quality,
            'timeliness': rating_sudo.timeliness,
            'communication': rating_sudo.communication,
            'value_for_money': rating_sudo.value_for_money,
            'feedback': rating_sudo.feedback,
        })
        values.update(self._get_frontend_layout_values())
        
        return request.render("auto_voyage.portal_rating_edit", values)
    
    @http.route(['/my/ratings/submit'], type='http', auth="user", website=True, methods=['POST'], csrf=True)
    def portal_rating_submit(self, **kw):
        """Submit or update a rating"""
        rating_id = int(kw.get('rating_id', 0) or 0)
        service_id = int(kw.get('service_id', 0) or 0)
        
        # Validate required fields
        required_fields = ['service_quality', 'timeliness', 'communication', 'value_for_money']
        values = {}
        for field in required_fields:
            if field in kw:
                try:
                    value = int(kw.get(field))
                    # Ensure the rating value is within the valid range (1 to 5)
                    if value < 1 or value > 5:
                        raise ValueError("Rating must be between 1 and 5.")
                    values[field] = str(value)  # Store as string to match the database type
                except (ValueError, TypeError):
                    values[field] = '0'  # Default to '0' as a string
        
        values['feedback'] = kw.get('feedback', '')
        
        if not all(field in values for field in required_fields):
            return request.redirect('/my/service-requests/%s' % service_id)
        
        Rating = request.env['auto.voyage.rating'].sudo()
        
        try:
            if rating_id:
                # Update existing rating
                rating_sudo = self._document_check_access('auto.voyage.rating', rating_id)
                # Only allow editing if not published and within 7 days
                if rating_sudo.state != 'published' and (fields.Datetime.now() - rating_sudo.create_date).days <= 7:
                    rating_sudo.write(values)
                    if rating_sudo.state == 'draft':
                        rating_sudo.action_submit()
                return request.redirect('/my/ratings/%s' % rating_id)
            elif service_id:
                # Create new rating
                service_sudo = request.env['auto.voyage.service.request'].sudo().browse(service_id)
                if service_sudo.exists() and service_sudo.partner_id.id == request.env.user.partner_id.id:
                    values.update({
                        'service_id': service_id,
                        'rating_date': fields.Date.today(),
                        'state': 'submitted'
                    })
                    new_rating = Rating.create(values)
                    return request.redirect('/my/ratings/%s' % new_rating.id)
        except Exception as e:
            self._logger.error("Error in rating submission: %s", str(e))
            return request.redirect('/my/ratings')
        
        return request.redirect('/my/ratings')

    @http.route(['/my/service-request/<int:service_request_id>/download'], type='http', auth="user", website=True)
    def portal_service_request_download(self, service_request_id, **kw):
        """Download service request report"""
        try:
            service_request_sudo = self._document_check_access('auto.voyage.service.request', service_request_id)
        except (AccessError, MissingError):
            return request.redirect('/my')
            
        if service_request_sudo.state != 'completed':
            return request.redirect('/my/service-request/%s' % service_request_id)
        
        values = self._prepare_portal_layout_values()
        values.update({
            'service_request': service_request_sudo,
            'page_name': 'service_request',
            'is_portal': True,
            'frontend_languages': request.env['res.lang'].sudo()._get_frontend(),
            'is_frontend_multilang': len(request.env['res.lang'].sudo()._get_frontend()) > 1,
        })
        values.update(self._get_frontend_layout_values())
            
        # Generate report content
        report_content = self._generate_service_report(service_request_sudo)
        
        # Convert to PDF
        pdf_content = self._html_to_pdf(report_content)
        
        # Prepare response
        filename = f'Service_Report_{service_request_sudo.name}.pdf'
        headers = [
            ('Content-Type', 'application/pdf'),
            ('Content-Disposition', f'attachment; filename="{filename}"'),
            ('Content-Length', len(pdf_content)),
        ]
        
        return request.make_response(pdf_content, headers=headers)
        
    def _generate_service_report(self, service_request):
        """Generate PDF report for service request"""
        values = self._prepare_portal_layout_values()
        values.update({
            'docs': [service_request],
            'company': request.env.company,
        })
        values.update(self._get_frontend_layout_values())
        
        return request.env['ir.ui.view']._render_template(
            'auto_voyage.service_report_template',
            values
        )
        
    def _html_to_pdf(self, html_content):
        """Convert HTML content to PDF"""
        return request.env['ir.actions.report']._run_wkhtmltopdf(
            [html_content],
            header=None,
            footer=None,
            landscape=False,
            specific_paperformat_args=None,
            set_viewport_size=False
        )
