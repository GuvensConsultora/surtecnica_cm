# -*- coding: utf-8 -*-

from odoo import models, fields


class ResCompany(models.Model):
    """Herencia res.company para agregar campos de Convenio Multilateral.

    // Por qué: La jurisdicción sede determina dónde tributa la empresa
    // como contribuyente directo (no por coeficiente).
    """
    _inherit = 'res.company'

    cm_sede_jurisdiction_id = fields.Many2one(
        'cm.jurisdiction', string='Jurisdicción Sede CM',
        help='Jurisdicción donde la empresa tiene su sede central',
    )
