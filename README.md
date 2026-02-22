# Convenio Multilateral IIBB — `surtecnica_cm`

## 1. Introduccion

### Glosario: organismos y sistemas involucrados

Antes de arrancar, conviene saber que es cada cosa:

| Sigla | Nombre completo | Que es | Que hace |
|---|---|---|---|
| **IIBB** | Impuesto sobre los Ingresos Brutos | Impuesto provincial | Cada provincia cobra un % sobre los ingresos de las empresas que operan en su territorio |
| **CM** | Convenio Multilateral | Acuerdo entre provincias | Regula como se reparte la base imponible cuando una empresa opera en mas de una provincia, para que no pague el 100% en cada una |
| **COMARB** | Comision Arbitral del Convenio Multilateral | Organismo inter-provincial | Administra el CM. Recibe las declaraciones juradas (CM03, CM05), publica el nomenclador NAES, y arbitra conflictos entre provincias |
| **SIRCAR** | Sistema de Recaudacion y Control de Agentes de Recaudacion | Sistema web de COMARB | Ahi se informan las percepciones y retenciones que la empresa **practico a terceros** (es decir, las que vos le cobraste a tus clientes por orden de la provincia) |
| **SIFERE** | Sistema Federal de Recaudacion | Sistema web de COMARB | Ahi se informan las percepciones y retenciones que la empresa **sufrio** (es decir, las que te cobraron a vos). Sirve para justificar las deducciones en la liquidacion CM |
| **SIRCREB** | Sistema de Recaudacion y Control de Acreditaciones Bancarias | Sistema bancario | Los bancos debitan automaticamente IIBB sobre los depositos/acreditaciones en cuenta. Cada provincia fija su alicuota via padron |
| **NAES** | Nomenclador de Actividades Economicas del Sistema Federal | Tabla de codigos | Catalogo de ~1030 actividades economicas que usa COMARB para clasificar que hace cada empresa. Reemplazo al viejo CUACM en 2018 |
| **ATM** | Administracion Tributaria Mendoza | Organismo provincial | Ejemplo de organismo de rentas provincial. Cada provincia tiene el suyo (ARBA en Buenos Aires, API en Santa Fe, DGR en Cordoba, etc.) |
| **CM03** | Declaracion Jurada CM formulario 03 | Archivo XML | DDJJ mensual que se presenta ante COMARB con el detalle de la liquidacion por jurisdiccion |
| **CM05** | Declaracion Jurada CM formulario 05 | Archivo Excel | Presentacion anual ante COMARB con la determinacion de los coeficientes unificados |

### El problema

Una empresa que vende desde Buenos Aires a clientes en Cordoba, Santa Fe y Mendoza tiene que pagar IIBB en **cada provincia** donde genera ingresos. Odoo no sabe esto: solo maneja un impuesto plano, sin distribuir la base entre jurisdicciones.

El regimen de **Convenio Multilateral** (CM) exige:

1. Calcular un **coeficiente unificado** (CU) por jurisdiccion, basado en ingresos y gastos del año anterior
2. **Distribuir** la base imponible mensual de cada jurisdiccion usando ese coeficiente
3. **Liquidar** el impuesto con la alicuota que fija cada provincia
4. **Presentar** archivos digitales ante COMARB (CM03, CM05) y las jurisdicciones (SIRCAR, SIFERE)

### Como funciona el Convenio Multilateral

Cuando una empresa opera en **una sola provincia**, paga IIBB directamente ahi sobre el 100% de sus ingresos. Pero cuando opera en varias, entra al regimen de **Convenio Multilateral** para evitar pagar el 100% en cada una.

**La mecanica es esta:**

```
 AÑO ANTERIOR (base para calcular coeficientes)
 ================================================

 El coeficiente se calcula con dos datos del año anterior:
 INGRESOS y GASTOS por jurisdiccion.


 ¿QUE SON LOS INGRESOS?
 ───────────────────────
 Son las facturas de venta, asignadas a la jurisdiccion del CLIENTE.
 Si le vendiste a un cliente de Cordoba, ese ingreso se computa en Cordoba.

 Ejemplo (año 2025):
   Ventas a clientes de Cordoba:       $3.500.000
   Ventas a clientes de Santa Fe:      $2.500.000
   Ventas a clientes de Buenos Aires:  $4.000.000
   TOTAL PAIS:                        $10.000.000


 ¿QUE SON LOS GASTOS?
 ─────────────────────
 Son las facturas de compra, asignadas a la jurisdiccion del PROVEEDOR.
 Si le compraste a un proveedor de Cordoba, ese gasto se computa en Cordoba.

 Incluye todo lo que la empresa pago para operar en cada provincia:
   - Compras de mercaderia a proveedores de esa provincia
   - Alquileres de oficinas, depositos, locales en esa provincia
   - Servicios (luz, gas, internet, telefono) de esa provincia
   - Honorarios profesionales de esa provincia
   - Sueldos del personal que trabaja en esa provincia
   - Fletes, logistica, mantenimiento en esa provincia
   - Cualquier factura de compra de un proveedor de esa provincia

 Ejemplo (año 2025):
   Compras a proveedores de Cordoba:       $2.800.000
   Compras a proveedores de Santa Fe:      $2.000.000
   Compras a proveedores de Buenos Aires:  $3.200.000
   TOTAL PAIS:                             $8.000.000


 ¿POR QUE SE USAN LOS DOS?
 ──────────────────────────
 Porque el coeficiente busca reflejar CUANTO opera realmente la empresa
 en cada provincia. Si solo se miraran los ingresos, una empresa que
 vende mucho a Cordoba pero no tiene ninguna oficina ni proveedor ahi
 tendria un coeficiente alto. Combinando ingresos Y gastos se mide
 mejor la presencia real:

   - Si vendes mucho a Cordoba Y compras mucho ahi → coeficiente alto
   - Si vendes mucho a Cordoba pero no gastas nada ahi → coeficiente medio
   - Si no vendes ni gastas en Cordoba → coeficiente cero


 EL CALCULO
 ──────────
 Se promedia 50% ingresos + 50% gastos:

   CU = (% ingresos de esa provincia × 50%) + (% gastos de esa provincia × 50%)

 Ejemplo completo:
 ┌─────────────┬──────────┬─────────┬──────────┬─────────┬────────┐
 │ Jurisdiccion│ Ingresos │ % Ing.  │ Gastos   │ % Gasto │   CU   │
 ├─────────────┼──────────┼─────────┼──────────┼─────────┼────────┤
 │ Cordoba     │ 3.500.000│ 35.00%  │ 2.800.000│ 35.00%  │ 0.3500 │
 │ Santa Fe    │ 2.500.000│ 25.00%  │ 2.000.000│ 25.00%  │ 0.2500 │
 │ Buenos Aires│ 4.000.000│ 40.00%  │ 3.200.000│ 40.00%  │ 0.4000 │
 ├─────────────┼──────────┼─────────┼──────────┼─────────┼────────┤
 │ TOTAL       │10.000.000│100.00%  │ 8.000.000│100.00%  │ 1.0000 │
 └─────────────┴──────────┴─────────┴──────────┴─────────┴────────┘

 Cordoba: (35.00% × 50%) + (35.00% × 50%) = 17.50% + 17.50% = 0.3500
 Santa Fe: (25.00% × 50%) + (25.00% × 50%) = 12.50% + 12.50% = 0.2500

 La suma de todos los CU siempre da 1.0000 (el 100% se reparte).
 Estos coeficientes se usan TODO el año siguiente (2026).


 NOTA IMPORTANTE
 ───────────────
 En Odoo, los "ingresos" se toman de las facturas de venta (out_invoice,
 out_refund) y los "gastos" de las facturas de compra (in_invoice,
 in_refund). La jurisdiccion se asigna por la provincia del cliente
 o proveedor. Por eso es fundamental que cada contacto tenga la
 provincia cargada en su direccion.
```

```
 CADA MES (liquidacion)
 ================================================

 1. Se toma el TOTAL de ingresos gravados del mes
    (todas las facturas de venta, sin importar a que provincia)

    Ejemplo: base gravada total del mes = $1.000.000

 2. Se DISTRIBUYE esa base a cada jurisdiccion usando el CU:

    Cordoba:     $1.000.000 × 0.3500 = $350.000
    Santa Fe:    $1.000.000 × 0.2500 = $250.000
    Buenos Aires:$1.000.000 × 0.4000 = $400.000

 3. Se aplica la ALICUOTA que fija cada provincia:

    Cordoba:     $350.000 × 3.50% = $12.250
    Santa Fe:    $250.000 × 3.60% =  $9.000
    Buenos Aires:$400.000 × 4.00% = $16.000

 4. Se restan las DEDUCCIONES (lo que ya te cobraron):

    - Retenciones sufridas: lo que tus clientes te retuvieron al pagarte
    - Percepciones sufridas: lo que tus proveedores te cobraron de mas
    - Recaudaciones bancarias: lo que el banco te debito (SIRCREB)
    - Saldo anterior: saldo a favor del mes pasado

 5. El SALDO es lo que hay que pagar (o queda a favor):

    ┌─────────────┬──────────┬─────────┬────────────┬─────────┐
    │ Jurisdiccion│ Impuesto │ Deduc.  │ Saldo      │         │
    ├─────────────┼──────────┼─────────┼────────────┼─────────┤
    │ Cordoba     │ $12.250  │ $2.500  │ +$9.750    │ A pagar │
    │ Santa Fe    │  $9.000  │ $9.500  │   -$500    │ A favor │
    │ Buenos Aires│ $16.000  │ $4.000  │ +$12.000   │ A pagar │
    └─────────────┴──────────┴─────────┴────────────┴─────────┘

    El saldo a favor de Santa Fe (-$500) se arrastra al mes siguiente.
```

```
 PRESENTACIONES
 ================================================

 Con la liquidacion hecha, la empresa presenta:

 MENSUAL:
   CM03 → DDJJ mensual ante COMARB (resumen de la liquidacion)
   SIRCAR → percepciones que la empresa le cobro a terceros (informativo)
   SIFERE → retenciones/percepciones que le cobraron a la empresa (para computar deducciones)

 ANUAL:
   CM05 → justificacion de como se calcularon los coeficientes del año
```

### Como convive el CM con cada provincia (ejemplo Mendoza)

Para entender bien el CM hay que entender primero **como cobra IIBB una provincia sin CM**.

**Contribuyente local (sin CM):**
Si una empresa opera SOLO en Mendoza, es "contribuyente local" de esa provincia. Paga IIBB directo a ATM (Administracion Tributaria Mendoza) sobre el **100%** de sus ingresos. No hay coeficientes ni distribucion: todo lo que factura tributa en Mendoza.

**Contribuyente CM (con CM):**
Si esa misma empresa abre operaciones en Cordoba y Buenos Aires, ya no puede pagar el 100% en cada provincia (pagaria 3 veces). Ahi entra al regimen de CM y Mendoza pasa a recibir solo la **porcion que le corresponde** segun el coeficiente.

Pero aca viene la parte clave: **las provincias no esperan a que la empresa liquide el CM para cobrar**. Cada provincia tiene mecanismos para cobrar IIBB por adelantado, en el momento en que ocurre la operacion.

```
 LAS 3 VIAS POR LAS QUE UNA PROVINCIA COBRA IIBB "POR ADELANTADO"
 ==================================================================

 1. PERCEPCIONES (te cobran de mas en las facturas de compra)
    ─────────────────────────────────────────────────────────
    Cuando un proveedor de Mendoza te factura, ATM le obliga a
    cobrarte un % extra en concepto de percepcion IIBB.

    Ejemplo: compras mercaderia por $100.000 + 21% IVA + 3% percepcion IIBB
    La factura del proveedor viene con $3.000 de percepcion.
    Ese dinero va directo a ATM como pago a cuenta de tu IIBB.

    ¿Quien lo cobra? → Tu proveedor, por orden de ATM
    ¿Cuando? → En cada factura de compra
    ¿Como se entera Odoo? → Es una linea de impuesto en la factura de compra


 2. RETENCIONES (te descuentan cuando te pagan)
    ────────────────────────────────────────────
    Cuando un cliente de Mendoza te paga una factura, ATM le obliga
    a retenerte un % y depositarlo en la provincia.

    Ejemplo: le facturaste $100.000. Al pagarte, el cliente te transfiere
    $97.000 y deposita $3.000 en ATM como retencion IIBB.

    ¿Quien lo cobra? → Tu cliente, por orden de ATM
    ¿Cuando? → En cada pago que te hacen
    ¿Como se entera Odoo? → Es una linea de impuesto en el recibo de cobro


 3. RECAUDACIONES BANCARIAS / SIRCREB (el banco te debita)
    ──────────────────────────────────────────────────────
    El banco donde tenes cuenta mira tus movimientos y le descuenta
    automaticamente un % a favor de cada provincia donde operas.

    Ejemplo: durante el mes entraron $500.000 a tu cuenta. El banco
    te debita $1.500 a favor de Mendoza (0.30% segun padron SIRCREB).

    ¿Quien lo cobra? → Tu banco, automaticamente
    ¿Cuando? → Mensual, segun movimientos bancarios
    ¿Como se entera Odoo? → Se carga manualmente en la liquidacion CM
```

```
 COMO SE CIERRA LA CUENTA CADA MES
 ==================================================================

 Al fin de mes, cuando la empresa hace la liquidacion CM, pasa esto:

 ┌─────────────────────────────────────────────────────────────────┐
 │ LIQUIDACION CM - MENDOZA (jurisdiccion 913) - Enero 2026       │
 ├─────────────────────────────────────────────────────────────────┤
 │                                                                 │
 │ Base gravada total del mes:           $1.000.000                │
 │ Coeficiente Mendoza:                  × 0.3000                  │
 │                                       ─────────                 │
 │ Base distribuida a Mendoza:           $300.000                  │
 │ Alicuota Mendoza:                     × 3.00%                   │
 │                                       ─────────                 │
 │ IMPUESTO DETERMINADO:                 $9.000   ← lo que Mendoza│
 │                                                    tiene derecho│
 │                                                    a cobrar     │
 │ Menos lo que Mendoza YA cobro:                                  │
 │   Percepciones sufridas:              -$2.000                   │
 │   Retenciones sufridas:               -$3.000                   │
 │   Recaudaciones bancarias (SIRCREB):  -$1.500                   │
 │   Saldo a favor mes anterior:         -$0                       │
 │                                       ─────────                 │
 │ TOTAL DEDUCCIONES:                    -$6.500                   │
 │                                       ─────────                 │
 │ SALDO A PAGAR:                        $2.500   ← solo falta    │
 │                                                    pagar esto   │
 └─────────────────────────────────────────────────────────────────┘

 Si las deducciones fueran MAS que el impuesto (por ejemplo $10.000
 de deducciones contra $9.000 de impuesto), el saldo seria -$1.000
 (a favor). Ese saldo se arrastra al mes siguiente como deduccion.
```

```
 ¿QUE PASA SI MENDOZA YA COBRO MAS DE LO QUE LE CORRESPONDE?
 ==================================================================

 Es comun. Las percepciones, retenciones y SIRCREB se calculan sobre
 montos brutos, sin considerar el coeficiente CM. Entonces puede pasar
 que Mendoza ya cobro $12.000 entre los 3 mecanismos, pero por CM le
 corresponden solo $9.000.

 En ese caso el saldo es -$3.000 (a favor de la empresa).
 Ese credito se usa el mes siguiente. Si se acumula mucho saldo a
 favor, la empresa puede pedir devolucion a ATM.
```

```
 RESUMEN: ¿QUIEN COBRA QUE?
 ==================================================================

 ┌────────────────────┬──────────────────┬─────────────┬──────────────────┐
 │ Concepto           │ Quien cobra      │ Cuando      │ Se deduce en CM? │
 ├────────────────────┼──────────────────┼─────────────┼──────────────────┤
 │ Percepciones IIBB  │ Tus proveedores  │ Al comprar  │ Si               │
 │ Retenciones IIBB   │ Tus clientes     │ Al cobrarte │ Si               │
 │ SIRCREB            │ Tu banco         │ Mensual     │ Si               │
 │ Saldo CM           │ La provincia     │ Mensual     │ Es el neto final │
 └────────────────────┴──────────────────┴─────────────┴──────────────────┘

 Los primeros 3 son pagos a cuenta. El saldo CM es la diferencia.
 Si los pagos a cuenta superan el impuesto, la empresa tiene credito.
```

**En resumen:** la empresa no paga IIBB sobre el total en cada provincia; reparte la base proporcionalmente usando un coeficiente que refleja cuanto opera realmente en cada una. Las provincias cobran adelantos por 3 vias (percepciones, retenciones, SIRCREB) y el CM cierra la cuenta descontando esos adelantos del impuesto que corresponde a cada jurisdiccion.

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
 2. Cargar actividades NAES          → una por jurisdiccion donde operas
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

### 3.3 Nomenclador NAES (viene pre-cargado)

**Menu:** Contabilidad > Configuracion > Convenio Multilateral > Nomenclador NAES

El modulo incluye las 1030 actividades del nomenclador NAES (Nomenclador de Actividades Economicas del Sistema Federal) pre-cargadas. Es la tabla de referencia oficial de COMARB que reemplaza al viejo CUACM desde 2018.

No requiere configuracion. Se usa como lookup al cargar actividades.

### 3.4 Actividades NAES

**Menu:** Contabilidad > Configuracion > Convenio Multilateral > Actividades NAES

Cargar una linea por cada jurisdiccion donde la empresa tiene actividad. La actividad se selecciona de un dropdown con busqueda por codigo o descripcion:

| Jurisdiccion | Actividad NAES | Alicuota % | Regimen |
|---|---|---|---|
| [904] Cordoba | [519000] Vta. mayor art. electricos | 3.50 | Art. 2 - General |
| [921] Santa Fe | [519000] Vta. mayor art. electricos | 3.60 | Art. 2 - General |
| [902] Buenos Aires | [519000] Vta. mayor art. electricos | 4.00 | Art. 2 - General |

**Donde conseguir los datos:**
- **Actividad NAES:** ya esta pre-cargada, buscar por codigo o descripcion en el dropdown
- **Alicuota:** pagina de rentas de cada provincia
- **Regimen:** Art. 2 (General) para la mayoria. Otros articulos para construccion, seguros, bancos, transporte, etc.
- **Vigencia (opcional):** si cambia la alicuota, poner fecha desde/hasta para tener historial

---

### 3.5 Coeficientes unificados

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
│   ├── cm_naes.py                # Nomenclador NAES (1030 actividades pre-cargadas)
│   ├── cm_activity.py            # Actividad NAES + alicuota por jurisdiccion
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
cm.naes ──────────┐
(1030 actividades) │
                   ▼
              cm.activity    cm.coefficient
              (NAES+alic)    (CU por año)
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

#### `cm.naes`

| Campo | Tipo | Descripcion |
|---|---|---|
| `code` | Char(6), unique, indexed | Codigo NAES |
| `name` | Char, required | Descripcion de la actividad |
| `active` | Boolean | Archivado logico |

1030 registros pre-cargados (noupdate=1). `name_get()` devuelve `[CODE] Descripcion`.

#### `cm.activity`

| Campo | Tipo | Descripcion |
|---|---|---|
| `company_id` | Many2one `res.company` | Empresa |
| `jurisdiction_id` | Many2one `cm.jurisdiction` | Jurisdiccion (restrict) |
| `naes_id` | Many2one `cm.naes` | Actividad NAES (restrict) |
| `alicuota` | Float(6,4) | Tasa IIBB % |
| `art_regimen` | Selection | Art. 2 a 13 del CM |
| `date_from` / `date_to` | Date | Vigencia |

Unique: `(company_id, jurisdiction_id, naes_id)`.

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
