# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta

class ServiceRequest(models.Model):
    _name = 'auto.voyage.service.request'
    _description = 'Service Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'scheduled_date desc, id desc'

    name = fields.Char(string='Request Reference', required=True, copy=False, readonly=True, 
                      default=lambda self: _('New'))
    
    # Basic Information
    partner_id = fields.Many2one('res.partner', string='Customer', required=True, tracking=True)
    vehicle_id = fields.Many2one('auto.voyage.vehicle', string='Vehicle', required=True, tracking=True,
                                domain="[('partner_id', '=', partner_id)]", ondelete='cascade')
    service_id = fields.Many2one('auto.voyage.service', string='Service', required=True, tracking=True)
    provider_id = fields.Many2one('auto.voyage.service.provider', string='Service Provider', tracking=True)
    provider_partner_id = fields.Many2one(related='provider_id.partner_id', string='Provider Partner', store=True, readonly=True)
    is_provider_user = fields.Boolean(compute='_compute_is_provider_user', string='Is Provider User')
    
    # Scheduling
    scheduled_date = fields.Datetime(string='Scheduled Date', required=True, tracking=True)
    scheduled_end_date = fields.Datetime(string='Scheduled End Date', tracking=True)
    estimated_duration = fields.Float(string='Estimated Duration', related='service_id.duration')
    completion_date = fields.Datetime(string='Completion Date', tracking=True)
    
    # Status and Progress
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', tracking=True)
    
    # Financial Information
    amount = fields.Float(string='Service Amount', compute='_compute_amount', store=True)
    currency_id = fields.Many2one('res.currency', string='Currency',
                                 default=lambda self: self.env.company.currency_id)
    
    # Additional Information
    description = fields.Text(string='Service Description')
    customer_notes = fields.Text(string='Customer Notes')
    internal_notes = fields.Text(string='Internal Notes')
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('auto.voyage.service.request') or _('New')
        return super(ServiceRequest, self).create(vals_list)
    
    @api.depends('service_id')
    def _compute_amount(self):
        for record in self:
            record.amount = record.service_id.price if record.service_id else 0.0
    
    @api.constrains('scheduled_date')
    def _check_scheduled_date(self):
        for record in self:
            if record.scheduled_date and record.scheduled_date < fields.Datetime.now():
                raise ValidationError(_("Scheduled date cannot be in the past."))
    
    def action_confirm(self):
        self.write({'state': 'confirmed'})
    
    def action_schedule(self):
        self.write({'state': 'scheduled'})
    
    def action_start(self):
        """Start the service - transition from scheduled to in_progress"""
        for request in self:
            if request.state != 'scheduled':
                raise UserError(_("Only scheduled services can be started."))
            
            # Check if current user is the service provider or has manager rights
            current_user = self.env.user
            is_provider = request.provider_id and request.provider_id.partner_id.id == current_user.partner_id.id
            is_manager = current_user.has_group('auto_voyage.group_auto_voyage_manager')
            
            if not (is_provider or is_manager):
                raise UserError(_("Only the assigned service provider or a manager can start this service."))
                
            request.write({
                'state': 'in_progress',
                'start_time': fields.Datetime.now(),
            })
            
            # Send notification to customer that service has started
            request.message_post(
                body=_("Service has been started by %s") % request.provider_id.name,
                message_type='notification',
                subtype_xmlid='mail.mt_comment',
                partner_ids=[(4, request.partner_id.id)],
            )
        return True
        
    def action_complete(self):
        """Complete the service - transition from in_progress to completed"""
        for request in self:
            if request.state != 'in_progress':
                raise UserError(_("Only in-progress services can be completed."))
            
            # Check if current user is the service provider or has manager rights
            current_user = self.env.user
            is_provider = request.provider_id and request.provider_id.partner_id.id == current_user.partner_id.id
            is_manager = current_user.has_group('auto_voyage.group_auto_voyage_manager')
            
            if not (is_provider or is_manager):
                raise UserError(_("Only the assigned service provider or a manager can complete this service."))
                
            request.write({
                'state': 'completed',
                'completion_date': fields.Datetime.now(),
            })
            
            # Send notification to customer that service has been completed
            request.message_post(
                body=_("Service has been completed by %s") % request.provider_id.name,
                message_type='notification',
                subtype_xmlid='mail.mt_comment',
                partner_ids=[(4, request.partner_id.id)],
            )
            
            # Create invoice if configured to auto-invoice
            if request.service_id.auto_invoice:
                self.env['auto.voyage.service.invoice'].create_invoice_from_request(request)
                
        return True
        
    # Additional status transition methods for completeness
    def action_cancel(self):
        """Cancel the service request"""
        for request in self:
            if request.state in ['completed', 'cancelled']:
                raise UserError(_("Cannot cancel a service that is already completed or cancelled."))
                
            request.write({'state': 'cancelled'})
            
            # Send notification to provider and customer about cancellation
            partners_to_notify = []
            if request.provider_id and request.provider_id.partner_id:
                partners_to_notify.append(request.provider_id.partner_id.id)
            if request.partner_id:
                partners_to_notify.append(request.partner_id.id)
                
            if partners_to_notify:
                request.message_post(
                    body=_("Service request has been cancelled."),
                    message_type='notification',
                    subtype_xmlid='mail.mt_comment',
                    partner_ids=[(6, 0, partners_to_notify)],
                )
        return True
    
    def action_reschedule(self):
        """Open reschedule wizard"""
        self.ensure_one()
        if self.state in ['completed', 'cancelled']:
            raise UserError(_("Cannot reschedule a service that is already completed or cancelled."))
            
        return {
            'name': _('Reschedule Service'),
            'type': 'ir.actions.act_window',
            'res_model': 'auto.voyage.reschedule.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_service_request_id': self.id, 
                        'default_scheduled_date': self.scheduled_date}
        }

    def write(self, vals):
        # Track completion date when status changes to completed
        if vals.get('state') == 'completed' and not vals.get('completion_date'):
            vals['completion_date'] = fields.Datetime.now()
        return super(ServiceRequest, self).write(vals)

    @api.depends('provider_id', 'provider_id.partner_id')
    def _compute_is_provider_user(self):
        """Determine if current user is the provider for this service request"""
        current_user = self.env.user
        current_partner = current_user.partner_id
        
        for request in self:
            request.is_provider_user = (request.provider_id and 
                                       request.provider_id.partner_id.id == current_partner.id) 

    @api.model
    def _search_service_requests_by_access(self):
        """Filter service requests based on user's role and access level"""
        domain = []
        user = self.env.user
        
        # Managers can see all service requests
        if user.has_group('auto_voyage.group_auto_voyage_manager'):
            return domain
        
        # Service providers can only see their own requests
        if user.has_group('auto_voyage.group_auto_voyage_provider'):
            provider = self.env['auto.voyage.service.provider'].sudo().search([
                ('partner_id', '=', user.partner_id.id)
            ], limit=1)
            if provider:
                domain = [('provider_id', '=', provider.id)]
            else:
                # If user has provider rights but no provider record, show nothing
                domain = [('id', '=', False)]
        
        # Customers can see their own service requests
        elif user.has_group('auto_voyage.group_auto_voyage_customer'):
            domain = [('partner_id', '=', user.partner_id.id)]
        
        return domain