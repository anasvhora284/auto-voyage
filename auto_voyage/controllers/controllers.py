# -*- coding: utf-8 -*-
# from odoo import http


# class AutoVoyage(http.Controller):
#     @http.route('/auto_voyage/auto_voyage', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/auto_voyage/auto_voyage/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('auto_voyage.listing', {
#             'root': '/auto_voyage/auto_voyage',
#             'objects': http.request.env['auto_voyage.auto_voyage'].search([]),
#         })

#     @http.route('/auto_voyage/auto_voyage/objects/<model("auto_voyage.auto_voyage"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('auto_voyage.object', {
#             'object': obj
#         })

