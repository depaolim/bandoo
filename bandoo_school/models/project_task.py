from odoo import api, fields, models


class ProjectTask(models.Model):
    _inherit = 'project.task'

    room_id = fields.Many2one('bandoo.room', string='Aula')
    attendance_line_ids = fields.One2many(
        'bandoo.lesson.student.line', 'task_id',
        string='Presenze',
    )
    x_is_held = fields.Boolean(
        string='Svolta', compute='_compute_x_is_held',
        search='_search_x_is_held',
        help='La lezione è svolta se e solo se l\'insegnante ha registrato '
             'le ore: nessuna fase da impostare a mano.',
    )

    @api.depends('timesheet_ids')
    def _compute_x_is_held(self):
        for task in self:
            task.x_is_held = bool(task.timesheet_ids)

    def _search_x_is_held(self, operator, value):
        held = (operator == '=') == bool(value)
        return [('timesheet_ids', '!=' if held else '=', False)]

    @api.model_create_multi
    def create(self, vals_list):
        tasks = super().create(vals_list)
        for task in tasks:
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
