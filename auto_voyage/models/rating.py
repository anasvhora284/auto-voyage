# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class ServiceRating(models.Model):
    _name = 'auto.voyage.rating'
    _description = 'Service Rating'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(string='Reference', readonly=True, copy=False,
                      default=lambda self: _('New Rating'))
    
    # Related Records
    service_id = fields.Many2one('auto.voyage.service.request', string='Service Request',
                                       required=True, tracking=True)
    vehicle_id = fields.Many2one('auto.voyage.vehicle', string='Vehicle',
                                related='service_id.vehicle_id', store=True, ondelete='cascade')
    partner_id = fields.Many2one('res.partner', string='Customer',
                                related='service_id.partner_id', store=True)
    provider_id = fields.Many2one('auto.voyage.service.provider', string='Service Provider',
                                 related='service_id.provider_id', store=True)
    
    # Rating Details
    rating_date = fields.Date(string='Rating Date', default=fields.Date.context_today, required=True)
    
    # Rating Scores (1-5 scale)
    service_quality = fields.Selection([
        ('1', 'Poor'),
        ('2', 'Below Average'),
        ('3', 'Average'),
        ('4', 'Good'),
        ('5', 'Excellent')
    ], string='Service Quality', required=True, default='3', tracking=True)
    
    timeliness = fields.Selection([
        ('1', 'Poor'),
        ('2', 'Below Average'),
        ('3', 'Average'),
        ('4', 'Good'),
        ('5', 'Excellent')
    ], string='Timeliness', required=True, default='3', tracking=True)
    
    communication = fields.Selection([
        ('1', 'Poor'),
        ('2', 'Below Average'),
        ('3', 'Average'),
        ('4', 'Good'),
        ('5', 'Excellent')
    ], string='Communication', required=True, default='3', tracking=True)
    
    value_for_money = fields.Selection([
        ('1', 'Poor'),
        ('2', 'Below Average'),
        ('3', 'Average'),
        ('4', 'Good'),
        ('5', 'Excellent')
    ], string='Value for Money', required=True, default='3', tracking=True)
    
    overall_rating = fields.Float(string='Overall Rating', compute='_compute_overall_rating', store=True)
    
    # Feedback
    feedback = fields.Text(string='Feedback', tracking=True)
    
    # Status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('published', 'Published'),
        ('archived', 'Archived')
    ], string='Status', default='draft', tracking=True)
    
    @api.depends('service_quality', 'timeliness', 'communication', 'value_for_money')
    def _compute_overall_rating(self):
        for record in self:
            ratings = [
                int(record.service_quality or '0'),
                int(record.timeliness or '0'),
                int(record.communication or '0'),
                int(record.value_for_money or '0')
            ]
            record.overall_rating = sum(ratings) / len(ratings) if ratings else 0.0
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['name'] = self.env['ir.sequence'].next_by_code('auto.voyage.rating') or _('New Rating')
        return super().create(vals_list)
    
    def action_submit(self):
        self.write({'state': 'submitted'})
    
    def action_publish(self):
        self.write({'state': 'published'})
    
    def action_archive(self):
        self.write({'state': 'archived'}) 