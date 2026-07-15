from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    x_student_id = fields.Many2one(
        'res.partner', string='Studente',
        domain=[('is_company', '=', False)],
    )
    x_project_id = fields.Many2one(
        'project.project', string='Corso',
        compute='_compute_x_project_id', store=True,
    )
    x_lesson_target = fields.Integer(
        string='Lezioni previste', compute='_compute_x_lesson_target',
        store=True, readonly=False,
        help='Lezioni coperte da questa iscrizione: proposte dal corso, '
             'da ridurre per le iscrizioni a metà anno (il conguaglio '
             'detrae le lezioni non erogate all\'iscritto rispetto a '
             'questo numero).',
    )

    @api.depends('project_id', 'product_id')
    def _compute_x_project_id(self):
        """Progetto del corso: per gli individuali è quello generato alla
        conferma (project_id standard), per i collettivi quello condiviso
        indicato sul prodotto."""
        for line in self:
            line.x_project_id = (
                line.project_id or line.product_id.x_course_project_id
            )

    @api.depends('product_id')
    def _compute_x_lesson_target(self):
        """Proposta dal corso (collettivo: progetto condiviso; individuale:
        template); resta modificabile per le iscrizioni a metà anno."""
        for line in self:
            product = line.product_id
            line.x_lesson_target = (
                product.x_course_project_id.x_lesson_target
                or product.project_template_id.x_lesson_target
                or 0
            )

    def _timesheet_create_project(self):
        project = super()._timesheet_create_project()
        if self.product_id.x_is_course and self.x_student_id:
            # Nome operativo al posto dello standard "S00042 - <template>".
            project.name = '%s - %s' % (
                self.product_id.name, self.x_student_id.name)
        return project

    @api.constrains('product_id', 'x_student_id')
    def _check_course_enrollment(self):
        """Riga con prodotto-corso: studente obbligatorio e socio, validato
        al salvataggio in qualunque stato (niente bozze incomplete: copre
        anche le righe aggiunte a ordini già confermati)."""
        for line in self:
            if not line.product_id.x_is_course:
                continue
            if not line.x_student_id:
                raise ValidationError(_(
                    'Riga "%s": indicare lo studente da iscrivere.',
                    line.product_id.display_name))
            if not line.x_student_id.x_is_member:
                raise ValidationError(_(
                    'Lo studente %s deve essere socio per iscriversi.',
                    line.x_student_id.display_name))
