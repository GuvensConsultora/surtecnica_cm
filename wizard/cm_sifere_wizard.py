# -*- coding: utf-8 -*-

import base64
import io
import zipfile
from datetime import date

from odoo import models, fields
from odoo.exceptions import UserError


class CmSifereWizard(models.TransientModel):
    """Exportación SIFERE — Retenciones/Percepciones sufridas.

    // Por qué: SIFERE (Sistema Federal de Recaudación) requiere un TXT
    // con las retenciones y percepciones que la empresa sufrió como
    // contribuyente, para computar como crédito fiscal en la liquidación CM.
    // Formato: TXT posición fija (sin separadores), distinto largo según tipo.
    """
    _name = 'cm.sifere.wizard'
    _description = 'Exportar SIFERE'

    date_from = fields.Date(
        string='Desde', required=True,
        default=lambda self: date.today().replace(day=1),
    )
    date_to = fields.Date(string='Hasta', required=True, default=fields.Date.today)
    export_type = fields.Selection([
        ('percepciones', 'Percepciones Sufridas'),
        ('retenciones', 'Retenciones Sufridas'),
    ], string='Tipo', default='percepciones', required=True)
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('done', 'Generado'),
    ], default='draft')
    file_data = fields.Binary(string='Archivo SIFERE')
    file_name = fields.Char(string='Nombre Archivo')
    records_count = fields.Integer(string='Registros Generados')

    def action_generate(self):
        """Genera archivo TXT SIFERE."""
        self.ensure_one()

        if self.date_from > self.date_to:
            raise UserError('La fecha desde debe ser anterior a la fecha hasta.')

        if self.export_type == 'percepciones':
            lines = self._generate_percepciones()
        else:
            lines = self._generate_retenciones()

        if not lines:
            raise UserError('No se encontraron registros en el período.')

        content = '\r\n'.join(lines)
        self.file_data = base64.b64encode(content.encode('latin-1', errors='replace'))
        self.file_name = f'SIFERE_{self.export_type.upper()}_{self.date_from.strftime("%Y%m")}.txt'
        self.records_count = len(lines)
        self.state = 'done'

        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def _generate_percepciones(self):
        """Genera líneas de percepciones sufridas (facturas de compra).

        // Por qué: Formato posición fija, 8 campos, sin separadores.
        // Campos: jurisdicción(3) + cuit(13) + fecha(10) + sucursal(4) +
        //         nro_cbte(8) + tipo(1) + letra(1) + monto(11)
        // Total: 51 caracteres por línea.
        """
        # Percepciones sufridas = tax lines IIBB en facturas de compra
        tax_lines = self.env['account.move.line'].search([
            ('move_id.state', '=', 'posted'),
            ('move_id.move_type', 'in', ('in_invoice', 'in_refund')),
            ('move_id.invoice_date', '>=', self.date_from),
            ('move_id.invoice_date', '<=', self.date_to),
            ('tax_line_id', '!=', False),
            ('tax_line_id.l10n_ar_tribute_afip_code', '=', '07'),
        ], order='move_id')

        lines = []
        for tl in tax_lines:
            move = tl.move_id
            jur = move.cm_jurisdiction_id
            jur_code = jur.code if jur else '900'

            cuit = self._fmt_cuit(move.partner_id.vat)
            fecha = move.invoice_date.strftime('%d/%m/%Y')
            sucursal, nro_emision = self._parse_cbte_number(move)

            # // Por qué: SIFERE percepciones usa tipo F/C/D y letra A/B/C
            tipo = 'C' if move.move_type == 'in_refund' else 'F'
            letra = self._get_letra(move)
            monto = self._fmt_amount(abs(tl.amount_currency), 11)

            # Concatenar sin separadores (posición fija)
            line = (
                jur_code.ljust(3)       # 1. Jurisdicción (3)
                + cuit                  # 2. CUIT (13, con guiones)
                + fecha                 # 3. Fecha (10)
                + sucursal              # 4. Sucursal (4)
                + nro_emision           # 5. Nro emisión (8)
                + tipo                  # 6. Tipo (1)
                + letra                 # 7. Letra (1)
                + monto                 # 8. Monto (11)
            )
            lines.append(line)

        return lines

    def _generate_retenciones(self):
        """Genera líneas de retenciones sufridas (pagos recibidos).

        // Por qué: Formato posición fija, 9 campos (agrega nro_constancia).
        // Campos: jurisdicción(3) + cuit(13) + fecha(10) + sucursal(4) +
        //         nro_cbte(8) + tipo(1) + letra(1) + nro_constancia(16) + monto(11)
        // Total: 67 caracteres por línea.
        """
        # // Por qué: Retenciones sufridas se buscan en pagos de clientes (inbound)
        # que tengan withholding de IIBB
        payments = self.env['account.payment'].search([
            ('state', '=', 'posted'),
            ('payment_type', '=', 'inbound'),
            ('date', '>=', self.date_from),
            ('date', '<=', self.date_to),
        ])

        lines = []
        for payment in payments:
            # // Por qué: Buscar si el pago tiene líneas de retención IIBB
            ret_lines = payment.move_id.line_ids.filtered(
                lambda l: l.tax_line_id and
                l.tax_line_id.l10n_ar_tribute_afip_code == '07'
            )
            for rl in ret_lines:
                jur = payment.move_id.cm_jurisdiction_id
                jur_code = jur.code if jur else '900'
                cuit = self._fmt_cuit(payment.partner_id.vat)
                fecha = payment.date.strftime('%d/%m/%Y')

                # Para retenciones el comprobante es el del pago
                sucursal = '0001'
                nro_emision = str(payment.name or '').replace('-', '').zfill(8)[-8:]

                tipo = 'R'  # Recibo de retención
                letra = ' '
                nro_constancia = str(payment.name or '').zfill(16)[-16:]
                monto = self._fmt_amount(abs(rl.amount_currency), 11)

                line = (
                    jur_code.ljust(3)       # 1. Jurisdicción (3)
                    + cuit                  # 2. CUIT (13)
                    + fecha                 # 3. Fecha (10)
                    + sucursal              # 4. Sucursal (4)
                    + nro_emision           # 5. Nro emisión (8)
                    + tipo                  # 6. Tipo (1)
                    + letra                 # 7. Letra (1)
                    + nro_constancia        # 8. Nro constancia (16)
                    + monto                 # 9. Monto (11)
                )
                lines.append(line)

        return lines

    def action_download(self):
        """Descarga archivo SIFERE como ZIP."""
        self.ensure_one()
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.writestr(self.file_name, base64.b64decode(self.file_data))
        buf.seek(0)

        zip_name = f'SIFERE_{self.date_from.strftime("%Y%m")}.zip'
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

    def _fmt_cuit(self, vat):
        """Formatea CUIT con guiones: XX-XXXXXXXX-X (13 chars)."""
        digits = ''.join(c for c in str(vat or '') if c.isdigit()).zfill(11)
        return f'{digits[:2]}-{digits[2:10]}-{digits[10]}'

    def _fmt_amount(self, amount, length):
        """Formatea importe: enteros + '.' + 2 decimales, rellenando con ceros.

        // Por qué: SIFERE usa formato numérico con punto decimal.
        // Ej para length=11: 8 enteros + '.' + 2 decimales = 11 chars.
        """
        int_len = length - 3  # restar punto y 2 decimales
        cents = round(amount, 2)
        int_part = int(cents)
        dec_part = int(round((cents - int_part) * 100))
        return f'{str(int_part).zfill(int_len)}.{str(dec_part).zfill(2)}'

    def _get_letra(self, move):
        """Obtiene letra del comprobante."""
        doc_type = move.l10n_latam_document_type_id
        if doc_type and doc_type.doc_code_prefix:
            parts = doc_type.doc_code_prefix.split('-')
            if len(parts) >= 2:
                return parts[-1][:1]
        return ' '

    def _parse_cbte_number(self, move):
        """Parsea número de comprobante de move.name.

        // Por qué: move.name formato "FA-A 0001-00000020"
        // Retorna (sucursal 4 chars, emisión 8 chars).
        """
        if move.name:
            parts = move.name.split(' ')
            if len(parts) >= 2:
                num_parts = parts[-1].split('-')
                if len(num_parts) >= 2:
                    return (
                        num_parts[0].zfill(4)[-4:],
                        num_parts[1].zfill(8)[-8:],
                    )
        return ('0001', '00000000')
