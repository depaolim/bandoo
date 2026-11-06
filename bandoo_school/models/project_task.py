from odoo import api, fields, models
from odoo.tools import format_date


class ProjectTask(models.Model):
    _inherit = 'project.task'

    room_id = fields.Many2one('bandoo.room', string='Aula')
    attendance_line_ids = fields.One2many(
        'bandoo.lesson.student.line', 'task_id',
        string='Presenze',
    )
    x_is_held = fields.Boolean(
        string='Rendicontata', compute='_compute_x_is_held',
        search='_search_x_is_held',
        help='La lezione è rendicontata se e solo se l\'insegnante ha '
             'registrato le ore: nessuna fase da impostare a mano.',
    )

    @api.depends('timesheet_ids')
    def _compute_x_is_held(self):
        for task in self:
            task.x_is_held = bool(task.timesheet_ids)

    @api.depends('date_deadline')
    @api.depends_context('tz', 'lang')
    def _compute_display_name(self):
        """La lezione si riconosce dalla data: «Lezione 08/12/2026».

        Il nome salvato resta «Lezione» o «Saggio»: una data scritta nel nome
        resterebbe quella vecchia dopo uno spostamento. Va subito dopo il nome,
        prima di quanto `hr_timesheet` può accodare (le ore rimanenti).
        """
        super()._compute_display_name()
        for task in self:
            if not (task.project_id and task.date_deadline and task.name):
                continue
            day = format_date(self.env, fields.Datetime.context_timestamp(
                task, task.date_deadline))
            if task.display_name.startswith(task.name):
                task.display_name = '%s %s%s' % (
                    task.name, day, task.display_name[len(task.name):])

    def _search_x_is_held(self, operator, value):
        held = (operator == '=') == bool(value)
        return [('timesheet_ids', '!=' if held else '=', False)]

    @api.model_create_multi
    def create(self, vals_list):
        tasks = super().create(vals_list)
        for task in tasks:
            # Ore attese dalla durata del corso: vale sia per le lezioni
            # generate dal wizard sia per quelle aggiunte a mano, i saggi
            # compresi. Un valore esplicito in creazione vince.
            duration = task.project_id and task.project_id._get_lesson_duration()
            if not task.allocated_hours and duration:
                task.allocated_hours = duration / 60.0
            # Insegnante dal responsabile del corso, per le generate come per
            # quelle aggiunte a mano. Un'assegnazione esplicita vince: è il
            # caso del supplente.
            if not task.user_ids and task.project_id.user_id:
                task.user_ids = task.project_id.user_id
            students = (
                task.project_id._get_enrolled_students()
                if task.project_id else self.env['res.partner']
            )
            if students:
                task.attendance_line_ids = [
                    (0, 0, {'partner_id': s.id, 'status': 'present'})
                    for s in students
                ]
        return tasks
