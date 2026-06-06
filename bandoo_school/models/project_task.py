from odoo import api, fields, models


class ProjectTask(models.Model):
    _inherit = 'project.task'

    room_id = fields.Many2one('bandoo.room', string='Aula')
    attendance_line_ids = fields.One2many(
        'bandoo.lesson.student.line', 'task_id',
        string='Presenze',
    )

    @api.model_create_multi
    def create(self, vals_list):
        tasks = super().create(vals_list)
        for task in tasks:
            if task.project_id.enrolled_student_ids:
                task.attendance_line_ids = [
                    (0, 0, {'partner_id': s.id, 'status': 'present'})
                    for s in task.project_id.enrolled_student_ids
                ]
        return tasks
