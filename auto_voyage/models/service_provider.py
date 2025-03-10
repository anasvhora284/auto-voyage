# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class ServiceProvider(models.Model):
    _name = 'auto.voyage.service.provider'
    _description = 'Service Provider'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'partner_id'

    partner_id = fields.Many2one('res.partner', string='Provider', required=True, tracking=True)
    code = fields.Char(string='Provider Code', required=True, tracking=True)
    expertise_level = fields.Selection([
        ('basic', 'Basic'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('specialist', 'Specialist')
    ], string='Expertise Level', required=True, default='basic', tracking=True)
    
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