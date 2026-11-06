from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ProjectProject(models.Model):
    _inherit = 'project.project'

    x_course_product_id = fields.Many2one(
        'product.template', string='Corso a catalogo',
        domain=[('x_lesson_duration', '>', 0), ('service_tracking', '=', 'no')])
    x_enrollment_line_ids = fields.One2many(
        'sale.order.line', 'project_id', string='Righe di iscrizione')
    # Ridichiarato per dare al compute (in bandoo_school) le dipendenze
    # reali: senza, il valore resterebbe in cache anche dopo la conferma
    # o l'annullamento di un ordine nella stessa transazione.
    enrolled_student_ids = fields.Many2many(
        'res.partner', string='Allievi iscritti',
        compute='_compute_enrolled_student_ids',
        depends=['x_enrollment_line_ids.state',
                 'x_enrollment_line_ids.order_id.partner_id',
                 'x_enrollment_line_ids.product_uom_qty'],
    )

    @api.constrains('x_course_product_id', 'x_lesson_duration')
    def _check_collective_duration(self):
        """Il corso collettivo ha una durata: senza, le sue lezioni nascono a
        tempo assegnato 0 e le ore dell'insegnante non hanno un termine di
        confronto, senza alcun errore."""
        for project in self:
            if project.x_course_product_id and project.x_lesson_duration <= 0:
                raise ValidationError(_(
                    'Il corso collettivo "%s" richiede la durata della lezione.',
                    project.display_name))

    def _get_lesson_duration(self):
        """Sul corso individuale è la quota del corso a catalogo della riga:
        il corso non ne porta una copia."""
        self.ensure_one()
        if self.sale_line_id.product_id.x_is_course:
            return self.sale_line_id.product_id.x_lesson_duration
        return super()._get_lesson_duration()

    def _get_lesson_target(self):
        """Individuale: le previste della riga, già ridotte per un'iscrizione
        a metà anno. Collettivo: quelle del suo corso a catalogo, per un
        anno intero."""
        self.ensure_one()
        if self.sale_line_id.product_id.x_is_course:
            return self.sale_line_id.x_lesson_target
        if self.x_course_product_id:
            return self.x_course_product_id.x_lesson_target
        return super()._get_lesson_target()

    def _get_recital_count(self):
        """Due saggi l'anno nei corsi individuali, nessuno nei collettivi:
        il solfeggio non ne ha (`S-05`)."""
        self.ensure_one()
        if self.sale_line_id.product_id.x_is_course:
            return 2
        return super()._get_recital_count()

    def _get_enrolled_students(self):
        """Iscritti = allievi delle righe di iscrizione confermate del corso.

        Quantità 0 = riga annullata (convenzione Odoo sugli ordini
        confermati): non iscrive.
        """
        self.ensure_one()
        lines = self.x_enrollment_line_ids.filtered(
            lambda l: l.state == 'sale' and l.product_uom_qty > 0)
        return super()._get_enrolled_students() | lines.order_id.partner_id
