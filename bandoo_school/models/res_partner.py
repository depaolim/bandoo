from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    x_is_student = fields.Boolean(string='È studente', default=False)
