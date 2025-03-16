# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    # Vehicle related fields
    vehicle_ids = fields.One2many('auto.voyage.vehicle', 'partner_id', string='Vehicles')
    vehicle_count = fields.Integer(string='Vehicle Count', compute='_compute_vehicle_count')
    
    # Service request related fields
    service_request_ids = fields.One2many('auto.voyage.service.request', 'partner_id', string='Service Requests')
    service_request_count = fields.Integer(string='Service Request Count', compute='_compute_service_request_count')
    
    # Contract related fields
    contract_ids = fields.One2many('auto.voyage.contract', 'partner_id', string='Contracts')
    contract_count = fields.Integer(string='Contract Count', compute='_compute_contract_count')
    
    # Rating related fields
    rating_ids = fields.One2many('auto.voyage.rating', 'partner_id', string='Ratings')
    rating_count = fields.Integer(string='Rating Count', compute='_compute_rating_count')
    avg_rating = fields.Float(string='Average Rating', compute='_compute_avg_rating', store=True)
    
    # Discussion related fields
    discussion_ids = fields.One2many('auto.voyage.discussion', 'partner_id', string='Discussions')
    discussion_count = fields.Integer(string='Discussion Count', compute='_compute_discussion_count')
    
    # Preferred service provider
    preferred_provider_id = fields.Many2one('auto.voyage.service.provider', string='Preferred Service Provider')
    
    # Customer type
    customer_type = fields.Selection([
        ('individual', 'Individual'),
        ('business', 'Business'),
        ('fleet', 'Fleet Owner')
    ], string='Customer Type', default='individual')
    
    # Loyalty points
    loyalty_points = fields.Integer(string='Loyalty Points', default=0)
    
    @api.depends('vehicle_ids')
    def _compute_vehicle_count(self):
        for partner in self:
            partner.vehicle_count = len(partner.vehicle_ids)
    
    @api.depends('service_request_ids')
    def _compute_service_request_count(self):
        for partner in self:
            partner.service_request_count = len(partner.service_request_ids)
    
    @api.depends('contract_ids')
    def _compute_contract_count(self):
        for partner in self:
            partner.contract_count = len(partner.contract_ids)
    
    @api.depends('rating_ids')
    def _compute_rating_count(self):
        for partner in self:
            partner.rating_count = len(partner.rating_ids)
    
    @api.depends('rating_ids.overall_rating')
    def _compute_avg_rating(self):
        for partner in self:
            if partner.rating_ids:
                partner.avg_rating = sum(partner.rating_ids.mapped('overall_rating')) / len(partner.rating_ids)
            else:
                partner.avg_rating = 0.0
    
    @api.depends('discussion_ids')
    def _compute_discussion_count(self):
        for partner in self:
            partner.discussion_count = len(partner.discussion_ids)
    
    def action_view_vehicles(self):
        self.ensure_one()
        return {
            'name': _('Vehicles'),
            'type': 'ir.actions.act_window',
            'res_model': 'auto.voyage.vehicle',
            'view_mode': 'list,form',
            'domain': [('partner_id', '=', self.id)],
            'context': {'default_partner_id': self.id},
        }
    
    def action_view_service_requests(self):
        self.ensure_one()
        return {
            'name': _('Service Requests'),
            'type': 'ir.actions.act_window',
            'res_model': 'auto.voyage.service.request',
            'view_mode': 'list,form',
            'domain': [('partner_id', '=', self.id)],
            'context': {'default_partner_id': self.id},
        }
    
    def action_view_contracts(self):
        self.ensure_one()
        return {
            'name': _('Contracts'),
            'type': 'ir.actions.act_window',
            'res_model': 'auto.voyage.contract',
            'view_mode': 'list,form',
            'domain': [('partner_id', '=', self.id)],
            'context': {'default_partner_id': self.id},
        } 