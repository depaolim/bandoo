from odoo import api, fields, models, tools


class OrderSettlement(models.Model):
    _name = 'bandoo.order.settlement'
    _description = 'Conguaglio per ordine'
    _auto = False
    _rec_name = 'order_id'
    _order = 'order_id'

    # --- grezzi dalla view SQL (una riga per ordine con righe d'iscrizione) ---
    order_id = fields.Many2one('sale.order', string='Ordine', readonly=True)
    payer_id = fields.Many2one('res.partner', string='Pagatore', readonly=True)
    total_price = fields.Float(string='Totale ordine', readonly=True)

    # --- aritmetica in Python: le rate si calcolano sul totale ordine ---
    deduction = fields.Float(
        string='Detrazione', compute='_compute_amounts',
        help="Somma delle detrazioni delle righe d'iscrizione dell'ordine.")
    installment_1 = fields.Float(string='Rata 1', compute='_compute_amounts')
    installment_2 = fields.Float(string='Rata 2', compute='_compute_amounts')
    installment_3 = fields.Float(
        string='Rata 3 (conguaglio)', compute='_compute_amounts',
        help="Totale − rata 1 − rata 2 − detrazione, mai negativa: il "
             "credito residuo oltre l'ordine è perso.")

    @api.depends('total_price', 'order_id')
    def _compute_amounts(self):
        lines = self.env['bandoo.enrollment.settlement'].search(
            [('order_id', 'in', self.order_id.ids)])
        for rec in self:
            total = rec.total_price or 0.0
            rec.deduction = sum(
                l.deduction for l in lines if l.order_id == rec.order_id)
            rec.installment_1 = round(total / 3)
            rec.installment_2 = round(total / 3)
            rec.installment_3 = max(
                0.0,
                total - rec.installment_1 - rec.installment_2 - rec.deduction,
            )

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE VIEW bandoo_order_settlement AS
            SELECT
                so.id AS id,
                so.id AS order_id,
                so.partner_id AS payer_id,
                SUM(sol.price_unit) AS total_price
            FROM sale_order_line sol
            JOIN sale_order so ON so.id = sol.order_id
            WHERE sol.x_student_id IS NOT NULL
              AND so.state = 'sale'
              AND sol.product_uom_qty > 0
            GROUP BY so.id
        """)
