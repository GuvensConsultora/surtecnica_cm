# -*- coding: utf-8 -*-

from odoo import models, fields


class CmJurisdiction(models.Model):
    """Jurisdicciones del Convenio Multilateral (códigos 901-924).

    // Por qué: COMARB asigna un código único (901-924) a cada provincia.
    // Se vincula con res.country.state de Odoo para resolver jurisdicción
    // automáticamente desde la dirección del partner.
    """
    _name = 'cm.jurisdiction'
    _description = 'Jurisdicción Convenio Multilateral'
    _order = 'code'

    code = fields.Char(
        string='Código CM', size=3, required=True, index=True,
        help='Código COMARB 901-924',
    )
    name = fields.Char(string='Provincia', required=True)
    state_id = fields.Many2one(
        'res.country.state', string='Provincia Odoo',
        domain="[('country_id.code', '=', 'AR')]",
        help='Vínculo con res.country.state para resolución automática',
    )
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('code_unique', 'unique(code)', 'El código CM debe ser único.'),
        ('state_unique', 'unique(state_id)', 'La provincia ya tiene una jurisdicción CM asignada.'),
    ]

    def name_get(self):
        return [(r.id, f"[{r.code}] {r.name}") for r in self]
