# -*- coding: utf-8 -*-
{
    'name': 'Convenio Multilateral IIBB',
    'version': '1.0.0',
    'category': 'Accounting',
    'summary': 'Liquidación IIBB Convenio Multilateral con exportaciones SIRCAR/SIFERE/CM03/CM05',
    'description': """
        Gestión del Impuesto sobre los Ingresos Brutos bajo régimen de Convenio Multilateral.

        Funcionalidades:
        - Jurisdicciones CM (901-924) pre-cargadas
        - Actividades CUACM con alícuotas por jurisdicción
        - Coeficiente unificado por ejercicio fiscal
        - Liquidación mensual por jurisdicción
        - Exportación SIRCAR (percepciones practicadas)
        - Exportación SIFERE (retenciones/percepciones sufridas)
        - Exportación CM03 XML (DDJJ mensual)
        - Exportación CM05 Excel (coeficiente anual)
    """,
    'author': 'Surtecnica',
    'website': '',
    # Por qué: l10n_ar provee estructura fiscal argentina (CUIT, doc types)
    # l10n_ar_withholding provee retenciones/percepciones IIBB nativas
    'depends': ['account', 'l10n_ar'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/cm_jurisdiction_data.xml',
        'views/cm_jurisdiction_views.xml',
        'views/cm_activity_views.xml',
        'views/cm_coefficient_views.xml',
        'views/cm_liquidation_views.xml',
        'views/res_company_views.xml',
        'views/account_move_views.xml',
        'wizard/cm_coefficient_wizard_views.xml',
        'wizard/cm_liquidation_wizard_views.xml',
        'wizard/cm_sircar_wizard_views.xml',
        'wizard/cm_sifere_wizard_views.xml',
        'wizard/cm_cm03_wizard_views.xml',
        'wizard/cm_cm05_wizard_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
