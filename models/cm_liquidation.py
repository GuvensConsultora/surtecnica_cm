# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError


class CmLiquidation(models.Model):
    """Liquidación mensual Convenio Multilateral.

    // Por qué: Agrupa las líneas por jurisdicción para un período.
    // El flujo es draft → calculated (wizard genera líneas) → confirmed (usuario valida).
    """
    _name = 'cm.liquidation'
    _description = 'Liquidación CM Mensual'
    _order = 'period desc'
    _inherit = ['mail.thread']

    name = fields.Char(
        string='Referencia', compute='_compute_name', store=True,
    )
    company_id = fields.Many2one(
        'res.company', string='Empresa', required=True,
        default=lambda self: self.env.company,
    )
    period = fields.Char(
        string='Período', size=7, required=True,
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
        string='Líneas por Jurisdicción',
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

    def action_confirm(self):
        """Confirmar liquidación calculada."""
        for rec in self:
            if rec.state != 'calculated':
                raise UserError('Solo se pueden confirmar liquidaciones calculadas.')
            rec.state = 'confirmed'

    def action_draft(self):
        """Volver a borrador."""
        for rec in self:
            if rec.state != 'calculated':
                raise UserError('Solo se pueden pasar a borrador liquidaciones calculadas.')
            rec.line_ids.unlink()
            rec.state = 'draft'

    _sql_constraints = [
        ('period_company_unique', 'unique(period, company_id)',
         'Ya existe una liquidación para este período y empresa.'),
    ]


class CmLiquidationLine(models.Model):
    """Línea de liquidación por jurisdicción.

    // Por qué: Cada jurisdicción donde la empresa tiene actividad genera
    // una línea con base imponible distribuida por coeficiente, alícuota
    // aplicable y deducciones (retenciones/percepciones sufridas).
    """
    _name = 'cm.liquidation.line'
    _description = 'Línea Liquidación CM'
    _order = 'jurisdiction_id'

    liquidation_id = fields.Many2one(
        'cm.liquidation', string='Liquidación', required=True,
        ondelete='cascade',
    )
    jurisdiction_id = fields.Many2one(
        'cm.jurisdiction', string='Jurisdicción', required=True,
    )
    activity_id = fields.Many2one(
        'cm.activity', string='Actividad CUACM',
    )
    coefficient = fields.Float(
        string='Coeficiente', digits=(8, 4),
        help='CU aplicado a esta jurisdicción',
    )

    # Bases
    base_gravada = fields.Float(string='Base Gravada Total', digits=(16, 2))
    base_no_gravada = fields.Float(string='Base No Gravada', digits=(16, 2))
    base_exenta = fields.Float(string='Base Exenta', digits=(16, 2))

    # // Por qué: base_distribuida es la porción del ingreso total que corresponde
    # a esta jurisdicción según el coeficiente unificado
    base_distribuida = fields.Float(
        string='Base Distribuida', digits=(16, 2),
        compute='_compute_impuesto', store=True,
    )
    alicuota = fields.Float(
        string='Alícuota %', digits=(6, 4),
    )
    impuesto_determinado = fields.Float(
        string='Impuesto Determinado', digits=(16, 2),
        compute='_compute_impuesto', store=True,
    )

    # Deducciones
    retenciones_sufridas = fields.Float(
        string='Retenciones Sufridas', digits=(16, 2),
    )
    percepciones_sufridas = fields.Float(
        string='Percepciones Sufridas', digits=(16, 2),
    )
    recaudaciones_bancarias = fields.Float(
        string='Recaudaciones Bancarias', digits=(16, 2),
    )
    saldo_anterior = fields.Float(
        string='Saldo Período Anterior', digits=(16, 2),
    )
    total_deducciones = fields.Float(
        string='Total Deducciones', digits=(16, 2),
        compute='_compute_saldo', store=True,
    )
    saldo = fields.Float(
        string='Saldo', digits=(16, 2),
        compute='_compute_saldo', store=True,
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
            # // Por qué: Saldo positivo = a pagar, negativo = a favor
            line.saldo = line.impuesto_determinado - line.total_deducciones
