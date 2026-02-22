# -*- coding: utf-8 -*-

from odoo import models, fields


class CmNaes(models.Model):
    """Nomenclador de Actividades Económicas del Sistema Federal (NAES).

    // Por qué: Tabla de referencia con los ~1030 códigos NAES oficiales
    // de COMARB. Se pre-carga al instalar para que el usuario seleccione
    // de un dropdown en vez de tipear códigos manualmente.
    // Reemplaza al viejo CUACM desde 2018 (RG CA 7/2017).
    """
    _name = 'cm.naes'
    _description = 'Actividad NAES (Nomenclador COMARB)'
    _order = 'code'

    code = fields.Char(
        string='Código NAES', size=6, required=True, index=True,
    )
    name = fields.Char(string='Descripción', required=True)
    active = fields.Boolean(default=True)

    def name_get(self):
        # // Por qué: mostrar "[código] descripción" para búsqueda rápida
        return [(r.id, f"[{r.code}] {r.name}") for r in self]

    _sql_constraints = [
        ('code_unique', 'unique(code)', 'El código NAES debe ser único.'),
    ]
