# -*- coding: utf-8 -*-

import base64
import io
import zipfile
from xml.etree import ElementTree as ET

from odoo import models, fields
from odoo.exceptions import UserError


class CmCm03Wizard(models.TransientModel):
    """Exportación CM03 — DDJJ Mensual XML.

    // Por qué: El formulario CM03 es la declaración jurada mensual del
    // Convenio Multilateral. Se presenta ante COMARB en formato XML.
    // Estructura: <CM03><Encabezado> + <Jurisdiccion> por cada línea.
    """
    _name = 'cm.cm03.wizard'
    _description = 'Exportar CM03 XML'

    liquidation_id = fields.Many2one(
        'cm.liquidation', string='Liquidación', required=True,
        domain="[('state', '=', 'confirmed')]",
        help='Liquidación confirmada a exportar',
    )
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('done', 'Generado'),
    ], default='draft')
    file_data = fields.Binary(string='Archivo CM03')
    file_name = fields.Char(string='Nombre Archivo')

    def action_generate(self):
        """Genera archivo XML CM03 desde la liquidación seleccionada."""
        self.ensure_one()
        liq = self.liquidation_id

        if liq.state != 'confirmed':
            raise UserError('La liquidación debe estar confirmada.')

        company = liq.company_id
        cuit = self._clean_cuit(company.vat)

        # Construir XML
        root = ET.Element('CM03')

        # Encabezado
        enc = ET.SubElement(root, 'Encabezado')
        ET.SubElement(enc, 'CUIT').text = cuit
        ET.SubElement(enc, 'Periodo').text = liq.period.replace('/', '')  # AAAAMM
        ET.SubElement(enc, 'RazonSocial').text = company.name or ''
        ET.SubElement(enc, 'FechaDesde').text = liq.date_from.strftime('%Y-%m-%d')
        ET.SubElement(enc, 'FechaHasta').text = liq.date_to.strftime('%Y-%m-%d')
        ET.SubElement(enc, 'TotalBaseImponible').text = f'{liq.total_base_gravada:.2f}'
        ET.SubElement(enc, 'TotalImpuestoDeterminado').text = f'{liq.total_impuesto:.2f}'
        ET.SubElement(enc, 'TotalDeducciones').text = f'{liq.total_deducciones:.2f}'
        ET.SubElement(enc, 'TotalSaldo').text = f'{liq.total_saldo:.2f}'

        # // Por qué: Sede se informa en el encabezado
        sede = company.cm_sede_jurisdiction_id
        if sede:
            ET.SubElement(enc, 'JurisdiccionSede').text = sede.code

        # Jurisdicciones (una por línea de liquidación)
        jurisdicciones = ET.SubElement(root, 'Jurisdicciones')
        for line in liq.line_ids:
            jur_elem = ET.SubElement(jurisdicciones, 'Jurisdiccion')
            ET.SubElement(jur_elem, 'Codigo').text = line.jurisdiction_id.code
            ET.SubElement(jur_elem, 'Nombre').text = line.jurisdiction_id.name
            if line.activity_id:
                ET.SubElement(jur_elem, 'CodigoCUACM').text = line.activity_id.cuacm_code
            ET.SubElement(jur_elem, 'Coeficiente').text = f'{line.coefficient:.4f}'
            ET.SubElement(jur_elem, 'BaseGravada').text = f'{line.base_gravada:.2f}'
            ET.SubElement(jur_elem, 'BaseDistribuida').text = f'{line.base_distribuida:.2f}'
            ET.SubElement(jur_elem, 'Alicuota').text = f'{line.alicuota:.4f}'
            ET.SubElement(jur_elem, 'ImpuestoDeterminado').text = f'{line.impuesto_determinado:.2f}'
            ET.SubElement(jur_elem, 'RetencionesSufridas').text = f'{line.retenciones_sufridas:.2f}'
            ET.SubElement(jur_elem, 'PercepcionesSufridas').text = f'{line.percepciones_sufridas:.2f}'
            ET.SubElement(jur_elem, 'RecaudacionesBancarias').text = f'{line.recaudaciones_bancarias:.2f}'
            ET.SubElement(jur_elem, 'SaldoAnterior').text = f'{line.saldo_anterior:.2f}'
            ET.SubElement(jur_elem, 'Saldo').text = f'{line.saldo:.2f}'

        # Serializar XML
        # // Por qué: encoding='unicode' genera string sin declaración XML,
        # luego la agregamos manualmente para control.
        xml_str = '<?xml version="1.0" encoding="UTF-8"?>\n'
        xml_str += ET.tostring(root, encoding='unicode')

        self.file_data = base64.b64encode(xml_str.encode('utf-8'))
        self.file_name = f'CM03_{liq.period.replace("/", "")}_{cuit}.xml'
        self.state = 'done'

        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_download(self):
        """Descarga CM03 como ZIP."""
        self.ensure_one()
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.writestr(self.file_name, base64.b64decode(self.file_data))
        buf.seek(0)

        zip_name = self.file_name.replace('.xml', '.zip')
        attachment = self.env['ir.attachment'].create({
            'name': zip_name,
            'type': 'binary',
            'datas': base64.b64encode(buf.read()),
            'mimetype': 'application/zip',
        })
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }

    def _clean_cuit(self, vat):
        if not vat:
            return '00000000000'
        return ''.join(c for c in str(vat) if c.isdigit()).zfill(11)
