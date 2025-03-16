# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date

class ServiceContract(models.Model):
    _name = 'auto.voyage.contract'
    _description = 'Service Contract'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(string='Contract Reference', required=True, copy=False, 
                      readonly=True, default=lambda self: _('New'))
    
    # Basic Information
    partner_id = fields.Many2one('res.partner', string='Customer', required=True, tracking=True)
    vehicle_id = fields.Many2one('auto.voyage.vehicle', string='Vehicle', required=True, tracking=True,
                                domain="[('partner_id', '=', partner_id)]")
    provider_id = fields.Many2one('auto.voyage.service.provider', string='Service Provider', 
                                 required=True, tracking=True)
    
    # Contract Details
    start_date = fields.Date(string='Start Date', required=True, tracking=True)
    end_date = fields.Date(string='End Date', required=True, tracking=True)
    contract_type = fields.Selection([
        ('basic', 'Basic Service'),
        ('premium', 'Premium Service'),
        ('comprehensive', 'Comprehensive'),
        ('custom', 'Custom Package')
    ], string='Contract Type', required=True, default='basic', tracking=True)
    
    # Financial Information
    amount = fields.Monetary(string='Contract Amount', required=True, tracking=True)
    currency_id = fields.Many2one('res.currency', string='Currency',
                                 default=lambda self: self.env.company.currency_id.id,
                                 required=True)
    payment_terms = fields.Char(string='Payment Terms')
    
    # Status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('signed', 'Signed'),
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', tracking=True)
    
    # Contract Details
    description = fields.Html(string='Contract Description')
    terms_conditions = fields.Html(string='Terms and Conditions')
    notes = fields.Text(string='Internal Notes')
    
    # Service Items
    service_ids = fields.Many2many('auto.voyage.service', string='Included Services')
    
    # Signatures
    customer_signature = fields.Binary(string='Customer Signature')
    provider_signature = fields.Binary(string='Provider Signature')
    signed_date = fields.Datetime(string='Signed Date')
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('auto.voyage.contract') or _('New')
        return super().create(vals_list)
    
    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for record in self:
            if record.start_date and record.end_date:
                if record.start_date > record.end_date:
                    raise ValidationError(_("End date cannot be before start date!"))
                if record.start_date < date.today():
                    raise ValidationError(_("Start date cannot be in the past!"))
    
    def action_send(self):
        self.write({'state': 'sent'})
    
    def action_sign(self):
        self.write({
            'state': 'signed',
            'signed_date': fields.Datetime.now()
        })
    
    def action_activate(self):
        self.write({'state': 'active'})
    
    def action_cancel(self):
        self.write({'state': 'cancelled'}) 