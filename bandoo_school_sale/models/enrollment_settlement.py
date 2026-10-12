from odoo import api, fields, models, tools


class EnrollmentSettlement(models.Model):
    _name = 'bandoo.enrollment.settlement'
    _description = 'Consuntivo allievo per riga di iscrizione'
    _auto = False
    _rec_name = 'partner_id'
    _order = 'project_id, partner_id'

    # --- grezzi dalla view SQL (una riga per riga d'ordine confermata) ---
    order_line_id = fields.Many2one('sale.order.line', string='Riga di iscrizione', readonly=True)
    order_id = fields.Many2one('sale.order', string='Iscrizione', readonly=True)
    partner_id = fields.Many2one('res.partner', string='Allievo', readonly=True)
    project_id = fields.Many2one('project.project', string='Corso', readonly=True)
    annual_price = fields.Float(string='Prezzo annuo (P)', readonly=True)
    target = fields.Integer(
        string='Lezioni previste', readonly=True,
        help='Dalla riga di iscrizione (proposte dal corso a catalogo, '
             'ridotte per le iscrizioni a metà anno). Lezioni ordinarie e '
             'saggi: la quota le copre tutte, ed è su questo numero che si '
             'divide.')
    lessons_held = fields.Integer(
        string='Lezioni erogate', readonly=True,
        help='Lezioni rendicontate in cui l\'allievo era in elenco presenze, '
             'con qualunque esito: quelle tenute prima dell\'iscrizione non '
             'contano. I saggi rientrano, sono lezioni a tutti gli effetti.')
    justified_absences = fields.Integer(
        string='Lezioni non fruite', readonly=True,
        help='Lezioni rendicontate con esito Assente giustificato: non si '
             'pagano.')

    # --- aritmetica in Python (non-stored, testabile a unità) ---
    price_per_lesson = fields.Float(
        string='Prezzo lezione', compute='_compute_amounts')
    missed_lessons = fields.Integer(
        string='Lezioni mai erogate', compute='_compute_amounts')
    paid_lessons = fields.Integer(
        string='Lezioni pagate', compute='_compute_amounts',
        help='Erogate meno non fruite, al massimo le previste: un recupero '
             'oltre le previste compensa una non fruita invece di andare '
             'perso.')
    deduction = fields.Float(
        string='Detrazione', compute='_compute_amounts')
    installment_1 = fields.Float(string='Rata 1', compute='_compute_amounts')
    installment_2 = fields.Float(string='Rata 2', compute='_compute_amounts')
    installment_3 = fields.Float(
        string='Rata 3', compute='_compute_amounts',
        help="P − rata 1 − rata 2 − detrazione, senza azzeramento: "
             "se negativa è il credito che la riga porta alle altre righe "
             "della stessa iscrizione. Le rate dovute si leggono sul "
             "consuntivo per iscrizione.")

    @api.depends('annual_price', 'target', 'lessons_held', 'justified_absences')
    def _compute_amounts(self):
        for rec in self:
            target = rec.target or 0
            price = rec.annual_price or 0.0
            rec.price_per_lesson = price / target if target else 0.0
            rec.missed_lessons = max(0, target - rec.lessons_held)
            rec.paid_lessons = min(
                target, rec.lessons_held - rec.justified_absences)
            rec.deduction = (target - rec.paid_lessons) * rec.price_per_lesson
            rec.installment_1 = round(price / 3)
            rec.installment_2 = round(price / 3)
            rec.installment_3 = (
                price - rec.installment_1 - rec.installment_2 - rec.deduction
            )

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE VIEW bandoo_enrollment_settlement AS
            SELECT
                sol.id AS id,
                sol.id AS order_line_id,
                sol.order_id AS order_id,
                so.partner_id AS partner_id,
                sol.project_id AS project_id,
                sol.price_unit AS annual_price,
                sol.x_lesson_target AS target,
                (SELECT count(*)
                   FROM project_task t
                  WHERE t.project_id IN (
                            SELECT p.id FROM project_project p
                             WHERE p.id = sol.project_id
                                OR p.x_course_product_id = pp_line.product_tmpl_id)
                    AND EXISTS (SELECT 1 FROM account_analytic_line al
                                 WHERE al.task_id = t.id)
                    AND EXISTS (SELECT 1 FROM bandoo_lesson_student_line sl
                                 WHERE sl.task_id = t.id
                                   AND sl.partner_id = so.partner_id)
                ) AS lessons_held,
                (SELECT count(*)
                   FROM bandoo_lesson_student_line sl
                  WHERE sl.project_id IN (
                            SELECT p.id FROM project_project p
                             WHERE p.id = sol.project_id
                                OR p.x_course_product_id = pp_line.product_tmpl_id)
                    AND sl.partner_id = so.partner_id
                    AND sl.status = 'absent_justified'
                    AND EXISTS (SELECT 1 FROM account_analytic_line al
                                 WHERE al.task_id = sl.task_id)) AS justified_absences
            FROM sale_order_line sol
            JOIN sale_order so ON so.id = sol.order_id
            JOIN product_product pp_line ON pp_line.id = sol.product_id
            JOIN product_template pt ON pt.id = pp_line.product_tmpl_id
            WHERE pt.x_lesson_target > 0
              AND so.state = 'sale'
              AND sol.product_uom_qty > 0
        """)
