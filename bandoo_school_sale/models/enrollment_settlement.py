from odoo import api, fields, models, tools


class EnrollmentSettlement(models.Model):
    _name = 'bandoo.enrollment.settlement'
    _description = 'Conguaglio iscrizione'
    _auto = False
    _rec_name = 'partner_id'
    _order = 'project_id, partner_id'

    # --- grezzi dalla view SQL (una riga per riga d'ordine confermata) ---
    order_line_id = fields.Many2one('sale.order.line', string='Riga ordine', readonly=True)
    order_id = fields.Many2one('sale.order', string='Ordine', readonly=True)
    payer_id = fields.Many2one('res.partner', string='Pagatore', readonly=True)
    partner_id = fields.Many2one('res.partner', string='Studente', readonly=True)
    project_id = fields.Many2one('project.project', string='Corso', readonly=True)
    annual_price = fields.Float(string='Prezzo annuo (P)', readonly=True)
    target = fields.Integer(string='Lezioni previste', readonly=True)
    lessons_held = fields.Integer(string='Lezioni tenute', readonly=True)
    justified_absences = fields.Integer(string='Assenze giustificate', readonly=True)

    # --- aritmetica in Python (non-stored, testabile a unità) ---
    price_per_lesson = fields.Float(
        string='Prezzo lezione', compute='_compute_amounts')
    missed_lessons = fields.Integer(
        string='Lezioni mai erogate', compute='_compute_amounts')
    deduction = fields.Float(
        string='Detrazione', compute='_compute_amounts')
    installment_1 = fields.Float(string='Rata 1', compute='_compute_amounts')
    installment_2 = fields.Float(string='Rata 2', compute='_compute_amounts')
    installment_3 = fields.Float(
        string='Rata 3 (conguaglio)', compute='_compute_amounts')

    @api.depends('annual_price', 'target', 'lessons_held', 'justified_absences')
    def _compute_amounts(self):
        for rec in self:
            target = rec.target or 0
            price = rec.annual_price or 0.0
            rec.price_per_lesson = price / target if target else 0.0
            rec.missed_lessons = max(0, target - rec.lessons_held)
            rec.deduction = (
                (rec.justified_absences + rec.missed_lessons) * rec.price_per_lesson
            )
            rec.installment_1 = round(price / 3)
            rec.installment_2 = round(price / 3)
            rec.installment_3 = max(
                0.0,
                price - rec.installment_1 - rec.installment_2 - rec.deduction,
            )

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE VIEW bandoo_enrollment_settlement AS
            SELECT
                sol.id AS id,
                sol.id AS order_line_id,
                sol.order_id AS order_id,
                so.partner_id AS payer_id,
                sol.x_student_id AS partner_id,
                sol.x_project_id AS project_id,
                sol.price_unit AS annual_price,
                pp.x_lesson_target AS target,
                (SELECT count(*)
                   FROM project_task t
                  WHERE t.project_id = sol.x_project_id
                    AND EXISTS (SELECT 1 FROM account_analytic_line al
                                 WHERE al.task_id = t.id)) AS lessons_held,
                (SELECT count(*)
                   FROM bandoo_lesson_student_line sl
                  WHERE sl.project_id = sol.x_project_id
                    AND sl.partner_id = sol.x_student_id
                    AND sl.status = 'absent_justified'
                    AND EXISTS (SELECT 1 FROM account_analytic_line al
                                 WHERE al.task_id = sl.task_id)) AS justified_absences
            FROM sale_order_line sol
            JOIN sale_order so ON so.id = sol.order_id
            JOIN project_project pp ON pp.id = sol.x_project_id
            WHERE sol.x_student_id IS NOT NULL
              AND so.state = 'sale'
        """)
