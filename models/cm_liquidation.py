# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError


class CmLiquidation(models.Model):
    """Liquidacion mensual Convenio Multilateral.

    // Por que: Agrupa las lineas por jurisdiccion para un periodo.
    // El flujo es draft -> calculated (wizard genera lineas) -> confirmed (usuario valida).
    """
    _name = 'cm.liquidation'
    _description = 'Liquidacion CM Mensual'
    _order = 'period desc'
    _inherit = ['mail.thread']

    name = fields.Char(
        string='Referencia', compute='_compute_name', store=True,
    )
    company_id = fields.Many2one(
        'res.company', string='Empresa', required=True,
        default=lambda self: self.env.company,
    )
    # // Por que: currency_id necesario para widget monetary en vistas kanban/form
    currency_id = fields.Many2one(
        'res.currency', string='Moneda',
        related='company_id.currency_id',
    )
    period = fields.Char(
        string='Periodo', size=7, required=True,
        help='Formato AAAA/MM (ej: 2026/01)',
    )
    date_from = fields.Date(string='Desde', required=True)
    date_to = fields.Date(string='Hasta', required=True)
    fiscal_year = fields.Char(
        string='Ejercicio Fiscal', size=4, required=True,
        help='Ejercicio del que se toman los coeficientes',
    )
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('calculated', 'Calculada'),
        ('confirmed', 'Confirmada'),
    ], string='Estado', default='draft', tracking=True)
    line_ids = fields.One2many(
        'cm.liquidation.line', 'liquidation_id',
        string='Lineas por Jurisdiccion',
    )

    # Totales computados
    total_base_gravada = fields.Float(
        string='Total Base Gravada', digits=(16, 2),
        compute='_compute_totals', store=True,
    )
    total_impuesto = fields.Float(
        string='Total Impuesto Determinado', digits=(16, 2),
        compute='_compute_totals', store=True,
    )
    total_deducciones = fields.Float(
        string='Total Deducciones', digits=(16, 2),
        compute='_compute_totals', store=True,
    )
    total_saldo = fields.Float(
        string='Saldo Total', digits=(16, 2),
        compute='_compute_totals', store=True,
    )

    @api.depends('period', 'company_id')
    def _compute_name(self):
        for rec in self:
            rec.name = f"CM {rec.period} - {rec.company_id.name or ''}"

    @api.depends(
        'line_ids.base_gravada', 'line_ids.impuesto_determinado',
        'line_ids.total_deducciones', 'line_ids.saldo',
    )
    def _compute_totals(self):
        for rec in self:
            rec.total_base_gravada = sum(rec.line_ids.mapped('base_gravada'))
            rec.total_impuesto = sum(rec.line_ids.mapped('impuesto_determinado'))
            rec.total_deducciones = sum(rec.line_ids.mapped('total_deducciones'))
            rec.total_saldo = sum(rec.line_ids.mapped('saldo'))

    # -- Validaciones antes de confirmar (Fase 4) --

    def _get_confirmation_warnings(self):
        """Detecta situaciones a revisar antes de confirmar.

        // Por que: Evita confirmaciones accidentales de liquidaciones
        // con datos faltantes o inconsistentes.
        """
        self.ensure_one()
        warnings = []
        coeff_sum = sum(self.line_ids.mapped('coefficient'))

        for line in self.line_ids:
            jur = line.jurisdiction_id.display_name
            if line.coefficient == 0:
                warnings.append(f"- {jur}: coeficiente = 0")
            if line.total_deducciones == 0:
                warnings.append(f"- {jur}: sin deducciones cargadas")
            if line.alicuota == 0 and line.base_gravada > 0:
                warnings.append(f"- {jur}: alicuota 0% con base gravada > 0")

        if self.line_ids and abs(coeff_sum - 1.0) > 0.0001:
            warnings.append(
                f"- Suma de coeficientes = {coeff_sum:.4f} (esperado: 1.0000)"
            )
        return warnings

    def action_confirm(self):
        """Confirmar liquidacion calculada.

        // Por que: Si hay advertencias, abre wizard de confirmacion para que el
        // usuario las revise antes de proceder. Si no hay, confirma directo.
        """
        for rec in self:
            if rec.state != 'calculated':
                raise UserError('Solo se pueden confirmar liquidaciones calculadas.')
            warnings = rec._get_confirmation_warnings()
            if warnings:
                wizard = self.env['cm.confirm.wizard'].create({
                    'liquidation_id': rec.id,
                    'warnings_text': '\n'.join(warnings),
                })
                return {
                    'type': 'ir.actions.act_window',
                    'name': 'Advertencias de Liquidacion',
                    'res_model': 'cm.confirm.wizard',
                    'res_id': wizard.id,
                    'view_mode': 'form',
                    'target': 'new',
                }
            rec.state = 'confirmed'

    def action_draft(self):
        """Volver a borrador."""
        for rec in self:
            if rec.state != 'calculated':
                raise UserError('Solo se pueden pasar a borrador liquidaciones calculadas.')
            rec.line_ids.unlink()
            rec.state = 'draft'

    # -- Botones de exportacion (Fase 3) --

    def action_export_cm03(self):
        """Abre wizard CM03 pre-poblado con esta liquidacion."""
        self.ensure_one()
        wizard = self.env['cm.cm03.wizard'].create({
            'liquidation_id': self.id,
        })
        return {
            'type': 'ir.actions.act_window',
            'name': 'Exportar CM03',
            'res_model': 'cm.cm03.wizard',
            'res_id': wizard.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_export_sircar(self):
        """Abre wizard SIRCAR pre-poblado con fechas de esta liquidacion."""
        self.ensure_one()
        wizard = self.env['cm.sircar.wizard'].create({
            'date_from': self.date_from,
            'date_to': self.date_to,
        })
        return {
            'type': 'ir.actions.act_window',
            'name': 'Exportar SIRCAR',
            'res_model': 'cm.sircar.wizard',
            'res_id': wizard.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_export_sifere(self):
        """Abre wizard SIFERE pre-poblado con fechas de esta liquidacion."""
        self.ensure_one()
        wizard = self.env['cm.sifere.wizard'].create({
            'date_from': self.date_from,
            'date_to': self.date_to,
        })
        return {
            'type': 'ir.actions.act_window',
            'name': 'Exportar SIFERE',
            'res_model': 'cm.sifere.wizard',
            'res_id': wizard.id,
            'view_mode': 'form',
            'target': 'new',
        }

    # -- Recalcular deducciones (Fase 6) --

    def action_recalculate_deductions(self):
        """Re-calcula deducciones sin regenerar toda la liquidacion.

        // Por que: Permite actualizar deducciones si se registraron
        // nuevas facturas o cobros despues de generar la liquidacion.
        """
        self.ensure_one()
        if self.state != 'calculated':
            raise UserError('Solo se pueden recalcular deducciones en estado calculado.')

        Wizard = self.env['cm.liquidation.wizard']
        perc = Wizard._get_percepciones_sufridas(
            self.date_from, self.date_to, self.company_id.id
        )
        ret = Wizard._get_retenciones_sufridas(
            self.date_from, self.date_to, self.company_id.id
        )
        saldo = Wizard._get_saldo_anterior(self.period, self.company_id.id)

        for line in self.line_ids:
            jur_id = line.jurisdiction_id.id
            p_data = perc.get(jur_id, {})
            r_data = ret.get(jur_id, {})
            s_data = saldo.get(jur_id, {})
            line.write({
                'percepciones_sufridas': p_data.get('amount', 0.0),
                'percepciones_move_ids': [(6, 0, p_data.get('move_ids', []))],
                'retenciones_sufridas': r_data.get('amount', 0.0),
                'retenciones_payment_ids': [(6, 0, r_data.get('payment_ids', []))],
                'saldo_anterior': s_data.get('amount', 0.0),
                'prev_liquidation_id': s_data.get('liquidation_id', False),
            })

    _sql_constraints = [
        ('period_company_unique', 'unique(period, company_id)',
         'Ya existe una liquidacion para este periodo y empresa.'),
    ]


class CmLiquidationLine(models.Model):
    """Linea de liquidacion por jurisdiccion.

    // Por que: Cada jurisdiccion donde la empresa tiene actividad genera
    // una linea con base imponible distribuida por coeficiente, alicuota
    // aplicable y deducciones (retenciones/percepciones sufridas).
    """
    _name = 'cm.liquidation.line'
    _description = 'Linea Liquidacion CM'
    _order = 'jurisdiction_id'
    _inherit = ['mail.thread']

    liquidation_id = fields.Many2one(
        'cm.liquidation', string='Liquidacion', required=True,
        ondelete='cascade',
    )
    jurisdiction_id = fields.Many2one(
        'cm.jurisdiction', string='Jurisdiccion', required=True,
    )
    currency_id = fields.Many2one(
        'res.currency', related='liquidation_id.currency_id',
    )
    activity_id = fields.Many2one(
        'cm.activity', string='Actividad CUACM',
    )
    coefficient = fields.Float(
        string='Coeficiente', digits=(8, 4),
        help='CU aplicado a esta jurisdiccion',
    )

    # Bases
    base_gravada = fields.Float(string='Base Gravada Total', digits=(16, 2))
    base_no_gravada = fields.Float(string='Base No Gravada', digits=(16, 2))
    base_exenta = fields.Float(string='Base Exenta', digits=(16, 2))

    # // Por que: base_distribuida es la porcion del ingreso total que corresponde
    # a esta jurisdiccion segun el coeficiente unificado
    base_distribuida = fields.Float(
        string='Base Distribuida', digits=(16, 2),
        compute='_compute_impuesto', store=True,
    )
    alicuota = fields.Float(
        string='Alicuota %', digits=(6, 4),
    )
    impuesto_determinado = fields.Float(
        string='Impuesto Determinado', digits=(16, 2),
        compute='_compute_impuesto', store=True,
    )

    # Deducciones — tracking para audit trail en chatter
    retenciones_sufridas = fields.Float(
        string='Retenciones Sufridas', digits=(16, 2), tracking=True,
    )
    percepciones_sufridas = fields.Float(
        string='Percepciones Sufridas', digits=(16, 2), tracking=True,
    )
    recaudaciones_bancarias = fields.Float(
        string='Recaudaciones Bancarias', digits=(16, 2), tracking=True,
    )
    saldo_anterior = fields.Float(
        string='Saldo Periodo Anterior', digits=(16, 2), tracking=True,
    )
    total_deducciones = fields.Float(
        string='Total Deducciones', digits=(16, 2),
        compute='_compute_saldo', store=True,
    )
    saldo = fields.Float(
        string='Saldo', digits=(16, 2),
        compute='_compute_saldo', store=True,
    )

    # -- Trazabilidad (Fase 2) --
    # // Por que: Vincula cada deduccion con su documento origen para que
    # el contador pueda verificar de donde sale cada numero.
    percepciones_move_ids = fields.Many2many(
        'account.move', 'cm_liq_line_perc_move_rel',
        'line_id', 'move_id',
        string='Facturas Percepciones',
    )
    retenciones_payment_ids = fields.Many2many(
        'account.payment', 'cm_liq_line_ret_payment_rel',
        'line_id', 'payment_id',
        string='Cobros Retenciones',
    )
    prev_liquidation_id = fields.Many2one(
        'cm.liquidation', string='Liquidacion Anterior',
        help='Liquidacion de donde se arrastra el saldo a favor',
    )
    percepciones_count = fields.Integer(
        string='Cant. Percepciones', compute='_compute_trace_counts',
    )
    retenciones_count = fields.Integer(
        string='Cant. Retenciones', compute='_compute_trace_counts',
    )

    @api.depends('base_gravada', 'coefficient', 'alicuota')
    def _compute_impuesto(self):
        for line in self:
            line.base_distribuida = round(line.base_gravada * line.coefficient, 2)
            line.impuesto_determinado = round(
                line.base_distribuida * line.alicuota / 100, 2
            )

    @api.depends(
        'impuesto_determinado', 'retenciones_sufridas',
        'percepciones_sufridas', 'recaudaciones_bancarias', 'saldo_anterior',
    )
    def _compute_saldo(self):
        for line in self:
            line.total_deducciones = (
                line.retenciones_sufridas
                + line.percepciones_sufridas
                + line.recaudaciones_bancarias
                + line.saldo_anterior
            )
            # // Por que: Saldo positivo = a pagar, negativo = a favor
            line.saldo = line.impuesto_determinado - line.total_deducciones

    @api.depends('percepciones_move_ids', 'retenciones_payment_ids')
    def _compute_trace_counts(self):
        for line in self:
            line.percepciones_count = len(line.percepciones_move_ids)
            line.retenciones_count = len(line.retenciones_payment_ids)

    # -- Smart buttons (Fase 2) --

    def action_view_percepciones(self):
        """Abre facturas de compra origen de percepciones sufridas."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Percepciones Sufridas',
            'res_model': 'account.move',
            'domain': [('id', 'in', self.percepciones_move_ids.ids)],
            'view_mode': 'list,form',
        }

    def action_view_retenciones(self):
        """Abre cobros origen de retenciones sufridas."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Retenciones Sufridas',
            'res_model': 'account.payment',
            'domain': [('id', 'in', self.retenciones_payment_ids.ids)],
            'view_mode': 'list,form',
        }

    def action_view_prev_liquidation(self):
        """Abre la liquidacion anterior vinculada."""
        self.ensure_one()
        if not self.prev_liquidation_id:
            raise UserError('No hay liquidacion anterior vinculada.')
        return {
            'type': 'ir.actions.act_window',
            'name': 'Liquidacion Anterior',
            'res_model': 'cm.liquidation',
            'res_id': self.prev_liquidation_id.id,
            'view_mode': 'form',
        }

    def action_open_form(self):
        """Abre el formulario detallado de esta linea."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.jurisdiction_id.display_name,
            'res_model': 'cm.liquidation.line',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
