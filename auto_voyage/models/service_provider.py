# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class ServiceProvider(models.Model):
    _name = 'auto.voyage.service.provider'
    _description = 'Service Provider'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'website.published.mixin']
    _rec_name = 'partner_id'

    partner_id = fields.Many2one('res.partner', string='Provider', required=True, tracking=True)
    code = fields.Char(string='Provider Code', required=True, tracking=True)
    image = fields.Binary(string='Provider Image', attachment=True, help="Provider image displayed on the website")
    expertise_level = fields.Selection([
        ('basic', 'Basic'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('specialist', 'Specialist')
    ], string='Expertise Level', required=True, default='basic', tracking=True)
    
    # Override name field for website.published.mixin
    name = fields.Char(related='partner_id.name', string='Name', readonly=True, store=True)
    
    service_ids = fields.Many2many('auto.voyage.service', string='Services Offered')
    
    # Availability
    available = fields.Boolean(string='Currently Available', default=True, tracking=True)
    work_schedule = fields.Selection([
        ('full_time', 'Full Time'),
        ('part_time', 'Part Time'),
        ('weekends', 'Weekends Only'),
        ('custom', 'Custom Schedule')
    ], string='Work Schedule', required=True, default='full_time', tracking=True)
    
    # Performance Metrics
    rating = fields.Float(string='Average Rating', compute='_compute_rating', store=True)
    total_services = fields.Integer(string='Total Services', compute='_compute_services')
    completion_rate = fields.Float(string='Service Completion Rate', compute='_compute_completion_rate')
    
    active = fields.Boolean(default=True, tracking=True)
    note = fields.Text(string='Internal Notes')
    
    # User access fields
    user_id = fields.Many2one(
        'res.users', string='Related User', 
        tracking=True, 
        help="User account for this service provider to access the system"
    )
    
    # Override is_published for security
    is_published = fields.Boolean(default=True)
    
    _sql_constraints = [
        ('provider_code_uniq', 'unique(code)', 'Provider Code must be unique!')
    ]
    
    @api.depends('partner_id')
    def _compute_rating(self):
        for provider in self:
            # This will be implemented when rating model is created
            provider.rating = 0.0
    
    def _compute_services(self):
        for provider in self:
            provider.total_services = self.env['auto.voyage.service.request'].search_count([
                ('provider_id', '=', provider.id),
                ('state', '=', 'completed')
            ])
    
    def _compute_completion_rate(self):
        for provider in self:
            total = self.env['auto.voyage.service.request'].search_count([
                ('provider_id', '=', provider.id),
                ('state', 'in', ['completed', 'cancelled'])
            ])
            completed = self.env['auto.voyage.service.request'].search_count([
                ('provider_id', '=', provider.id),
                ('state', '=', 'completed')
            ])
            provider.completion_rate = (completed / total * 100) if total > 0 else 0.0 

    # Methods for user access management
    def action_create_user(self):
        """Create a user account for the service provider"""
        for provider in self:
            if provider.user_id:
                continue
                
            # Check if partner already has a user
            existing_user = self.env['res.users'].sudo().search([
                ('partner_id', '=', provider.partner_id.id)
            ], limit=1)
            
            if existing_user:
                provider.user_id = existing_user.id
                # Add provider group to existing user
                provider_group = self.env.ref('auto_voyage.group_auto_voyage_provider')
                if provider_group and provider_group.id not in existing_user.groups_id.ids:
                    existing_user.sudo().write({'groups_id': [(4, provider_group.id)]})
            else:
                # Create new user for provider
                values = {
                    'name': provider.partner_id.name,
                    'login': provider.partner_id.email or f"provider_{provider.id}@example.com",
                    'email': provider.partner_id.email or f"provider_{provider.id}@example.com",
                    'partner_id': provider.partner_id.id,
                    'groups_id': [(6, 0, [self.env.ref('auto_voyage.group_auto_voyage_provider').id])],
                }
                
                new_user = self.env['res.users'].sudo().create(values)
                provider.user_id = new_user.id
                
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('User account created successfully.'),
                'sticky': False,
                'type': 'success',
            }
        }
        
    def action_reset_password(self):
        """Reset password for the provider user"""
        for provider in self:
            if not provider.user_id:
                continue
                
            # Reset password
            provider.user_id.sudo().action_reset_password()
                
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('Password reset email has been sent.'),
                'sticky': False,
                'type': 'success',
            }
        }
    
    def action_view_dashboard(self):
        """Open provider dashboard view"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Provider Dashboard'),
            'res_model': 'auto.voyage.service.request',
            'view_mode': 'kanban,list,form,calendar',
            'domain': [('provider_id', '=', self.id)],
            'context': {'search_default_today': 1},
            'views': [(self.env.ref('auto_voyage.view_auto_voyage_provider_dashboard').id, 'kanban'),
                      (self.env.ref('auto_voyage.view_auto_voyage_service_request_provider_list').id, 'list'),
                      (self.env.ref('auto_voyage.view_auto_voyage_service_request_provider_form').id, 'form')],
        } 