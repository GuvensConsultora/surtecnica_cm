# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AccountMove(models.Model):
    """Herencia account.move para agregar jurisdicción CM.

    // Por qué: Cada factura debe asociarse a una jurisdicción CM para poder
    // distribuir la base imponible en la liquidación mensual.
    // Se resuelve automáticamente desde la dirección de envío o del partner.
    """
    _inherit = 'account.move'

    cm_jurisdiction_id = fields.Many2one(
        'cm.jurisdiction', string='Jurisdicción CM',
        compute='_compute_cm_jurisdiction_id', store=True, readonly=False,
        help='Jurisdicción CM determinada por la provincia del cliente/proveedor',
    )

    @api.depends('partner_shipping_id', 'partner_shipping_id.state_id',
                 'partner_id', 'partner_id.state_id')
    def _compute_cm_jurisdiction_id(self):
        """Resuelve jurisdicción CM desde provincia del partner.

        // Por qué: Prioriza partner_shipping_id (dirección de entrega) sobre
        // partner_id porque el lugar de entrega determina la jurisdicción
        // donde se genera el ingreso (criterio CM).
        """
        Jurisdiction = self.env['cm.jurisdiction']
        # // Tip: Cache de búsqueda para evitar N+1 queries
        cache = {}
        for move in self:
            state = (
                move.partner_shipping_id.state_id
                or move.partner_id.state_id
            )
            if not state:
                move.cm_jurisdiction_id = False
                continue
            if state.id not in cache:
                cache[state.id] = Jurisdiction.search(
                    [('state_id', '=', state.id)], limit=1
                )
            move.cm_jurisdiction_id = cache[state.id]
