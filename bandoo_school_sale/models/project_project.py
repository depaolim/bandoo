from odoo import fields, models


class ProjectProject(models.Model):
    _inherit = 'project.project'

    x_is_course = fields.Boolean(string='È un corso', default=False)
    x_is_solfeggio = fields.Boolean(
        string='Corso di solfeggio', default=False,
        help='Corso di teoria proposto in automatico insieme allo strumento.',
    )
    x_list_price = fields.Float(string='Prezzo annuo (listino)', default=0.0)
    x_lesson_target = fields.Integer(string='Lezioni previste', default=28)
