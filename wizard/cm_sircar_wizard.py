# -*- coding: utf-8 -*-

import base64
import io
import zipfile
from datetime import date

from odoo import models, fields
from odoo.exceptions import UserError

# // Por qué: Mapeo de tipo de comprobante Odoo → código SIRCAR
# SIRCAR usa: 1=Factura, 2=ND, 3=NC, 4=Recibo
SIRCAR_TIPO_CBTE = {
    'out_invoice': '1',
    'out_refund': '3',
}


class CmSircarWizard(models.TransientModel):
    """Exportación SIRCAR — Percepciones practicadas.

    // Por qué: SIRCAR (Sistema de Recaudación y Control de Agentes de
    // Recaudación) requiere un CSV con las percepciones practicadas
    // a terceros, para informar a cada jurisdicción.
    // Formato: CSV separado por comas, 11 campos por línea.
    """
    _name = 'cm.sircar.wizard'
    _description = 'Exportar SIRCAR'

    date_from = fields.Date(
        string='Desde', required=True,
        default=lambda self: date.today().replace(day=1),
    )
    date_to = fields.Date(string='Hasta', required=True, default=fields.Date.today)
    jurisdiction_id = fields.Many2one(
        'cm.jurisdiction', string='Jurisdicción',
        help='Filtrar por jurisdicción (vacío = todas)',
    )
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('done', 'Generado'),
    ], default='draft')
    file_data = fields.Binary(string='Archivo SIRCAR')
    file_name = fields.Char(string='Nombre Archivo')
    records_count = fields.Integer(string='Registros Generados')

    def action_generate(self):
        """Genera archivo CSV SIRCAR con percepciones del período."""
        self.ensure_one()

        if self.date_from > self.date_to:
            raise UserError('La fecha desde debe ser anterior a la fecha hasta.')

        # // Por qué: Buscar tax lines que sean percepciones IIBB del período
        # Las percepciones IIBB tienen l10n_ar_tribute_afip_code = '07'
        domain = [
            ('move_id.state', '=', 'posted'),
            ('move_id.move_type', 'in', ('out_invoice', 'out_refund')),
            ('move_id.invoice_date', '>=', self.date_from),
            ('move_id.invoice_date', '<=', self.date_to),
            ('tax_line_id', '!=', False),
            ('tax_line_id.l10n_ar_tribute_afip_code', '=', '07'),
        ]
        if self.jurisdiction_id:
            domain.append(
                ('move_id.cm_jurisdiction_id', '=', self.jurisdiction_id.id)
            )

        tax_lines = self.env['account.move.line'].search(domain, order='move_id')

        if not tax_lines:
            raise UserError('No se encontraron percepciones IIBB en el período.')

        lines = []
        nro = 0
        for tl in tax_lines:
            move = tl.move_id
            nro += 1

            # Extraer datos del comprobante
            cuit = self._clean_cuit(move.partner_id.vat)
            fecha = move.invoice_date.strftime('%d/%m/%Y')
            tipo_cbte = SIRCAR_TIPO_CBTE.get(move.move_type, '1')
            letra = self._get_letra(move)
            nro_cbte = self._get_nro_cbte(move)
            jurisdiction = move.cm_jurisdiction_id

            # // Por qué: monto_sujeto es la base imponible de la percepción
            monto_sujeto = abs(tl.tax_base_amount)
            alicuota = abs(tl.tax_line_id.amount) if tl.tax_line_id else 0.0
            monto_percibido = abs(tl.amount_currency)

            # Tipo régimen: 1 = Régimen General
            tipo_regimen = '1'
            jur_code = jurisdiction.code if jurisdiction else '900'

            # // Por qué: SIRCAR usa CSV con 11 campos separados por coma
            line = ','.join([
                str(nro),                               # 1. Nro renglón
                tipo_cbte,                              # 2. Tipo comprobante
                letra,                                  # 3. Letra
                nro_cbte,                               # 4. Nro comprobante
                cuit,                                   # 5. CUIT percibido
                fecha,                                  # 6. Fecha
                f'{monto_sujeto:.2f}',                  # 7. Monto sujeto
                f'{alicuota:.2f}',                      # 8. Alícuota
                f'{monto_percibido:.2f}',               # 9. Monto percibido
                tipo_regimen,                           # 10. Tipo régimen
                jur_code,                               # 11. Jurisdicción
            ])
            lines.append(line)

        content = '\r\n'.join(lines)
        self.file_data = base64.b64encode(content.encode('latin-1', errors='replace'))
        self.file_name = f'SIRCAR_{self.date_from.strftime("%Y%m")}.csv'
        self.records_count = len(lines)
        self.state = 'done'

        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_download(self):
        """Descarga archivo SIRCAR como ZIP."""
        self.ensure_one()
        return self._download_zip(
            self.file_data, self.file_name,
            f'SIRCAR_{self.date_from.strftime("%Y%m")}.zip'
        )

    def _download_zip(self, file_data, file_name, zip_name):
        """Crea ZIP y retorna acción de descarga.

        // Patrón: Mismo patrón que surtecnica_arca para descarga de archivos.
        """
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.writestr(file_name, base64.b64decode(file_data))
        buf.seek(0)

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
        """Extrae 11 dígitos del CUIT."""
        if not vat:
            return '00000000000'
        return ''.join(c for c in str(vat) if c.isdigit()).zfill(11)

    def _get_letra(self, move):
        """Obtiene letra del comprobante (A, B, C, etc.)."""
        doc_type = move.l10n_latam_document_type_id
        if doc_type and doc_type.doc_code_prefix:
            prefix = doc_type.doc_code_prefix
            # // Por qué: El prefix tiene formato "FA-A", "NC-B", etc.
            # La letra es el último carácter
            parts = prefix.split('-')
            if len(parts) >= 2:
                return parts[-1][:1]
        return ' '

    def _get_nro_cbte(self, move):
        """Obtiene número de comprobante completo (sucursal-número)."""
        if move.name:
            # // Por qué: move.name formato "FA-A 0001-00000020"
            parts = move.name.split(' ')
            if len(parts) >= 2:
                return parts[-1]  # "0001-00000020"
        return '0000-00000000'
