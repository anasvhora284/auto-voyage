# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class Discussion(models.Model):
    _name = 'auto.voyage.discussion'
    _description = 'Service Discussion'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(string='Subject', required=True, tracking=True)
    
    # Related Records
    service_id = fields.Many2one('auto.voyage.service.request', string='Service Request',
                                       tracking=True)
    vehicle_id = fields.Many2one('auto.voyage.vehicle', string='Vehicle',
                                related='service_id.vehicle_id', store=True)
    partner_id = fields.Many2one('res.partner', string='Customer',
                                related='service_id.partner_id', store=True)
    provider_id = fields.Many2one('auto.voyage.service.provider', string='Service Provider',
                                 related='service_id.provider_id', store=True)
    
    # Discussion Details
    category = fields.Selection([
        ('general', 'General Inquiry'),
        ('technical', 'Technical Issue'),
        ('scheduling', 'Scheduling'),
        ('payment', 'Payment'),
        ('complaint', 'Complaint'),
        ('feedback', 'Feedback')
    ], string='Category', required=True, default='general', tracking=True)
    
    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Normal'),
        ('2', 'High'),
        ('3', 'Urgent')
    ], string='Priority', default='1', tracking=True)
    
    state = fields.Selection([
        ('new', 'New'),
        ('in_progress', 'In Progress'),
        ('waiting', 'Waiting'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed')
    ], string='Status', default='new', tracking=True)
    
    description = fields.Html(string='Description')
    resolution = fields.Html(string='Resolution')
    
    # Dates
    start_date = fields.Datetime(string='Start Date', default=fields.Datetime.now)
    close_date = fields.Datetime(string='Close Date')
    
    # Tags for better organization
    tag_ids = fields.Many2many('auto.voyage.discussion.tag', string='Tags')
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name', '').strip():
                vals['name'] = _("New Discussion")
        return super().create(vals_list)
    
    def action_in_progress(self):
        self.write({'state': 'in_progress'})
    
    def action_mark_waiting(self):
        self.write({'state': 'waiting'})
    
    def action_resolve(self):
        self.write({'state': 'resolved'})
    
    def action_close(self):
        self.write({
            'state': 'closed',
            'close_date': fields.Datetime.now()
        })

class DiscussionTag(models.Model):
    _name = 'auto.voyage.discussion.tag'
    _description = 'Discussion Tag'
    
    name = fields.Char(string='Name', required=True)
    color = fields.Integer(string='Color Index')
    
    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Tag name already exists!"),
    ] 