# -*- coding: utf-8 -*-

from odoo import models, fields


class CmActivity(models.Model):
    """Actividad NAES por jurisdicción.

    // Por qué: Cada jurisdicción puede tener distintas actividades con
    // alícuotas diferentes. El NAES (Nomenclador de Actividades Económicas
    // del Sistema Federal) reemplaza al CUACM desde 2018 (RG CA 7/2017).
    """
    _name = 'cm.activity'
    _description = 'Actividad NAES por Jurisdicción'
    _order = 'jurisdiction_id, naes_id'

    company_id = fields.Many2one(
        'res.company', string='Empresa', required=True,
        default=lambda self: self.env.company,
    )
    jurisdiction_id = fields.Many2one(
        'cm.jurisdiction', string='Jurisdicción', required=True,
        ondelete='restrict',
    )
    # // Por qué: Many2one a cm.naes permite seleccionar de un dropdown
    # // con los ~1030 códigos pre-cargados en vez de tipear manualmente
    naes_id = fields.Many2one(
        'cm.naes', string='Actividad NAES', required=True,
        ondelete='restrict',
        help='Actividad del Nomenclador NAES (ex-CUACM)',
    )
    alicuota = fields.Float(
        string='Alícuota %', digits=(6, 4), required=True,
        help='Tasa IIBB para esta actividad en esta jurisdicción',
    )
    # // Por qué: El art. del régimen determina reglas especiales de distribución
    art_regimen = fields.Selection([
        ('art2', 'Art. 2 - Régimen General'),
        ('art6', 'Art. 6 - Construcción'),
        ('art7', 'Art. 7 - Seguros'),
        ('art8', 'Art. 8 - Entidades Financieras'),
        ('art9', 'Art. 9 - Transporte'),
        ('art10', 'Art. 10 - Profesiones Liberales'),
        ('art11', 'Art. 11 - Comisionistas'),
        ('art12', 'Art. 12 - Tabaco'),
        ('art13', 'Art. 13 - Actividades Especiales'),
    ], string='Régimen', default='art2', required=True)
    date_from = fields.Date(string='Vigencia Desde')
    date_to = fields.Date(string='Vigencia Hasta')

    _sql_constraints = [
        ('activity_unique', 'unique(company_id, jurisdiction_id, naes_id)',
         'Ya existe esta actividad NAES en esta jurisdicción para esta empresa.'),
    ]
