# Convenio Multilateral IIBB — `surtecnica_cm`

## Bloque 1: Introducción

### Qué hace Odoo nativamente

Odoo 19 con localización argentina (`l10n_ar`, `l10n_ar_withholding`) gestiona retenciones y percepciones de IIBB en pagos y cobros. Permite configurar tasas de retención por jurisdicción y aplicarlas automáticamente en el circuito de pagos.

### Qué limitación existe

Odoo **no contempla** el régimen de Convenio Multilateral (CM). Empresas que operan en más de una provincia necesitan:

- Distribuir sus ingresos entre jurisdicciones según un **coeficiente unificado** (CU)
- Liquidar IIBB mensualmente por cada jurisdicción donde tienen actividad
- Presentar declaraciones juradas ante **COMARB** (CM03 mensual, CM05 anual)
- Informar percepciones practicadas a **SIRCAR** y deducciones sufridas a **SIFERE**

Nada de esto existe en Odoo estándar.

### Qué mejora propone este módulo

`surtecnica_cm` agrega al sistema contable de Odoo 19 la gestión completa del Convenio Multilateral:

| Funcionalidad | Descripción |
|---|---|
| Jurisdicciones CM | 24 jurisdicciones (901-924) pre-cargadas y mapeadas a provincias de Odoo |
| Actividades CUACM | Nomenclador de actividades con alícuota por jurisdicción |
| Coeficiente Unificado | Cálculo automático desde facturas del ejercicio anterior |
| Liquidación mensual | Distribución de base imponible por CU, cálculo de impuesto y deducciones |
| SIRCAR | Exportación CSV de percepciones practicadas |
| SIFERE | Exportación TXT de retenciones/percepciones sufridas |
| CM03 | Exportación XML de DDJJ mensual para COMARB |
| CM05 | Exportación Excel de determinación de coeficiente anual |

---

## Bloque 2: Funcionamiento para el usuario final

### Flujo general de trabajo mensual

```
1. Configurar jurisdicciones + actividades + coeficientes (una vez al año)
         ↓
2. Facturar normalmente (la jurisdicción CM se asigna automáticamente)
         ↓
3. Fin de mes: Generar liquidación CM (wizard)
         ↓
4. Revisar líneas por jurisdicción, cargar deducciones
         ↓
5. Confirmar liquidación
         ↓
6. Exportar archivos (SIRCAR, SIFERE, CM03, CM05)
```

### Asignación automática de jurisdicción en facturas

Cada factura de venta o compra recibe automáticamente su jurisdicción CM según la provincia del cliente/proveedor:

- **Prioridad 1:** Dirección de envío (`partner_shipping_id.state_id`)
- **Prioridad 2:** Dirección fiscal (`partner_id.state_id`)

El usuario puede modificar la jurisdicción manualmente si es necesario. El campo aparece en el formulario de factura, debajo de la fecha.

**Ejemplo:**
| Factura | Cliente | Provincia | Jurisdicción CM |
|---|---|---|---|
| FA-A 0001-00000150 | Distribuidora Norte SRL | Córdoba | [904] Córdoba |
| FA-A 0001-00000151 | Comercial Litoral SA | Santa Fe | [921] Santa Fe |
| NC-A 0001-00000010 | Distribuidora Norte SRL | Córdoba | [904] Córdoba |

### Generar liquidación mensual

1. Ir a **Contabilidad > Informes > Convenio Multilateral > Generar Liquidación**
2. Seleccionar período (Desde/Hasta) y ejercicio fiscal
3. Click en **Generar Liquidación**

El wizard:
- Busca todas las facturas de venta con jurisdicción CM del período
- Agrupa las bases imponibles por jurisdicción
- Aplica el coeficiente unificado de cada jurisdicción
- Calcula el impuesto determinado = base distribuida × alícuota
- Crea la liquidación en estado "Calculada"

### Revisar y confirmar liquidación

En **Contabilidad > Contabilidad > Liquidación CM** se ve la liquidación generada.

Cada línea muestra:

| Jurisdicción | Coef. | Base Gravada | Base Distribuida | Alícuota | Impuesto | Ret. Sufridas | Perc. Sufridas | Saldo |
|---|---|---|---|---|---|---|---|---|
| [904] Córdoba | 0.3500 | 1.000.000 | 350.000 | 3.50% | 12.250 | 2.000 | 500 | 9.750 |
| [921] Santa Fe | 0.2500 | 1.000.000 | 250.000 | 3.60% | 9.000 | 1.500 | 300 | 7.200 |
| [902] Buenos Aires | 0.4000 | 1.000.000 | 400.000 | 4.00% | 16.000 | 3.000 | 1.000 | 12.000 |

**Deducciones:** El usuario carga manualmente las retenciones sufridas, percepciones sufridas, recaudaciones bancarias y saldo del período anterior en cada línea.

- **Saldo positivo** = A pagar
- **Saldo negativo** = A favor (se arrastra al período siguiente)

Una vez revisado, click en **Confirmar**.

### Exportar archivos

Desde **Contabilidad > Informes > Convenio Multilateral**:

| Menú | Qué exporta | Formato | Para qué |
|---|---|---|---|
| SIRCAR (Percepciones) | Percepciones IIBB practicadas a terceros | CSV | Informar a cada jurisdicción |
| SIFERE (Deducciones) | Retenciones/percepciones IIBB sufridas | TXT pos. fija | Computar como crédito fiscal |
| CM03 (DDJJ Mensual) | Declaración jurada mensual | XML | Presentar ante COMARB |
| CM05 (Coef. Anual) | Determinación de coeficiente unificado | Excel (.xlsx) | Presentación anual COMARB |

Todos los wizards siguen el mismo flujo:
1. Seleccionar parámetros (período, jurisdicción, liquidación)
2. Click en **Generar**
3. Click en **Descargar ZIP**

---

## Bloque 3: Parametrización

### Paso 1: Verificar jurisdicciones (viene pre-cargado)

**Menú:** Contabilidad > Configuración > Convenio Multilateral > Jurisdicciones CM

Las 24 jurisdicciones se cargan automáticamente al instalar el módulo:

| Código | Provincia | Vinculada a |
|---|---|---|
| 901 | Capital Federal | base.state_ar_c |
| 902 | Buenos Aires | base.state_ar_b |
| 903 | Catamarca | base.state_ar_k |
| 904 | Córdoba | base.state_ar_x |
| 905 | Corrientes | base.state_ar_w |
| 906 | Chaco | base.state_ar_h |
| 907 | Chubut | base.state_ar_u |
| 908 | Entre Ríos | base.state_ar_e |
| 909 | Formosa | base.state_ar_p |
| 910 | Jujuy | base.state_ar_y |
| 911 | La Pampa | base.state_ar_l |
| 912 | La Rioja | base.state_ar_f |
| 913 | Mendoza | base.state_ar_m |
| 914 | Misiones | base.state_ar_n |
| 915 | Neuquén | base.state_ar_q |
| 916 | Río Negro | base.state_ar_r |
| 917 | Salta | base.state_ar_a |
| 918 | San Juan | base.state_ar_j |
| 919 | San Luis | base.state_ar_d |
| 920 | Santa Cruz | base.state_ar_z |
| 921 | Santa Fe | base.state_ar_s |
| 922 | Santiago del Estero | base.state_ar_g |
| 923 | Tierra del Fuego | base.state_ar_v |
| 924 | Tucumán | base.state_ar_t |

No requiere configuración adicional. Solo verificar que estén correctas.

### Paso 2: Configurar jurisdicción sede de la empresa

**Menú:** Ajustes > Compañías > (su empresa) > pestaña "Convenio Multilateral"

Seleccionar la jurisdicción donde la empresa tiene su sede central. Esto se informa en el CM03.

### Paso 3: Cargar actividades CUACM

**Menú:** Contabilidad > Configuración > Convenio Multilateral > Actividades CUACM

Cargar una actividad por cada jurisdicción donde la empresa opera:

| Jurisdicción | Código CUACM | Descripción | Alícuota % | Régimen |
|---|---|---|---|---|
| [904] Córdoba | 519000 | Venta al por mayor de artículos eléctricos | 3.50 | Art. 2 - Régimen General |
| [921] Santa Fe | 519000 | Venta al por mayor de artículos eléctricos | 3.60 | Art. 2 - Régimen General |
| [902] Buenos Aires | 519000 | Venta al por mayor de artículos eléctricos | 4.00 | Art. 2 - Régimen General |

**Campos:**
- **Código CUACM:** Código del nomenclador COMARB (consultar en siti.comarb.gob.ar)
- **Alícuota %:** Tasa de IIBB que cobra esa jurisdicción para esa actividad
- **Régimen:** Art. 2 (General) para la mayoría. Otros artículos para actividades especiales
- **Vigencia:** Opcional, para controlar cambios de alícuota en el tiempo

### Paso 4: Cargar coeficientes unificados

**Opción A — Cálculo automático:**

1. Ir a **Contabilidad > Informes > Convenio Multilateral > Calcular Coeficientes**
2. Ingresar Año Base (ej: 2025) y Año Aplicación (ej: 2026)
3. Click en **Calcular Coeficientes**

El wizard busca todas las facturas del año base, agrupa ingresos (ventas) y gastos (compras) por jurisdicción, y calcula:

```
Coef. Ingresos = Ingresos jurisdicción / Ingresos totales
Coef. Gastos   = Gastos jurisdicción / Gastos totales
CU = (Coef. Ingresos × 0.50) + (Coef. Gastos × 0.50)
```

**Opción B — Carga manual:**

1. Ir a **Contabilidad > Configuración > Convenio Multilateral > Coeficientes Unificados**
2. Crear un registro por cada jurisdicción con actividad

Ejemplo para ejercicio 2026:

| Ejercicio | Jurisdicción | Ingresos Jur. | Ingresos Total | Gastos Jur. | Gastos Total | CU |
|---|---|---|---|---|---|---|
| 2026 | [904] Córdoba | 3.500.000 | 10.000.000 | 2.800.000 | 8.000.000 | 0.3500 |
| 2026 | [921] Santa Fe | 2.500.000 | 10.000.000 | 2.000.000 | 8.000.000 | 0.2500 |
| 2026 | [902] Buenos Aires | 4.000.000 | 10.000.000 | 3.200.000 | 8.000.000 | 0.4000 |

Los coeficientes se calculan automáticamente a partir de los montos ingresados.

### Paso 5: Verificar provincia en partners

Para que la jurisdicción CM se asigne automáticamente, cada cliente/proveedor debe tener configurada la **provincia** en su dirección:

**Menú:** Contactos > (partner) > Dirección > Provincia

---

## Bloque 4: Referencia técnica

### Arquitectura del módulo

```
surtecnica_cm/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   ├── cm_jurisdiction.py          # Modelo propio: 24 jurisdicciones COMARB
│   ├── cm_activity.py              # Modelo propio: actividad CUACM + alícuota
│   ├── cm_coefficient.py           # Modelo propio: coeficiente unificado
│   ├── cm_liquidation.py           # Modelo propio: liquidación + líneas
│   ├── res_company.py              # Herencia: agrega sede CM
│   └── account_move.py             # Herencia: agrega jurisdicción CM computed
├── wizard/
│   ├── __init__.py
│   ├── cm_coefficient_wizard.py    # Cálculo automático de coeficientes
│   ├── cm_liquidation_wizard.py    # Generación de liquidación mensual
│   ├── cm_sircar_wizard.py         # Exportación SIRCAR (CSV)
│   ├── cm_sifere_wizard.py         # Exportación SIFERE (TXT posición fija)
│   ├── cm_cm03_wizard.py           # Exportación CM03 (XML)
│   └── cm_cm05_wizard.py           # Exportación CM05 (Excel)
├── views/
│   ├── cm_jurisdiction_views.xml
│   ├── cm_activity_views.xml
│   ├── cm_coefficient_views.xml
│   ├── cm_liquidation_views.xml
│   ├── res_company_views.xml
│   ├── account_move_views.xml
│   └── menu_views.xml
├── security/
│   ├── security.xml                # Grupos: cm_user, cm_manager
│   └── ir.model.access.csv         # ACL por grupo
├── data/
│   └── cm_jurisdiction_data.xml    # 24 jurisdicciones pre-cargadas (noupdate=1)
└── static/description/icon.png
```

### Modelos y relaciones

```
res.company ──────────────┐
  cm_sede_jurisdiction_id │
                          ▼
               cm.jurisdiction (901-924)
                    ▲           ▲
                    │           │
              cm.activity    cm.coefficient
              (CUACM+alíc)   (CU por año)
                    ▲           ▲
                    │           │
              cm.liquidation.line
                    │
                    ▼
              cm.liquidation (mensual)

account.move ──→ cm.jurisdiction (computed desde partner.state_id)
```

### Modelo `cm.jurisdiction`

| Campo | Tipo | Descripción |
|---|---|---|
| `code` | Char(3) | Código COMARB 901-924 (unique, indexed) |
| `name` | Char | Nombre de la provincia |
| `state_id` | Many2one `res.country.state` | Vínculo con provincia Odoo (unique) |
| `active` | Boolean | Archivado lógico |

```python
class CmJurisdiction(models.Model):
    _name = 'cm.jurisdiction'
    _order = 'code'

    code = fields.Char(string='Código CM', size=3, required=True, index=True)
    name = fields.Char(string='Provincia', required=True)
    state_id = fields.Many2one(
        'res.country.state', string='Provincia Odoo',
        domain="[('country_id.code', '=', 'AR')]",
    )
    active = fields.Boolean(default=True)

    def name_get(self):
        return [(r.id, f"[{r.code}] {r.name}") for r in self]
```

**SQL constraints:** `code` unique, `state_id` unique.

### Modelo `cm.activity`

| Campo | Tipo | Descripción |
|---|---|---|
| `company_id` | Many2one `res.company` | Empresa |
| `jurisdiction_id` | Many2one `cm.jurisdiction` | Jurisdicción |
| `cuacm_code` | Char(10) | Código CUACM del nomenclador COMARB |
| `name` | Char | Descripción de la actividad |
| `alicuota` | Float(6,4) | Tasa IIBB (%) |
| `art_regimen` | Selection | Art. 2 a 13 del CM |
| `date_from` / `date_to` | Date | Vigencia |

**SQL constraint:** unique(`company_id`, `jurisdiction_id`, `cuacm_code`).

### Modelo `cm.coefficient`

| Campo | Tipo | Descripción |
|---|---|---|
| `company_id` | Many2one | Empresa |
| `fiscal_year` | Char(4) | Ejercicio de aplicación |
| `jurisdiction_id` | Many2one | Jurisdicción |
| `income_amount` / `income_total` | Float(16,2) | Ingresos jurisdicción / totales |
| `income_ratio` | Float(8,4) | **Computed stored:** income_amount / income_total |
| `expense_amount` / `expense_total` | Float(16,2) | Gastos jurisdicción / totales |
| `expense_ratio` | Float(8,4) | **Computed stored:** expense_amount / expense_total |
| `coefficient` | Float(8,4) | **Computed stored:** income_ratio×0.50 + expense_ratio×0.50 |

```python
@api.depends('income_amount', 'income_total', 'expense_amount', 'expense_total')
def _compute_ratios(self):
    for rec in self:
        rec.income_ratio = round(rec.income_amount / rec.income_total, 4) if rec.income_total else 0.0
        rec.expense_ratio = round(rec.expense_amount / rec.expense_total, 4) if rec.expense_total else 0.0
        rec.coefficient = round(rec.income_ratio * 0.50 + rec.expense_ratio * 0.50, 4)
```

**SQL constraint:** unique(`fiscal_year`, `jurisdiction_id`, `company_id`).

### Modelo `cm.liquidation` + `cm.liquidation.line`

**Cabecera (`cm.liquidation`):**

| Campo | Tipo | Descripción |
|---|---|---|
| `period` | Char(7) | Formato AAAA/MM |
| `date_from` / `date_to` | Date | Rango del período |
| `fiscal_year` | Char(4) | Ejercicio de los coeficientes |
| `state` | Selection | `draft` → `calculated` → `confirmed` |
| `line_ids` | One2many | Líneas por jurisdicción |
| `total_*` | Float(16,2) | **Computed stored** desde line_ids |

Hereda `mail.thread` para tracking de cambios de estado en el chatter.

**Línea (`cm.liquidation.line`):**

| Campo | Tipo | Descripción |
|---|---|---|
| `jurisdiction_id` | Many2one | Jurisdicción |
| `activity_id` | Many2one | Actividad CUACM |
| `coefficient` | Float(8,4) | CU aplicado |
| `base_gravada` | Float(16,2) | Base imponible total |
| `base_distribuida` | Float(16,2) | **Computed:** base_gravada × coefficient |
| `alicuota` | Float(6,4) | Tasa IIBB |
| `impuesto_determinado` | Float(16,2) | **Computed:** base_distribuida × alícuota / 100 |
| Deducciones | Float(16,2) | retenciones, percepciones, bancarias, saldo anterior |
| `total_deducciones` | Float(16,2) | **Computed:** suma de deducciones |
| `saldo` | Float(16,2) | **Computed:** impuesto - deducciones |

### Herencias

**`res.company`:** Agrega campo `cm_sede_jurisdiction_id` (Many2one a `cm.jurisdiction`).

**`account.move`:** Agrega campo computed `cm_jurisdiction_id` que se resuelve automáticamente:

```python
@api.depends('partner_shipping_id.state_id', 'partner_id.state_id')
def _compute_cm_jurisdiction_id(self):
    # Prioriza dirección de envío sobre dirección fiscal
    # Usa cache para evitar N+1 queries
    cache = {}
    for move in self:
        state = move.partner_shipping_id.state_id or move.partner_id.state_id
        if state.id not in cache:
            cache[state.id] = Jurisdiction.search([('state_id', '=', state.id)], limit=1)
        move.cm_jurisdiction_id = cache[state.id]
```

El campo es `store=True, readonly=False` para permitir edición manual.

### Wizards de exportación

#### SIRCAR — `cm.sircar.wizard`

**Qué exporta:** Percepciones IIBB practicadas a terceros (facturas de venta con tax IIBB).

**Formato:** CSV separado por comas, 11 campos:

| # | Campo | Ejemplo |
|---|---|---|
| 1 | Nro renglón | `1` |
| 2 | Tipo comprobante | `1` (Factura) |
| 3 | Letra | `A` |
| 4 | Nro comprobante | `0001-00000020` |
| 5 | CUIT percibido | `20123456789` |
| 6 | Fecha | `06/05/2026` |
| 7 | Monto sujeto | `1500.00` |
| 8 | Alícuota | `3.00` |
| 9 | Monto percibido | `45.00` |
| 10 | Tipo régimen | `1` (General) |
| 11 | Jurisdicción | `904` |

**Detección de percepciones:** Busca `account.move.line` con `tax_line_id.l10n_ar_tribute_afip_code = '07'` (código AFIP para IIBB).

#### SIFERE — `cm.sifere.wizard`

**Qué exporta:** Retenciones y percepciones IIBB sufridas por la empresa.

**Formato percepciones:** TXT posición fija, 51 chars/línea, 8 campos:
```
jurisdicción(3) + cuit(13) + fecha(10) + sucursal(4) + nro_cbte(8) + tipo(1) + letra(1) + monto(11)
```

**Formato retenciones:** TXT posición fija, 67 chars/línea, 9 campos (agrega `nro_constancia(16)`).

**Fuente percepciones:** Tax lines IIBB en facturas de compra.
**Fuente retenciones:** Tax lines IIBB en pagos recibidos (inbound).

#### CM03 — `cm.cm03.wizard`

**Qué exporta:** Declaración jurada mensual para COMARB.

**Formato:** XML con estructura:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<CM03>
  <Encabezado>
    <CUIT>30999999999</CUIT>
    <Periodo>202601</Periodo>
    <RazonSocial>Surtecnica SA</RazonSocial>
    <TotalBaseImponible>1000000.00</TotalBaseImponible>
    <TotalImpuestoDeterminado>37250.00</TotalImpuestoDeterminado>
    <JurisdiccionSede>902</JurisdiccionSede>
  </Encabezado>
  <Jurisdicciones>
    <Jurisdiccion>
      <Codigo>904</Codigo>
      <Coeficiente>0.3500</Coeficiente>
      <BaseDistribuida>350000.00</BaseDistribuida>
      <Alicuota>3.5000</Alicuota>
      <ImpuestoDeterminado>12250.00</ImpuestoDeterminado>
      <Saldo>9750.00</Saldo>
    </Jurisdiccion>
  </Jurisdicciones>
</CM03>
```

**Requisito:** La liquidación debe estar en estado "Confirmada".

#### CM05 — `cm.cm05.wizard`

**Qué exporta:** Determinación del coeficiente unificado anual.

**Formato:** Excel (.xlsx) con 2 hojas:
- **Hoja 1 "Determinación CU":** Tabla de coeficientes por jurisdicción con ingresos, gastos, ratios y CU.
- **Hoja 2 "Detalle Mensual":** Liquidaciones del ejercicio con base gravada, impuesto y saldo por jurisdicción.

**Dependencia:** Requiere `openpyxl`. Si no está instalado, muestra error claro al usuario.

### Seguridad

**Grupos:**

| Grupo | Hereda de | Permisos |
|---|---|---|
| `group_cm_user` | `account.group_account_user` | Lectura en maestros, lectura/escritura en liquidaciones, uso de wizards de exportación |
| `group_cm_manager` | `group_cm_user` | CRUD completo en todos los modelos, acceso a calcular coeficientes |

**ACL detallado:**

| Modelo | User | Manager |
|---|---|---|
| `cm.jurisdiction` | R | CRUD |
| `cm.activity` | R | CRUD |
| `cm.coefficient` | R | CRUD |
| `cm.liquidation` | RW | CRUD |
| `cm.liquidation.line` | RW | CRUD |
| Wizards de exportación | CRUD | CRUD |
| Wizard coeficientes | — | CRUD |

### Dependencias

| Módulo | Por qué |
|---|---|
| `account` | Modelo `account.move`, menús de contabilidad, grupos de seguridad |
| `l10n_ar` | Localización argentina: CUIT, tipos de documento AFIP, `l10n_ar_tribute_afip_code` |

**Librería Python opcional:** `openpyxl` (solo para CM05 Excel).

### Decisiones técnicas

| Decisión | Justificación |
|---|---|
| `cm.jurisdiction` como modelo separado (no herencia de `res.country.state`) | Permite agregar código CM, constraints propias, y desacoplar de datos base de Odoo |
| Coeficientes como stored computed | Evitar recálculo en cada liquidación. Se calculan una vez cuando cambian los montos |
| Campo `cm_jurisdiction_id` computed + store + readonly=False | Se calcula automáticamente pero el usuario puede corregir manualmente |
| Cache en `_compute_cm_jurisdiction_id` | Evitar N+1 queries al resolver jurisdicción por state_id |
| Liquidación con estados draft → calculated → confirmed | Flujo controlado: el wizard genera (calculated), el usuario revisa y confirma |
| Exportaciones como TransientModel con estado draft/done | Patrón consistente con `surtecnica_arca` (Libro IVA Digital) |
| Percepciones IIBB identificadas por `l10n_ar_tribute_afip_code = '07'` | Estándar de la localización argentina de Odoo, código AFIP para IIBB |
| `noupdate=1` en jurisdicciones | Datos maestros que no deben sobrescribirse en actualizaciones del módulo |

### Verificación / Testing

1. **Instalar módulo** en Odoo 19 con localización argentina activa
2. **Verificar jurisdicciones:** Contabilidad > Configuración > CM > Jurisdicciones — deben aparecer 24 registros (901-924)
3. **Configurar actividades:** Crear al menos 2 actividades CUACM con alícuotas para jurisdicciones distintas
4. **Cargar coeficientes:** Manualmente o con el wizard (requiere facturas del año base)
5. **Generar liquidación:**
   - Crear facturas de venta a clientes de distintas provincias
   - Ejecutar wizard de liquidación
   - Verificar que las líneas se distribuyan correctamente por coeficiente
   - Verificar cálculo: `base_distribuida = base_gravada × coefficient`
   - Verificar cálculo: `impuesto = base_distribuida × alícuota / 100`
6. **SIRCAR:** Requiere facturas con percepciones IIBB (tax con `l10n_ar_tribute_afip_code = '07'`). Verificar formato CSV con 11 campos por línea
7. **SIFERE:** Requiere facturas de compra con percepciones IIBB. Verificar formato TXT posición fija
8. **CM03:** Confirmar una liquidación, exportar XML, verificar estructura y totales
9. **CM05:** Cargar coeficientes, exportar Excel, verificar 2 hojas con datos correctos
