# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta

class AssignServiceWizard(models.TransientModel):
    _name = 'auto.voyage.assign.service.wizard'
    _description = 'Assign Service Provider Wizard'
    
    service_request_id = fields.Many2one('auto.voyage.service.request', string='Service Request', required=True,
                                        default=lambda self: self.env.context.get('active_id', False))
    provider_id = fields.Many2one('auto.voyage.service.provider', string='Service Provider', required=True,
                                 domain="[('service_ids', 'in', service_id)]")
    service_id = fields.Many2one('auto.voyage.service', string='Service', related='service_request_id.service_id', readonly=True)
    scheduled_date = fields.Datetime(string='Scheduled Date', required=True,
                                    default=lambda self: datetime.now() + timedelta(days=1))
    notes = fields.Text(string='Notes')
    
    @api.onchange('service_request_id')
    def _onchange_service_request_id(self):
        if self.service_request_id:
            # Check if the service request is already assigned
            if self.service_request_id.provider_id:
                return {'warning': {
                    'title': _('Warning'),
                    'message': _('This service request is already assigned to a provider.')
                }}
            
            # Set default scheduled date based on request date
            if self.service_request_id.scheduled_date:
                self.scheduled_date = self.service_request_id.scheduled_date + timedelta(days=1)
    
    @api.onchange('provider_id')
    def _onchange_provider_id(self):
        if self.provider_id and self.scheduled_date:
            # Check provider availability
            domain = [
                ('provider_id', '=', self.provider_id.id),
                ('state', 'in', ['scheduled', 'in_progress']),
                '|',
                '&', ('scheduled_date', '<=', self.scheduled_date), 
                ('scheduled_end_date', '>=', self.scheduled_date),
                '&', ('scheduled_date', '>=', self.scheduled_date), 
                ('scheduled_date', '<=', self.scheduled_date + timedelta(hours=2))
            ]
            conflicting_requests = self.env['auto.voyage.service.request'].search(domain)
            
            if conflicting_requests:
                return {'warning': {
                    'title': _('Availability Conflict'),
                    'message': _('The selected provider has conflicting appointments at this time. Consider choosing another time or provider.')
                }}
    
    def action_assign(self):
        self.ensure_one()
        
        if not self.service_request_id:
            raise ValidationError(_("No service request selected."))
        
        if self.service_request_id.state not in ['draft', 'confirmed']:
            raise ValidationError(_("Cannot assign provider to a service request that is not in 'Draft' or 'Confirmed' state."))
        
        # Calculate estimated end time (2 hours by default)
        scheduled_end_date = self.scheduled_date + timedelta(hours=2)
        
        # Update the service request
        self.service_request_id.write({
            'provider_id': self.provider_id.id,
            'scheduled_date': self.scheduled_date,
            'scheduled_end_date': scheduled_end_date,
            'state': 'scheduled',
            'internal_notes': self.notes if self.notes else self.service_request_id.internal_notes,
        })
        
        # Create a message in the chatter
        self.service_request_id.message_post(
            body=_("Service request assigned to %s on %s") % (
                self.provider_id.name, 
                self.scheduled_date.strftime('%Y-%m-%d %H:%M')
            )
        )
        
        # Return to the service request form
        return {
            'name': _('Service Request'),
            'view_mode': 'form',
            'res_model': 'auto.voyage.service.request',
            'res_id': self.service_request_id.id,
            'type': 'ir.actions.act_window',
        } 