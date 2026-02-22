# Convenio Multilateral IIBB — `surtecnica_cm`

## 1. Introduccion

### El problema

Una empresa que vende desde Buenos Aires a clientes en Cordoba, Santa Fe y Mendoza tiene que pagar IIBB en **cada provincia** donde genera ingresos. Odoo no sabe esto: solo maneja un impuesto plano, sin distribuir la base entre jurisdicciones.

El regimen de **Convenio Multilateral** (CM) exige:

1. Calcular un **coeficiente unificado** (CU) por jurisdiccion, basado en ingresos y gastos del año anterior
2. **Distribuir** la base imponible mensual de cada jurisdiccion usando ese coeficiente
3. **Liquidar** el impuesto con la alicuota que fija cada provincia
4. **Presentar** archivos digitales ante COMARB (CM03, CM05) y las jurisdicciones (SIRCAR, SIFERE)

### Que resuelve este modulo

| Necesidad | Sin el modulo | Con el modulo |
|---|---|---|
| Saber a que jurisdiccion corresponde cada factura | Manual, en planilla | Automatico por provincia del cliente |
| Calcular coeficientes anuales | Planilla Excel externa | Un click desde las facturas del año |
| Liquidar IIBB mensual por jurisdiccion | Planilla Excel con formulas | Wizard que genera todo desde Odoo |
| Archivo SIRCAR (percepciones practicadas) | Cargar a mano en el sitio | CSV listo para subir |
| Archivo SIFERE (retenciones/percepciones sufridas) | Cargar a mano en el sitio | TXT listo para subir |
| CM03 (DDJJ mensual COMARB) | Carga manual en SIFERE web | XML generado desde la liquidacion |
| CM05 (coeficiente anual COMARB) | Planilla Excel manual | Excel generado con 2 hojas |

---

## 2. Como se usa (paso a paso)

### El ciclo completo

```
 CONFIGURACION INICIAL (una vez al año)
 ========================================
 1. Verificar jurisdicciones         → vienen cargadas
 2. Cargar actividades CUACM         → una por jurisdiccion donde operas
 3. Calcular coeficientes            → wizard automatico o carga manual
 4. Definir sede de la empresa       → en configuracion de la compañia

 OPERATORIA MENSUAL
 ========================================
 5. Facturar normalmente             → la jurisdiccion se asigna sola
 6. Generar liquidacion              → wizard de fin de mes
 7. Revisar y cargar deducciones     → retenciones, percepciones sufridas
 8. Confirmar liquidacion            → queda firme
 9. Exportar archivos                → SIRCAR, SIFERE, CM03, CM05
```

---

### Paso 5: Facturar normalmente

No hay que hacer nada especial. Cada vez que se crea una factura, el modulo mira la provincia del cliente y le asigna la jurisdiccion CM automaticamente.

**Donde se ve:** en el formulario de la factura, debajo de la fecha, aparece el campo "Jurisdiccion CM".

```
 Factura FA-A 0001-00000150
 Cliente:       Distribuidora Norte SRL
 Provincia:     Cordoba
 Jurisdiccion:  [904] Cordoba  ← se completo solo
```

**Regla de prioridad:**
- Si el cliente tiene direccion de envio → usa esa provincia
- Si no → usa la provincia de la direccion fiscal

**Se puede editar:** si la jurisdiccion automatica no es correcta, el usuario la cambia a mano.

---

### Paso 6: Generar liquidacion mensual

**Menu:** Contabilidad > Informes > Convenio Multilateral > Generar Liquidacion

El wizard pide 3 datos:

| Campo | Ejemplo | Que significa |
|---|---|---|
| Desde | 01/01/2026 | Inicio del periodo a liquidar |
| Hasta | 31/01/2026 | Fin del periodo |
| Ejercicio fiscal | 2026 | De que año toma los coeficientes |

Click en **Generar Liquidacion** y el sistema:

1. Busca todas las facturas de venta del periodo que tengan jurisdiccion CM
2. Suma las bases imponibles por jurisdiccion
3. Aplica el coeficiente de cada jurisdiccion
4. Multiplica la base distribuida por la alicuota
5. Crea la liquidacion en estado **"Calculada"**

---

### Paso 7: Revisar y cargar deducciones

**Menu:** Contabilidad > Contabilidad > Liquidacion CM

Se abre la liquidacion generada. Tiene una linea por cada jurisdiccion donde hubo ventas:

```
 LIQUIDACION CM 2026/01 - Mi Empresa SA
 ═══════════════════════════════════════════════════════════════════════════════

 Jurisdiccion  │ Coef.  │ Base Gravada │ Base Distrib. │ Alic. │ Impuesto
 ──────────────┼────────┼──────────────┼───────────────┼───────┼──────────
 [904] Cordoba │ 0.3500 │ 1.000.000    │ 350.000       │ 3.50% │ 12.250
 [921] Santa Fe│ 0.2500 │ 1.000.000    │ 250.000       │ 3.60% │  9.000
 [902] Bs. As. │ 0.4000 │ 1.000.000    │ 400.000       │ 4.00% │ 16.000
```

**La cuenta que se hace en cada linea:**

```
 Base Distribuida = Base Gravada × Coeficiente
                  = 1.000.000 × 0.3500
                  = 350.000

 Impuesto = Base Distribuida × Alicuota / 100
           = 350.000 × 3.50 / 100
           = 12.250
```

**Deducciones:** el usuario carga en cada linea lo que la empresa ya pago o le retuvieron:

| Campo | Que es |
|---|---|
| Retenciones sufridas | IIBB que te retuvieron tus clientes al cobrarte |
| Percepciones sufridas | IIBB que te percibieron tus proveedores al facturarte |
| Recaudaciones bancarias | IIBB que el banco te debito automaticamente |
| Saldo anterior | Saldo a favor que arrastra del mes pasado |

**El saldo final:**

```
 Saldo = Impuesto Determinado − Total Deducciones

 Si el saldo es positivo → hay que pagar
 Si el saldo es negativo → queda a favor para el mes siguiente
```

---

### Paso 8: Confirmar liquidacion

Una vez revisado todo, click en el boton **"Confirmar"** en la cabecera.

La liquidacion pasa a estado "Confirmada" y queda lista para exportar.

> Solo usuarios con rol **Responsable CM** pueden confirmar.
> Si hay que corregir algo, el boton **"Volver a Borrador"** permite reabrir.

---

### Paso 9: Exportar archivos

Todos los exportadores estan en **Contabilidad > Informes > Convenio Multilateral**.

#### SIRCAR — Percepciones practicadas a terceros

**Que es:** las percepciones de IIBB que tu empresa le cobro a sus clientes en las facturas de venta.

**Quien lo pide:** cada jurisdiccion donde practicas percepciones.

| Parametro | Que poner |
|---|---|
| Desde / Hasta | El periodo mensual |
| Jurisdiccion | Opcional: filtrar por una sola |

Click **Generar** → se genera el CSV → click **Descargar ZIP**.

**Formato del CSV:** una linea por cada percepcion, con CUIT, comprobante, monto, alicuota y jurisdiccion.

---

#### SIFERE — Retenciones y percepciones sufridas

**Que es:** lo que a tu empresa le retuvieron o percibieron terceros. Se usa para justificar las deducciones en la liquidacion.

**Quien lo pide:** COMARB a traves del sistema SIFERE.

| Parametro | Que poner |
|---|---|
| Desde / Hasta | El periodo mensual |
| Tipo | "Percepciones" (de facturas de compra) o "Retenciones" (de cobros recibidos) |

Click **Generar** → TXT posicion fija → **Descargar ZIP**.

---

#### CM03 — Declaracion jurada mensual

**Que es:** la DDJJ mensual del Convenio Multilateral que resume la liquidacion de todas las jurisdicciones.

**Quien lo pide:** COMARB.

| Parametro | Que poner |
|---|---|
| Liquidacion | Elegir una liquidacion en estado "Confirmada" |

Click **Generar** → XML con encabezado + detalle por jurisdiccion → **Descargar ZIP**.

---

#### CM05 — Determinacion de coeficiente anual

**Que es:** la justificacion anual de como se calcularon los coeficientes unificados.

**Quien lo pide:** COMARB.

| Parametro | Que poner |
|---|---|
| Ejercicio fiscal | El año (ej: 2026) |

Click **Generar** → Excel con 2 hojas:
- **Hoja 1 "Determinacion CU"**: tabla de coeficientes con ingresos, gastos y ratios por jurisdiccion
- **Hoja 2 "Detalle Mensual"**: todas las liquidaciones del año con base, impuesto y saldo

---

## 3. Parametrizacion

### Prerequisitos

- Odoo 19 con localizacion argentina (`l10n_ar`) instalada
- Clientes y proveedores con **provincia cargada** en su direccion (Contactos > direccion > Provincia)
- Para SIRCAR/SIFERE: impuestos de IIBB configurados con `l10n_ar_tribute_afip_code = '07'`

---

### 3.1 Jurisdicciones CM (viene pre-cargado)

**Menu:** Contabilidad > Configuracion > Convenio Multilateral > Jurisdicciones CM

Las 24 jurisdicciones del Convenio Multilateral se cargan automaticamente al instalar:

| Codigo | Provincia | Codigo | Provincia |
|--------|-----------|--------|-----------|
| 901 | Capital Federal | 913 | Mendoza |
| 902 | Buenos Aires | 914 | Misiones |
| 903 | Catamarca | 915 | Neuquen |
| 904 | Cordoba | 916 | Rio Negro |
| 905 | Corrientes | 917 | Salta |
| 906 | Chaco | 918 | San Juan |
| 907 | Chubut | 919 | San Luis |
| 908 | Entre Rios | 920 | Santa Cruz |
| 909 | Formosa | 921 | Santa Fe |
| 910 | Jujuy | 922 | Sgo. del Estero |
| 911 | La Pampa | 923 | Tierra del Fuego |
| 912 | La Rioja | 924 | Tucuman |

No requiere configuracion. Solo verificar que esten activas las jurisdicciones donde la empresa opera.

---

### 3.2 Sede de la empresa

**Menu:** Ajustes > Compañias > (tu empresa) > pestaña "Convenio Multilateral"

Seleccionar la jurisdiccion donde la empresa tiene su sede principal. Se informa en el CM03.

---

### 3.3 Actividades CUACM

**Menu:** Contabilidad > Configuracion > Convenio Multilateral > Actividades CUACM

Cargar una linea por cada jurisdiccion donde la empresa tiene actividad:

| Jurisdiccion | Cod. CUACM | Descripcion | Alicuota % | Regimen |
|---|---|---|---|---|
| [904] Cordoba | 519000 | Vta. mayor art. electricos | 3.50 | Art. 2 - General |
| [921] Santa Fe | 519000 | Vta. mayor art. electricos | 3.60 | Art. 2 - General |
| [902] Buenos Aires | 519000 | Vta. mayor art. electricos | 4.00 | Art. 2 - General |

**Donde conseguir los datos:**
- **Codigo CUACM:** nomenclador COMARB en [siti.comarb.gob.ar](https://siti.comarb.gob.ar)
- **Alicuota:** pagina de rentas de cada provincia
- **Regimen:** Art. 2 (General) para la mayoria. Otros articulos para construccion, seguros, bancos, transporte, etc.
- **Vigencia (opcional):** si cambia la alicuota, poner fecha desde/hasta para tener historial

---

### 3.4 Coeficientes unificados

Hay dos formas de cargarlos:

#### Opcion A: Calculo automatico (recomendado)

**Menu:** Contabilidad > Informes > Convenio Multilateral > Calcular Coeficientes

| Campo | Que poner | Ejemplo |
|---|---|---|
| Año base | El año del que se toman los datos (ingresos y gastos) | 2025 |
| Año aplicacion | El año donde se usan los coeficientes | 2026 |

El wizard:
1. Suma las facturas de venta del 2025 por jurisdiccion → calcula ratio de ingresos
2. Suma las facturas de compra del 2025 por jurisdiccion → calcula ratio de gastos
3. Promedia: `CU = (ratio ingresos × 50%) + (ratio gastos × 50%)`

**Requisito:** las facturas del año base deben tener jurisdiccion CM asignada.

#### Opcion B: Carga manual

**Menu:** Contabilidad > Configuracion > Convenio Multilateral > Coeficientes Unificados

Crear una linea por jurisdiccion. Al ingresar los montos, el coeficiente se calcula solo:

| Ejercicio | Jurisdiccion | Ing. Jur. | Ing. Total | Gasto Jur. | Gasto Total | CU |
|---|---|---|---|---|---|---|
| 2026 | [904] Cordoba | 3.500.000 | 10.000.000 | 2.800.000 | 8.000.000 | 0.3500 |
| 2026 | [921] Santa Fe | 2.500.000 | 10.000.000 | 2.000.000 | 8.000.000 | 0.2500 |
| 2026 | [902] Bs. As. | 4.000.000 | 10.000.000 | 3.200.000 | 8.000.000 | 0.4000 |

---

## 4. Referencia tecnica

### Arquitectura

```
surtecnica_cm/
├── models/
│   ├── cm_jurisdiction.py        # 24 jurisdicciones COMARB (901-924)
│   ├── cm_activity.py            # Actividad CUACM + alicuota por jurisdiccion
│   ├── cm_coefficient.py         # Coeficiente unificado por ejercicio
│   ├── cm_liquidation.py         # Liquidacion mensual + lineas
│   ├── res_company.py            # Herencia: sede CM en la empresa
│   └── account_move.py           # Herencia: jurisdiccion CM en facturas
├── wizard/
│   ├── cm_coefficient_wizard.py  # Calculo automatico de CU
│   ├── cm_liquidation_wizard.py  # Generacion de liquidacion mensual
│   ├── cm_sircar_wizard.py       # Export SIRCAR (CSV)
│   ├── cm_sifere_wizard.py       # Export SIFERE (TXT posicion fija)
│   ├── cm_cm03_wizard.py         # Export CM03 (XML)
│   └── cm_cm05_wizard.py         # Export CM05 (Excel)
├── views/
├── security/
├── data/
│   └── cm_jurisdiction_data.xml  # 24 jurisdicciones (noupdate=1)
└── static/description/icon.png
```

### Relaciones entre modelos

```
res.company ──────────────┐
  cm_sede_jurisdiction_id │
                          ▼
               cm.jurisdiction (901-924)
                    ▲           ▲
                    │           │
              cm.activity    cm.coefficient
              (CUACM+alic)   (CU por año)
                    ▲           ▲
                    │           │
              cm.liquidation.line
                    │
                    ▼
              cm.liquidation (mensual, mail.thread)

account.move ──→ cm.jurisdiction (computed desde partner.state_id)
```

### Modelos

#### `cm.jurisdiction`

| Campo | Tipo | Descripcion |
|---|---|---|
| `code` | Char(3), unique, indexed | Codigo COMARB (901-924) |
| `name` | Char, required | Nombre de la provincia |
| `state_id` | Many2one `res.country.state`, unique | Vinculo con provincia Odoo |
| `active` | Boolean | Archivado logico |

`name_get()` devuelve `[CODE] Nombre`.

#### `cm.activity`

| Campo | Tipo | Descripcion |
|---|---|---|
| `company_id` | Many2one `res.company` | Empresa |
| `jurisdiction_id` | Many2one `cm.jurisdiction` | Jurisdiccion (restrict) |
| `cuacm_code` | Char(10) | Codigo nomenclador COMARB |
| `name` | Char | Descripcion de la actividad |
| `alicuota` | Float(6,4) | Tasa IIBB % |
| `art_regimen` | Selection | Art. 2 a 13 del CM |
| `date_from` / `date_to` | Date | Vigencia |

Unique: `(company_id, jurisdiction_id, cuacm_code)`.

#### `cm.coefficient`

| Campo | Tipo | Descripcion |
|---|---|---|
| `fiscal_year` | Char(4) | Ejercicio de aplicacion |
| `jurisdiction_id` | Many2one `cm.jurisdiction` | Jurisdiccion (restrict) |
| `income_amount` / `income_total` | Float(16,2) | Ingresos jurisdiccion / pais |
| `income_ratio` | Float(8,4), computed stored | `income_amount / income_total` |
| `expense_amount` / `expense_total` | Float(16,2) | Gastos jurisdiccion / pais |
| `expense_ratio` | Float(8,4), computed stored | `expense_amount / expense_total` |
| `coefficient` | Float(8,4), computed stored | `income_ratio * 0.50 + expense_ratio * 0.50` |

Unique: `(fiscal_year, jurisdiction_id, company_id)`.

#### `cm.liquidation`

| Campo | Tipo | Descripcion |
|---|---|---|
| `name` | Char, computed stored | "CM YYYY/MM - Empresa" |
| `period` | Char(7) | Formato AAAA/MM |
| `date_from` / `date_to` | Date | Rango del periodo |
| `fiscal_year` | Char(4) | Ejercicio de coeficientes |
| `state` | Selection | `draft` → `calculated` → `confirmed` |
| `line_ids` | One2many `cm.liquidation.line` | Lineas por jurisdiccion |
| `total_*` | Float(16,2), computed stored | Sumas desde line_ids |

Hereda `mail.thread`. Unique: `(period, company_id)`.

#### `cm.liquidation.line`

| Campo | Tipo | Descripcion |
|---|---|---|
| `liquidation_id` | Many2one (cascade) | Liquidacion padre |
| `jurisdiction_id` | Many2one (restrict) | Jurisdiccion |
| `coefficient` | Float(8,4) | CU aplicado |
| `base_gravada` | Float(16,2) | Base imponible total |
| `base_distribuida` | Float(16,2), computed stored | `base_gravada * coefficient` |
| `alicuota` | Float(6,4) | Tasa IIBB |
| `impuesto_determinado` | Float(16,2), computed stored | `base_distribuida * alicuota / 100` |
| `retenciones_sufridas` | Float(16,2) | Ret. IIBB sufridas |
| `percepciones_sufridas` | Float(16,2) | Perc. IIBB sufridas |
| `recaudaciones_bancarias` | Float(16,2) | Rec. bancarias |
| `saldo_anterior` | Float(16,2) | Arrastre periodo anterior |
| `total_deducciones` | Float(16,2), computed stored | Suma de deducciones |
| `saldo` | Float(16,2), computed stored | `impuesto - deducciones` |

### Herencias

**`res.company`:** agrega `cm_sede_jurisdiction_id` (Many2one → `cm.jurisdiction`).

**`account.move`:** agrega `cm_jurisdiction_id` (computed, stored, readonly=False). Se resuelve automaticamente desde `partner_shipping_id.state_id` o `partner_id.state_id`. Usa cache local para evitar N+1 queries.

### Formatos de exportacion

#### SIRCAR (CSV, 11 campos)

```
nro_renglon, tipo_cbte, letra, nro_cbte, cuit, fecha, monto_sujeto, alicuota, monto_percibido, tipo_regimen, jurisdiccion
```

Fuente: `account.move.line` con `tax_line_id.l10n_ar_tribute_afip_code = '07'` en facturas de venta.

#### SIFERE Percepciones (TXT, 51 chars/linea)

```
jurisdiccion(3) + cuit(13) + fecha(10) + sucursal(4) + nro_cbte(8) + tipo(1) + letra(1) + monto(11)
```

Fuente: tax lines IIBB en facturas de compra.

#### SIFERE Retenciones (TXT, 67 chars/linea)

```
jurisdiccion(3) + cuit(13) + fecha(10) + sucursal(4) + nro_cbte(8) + tipo(1) + letra(1) + nro_constancia(16) + monto(11)
```

Fuente: tax lines IIBB en pagos inbound.

#### CM03 (XML)

```xml
<CM03>
  <Encabezado>
    <CUIT/> <Periodo/> <RazonSocial/>
    <TotalBaseImponible/> <TotalImpuestoDeterminado/>
    <TotalDeducciones/> <TotalSaldo/> <JurisdiccionSede/>
  </Encabezado>
  <Jurisdicciones>
    <Jurisdiccion>
      <Codigo/> <Coeficiente/> <BaseDistribuida/>
      <Alicuota/> <ImpuestoDeterminado/> <Saldo/>
    </Jurisdiccion>
  </Jurisdicciones>
</CM03>
```

Fuente: `cm.liquidation` en estado "confirmed".

#### CM05 (Excel .xlsx, 2 hojas)

- **Hoja 1 "Determinacion CU"**: coeficientes con ratios de ingresos y gastos
- **Hoja 2 "Detalle Mensual"**: liquidaciones del ejercicio

Requiere `openpyxl`.

### Seguridad

| Grupo | Hereda de | Puede hacer |
|---|---|---|
| `group_cm_user` | `account.group_account_user` | Ver maestros, editar liquidaciones, usar exportadores |
| `group_cm_manager` | `group_cm_user` | Todo: crear/editar/borrar maestros, calcular coeficientes, confirmar liquidaciones |

### Dependencias

| Modulo | Razon |
|---|---|
| `account` | account.move, menus contabilidad, grupos seguridad |
| `l10n_ar` | CUIT, tipos documento AFIP, codigo tributo IIBB (`07`) |

Libreria Python opcional: `openpyxl` (solo para CM05).

### Decisiones tecnicas

| Decision | Por que |
|---|---|
| `cm.jurisdiction` separado de `res.country.state` | Codigo CM propio, constraints propias, desacoplado de datos base |
| Coeficientes como stored computed | Se calculan una vez, no en cada liquidacion |
| `cm_jurisdiction_id` computed + store + readonly=False | Automatico pero editable manualmente |
| Cache en `_compute_cm_jurisdiction_id` | Evita N+1 queries al resolver state → jurisdiction |
| Estados `draft → calculated → confirmed` | Wizard genera, usuario revisa, confirma cuando esta listo |
| Exportadores como TransientModel con estado draft/done | Auto-limpieza, patron consistente |
| Percepciones por `l10n_ar_tribute_afip_code = '07'` | Estandar de la localizacion argentina |
| `noupdate=1` en jurisdicciones | No se sobrescriben al actualizar el modulo |
