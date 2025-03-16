# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date

class Vehicle(models.Model):
    _name = 'auto.voyage.vehicle'
    _description = 'Vehicle Information'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    name = fields.Char(string='Vehicle Name', compute='_compute_vehicle_name', store=True)
    partner_id = fields.Many2one('res.partner', string='Owner', required=True, tracking=True)
    make = fields.Char(string='Make', required=True, tracking=True)
    model = fields.Char(string='Model', required=True, tracking=True)
    year = fields.Integer(string='Year', required=True, tracking=True)
    vin = fields.Char(string='VIN', required=True, tracking=True)
    license_plate = fields.Char(string='License Plate', required=True, tracking=True)
    color = fields.Char(string='Color', tracking=True)
    
    # Technical Information
    fuel_type = fields.Selection([
        ('petrol', 'Petrol'),
        ('diesel', 'Diesel'),
        ('electric', 'Electric'),
        ('hybrid', 'Hybrid'),
        ('cng', 'CNG'),
        ('lpg', 'LPG')
    ], string='Fuel Type', required=True, tracking=True)
    
    transmission = fields.Selection([
        ('manual', 'Manual'),
        ('automatic', 'Automatic'),
        ('cvt', 'CVT'),
        ('amt', 'AMT')
    ], string='Transmission', required=True, tracking=True)
    
    mileage = fields.Float(string='Current Mileage', tracking=True)
    
    # Documents
    insurance_number = fields.Char(string='Insurance Number', tracking=True)
    insurance_provider = fields.Char(string='Insurance Provider', tracking=True)
    insurance_expiry = fields.Date(string='Insurance Expiry Date', tracking=True)
    registration_expiry = fields.Date(string='Registration Expiry Date', tracking=True)
    
    # Status
    state = fields.Selection([
        ('active', 'Active'),
        ('in_service', 'In Service'),
        ('inactive', 'Inactive')
    ], string='Status', default='active', tracking=True)
    
    active = fields.Boolean(string='Active', default=True, tracking=True)
    
    # Service History
    service_count = fields.Integer(compute='_compute_service_count', string='Services')
    last_service_date = fields.Date(string='Last Service Date', compute='_compute_last_service')
    next_service_date = fields.Date(string='Next Service Due', compute='_compute_next_service')
    
    _sql_constraints = [
        ('vin_unique', 'unique(vin)', 'VIN must be unique!'),
        ('license_plate_unique', 'unique(license_plate)', 'License Plate must be unique!')
    ]
    
    @api.depends('make', 'model', 'year')
    def _compute_vehicle_name(self):
        for vehicle in self:
            vehicle.name = f"{vehicle.make} {vehicle.model} ({vehicle.year})"
    
    @api.constrains('year')
    def _check_year(self):
        current_year = date.today().year
        for record in self:
            if record.year > current_year:
                raise ValidationError(_("Vehicle year cannot be in the future!"))
            if record.year < 1900:
                raise ValidationError(_("Invalid vehicle year!"))
    
    def _compute_service_count(self):
        for vehicle in self:
            vehicle.service_count = self.env['auto.voyage.service.request'].search_count([
                ('vehicle_id', '=', vehicle.id)
            ])
    
    def _compute_last_service(self):
        for vehicle in self:
            last_service = self.env['auto.voyage.service.request'].search([
                ('vehicle_id', '=', vehicle.id),
                ('state', '=', 'completed')
            ], order='completion_date desc', limit=1)
            vehicle.last_service_date = last_service.completion_date.date() if last_service and last_service.completion_date else False
    
    def _compute_next_service(self):
        for vehicle in self:
            next_service = self.env['auto.voyage.service.request'].search([
                ('vehicle_id', '=', vehicle.id),
                ('state', 'in', ['draft', 'scheduled'])
            ], order='scheduled_date asc', limit=1)
            vehicle.next_service_date = next_service.scheduled_date.date() if next_service and next_service.scheduled_date else False
    
    def action_view_services(self):
        self.ensure_one()
        return {
            'name': _('Services'),
            'type': 'ir.actions.act_window',
            'view_mode': 'list,form',
            'res_model': 'auto.voyage.service.request',
            'domain': [('vehicle_id', '=', self.id)],
            'context': {'default_vehicle_id': self.id},
        } 