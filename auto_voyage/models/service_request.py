# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
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
                                domain="[('partner_id', '=', partner_id)]")
    service_id = fields.Many2one('auto.voyage.service', string='Service', required=True, tracking=True)
    provider_id = fields.Many2one('auto.voyage.service.provider', string='Service Provider', tracking=True)
    
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
        self.write({'state': 'in_progress'})
    
    def action_complete(self):
        self.write({
            'state': 'completed',
            'completion_date': fields.Datetime.now()
        })
    
    def action_cancel(self):
        self.write({'state': 'cancelled'}) 