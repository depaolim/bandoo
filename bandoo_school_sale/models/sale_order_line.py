from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    x_student_id = fields.Many2one(
        'res.partner', string='Studente',
        domain=[('is_company', '=', False)],
    )
    x_project_id = fields.Many2one(
        'project.project', string='Corso',
        domain=[('x_is_course', '=', True)],
    )

    @api.onchange('x_project_id')
    def _onchange_x_project_id(self):
        """Riga d'iscrizione: prodotto generico + prezzo concordato dal listino corso.

        Il prezzo proposto resta modificabile: è il concordato a fare fede (vedi spec).
        """
        if not self.x_project_id:
            return
        if not self.product_id:
            product = self.env.ref(
                'bandoo_school_sale.product_enrollment', raise_if_not_found=False,
            )
            if product:
                self.product_id = product
        self.name = self.x_project_id.display_name
        self.price_unit = self.x_project_id.x_list_price
