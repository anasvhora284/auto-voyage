# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class Service(models.Model):
    _name = 'auto.voyage.service'
    _description = 'Auto Service'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence,id'

    name = fields.Char(string='Service Name', required=True, tracking=True)
    sequence = fields.Integer(string='Sequence', default=10)
    code = fields.Char(string='Service Code', required=True, tracking=True)
    category = fields.Selection([
        ('maintenance', 'Maintenance'),
        ('repair', 'Repair'),
        ('inspection', 'Inspection'),
        ('cleaning', 'Cleaning'),
        ('custom', 'Custom Service')
    ], string='Category', required=True, tracking=True)
    
    description = fields.Text(string='Description')
    duration = fields.Float(string='Expected Duration (Hours)', default=1.0)
    price = fields.Float(string='Standard Price', tracking=True)
    icon = fields.Char(string='Font Awesome Icon', default='fa-wrench', help='Font Awesome icon class (e.g. fa-wrench, fa-car)')
    
    active = fields.Boolean(default=True, tracking=True)
    note = fields.Text(string='Internal Notes')
    
    # Service Requirements
    requires_appointment = fields.Boolean(string='Requires Appointment', default=True)
    requires_inspection = fields.Boolean(string='Requires Initial Inspection')
    
    # Service Provider Requirements
    required_expertise = fields.Selection([
        ('basic', 'Basic'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('specialist', 'Specialist')
    ], string='Required Expertise', default='basic', required=True)
    
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)
    
    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'Service Code must be unique!')
    ] 