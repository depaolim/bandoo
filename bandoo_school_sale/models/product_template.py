from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    service_tracking = fields.Selection(
        # L'etichetta nomina l'oggetto che si andrà a indicare, come le altre
        # voci della tendina. Il valore tecnico resta 'course_collective':
        # cambiarlo romperebbe i dati esistenti e i test.
        selection_add=[('course_collective', 'Progetto condiviso')],
        ondelete={'course_collective': 'set default'},
    )
    x_course_project_id = fields.Many2one(
        'project.project', string='Progetto condiviso',
        help='Corso collettivo: progetto comune a cui si agganciano le '
             'iscrizioni. Per i corsi individuali usare invece '
             '"Progetto" come tracciamento con un template di progetto.',
    )
    # In minuti, che e' l'unita' in cui la scuola parla: 30, 45, 60. Le ore
    # decimali servono solo ai fogli ore, e la divisione sta li'.
    x_lesson_duration = fields.Integer(
        string='Durata lezione (minuti)',
        help='Durata di una singola lezione. Serve a comporre il nome del '
             'registro e a proporre le ore attese sulla lezione.',
    )
    # Un prodotto è un corso quando il tracciamento è "Progetto" (individuale)
    # o "Corso collettivo".
    x_is_course = fields.Boolean(compute='_compute_x_is_course')

    @api.depends('service_tracking')
    def _compute_x_is_course(self):
        for product in self:
            product.x_is_course = product.service_tracking in (
                'project_only', 'course_collective')

    @api.constrains('x_course_project_id', 'type',
                    'service_tracking', 'project_template_id')
    def _check_course_configuration(self):
        for product in self:
            if product.x_course_project_id and (
                    product.service_tracking != 'course_collective'):
                raise ValidationError(_(
                    'Il progetto condiviso si imposta solo sui corsi '
                    'collettivi.'))
            if product.service_tracking == 'course_collective':
                if product.type != 'service':
                    raise ValidationError(_(
                        'Un prodotto-corso deve essere un servizio.'))
                if not product.x_course_project_id:
                    raise ValidationError(_(
                        'Un corso collettivo richiede il progetto condiviso.'))
            elif product.service_tracking == 'project_only':
                if product.type != 'service':
                    raise ValidationError(_(
                        'Un prodotto-corso deve essere un servizio.'))
                if not product.project_template_id:
                    raise ValidationError(_(
                        'Un corso individuale ("Progetto") richiede il '
                        'template di progetto.'))
