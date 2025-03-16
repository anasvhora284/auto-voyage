# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    
    # Add the missing field to prevent errors
    pay_invoices_online = fields.Boolean(string='Pay Invoices Online', default=False) 