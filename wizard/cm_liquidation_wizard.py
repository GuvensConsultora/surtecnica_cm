# -*- coding: utf-8 -*-

from datetime import date

from odoo import models, fields
from odoo.exceptions import UserError


class CmLiquidationWizard(models.TransientModel):
    """Wizard para generar liquidación mensual CM.

    // Por qué: Busca facturas del período, agrupa por jurisdicción,
    // aplica coeficientes y genera las líneas de liquidación.
    // Patrón: TransientModel con estado draft → done.
    """
    _name = 'cm.liquidation.wizard'
    _description = 'Generar Liquidación CM'

    date_from = fields.Date(
        string='Desde', required=True,
        default=lambda self: date.today().replace(day=1),
    )
    date_to = fields.Date(string='Hasta', required=True, default=fields.Date.today)
    fiscal_year = fields.Char(
        string='Ejercicio Fiscal', size=4, required=True,
        default=lambda self: str(date.today().year),
        help='Ejercicio del que se toman los coeficientes unificados',
    )

    def action_generate(self):
        """Genera liquidación mensual a partir de facturas del período."""
        self.ensure_one()

        if self.date_from > self.date_to:
            raise UserError('La fecha desde debe ser anterior a la fecha hasta.')

        company = self.env.company
        period = self.date_from.strftime('%Y/%m')

        # // Por qué: Verificar que no exista liquidación para el mismo período
        existing = self.env['cm.liquidation'].search([
            ('period', '=', period),
            ('company_id', '=', company.id),
        ], limit=1)
        if existing:
            raise UserError(
                f'Ya existe una liquidación para el período {period}. '
                'Elimínela o vuelva a borrador primero.'
            )

        # Buscar facturas de venta posted del período con jurisdicción CM
        moves = self.env['account.move'].search([
            ('state', '=', 'posted'),
            ('move_type', 'in', ('out_invoice', 'out_refund')),
            ('invoice_date', '>=', self.date_from),
            ('invoice_date', '<=', self.date_to),
            ('company_id', '=', company.id),
            ('cm_jurisdiction_id', '!=', False),
        ])

        if not moves:
            raise UserError('No se encontraron facturas con jurisdicción CM en el período.')

        # // Por qué: Agrupar bases por jurisdicción para distribuir
        bases_by_jurisdiction = {}
        for move in moves:
            jur_id = move.cm_jurisdiction_id.id
            # // Tip: sign maneja NC automáticamente (amount negativo)
            sign = -1 if move.move_type == 'out_refund' else 1
            base = sign * move.amount_untaxed
            bases_by_jurisdiction.setdefault(jur_id, {
                'base_gravada': 0.0,
                'base_no_gravada': 0.0,
                'base_exenta': 0.0,
            })
            # // Por qué: Simplificación — todo el untaxed va a base_gravada.
            # En una implementación más detallada se clasificaría por tipo de IVA.
            bases_by_jurisdiction[jur_id]['base_gravada'] += base

        # Obtener coeficientes del ejercicio
        coefficients = self.env['cm.coefficient'].search([
            ('fiscal_year', '=', self.fiscal_year),
            ('company_id', '=', company.id),
        ])
        coeff_map = {c.jurisdiction_id.id: c.coefficient for c in coefficients}

        # Obtener actividades (primera vigente por jurisdicción)
        activities = self.env['cm.activity'].search([
            ('company_id', '=', company.id),
            '|', ('date_to', '=', False), ('date_to', '>=', self.date_from),
            '|', ('date_from', '=', False), ('date_from', '<=', self.date_to),
        ])
        activity_map = {}
        for act in activities:
            if act.jurisdiction_id.id not in activity_map:
                activity_map[act.jurisdiction_id.id] = act

        # Crear liquidación con líneas
        lines_vals = []
        for jur_id, bases in bases_by_jurisdiction.items():
            activity = activity_map.get(jur_id)
            coeff = coeff_map.get(jur_id, 0.0)
            alicuota = activity.alicuota if activity else 0.0

            lines_vals.append((0, 0, {
                'jurisdiction_id': jur_id,
                'activity_id': activity.id if activity else False,
                'coefficient': coeff,
                'base_gravada': bases['base_gravada'],
                'base_no_gravada': bases['base_no_gravada'],
                'base_exenta': bases['base_exenta'],
                'alicuota': alicuota,
            }))

        liquidation = self.env['cm.liquidation'].create({
            'period': period,
            'date_from': self.date_from,
            'date_to': self.date_to,
            'fiscal_year': self.fiscal_year,
            'company_id': company.id,
            'state': 'calculated',
            'line_ids': lines_vals,
        })

        # Abrir la liquidación creada
        return {
            'type': 'ir.actions.act_window',
            'name': 'Liquidación CM',
            'res_model': 'cm.liquidation',
            'res_id': liquidation.id,
            'view_mode': 'form',
            'target': 'current',
        }
