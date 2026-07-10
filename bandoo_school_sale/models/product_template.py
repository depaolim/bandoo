from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    x_is_course = fields.Boolean(string='È un corso', default=False)
    x_course_project_id = fields.Many2one(
        'project.project', string='Progetto condiviso (corso collettivo)',
        help='Corso collettivo: progetto comune a cui si agganciano le '
             'iscrizioni. Per i corsi individuali usare invece '
             '"Progetto" come tracciamento con un template di progetto.',
    )

    @api.constrains('x_is_course', 'x_course_project_id', 'type',
                    'service_tracking', 'project_template_id')
    def _check_course_configuration(self):
        for product in self:
            if not product.x_is_course:
                if product.x_course_project_id:
                    raise ValidationError(_(
                        'Il progetto condiviso si imposta solo sui '
                        'prodotti-corso.'))
                continue
            if product.type != 'service':
                raise ValidationError(_(
                    'Un prodotto-corso deve essere un servizio.'))
            is_collective = (
                product.service_tracking == 'no'
                and product.x_course_project_id
            )
            is_individual = (
                product.service_tracking == 'project_only'
                and product.project_template_id
            )
            if not (is_collective or is_individual):
                raise ValidationError(_(
                    'Un prodotto-corso va configurato in uno dei due modi: '
                    'collettivo (tracciamento "Niente" + progetto condiviso) '
                    'oppure individuale (tracciamento "Progetto" + template '
                    'di progetto).'))
