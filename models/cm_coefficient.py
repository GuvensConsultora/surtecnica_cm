# -*- coding: utf-8 -*-

from odoo import models, fields, api


class CmCoefficient(models.Model):
    """Coeficiente Unificado por ejercicio fiscal y jurisdicción.

    // Por qué: El CU se calcula con datos del ejercicio anterior (ingresos
    // y gastos por jurisdicción) y se aplica durante todo el ejercicio actual.
    // Fórmula: CU = (ingreso_ratio * 0.50) + (gasto_ratio * 0.50)
    // Patrón: Stored computed fields para evitar recálculo en cada liquidación.
    """
    _name = 'cm.coefficient'
    _description = 'Coeficiente Unificado CM'
    _order = 'fiscal_year desc, jurisdiction_id'

    company_id = fields.Many2one(
        'res.company', string='Empresa', required=True,
        default=lambda self: self.env.company,
    )
    fiscal_year = fields.Char(
        string='Ejercicio Fiscal', size=4, required=True,
        help='Año en que se aplica el coeficiente (ej: 2026)',
    )
    jurisdiction_id = fields.Many2one(
        'cm.jurisdiction', string='Jurisdicción', required=True,
        ondelete='restrict',
    )

    # Ingresos
    income_amount = fields.Float(
        string='Ingresos Jurisdicción', digits=(16, 2),
        help='Ingresos computables en esta jurisdicción (ejercicio anterior)',
    )
    income_total = fields.Float(
        string='Ingresos Totales', digits=(16, 2),
        help='Ingresos computables totales país (ejercicio anterior)',
    )
    income_ratio = fields.Float(
        string='Coef. Ingresos', digits=(8, 4),
        compute='_compute_ratios', store=True,
    )

    # Gastos
    expense_amount = fields.Float(
        string='Gastos Jurisdicción', digits=(16, 2),
        help='Gastos computables en esta jurisdicción (ejercicio anterior)',
    )
    expense_total = fields.Float(
        string='Gastos Totales', digits=(16, 2),
        help='Gastos computables totales país (ejercicio anterior)',
    )
    expense_ratio = fields.Float(
        string='Coef. Gastos', digits=(8, 4),
        compute='_compute_ratios', store=True,
    )

    # Coeficiente unificado
    coefficient = fields.Float(
        string='Coeficiente Unificado', digits=(8, 4),
        compute='_compute_ratios', store=True,
    )

    @api.depends('income_amount', 'income_total', 'expense_amount', 'expense_total')
    def _compute_ratios(self):
        for rec in self:
            # // Por qué: Evitar división por cero si no hay totales cargados
            rec.income_ratio = (
                round(rec.income_amount / rec.income_total, 4)
                if rec.income_total else 0.0
            )
            rec.expense_ratio = (
                round(rec.expense_amount / rec.expense_total, 4)
                if rec.expense_total else 0.0
            )
            # // Por qué: CU = promedio ponderado 50/50 de ingresos y gastos
            rec.coefficient = round(
                rec.income_ratio * 0.50 + rec.expense_ratio * 0.50, 4
            )

    _sql_constraints = [
        ('coeff_unique', 'unique(fiscal_year, jurisdiction_id, company_id)',
         'Ya existe un coeficiente para esta jurisdicción y ejercicio.'),
    ]
