# -*- coding: utf-8 -*-

from datetime import date

from odoo import models, fields
from odoo.exceptions import UserError


class CmLiquidationWizard(models.TransientModel):
    """Wizard para generar liquidacion mensual CM.

    // Por que: Busca facturas del periodo, agrupa por jurisdiccion,
    // aplica coeficientes y genera las lineas de liquidacion.
    // Tambien pre-carga deducciones (percepciones/retenciones sufridas
    // y saldo anterior) para evitar carga manual.
    // Patron: TransientModel con estado draft -> done.
    """
    _name = 'cm.liquidation.wizard'
    _description = 'Generar Liquidacion CM'

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

    # -- Metodos de calculo de deducciones (Fase 1) --

    def _get_percepciones_sufridas(self, date_from, date_to, company_id):
        """Busca percepciones IIBB sufridas en facturas de compra del periodo.

        // Por que: Las percepciones que nos aplicaron proveedores se deducen
        // del impuesto determinado en la liquidacion CM.
        // Busca tax lines con codigo AFIP '07' (IIBB) en compras posted.

        Returns:
            dict {jur_id: {'amount': float, 'move_ids': [int]}}
        """
        tax_lines = self.env['account.move.line'].search([
            ('move_id.state', '=', 'posted'),
            ('move_id.move_type', 'in', ('in_invoice', 'in_refund')),
            ('move_id.invoice_date', '>=', date_from),
            ('move_id.invoice_date', '<=', date_to),
            ('move_id.company_id', '=', company_id),
            ('tax_line_id', '!=', False),
            ('tax_line_id.l10n_ar_tribute_afip_code', '=', '07'),
            ('move_id.cm_jurisdiction_id', '!=', False),
        ])

        result = {}
        for tl in tax_lines:
            jur_id = tl.move_id.cm_jurisdiction_id.id
            # // Por que: NC de compra (in_refund) reduce la percepcion sufrida
            sign = -1 if tl.move_id.move_type == 'in_refund' else 1
            amount = sign * abs(tl.amount_currency)

            if jur_id not in result:
                result[jur_id] = {'amount': 0.0, 'move_ids': set()}
            result[jur_id]['amount'] += amount
            result[jur_id]['move_ids'].add(tl.move_id.id)

        # Convertir sets a listas para compatibilidad con ORM
        for data in result.values():
            data['move_ids'] = list(data['move_ids'])
        return result

    def _get_retenciones_sufridas(self, date_from, date_to, company_id):
        """Busca retenciones IIBB sufridas en cobros del periodo.

        // Por que: Cuando un cliente nos paga y retiene IIBB, esa retencion
        // se deduce del impuesto determinado en la jurisdiccion del cliente.
        // Se resuelve jurisdiccion desde partner_id.state_id con cache.

        Returns:
            dict {jur_id: {'amount': float, 'payment_ids': [int]}}
        """
        payments = self.env['account.payment'].search([
            ('state', '=', 'posted'),
            ('payment_type', '=', 'inbound'),
            ('date', '>=', date_from),
            ('date', '<=', date_to),
            ('company_id', '=', company_id),
        ])

        Jurisdiction = self.env['cm.jurisdiction']
        # // Tip: Cache evita N+1 queries al resolver state -> jurisdiccion
        jur_cache = {}
        result = {}

        for payment in payments:
            # Buscar lineas de retencion IIBB en el asiento del pago
            ret_lines = payment.move_id.line_ids.filtered(
                lambda l: l.tax_line_id
                and l.tax_line_id.l10n_ar_tribute_afip_code == '07'
            )
            if not ret_lines:
                continue

            # Resolver jurisdiccion desde provincia del partner
            state = payment.partner_id.state_id
            if not state:
                continue
            if state.id not in jur_cache:
                jur_cache[state.id] = Jurisdiction.search(
                    [('state_id', '=', state.id)], limit=1
                )
            jur = jur_cache[state.id]
            if not jur:
                continue
            jur_id = jur.id

            for rl in ret_lines:
                if jur_id not in result:
                    result[jur_id] = {'amount': 0.0, 'payment_ids': set()}
                result[jur_id]['amount'] += abs(rl.amount_currency)
                result[jur_id]['payment_ids'].add(payment.id)

        for data in result.values():
            data['payment_ids'] = list(data['payment_ids'])
        return result

    def _get_saldo_anterior(self, period, company_id):
        """Busca saldo a favor del periodo anterior para arrastrar.

        // Por que: Si en el periodo anterior quedo saldo negativo (a favor),
        // se arrastra como deduccion en el periodo actual.
        // Solo arrastra de liquidaciones confirmadas o calculadas.

        Returns:
            dict {jur_id: {'amount': float, 'liquidation_id': int}}
        """
        year, month = map(int, period.split('/'))
        if month == 1:
            prev_period = f'{year - 1}/12'
        else:
            prev_period = f'{year}/{str(month - 1).zfill(2)}'

        prev_liq = self.env['cm.liquidation'].search([
            ('period', '=', prev_period),
            ('company_id', '=', company_id),
            ('state', 'in', ('calculated', 'confirmed')),
        ], limit=1)

        if not prev_liq:
            return {}

        result = {}
        for line in prev_liq.line_ids:
            # // Por que: Solo se arrastra saldo negativo (a favor del contribuyente)
            if line.saldo < 0:
                result[line.jurisdiction_id.id] = {
                    'amount': abs(line.saldo),
                    'liquidation_id': prev_liq.id,
                }
        return result

    # -- Generacion de liquidacion --

    def action_generate(self):
        """Genera liquidacion mensual a partir de facturas del periodo.

        // Por que: Centraliza la generacion en un solo paso:
        // 1. Busca ventas y agrupa por jurisdiccion
        // 2. Auto-carga percepciones/retenciones sufridas y saldo anterior
        // 3. Incluye jurisdicciones con deducciones pero sin ventas
        // 4. Campos de deduccion quedan editables para ajuste manual
        """
        self.ensure_one()

        if self.date_from > self.date_to:
            raise UserError('La fecha desde debe ser anterior a la fecha hasta.')

        company = self.env.company
        period = self.date_from.strftime('%Y/%m')

        # Verificar que no exista liquidacion para el mismo periodo
        existing = self.env['cm.liquidation'].search([
            ('period', '=', period),
            ('company_id', '=', company.id),
        ], limit=1)
        if existing:
            raise UserError(
                f'Ya existe una liquidacion para el periodo {period}. '
                'Eliminela o vuelva a borrador primero.'
            )

        # Buscar facturas de venta posted del periodo con jurisdiccion CM
        moves = self.env['account.move'].search([
            ('state', '=', 'posted'),
            ('move_type', 'in', ('out_invoice', 'out_refund')),
            ('invoice_date', '>=', self.date_from),
            ('invoice_date', '<=', self.date_to),
            ('company_id', '=', company.id),
            ('cm_jurisdiction_id', '!=', False),
        ])

        # Agrupar bases por jurisdiccion
        bases_by_jurisdiction = {}
        for move in moves:
            jur_id = move.cm_jurisdiction_id.id
            # // Tip: sign maneja NC automaticamente (amount negativo)
            sign = -1 if move.move_type == 'out_refund' else 1
            base = sign * move.amount_untaxed
            bases_by_jurisdiction.setdefault(jur_id, {
                'base_gravada': 0.0,
                'base_no_gravada': 0.0,
                'base_exenta': 0.0,
            })
            bases_by_jurisdiction[jur_id]['base_gravada'] += base

        # // Por que: Auto-poblar deducciones desde datos contables (Fase 1)
        perc_data = self._get_percepciones_sufridas(
            self.date_from, self.date_to, company.id
        )
        ret_data = self._get_retenciones_sufridas(
            self.date_from, self.date_to, company.id
        )
        saldo_data = self._get_saldo_anterior(period, company.id)

        # Obtener coeficientes del ejercicio
        coefficients = self.env['cm.coefficient'].search([
            ('fiscal_year', '=', self.fiscal_year),
            ('company_id', '=', company.id),
        ])
        coeff_map = {c.jurisdiction_id.id: c.coefficient for c in coefficients}

        # Obtener actividades (primera vigente por jurisdiccion)
        activities = self.env['cm.activity'].search([
            ('company_id', '=', company.id),
            '|', ('date_to', '=', False), ('date_to', '>=', self.date_from),
            '|', ('date_from', '=', False), ('date_from', '<=', self.date_to),
        ])
        activity_map = {}
        for act in activities:
            if act.jurisdiction_id.id not in activity_map:
                activity_map[act.jurisdiction_id.id] = act

        # // Por que: Incluir jurisdicciones con deducciones aunque no tengan ventas.
        # Ej: puede haber percepciones sufridas en una provincia sin ventas del periodo.
        all_jur_ids = set(bases_by_jurisdiction.keys())
        all_jur_ids |= set(perc_data.keys())
        all_jur_ids |= set(ret_data.keys())
        all_jur_ids |= set(saldo_data.keys())

        if not all_jur_ids:
            raise UserError('No se encontraron facturas ni deducciones en el periodo.')

        # Construir lineas con deducciones pre-cargadas
        default_bases = {
            'base_gravada': 0.0, 'base_no_gravada': 0.0, 'base_exenta': 0.0,
        }
        lines_vals = []
        for jur_id in all_jur_ids:
            bases = bases_by_jurisdiction.get(jur_id, default_bases)
            activity = activity_map.get(jur_id)
            coeff = coeff_map.get(jur_id, 0.0)
            alicuota = activity.alicuota if activity else 0.0

            p_data = perc_data.get(jur_id, {})
            r_data = ret_data.get(jur_id, {})
            s_data = saldo_data.get(jur_id, {})

            lines_vals.append((0, 0, {
                'jurisdiction_id': jur_id,
                'activity_id': activity.id if activity else False,
                'coefficient': coeff,
                'base_gravada': bases['base_gravada'],
                'base_no_gravada': bases['base_no_gravada'],
                'base_exenta': bases['base_exenta'],
                'alicuota': alicuota,
                # Deducciones pre-cargadas (quedan editables)
                'percepciones_sufridas': p_data.get('amount', 0.0),
                'percepciones_move_ids': [(6, 0, p_data.get('move_ids', []))],
                'retenciones_sufridas': r_data.get('amount', 0.0),
                'retenciones_payment_ids': [(6, 0, r_data.get('payment_ids', []))],
                'saldo_anterior': s_data.get('amount', 0.0),
                'prev_liquidation_id': s_data.get('liquidation_id', False),
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

        return {
            'type': 'ir.actions.act_window',
            'name': 'Liquidacion CM',
            'res_model': 'cm.liquidation',
            'res_id': liquidation.id,
            'view_mode': 'form',
            'target': 'current',
        }
