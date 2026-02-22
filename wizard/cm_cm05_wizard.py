# -*- coding: utf-8 -*-

import base64
import io
import zipfile
from datetime import date

from odoo import models, fields
from odoo.exceptions import UserError

# // Por qué: openpyxl puede no estar instalado en todos los entornos.
# Se importa dentro del método para dar error claro al usuario.


class CmCm05Wizard(models.TransientModel):
    """Exportación CM05 — Coeficiente Anual Excel.

    // Por qué: El CM05 es la declaración jurada anual del Convenio
    // Multilateral donde se determinan los coeficientes unificados.
    // Se exporta en Excel con 2 hojas: detalle mensual + determinación.
    """
    _name = 'cm.cm05.wizard'
    _description = 'Exportar CM05 Excel'

    fiscal_year = fields.Char(
        string='Ejercicio Fiscal', size=4, required=True,
        default=lambda self: str(date.today().year),
    )
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('done', 'Generado'),
    ], default='draft')
    file_data = fields.Binary(string='Archivo CM05')
    file_name = fields.Char(string='Nombre Archivo')

    def action_generate(self):
        """Genera archivo Excel CM05 con coeficientes del ejercicio."""
        self.ensure_one()
        try:
            import openpyxl
            from openpyxl.styles import Font, Alignment, Border, Side
        except ImportError:
            raise UserError(
                'Se requiere la librería openpyxl para generar Excel. '
                'Instalar con: pip install openpyxl'
            )

        company = self.env.company

        coefficients = self.env['cm.coefficient'].search([
            ('fiscal_year', '=', self.fiscal_year),
            ('company_id', '=', company.id),
        ], order='jurisdiction_id')

        if not coefficients:
            raise UserError(
                f'No hay coeficientes cargados para el ejercicio {self.fiscal_year}.'
            )

        wb = openpyxl.Workbook()

        # --- Hoja 1: Determinación del Coeficiente ---
        ws1 = wb.active
        ws1.title = 'Determinación CU'

        # Estilos
        header_font = Font(bold=True, size=12)
        col_font = Font(bold=True, size=10)
        border = Border(
            bottom=Side(style='thin'),
            top=Side(style='thin'),
            left=Side(style='thin'),
            right=Side(style='thin'),
        )

        # Encabezado
        ws1.merge_cells('A1:I1')
        ws1['A1'] = f'CM05 - Determinación Coeficiente Unificado - Ejercicio {self.fiscal_year}'
        ws1['A1'].font = header_font
        ws1['A2'] = f'Empresa: {company.name}'
        ws1['A3'] = f'CUIT: {company.vat or ""}'

        # Columnas
        headers = [
            'Jurisdicción', 'Código',
            'Ingresos Jur.', 'Ingresos Total', 'Coef. Ingresos',
            'Gastos Jur.', 'Gastos Total', 'Coef. Gastos',
            'Coef. Unificado',
        ]
        for col, h in enumerate(headers, 1):
            cell = ws1.cell(row=5, column=col, value=h)
            cell.font = col_font
            cell.border = border
            cell.alignment = Alignment(horizontal='center')

        # Datos
        for row, coeff in enumerate(coefficients, 6):
            ws1.cell(row=row, column=1, value=coeff.jurisdiction_id.name)
            ws1.cell(row=row, column=2, value=coeff.jurisdiction_id.code)
            ws1.cell(row=row, column=3, value=coeff.income_amount)
            ws1.cell(row=row, column=4, value=coeff.income_total)
            ws1.cell(row=row, column=5, value=coeff.income_ratio)
            ws1.cell(row=row, column=6, value=coeff.expense_amount)
            ws1.cell(row=row, column=7, value=coeff.expense_total)
            ws1.cell(row=row, column=8, value=coeff.expense_ratio)
            cell_cu = ws1.cell(row=row, column=9, value=coeff.coefficient)
            cell_cu.font = Font(bold=True)
            # Aplicar bordes
            for c in range(1, 10):
                ws1.cell(row=row, column=c).border = border

        # Totales
        total_row = 6 + len(coefficients)
        ws1.cell(row=total_row, column=1, value='TOTALES').font = col_font
        ws1.cell(row=total_row, column=5, value=sum(c.income_ratio for c in coefficients))
        ws1.cell(row=total_row, column=8, value=sum(c.expense_ratio for c in coefficients))
        ws1.cell(row=total_row, column=9, value=sum(c.coefficient for c in coefficients))

        # Ajustar anchos
        ws1.column_dimensions['A'].width = 25
        for col_letter in ['C', 'D', 'F', 'G']:
            ws1.column_dimensions[col_letter].width = 18
        for col_letter in ['E', 'H', 'I']:
            ws1.column_dimensions[col_letter].width = 15

        # --- Hoja 2: Detalle Mensual ---
        ws2 = wb.create_sheet('Detalle Mensual')
        ws2.merge_cells('A1:D1')
        ws2['A1'] = f'Detalle de Ingresos y Gastos Mensuales - {self.fiscal_year}'
        ws2['A1'].font = header_font

        # // Por qué: El detalle mensual muestra liquidaciones del ejercicio
        # para verificar la composición de los ingresos/gastos.
        liquidations = self.env['cm.liquidation'].search([
            ('fiscal_year', '=', self.fiscal_year),
            ('company_id', '=', company.id),
        ], order='period')

        detail_headers = ['Período', 'Jurisdicción', 'Base Gravada', 'Impuesto Det.', 'Saldo']
        for col, h in enumerate(detail_headers, 1):
            cell = ws2.cell(row=3, column=col, value=h)
            cell.font = col_font
            cell.border = border

        row = 4
        for liq in liquidations:
            for line in liq.line_ids:
                ws2.cell(row=row, column=1, value=liq.period)
                ws2.cell(row=row, column=2, value=line.jurisdiction_id.name)
                ws2.cell(row=row, column=3, value=line.base_gravada)
                ws2.cell(row=row, column=4, value=line.impuesto_determinado)
                ws2.cell(row=row, column=5, value=line.saldo)
                for c in range(1, 6):
                    ws2.cell(row=row, column=c).border = border
                row += 1

        ws2.column_dimensions['A'].width = 12
        ws2.column_dimensions['B'].width = 25
        for col_letter in ['C', 'D', 'E']:
            ws2.column_dimensions[col_letter].width = 18

        # Guardar en buffer
        buf = io.BytesIO()
        wb.save(buf)
        buf.seek(0)

        cuit = self._clean_cuit(company.vat)
        self.file_data = base64.b64encode(buf.read())
        self.file_name = f'CM05_{self.fiscal_year}_{cuit}.xlsx'
        self.state = 'done'

        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_download(self):
        """Descarga CM05 como ZIP."""
        self.ensure_one()
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.writestr(self.file_name, base64.b64decode(self.file_data))
        buf.seek(0)

        zip_name = self.file_name.replace('.xlsx', '.zip')
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
