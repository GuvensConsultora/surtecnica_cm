# -*- coding: utf-8 -*-

from odoo import models, fields


class CmConfirmWizard(models.TransientModel):
    """Wizard de confirmacion con advertencias.

    // Por que: Muestra al contador las situaciones a revisar antes de
    // confirmar la liquidacion. Si acepta, confirma; si no, cancela
    // y puede corregir los datos.
    // Patron: TransientModel intermedio entre action_confirm y el cambio de estado.
    """
    _name = 'cm.confirm.wizard'
    _description = 'Confirmar Liquidacion CM'

    liquidation_id = fields.Many2one(
        'cm.liquidation', string='Liquidacion', required=True,
    )
    warnings_text = fields.Text(
        string='Advertencias', readonly=True,
    )

    def action_confirm_anyway(self):
        """Confirma la liquidacion a pesar de las advertencias."""
        self.ensure_one()
        self.liquidation_id.state = 'confirmed'
        return {'type': 'ir.actions.act_window_close'}
