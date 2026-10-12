from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # In minuti, che e' l'unita' in cui la scuola parla: 30, 45, 60. Le ore
    # decimali servono solo ai fogli ore, e la divisione sta li'.
    x_lesson_duration = fields.Integer(
        string='Durata lezione (minuti)',
        help='Durata di una singola lezione. Serve a comporre il nome del '
             'corso individuale e a proporre il tempo assegnato sulla lezione.',
    )
    x_lesson_target = fields.Integer(
        string='Lezioni previste',
        help='Lezioni incluse nel prezzo annuale, saggi compresi.',
    )
    # Un prodotto è un corso a catalogo quando ha lezioni previste
    x_is_course = fields.Boolean(compute='_compute_x_is_course')

    @api.depends('x_lesson_target')
    def _compute_x_is_course(self):
        for product in self:
            product.x_is_course = bool(product.x_lesson_target)

    @api.constrains('x_lesson_duration', 'x_lesson_target',
                    'project_template_id', 'service_tracking', 'type')
    def _check_course_configuration(self):
        for product in self:
            if product.x_lesson_target:
                if product.type != 'service':
                    raise ValidationError(_(
                        'Un corso a catalogo deve essere un servizio.'))
                if product.service_tracking not in ('project_only', 'no'):
                    raise ValidationError(_('Un corso a catalogo deve essere individuale o collettivo.'))
            if product.service_tracking == 'project_only':
                if not product.x_lesson_duration:
                    raise ValidationError(_(
                        'Un corso a catalogo individuale richiede la durata delle lezioni.'))
                if not product.x_lesson_target:
                    raise ValidationError(_(
                        'Un corso a catalogo individuale richiede le lezioni previste.'))
                if not product.project_template_id:
                    raise ValidationError(_(
                        'Un corso a catalogo individuale richiede il modello di progetto.'))
                if product.type != 'service':
                    raise ValidationError(_(
                        'Un corso a catalogo individuale deve essere un servizio.'))
