from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

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
        if self.product_id.x_is_course and self.order_id.partner_id:
            # Nome operativo al posto dello standard "S00042 - <template>".
            # Il nome progetto è traducibile e la copia del template porta le
            # traduzioni: va riscritto in ogni lingua installata, non solo in
            # quella della sessione.
            for lang, _lang_name in self.env['res.lang'].get_installed():
                project.with_context(lang=lang).name = '%s - %s' % (
                    self.product_id.with_context(lang=lang).name,
                    self.order_id.partner_id.name)
        return project
