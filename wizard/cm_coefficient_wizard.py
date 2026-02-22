# -*- coding: utf-8 -*-

from datetime import date

from odoo import models, fields
from odoo.exceptions import UserError


class CmCoefficientWizard(models.TransientModel):
    """Wizard para calcular coeficientes unificados automáticamente.

    // Por qué: El CU se calcula con datos del ejercicio anterior.
    // Busca facturas de venta del año base, agrupa ingresos por jurisdicción
    // y gastos (facturas de compra), y calcula el ratio para cada jurisdicción.
    """
    _name = 'cm.coefficient.wizard'
    _description = 'Calcular Coeficientes CM'

    base_year = fields.Char(
        string='Año Base (datos)', size=4, required=True,
        default=lambda self: str(date.today().year - 1),
        help='Ejercicio del que se toman los datos (año anterior)',
    )
    target_year = fields.Char(
        string='Año Aplicación', size=4, required=True,
        default=lambda self: str(date.today().year),
        help='Ejercicio en que se aplicarán los coeficientes',
    )

    def action_calculate(self):
        """Calcula coeficientes a partir de facturas del año base."""
        self.ensure_one()
        company = self.env.company

        base_from = date(int(self.base_year), 1, 1)
        base_to = date(int(self.base_year), 12, 31)

        # // Por qué: Verificar que no existan coeficientes para el año target
        existing = self.env['cm.coefficient'].search([
            ('fiscal_year', '=', self.target_year),
            ('company_id', '=', company.id),
        ])
        if existing:
            raise UserError(
                f'Ya existen coeficientes para {self.target_year}. '
                'Elimínelos primero si desea recalcular.'
            )

        # Ingresos por jurisdicción (ventas)
        sales = self.env['account.move'].search([
            ('state', '=', 'posted'),
            ('move_type', 'in', ('out_invoice', 'out_refund')),
            ('invoice_date', '>=', base_from),
            ('invoice_date', '<=', base_to),
            ('company_id', '=', company.id),
            ('cm_jurisdiction_id', '!=', False),
        ])

        income_by_jur = {}
        income_total = 0.0
        for move in sales:
            sign = -1 if move.move_type == 'out_refund' else 1
            amount = sign * move.amount_untaxed
            jur_id = move.cm_jurisdiction_id.id
            income_by_jur[jur_id] = income_by_jur.get(jur_id, 0.0) + amount
            income_total += amount

        # Gastos por jurisdicción (compras)
        purchases = self.env['account.move'].search([
            ('state', '=', 'posted'),
            ('move_type', 'in', ('in_invoice', 'in_refund')),
            ('invoice_date', '>=', base_from),
            ('invoice_date', '<=', base_to),
            ('company_id', '=', company.id),
            ('cm_jurisdiction_id', '!=', False),
        ])

        expense_by_jur = {}
        expense_total = 0.0
        for move in purchases:
            sign = -1 if move.move_type == 'in_refund' else 1
            amount = sign * move.amount_untaxed
            jur_id = move.cm_jurisdiction_id.id
            expense_by_jur[jur_id] = expense_by_jur.get(jur_id, 0.0) + amount
            expense_total += amount

        if not income_total and not expense_total:
            raise UserError(
                f'No se encontraron facturas con jurisdicción CM en {self.base_year}.'
            )

        # Crear coeficientes para todas las jurisdicciones con actividad
        all_jur_ids = set(list(income_by_jur.keys()) + list(expense_by_jur.keys()))
        vals_list = []
        for jur_id in all_jur_ids:
            vals_list.append({
                'company_id': company.id,
                'fiscal_year': self.target_year,
                'jurisdiction_id': jur_id,
                'income_amount': income_by_jur.get(jur_id, 0.0),
                'income_total': income_total,
                'expense_amount': expense_by_jur.get(jur_id, 0.0),
                'expense_total': expense_total,
            })

        self.env['cm.coefficient'].create(vals_list)

        return {
            'type': 'ir.actions.act_window',
            'name': 'Coeficientes Generados',
            'res_model': 'cm.coefficient',
            'view_mode': 'list,form',
            'domain': [
                ('fiscal_year', '=', self.target_year),
                ('company_id', '=', company.id),
            ],
            'target': 'current',
        }
