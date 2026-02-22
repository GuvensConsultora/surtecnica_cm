# -*- coding: utf-8 -*-

from odoo import models, fields, api


class CmActivity(models.Model):
    """Actividad CUACM por jurisdicción.

    // Por qué: Cada jurisdicción puede tener distintas actividades con
    // alícuotas diferentes. El CUACM (Código Único de Actividad CM)
    // es el nomenclador oficial de COMARB.
    """
    _name = 'cm.activity'
    _description = 'Actividad CUACM por Jurisdicción'
    _order = 'jurisdiction_id, cuacm_code'

    company_id = fields.Many2one(
        'res.company', string='Empresa', required=True,
        default=lambda self: self.env.company,
    )
    jurisdiction_id = fields.Many2one(
        'cm.jurisdiction', string='Jurisdicción', required=True,
        ondelete='restrict',
    )
    cuacm_code = fields.Char(
        string='Código CUACM', size=10, required=True,
        help='Código Único de Actividad del Convenio Multilateral',
    )
    name = fields.Char(string='Descripción Actividad', required=True)
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
        ('activity_unique', 'unique(company_id, jurisdiction_id, cuacm_code)',
         'Ya existe esta actividad CUACM en esta jurisdicción para esta empresa.'),
    ]
