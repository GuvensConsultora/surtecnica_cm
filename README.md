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

Una empresa que vende desde Mendoza a clientes en Buenos Aires, Cordoba y Santa Fe tiene que pagar IIBB en **cada provincia** donde genera ingresos. Odoo no sabe esto: solo maneja un impuesto plano, sin distribuir la base entre jurisdicciones.

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

 ¿QUE MONTO SE TOMA?
 El monto NETO de la factura, sin IVA ni otros impuestos nacionales.
 En Odoo es el campo "Base Imponible" (amount_untaxed).

 Se llama "ingreso bruto" porque no se le restan costos, gastos ni
 deducciones de ganancias — es la venta pura. Pero se EXCLUYEN los
 impuestos que son recaudacion de otro fisco (IVA, Imp. Internos, etc.)
 porque esos no son ingresos de la empresa, son recaudacion del Estado.

 Ejemplo de una factura:
   Subtotal (precio × cantidad):        $100.000  ← ESTO se toma
   IVA 21%:                              $21.000  ← esto NO
   Percepcion IIBB 3%:                    $3.000  ← esto NO
   Total factura:                        $124.000

 Ejemplo (año 2025, empresa con sede en Mendoza):
   Ventas a clientes de Mendoza:       $4.000.000  (neto sin IVA)
   Ventas a clientes de Buenos Aires:  $3.500.000  (neto sin IVA)
   Ventas a clientes de Cordoba:       $2.500.000  (neto sin IVA)
   TOTAL PAIS:                        $10.000.000


 ¿QUE SON LOS GASTOS?
 ─────────────────────
 Son las facturas de compra, asignadas a la jurisdiccion del PROVEEDOR.
 Si le compraste a un proveedor de Cordoba, ese gasto se computa en Cordoba.
 Tambien se toma el monto neto sin IVA (amount_untaxed).

 Incluye todo lo que la empresa pago para operar en cada provincia:
   - Compras de mercaderia a proveedores de esa provincia
   - Alquileres de oficinas, depositos, locales en esa provincia
   - Servicios (luz, gas, internet, telefono) de esa provincia
   - Honorarios profesionales de esa provincia
   - Sueldos del personal que trabaja en esa provincia
   - Fletes, logistica, mantenimiento en esa provincia
   - Cualquier factura de compra de un proveedor de esa provincia

 Ejemplo (año 2025, empresa con sede en Mendoza):
   Compras a proveedores de Mendoza:       $3.200.000
   Compras a proveedores de Buenos Aires:  $2.800.000
   Compras a proveedores de Cordoba:       $2.000.000
   TOTAL PAIS:                             $8.000.000


 ¿POR QUE SE USAN LOS DOS?
 ──────────────────────────
 Porque el coeficiente busca reflejar CUANTO opera realmente la empresa
 en cada provincia. Si solo se miraran los ingresos, una empresa que
 vende mucho a Cordoba pero no tiene ninguna oficina ni proveedor ahi
 tendria un coeficiente alto. Combinando ingresos Y gastos se mide
 mejor la presencia real:

   - Si vendes mucho a Mendoza Y compras mucho ahi → coeficiente alto
   - Si vendes mucho a Buenos Aires pero no gastas nada ahi → coeficiente medio
   - Si no vendes ni gastas en Cordoba → coeficiente cero


 EL CALCULO
 ──────────
 Se promedia 50% ingresos + 50% gastos:

   CU = (% ingresos de esa provincia × 50%) + (% gastos de esa provincia × 50%)

 Ejemplo completo (empresa con sede en Mendoza):
 ┌─────────────┬──────────┬─────────┬──────────┬─────────┬────────┐
 │ Jurisdiccion│ Ingresos │ % Ing.  │ Gastos   │ % Gasto │   CU   │
 ├─────────────┼──────────┼─────────┼──────────┼─────────┼────────┤
 │ Mendoza     │ 4.000.000│ 40.00%  │ 3.200.000│ 40.00%  │ 0.4000 │
 │ Buenos Aires│ 3.500.000│ 35.00%  │ 2.800.000│ 35.00%  │ 0.3500 │
 │ Cordoba     │ 2.500.000│ 25.00%  │ 2.000.000│ 25.00%  │ 0.2500 │
 ├─────────────┼──────────┼─────────┼──────────┼─────────┼────────┤
 │ TOTAL       │10.000.000│100.00%  │ 8.000.000│100.00%  │ 1.0000 │
 └─────────────┴──────────┴─────────┴──────────┴─────────┴────────┘

 Mendoza:      (40.00% × 50%) + (40.00% × 50%) = 20.00% + 20.00% = 0.4000
 Buenos Aires: (35.00% × 50%) + (35.00% × 50%) = 17.50% + 17.50% = 0.3500

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

    Mendoza:      $1.000.000 × 0.4000 = $400.000
    Buenos Aires: $1.000.000 × 0.3500 = $350.000
    Cordoba:      $1.000.000 × 0.2500 = $250.000

 3. Se aplica la ALICUOTA que fija cada provincia:

    Mendoza:      $400.000 × 3.00% = $12.000
    Buenos Aires: $350.000 × 4.00% = $14.000
    Cordoba:      $250.000 × 3.50% =  $8.750

 4. Se restan las DEDUCCIONES (lo que ya te cobraron):

    - Retenciones sufridas: lo que tus clientes te retuvieron al pagarte
    - Percepciones sufridas: lo que tus proveedores te cobraron de mas
    - Recaudaciones bancarias: lo que el banco te debito (SIRCREB)
    - Saldo anterior: saldo a favor del mes pasado

 5. El SALDO es lo que hay que pagar (o queda a favor):

    ┌─────────────┬──────────┬─────────┬────────────┬─────────┐
    │ Jurisdiccion│ Impuesto │ Deduc.  │ Saldo      │         │
    ├─────────────┼──────────┼─────────┼────────────┼─────────┤
    │ Mendoza     │ $12.000  │ $13.500 │   -$1.500  │ A favor │
    │ Buenos Aires│ $14.000  │  $4.000 │ +$10.000   │ A pagar │
    │ Cordoba     │  $8.750  │  $2.500 │  +$6.250   │ A pagar │
    └─────────────┴──────────┴─────────┴────────────┴─────────┘

    El saldo a favor de Mendoza (-$1.500) se arrastra al mes siguiente.
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

### Como convive el CM con cada provincia

Para entender bien el CM hay que entender primero **como cobra IIBB una provincia sin CM**.

**Contribuyente local (sin CM):**
Si la empresa opera SOLO en Mendoza, es "contribuyente local" de esa provincia. Paga IIBB directo a ATM (Administracion Tributaria Mendoza) sobre el **100%** de sus ingresos. No hay coeficientes ni distribucion: todo lo que factura tributa en Mendoza.

**Contribuyente CM (con CM):**
Cuando la empresa empieza a vender tambien a Buenos Aires y Cordoba, ya no puede pagar el 100% en cada provincia (pagaria 3 veces). Ahi entra al regimen de CM y cada provincia pasa a recibir solo la **porcion que le corresponde** segun el coeficiente.

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

### Padrones provinciales: ARBA, AGIP, DGR y las alicuotas que cambian

Cada provincia tiene su propio organismo de rentas y sus propias reglas para percepciones y retenciones. La empresa de Mendoza que vende a Buenos Aires, CABA y Cordoba tiene que lidiar con todos ellos.

```
 LOS ORGANISMOS DE RENTAS PROVINCIALES
 ==================================================================

 Cada provincia tiene un organismo que administra IIBB:

 ┌──────────────────┬────────────┬────────────────────────────────┐
 │ Provincia        │ Organismo  │ Nombre completo                │
 ├──────────────────┼────────────┼────────────────────────────────┤
 │ Buenos Aires     │ ARBA       │ Agencia de Recaudacion de      │
 │                  │            │ Buenos Aires                   │
 │ CABA             │ AGIP       │ Administracion Gubernamental   │
 │                  │            │ de Ingresos Publicos           │
 │ Cordoba          │ DGR        │ Direccion General de Rentas    │
 │ Mendoza          │ ATM        │ Administracion Tributaria      │
 │                  │            │ Mendoza                        │
 │ Santa Fe         │ API        │ Administracion Provincial de   │
 │                  │            │ Impuestos                      │
 │ Tucuman          │ DGR        │ Direccion General de Rentas    │
 │ (otras)          │ DGR/DPR    │ Cada provincia tiene el suyo   │
 └──────────────────┴────────────┴────────────────────────────────┘

 Cada organismo fija SUS PROPIAS reglas:
   - Que alicuota de percepcion/retencion aplica a cada contribuyente
   - Cada cuanto se actualizan las alicuotas
   - En que formato hay que informar
   - Que contribuyentes estan obligados a actuar como agentes
```

```
 ¿QUE ES UN PADRON?
 ==================================================================

 Un padron es un archivo que publica cada provincia con la lista de
 contribuyentes y la alicuota que le corresponde a cada uno.

 Cuando ARBA publica su padron, basicamente dice:

   "Si le vendes a CUIT 20-12345678-9, cobrale 3.00% de percepcion.
    Si le vendes a CUIT 30-98765432-1, cobrale 1.50%.
    Si le vendes a CUIT 27-11111111-1, no le cobres nada (0.00%)."

 Cada CUIT tiene su propia alicuota, que ARBA calcula segun el
 comportamiento fiscal del contribuyente (si pago en termino, si tiene
 deuda, si presento las DDJJ, etc.).

 ┌─────────────────┬─────────────────────────┬───────────────────────┐
 │ Provincia       │ Nombre del padron       │ Frecuencia de cambio  │
 ├─────────────────┼─────────────────────────┼───────────────────────┤
 │ Buenos Aires    │ Padron ARBA (IIBB)      │ Cada 2 meses (bim.)  │
 │ CABA            │ Padron AGIP             │ Cada 6 meses (sem.)  │
 │ Cordoba         │ Padron DGR Cordoba      │ Mensual               │
 │ Mendoza         │ Padron ATM              │ Variable              │
 │ Santa Fe        │ Padron API              │ Mensual               │
 └─────────────────┴─────────────────────────┴───────────────────────┘

 IMPORTANTE: las alicuotas cambian periodicamente. Un cliente al que
 hoy le percibis 3.00% puede pasar a 1.50% el proximo bimestre.
 La empresa tiene la obligacion de descargar el padron actualizado
 y aplicar las alicuotas vigentes.
```

```
 LOS DOS ROLES DE LA EMPRESA
 ==================================================================

 La empresa de Mendoza tiene DOS roles al mismo tiempo:


 ROL 1: AGENTE DE PERCEPCION/RETENCION (cobra impuesto de terceros)
 ───────────────────────────────────────────────────────────────────
 Si la provincia designa a la empresa como "agente", la empresa esta
 OBLIGADA a cobrarles IIBB a sus clientes e ingresarlo a la provincia.

 Ejemplo: ARBA designa a la empresa como agente de percepcion
 de Buenos Aires. Cuando la empresa le factura a un cliente de
 Buenos Aires, tiene que:

   1. Consultar el padron de ARBA para ver que alicuota le corresponde
      a ese cliente (ej: 3.00%)
   2. Agregar una linea de percepcion IIBB en la factura
   3. Cobrarle ese monto al cliente junto con la factura
   4. Depositarlo en ARBA a fin de mes
   5. Informarlo en SIRCAR

 ┌──────────────────────────────────────────────────────────────────┐
 │ Factura de venta a cliente de Buenos Aires                      │
 ├──────────────────────────────────────────────────────────────────┤
 │ Subtotal:                          $100.000                     │
 │ IVA 21%:                            $21.000                     │
 │ Percepcion IIBB Bs.As. (3.00%):     $3.000  ← la empresa cobra │
 │                                              por orden de ARBA  │
 │ TOTAL:                             $124.000                     │
 └──────────────────────────────────────────────────────────────────┘

 Esos $3.000 NO son ingreso de la empresa. Son plata de ARBA
 que la empresa recauda por obligacion. Se informa en SIRCAR.


 ROL 2: SUJETO PERCIBIDO/RETENIDO (le cobran impuesto a ella)
 ─────────────────────────────────────────────────────────────
 Cuando la empresa compra a un proveedor que es agente de percepcion,
 o cuando un cliente que es agente de retencion le paga, la empresa
 SUFRE esas percepciones/retenciones.

 Ejemplo: la empresa compra mercaderia a un proveedor de Cordoba
 que es agente de percepcion de DGR Cordoba:

 ┌──────────────────────────────────────────────────────────────────┐
 │ Factura de compra de proveedor de Cordoba                       │
 ├──────────────────────────────────────────────────────────────────┤
 │ Subtotal:                          $100.000                     │
 │ IVA 21%:                            $21.000                     │
 │ Percepcion IIBB Cordoba (2.50%):     $2.500  ← el proveedor    │
 │                                              cobra por orden    │
 │                                              de DGR Cordoba     │
 │ TOTAL:                             $123.500                     │
 └──────────────────────────────────────────────────────────────────┘

 Esos $2.500 son plata que la empresa YA PAGO a Cordoba de
 forma anticipada. Se descuentan en la liquidacion CM como
 "percepciones sufridas" en la jurisdiccion Cordoba.
 Se informan en SIFERE.
```

```
 COMO ENCAJA TODO JUNTO (ejemplo mes de enero)
 ==================================================================

 La empresa de Mendoza durante enero:

 1. VENDIO a clientes de 3 provincias y les PERCIBIO IIBB:
    (porque ARBA, DGR y ATM la designaron agente de percepcion)

    Buenos Aires: percibio $8.000 de sus clientes → deposita en ARBA
    Cordoba:      percibio $4.000 de sus clientes → deposita en DGR
    Mendoza:      percibio $5.000 de sus clientes → deposita en ATM

    Todo esto se informa en SIRCAR.

 2. COMPRO a proveedores que le PERCIBIERON IIBB:
    (porque esos proveedores son agentes de sus respectivas provincias)

    Un proveedor de Bs.As. le percibio:  $2.000 a favor de ARBA
    Un proveedor de Cordoba le percibio: $1.500 a favor de DGR
    Un proveedor de Mendoza le percibio: $3.000 a favor de ATM

 3. COBRO facturas y sus clientes le RETUVIERON IIBB:

    Un cliente de Bs.As. le retuvo:      $1.500 a favor de ARBA
    Un cliente de Mendoza le retuvo:     $2.000 a favor de ATM

 4. El banco le DEBITO SIRCREB:

    Buenos Aires: $500
    Cordoba:      $300
    Mendoza:      $1.200

 5. En la LIQUIDACION CM se cierra la cuenta por jurisdiccion:

    ┌─────────────┬──────────┬─────────┬────────┬─────────┬─────────┐
    │ Jurisdiccion│ Impuesto │ Perc.   │ Ret.   │ SIRCREB │ Saldo   │
    │             │ CM       │sufridas │sufridas│         │         │
    ├─────────────┼──────────┼─────────┼────────┼─────────┼─────────┤
    │ Mendoza     │ $12.000  │ $3.000  │ $2.000 │ $1.200  │ +$5.800 │
    │ Buenos Aires│ $14.000  │ $2.000  │ $1.500 │   $500  │+$10.000 │
    │ Cordoba     │  $8.750  │ $1.500  │   $0   │   $300  │ +$6.950 │
    └─────────────┴──────────┴─────────┴────────┴─────────┴─────────┘

    La empresa paga el saldo a cada provincia por separado:
      → $5.800 a ATM (Mendoza)
      → $10.000 a ARBA (Buenos Aires)
      → $6.950 a DGR (Cordoba)

 RESUMEN DEL FLUJO DE PLATA:
 ┌─────────────────────────────────────────────────────────────────┐
 │ Lo que la empresa COBRO de terceros  →  lo deposita en SIRCAR  │
 │ (percepciones/retenciones practicadas)  (no es plata suya)     │
 │                                                                 │
 │ Lo que a la empresa LE COBRARON     →  lo deduce en la liquid. │
 │ (percepciones/retenciones sufridas)    CM y lo informa en      │
 │ (SIRCREB)                              SIFERE                  │
 │                                                                 │
 │ La diferencia                       →  la paga a cada provincia│
 │ (saldo CM)                             por VEP/transferencia   │
 └─────────────────────────────────────────────────────────────────┘
```

```
 ¿DE DONDE SALEN LAS ALICUOTAS EN ODOO?
 ==================================================================

 En Odoo, las alicuotas de percepcion/retencion se configuran en los
 impuestos (account.tax). Hay dos formas de mantenerlas actualizadas:

 1. MANUAL: el contador descarga el padron de cada provincia, busca
    los CUITs de sus clientes/proveedores, y actualiza las alicuotas
    en Odoo cuando cambian. Funciona para pocas operaciones.

 2. AUTOMATICA: modulos de localizacion argentina (como
    l10n_ar_withholding) permiten importar los padrones y aplicar
    las alicuotas automaticamente segun el CUIT del cliente/proveedor.
    Recomendado cuando hay muchas operaciones.

 El modulo surtecnica_cm NO gestiona las alicuotas de percepcion/
 retencion (eso lo hace la localizacion argentina). Lo que SI hace
 es tomar las percepciones y retenciones ya registradas en Odoo y
 exportarlas en los formatos que piden SIRCAR y SIFERE.
```

### Modulo de retenciones/percepciones en Odoo 19 (withholding)

Las percepciones y retenciones que se mencionaron arriba no las maneja `surtecnica_cm`. Las maneja un conjunto de modulos de la comunidad argentina (`a2systems/odoo-argentina`):

```
 ARQUITECTURA DE MODULOS
 ==================================================================

 account_payment_group          ← Agrupa pagos (base)
   └── account_withholding_automatic  ← Calcula retenciones automaticas
        └── l10n_ar_account_withholding        ← Argentinizacion (Ganancias, IIBB)
             └── l10n_ar_account_withholding_automatic  ← Padrones ARBA/AGIP
```

```
 ¿QUE HACE CADA UNO?
 ==================================================================

 account_payment_group
 ─────────────────────
 Agrega el concepto de "Orden de Pago" (account.payment.group):
 en vez de pagar factura por factura, agrupa varias facturas de un
 proveedor en un solo pago. El grupo contiene N lineas de pago
 (account.payment) que pueden ser transferencias, cheques, etc.

 Flujo: draft → confirmed → posted
   - En draft: se seleccionan facturas a pagar
   - En confirmed: se agregan los medios de pago
   - En posted: se generan asientos y se concilia todo


 account_withholding_automatic
 ─────────────────────────────
 Extiende el payment group con un boton "Calcular Retenciones".
 Para cada impuesto con tipo retencion != 'none':

   1. Calcula la base imponible (neto o bruto segun config)
   2. Acumula pagos previos del periodo (mes/año)
   3. Aplica minimo no imponible
   4. Calcula la retencion segun el tipo:
      - based_on_rule: porcentaje + monto fijo segun reglas
      - code: ejecuta codigo Python custom
      - partner_tax: lee alicuota del partner
      - tabla_ganancias: escala progresiva AFIP
   5. Resta retenciones ya practicadas en el periodo
   6. Crea un account.payment automatico con el monto


 l10n_ar_account_withholding
 ───────────────────────────
 Agrega la logica argentina:

 IMPUESTO A LAS GANANCIAS:
   - Busca condicion del partner: AC (inscripto), NI (no inscripto),
     EX (exento), NC (no categorizado)
   - Si AC: busca regimen (ej: Regimen 21 - Intereses, porcentaje 6%)
     Si porcentaje = -1: usa tabla de escalas (fijo + % sobre excedente)
   - Si NI: aplica alicuota no inscripto (ej: 28%)
   - Si EX/NC: no retiene

 IIBB PROVINCIAL:
   - Agrega amount_type = 'partner_tax' en account.tax
   - Lee la alicuota desde el partner (res.partner.perception_ids)
   - La alicuota se busca por impuesto + vigencia de fechas


 l10n_ar_account_withholding_automatic
 ─────────────────────────────────────
 Agrega integracion con padrones provinciales:

 ARBA:
   - Consulta WebService de ARBA con CUIT del partner
   - Obtiene alicuota_percepcion y alicuota_retencion
   - Cachea en res.partner.arba_alicuot (por periodo/empresa)
   - Configuracion: CUIT agente + certificado en res.company

 AGIP:
   - Campos para alicuota no inscripto (percepcion y retencion)
   - Tipo de padron (regimenes generales)
```

```
 EJEMPLO: PAGO A PROVEEDOR CON RETENCIONES
 ==================================================================

 Factura proveedor: $100.000 + IVA 21% = $121.000
 El proveedor esta inscripto en Ganancias (regimen 21, 6%)
 y tiene alicuota IIBB Mendoza del 3%

 1. CREAR ORDEN DE PAGO
    ├── Seleccionar proveedor
    ├── Seleccionar la factura ($121.000)
    └── selected_debt = $121.000

 2. CLICK "CALCULAR RETENCIONES"
    El sistema busca todos los impuestos con retencion activa:

    Retencion Ganancias:
      Base = $100.000 (neto, amount_untaxed)
      Regimen 21, porcentaje inscripto = 6%
      Monto no sujeto a retencion = $7.870
      Base imponible = $100.000 - $7.870 = $92.130
      Retencion = $92.130 × 6% = $5.527,80

    Retencion IIBB Mendoza:
      Base = $100.000 (neto)
      Alicuota del partner = 3%
      Retencion = $100.000 × 3% = $3.000

 3. EL PAYMENT GROUP QUEDA CON 3 PAGOS:
    ┌─────────────────────────────────┬────────────┐
    │ Concepto                        │ Monto      │
    ├─────────────────────────────────┼────────────┤
    │ Transferencia banco             │ $112.472,20│
    │ Ret. Ganancias (automatica)     │   $5.527,80│
    │ Ret. IIBB Mendoza (automatica)  │   $3.000,00│
    ├─────────────────────────────────┼────────────┤
    │ TOTAL                           │ $121.000,00│
    └─────────────────────────────────┴────────────┘

 4. AL CONFIRMAR:
    - Se postean los 3 pagos (3 asientos contables)
    - Se concilian contra la factura
    - La factura queda en estado "paid"
    - El proveedor recibio $112.472,20
    - Las retenciones quedan en cuentas contables separadas
      para depositar a AFIP y ATM respectivamente
```

```
 ACUMULACION EN EL PERIODO
 ==================================================================

 Si en el mismo mes se le pagan 3 facturas al mismo proveedor:

   Pago 1 (5/ene): base $50.000 → ret. Ganancias $2.527,80
   Pago 2 (15/ene): base $30.000 → acumulado $80.000
     → periodo = $80.000 - $7.870 = $72.130 × 6% = $4.327,80
     → ya retenido = $2.527,80
     → retencion pago 2 = $4.327,80 - $2.527,80 = $1.800,00
   Pago 3 (25/ene): base $20.000 → acumulado $100.000
     → periodo = $100.000 - $7.870 = $92.130 × 6% = $5.527,80
     → ya retenido = $4.327,80
     → retencion pago 3 = $5.527,80 - $4.327,80 = $1.200,00

 El sistema acumula automaticamente los pagos del mes para que
 la retencion total del periodo sea correcta, sin importar en
 cuantas cuotas se pague.
```

```
 MEJORAS PENDIENTES DEL MODULO WITHHOLDING
 ==================================================================

 1. PADRONES PROVINCIALES LIMITADOS
    Solo tiene integracion con ARBA (Buenos Aires).
    Falta:
    ├── AGIP (CABA) → tiene WebService pero no esta implementado
    ├── ATM (Mendoza) → requiere carga manual de padron CSV
    ├── API (Santa Fe) → idem
    ├── DGR (Cordoba) → idem
    └── Resto de provincias
    Mejora: wizard de importacion de padrones CSV/TXT generico
    que actualice las alicuotas en res.partner automaticamente.

 2. NO HAY CERTIFICADOS DE RETENCION
    Cuando la empresa retiene, debe entregar un certificado al
    proveedor. El reporte existe pero esta comentado en el codigo.
    Mejora: implementar PDF con datos del agente, sujeto retenido,
    nro certificado, fecha, monto, regimen.

 3. NO HAY EXPORTACION MASIVA
    Las retenciones practicadas deben informarse a:
    ├── SICORE (retenciones Ganancias/IVA → AFIP)
    ├── SIFERE (informar retenciones sufridas → COMARB)
    └── Archivo de cada provincia (ARBA, ATM, etc.)
    Mejora: wizards de exportacion (surtecnica_cm ya resuelve
    SIRCAR/SIFERE para Convenio Multilateral).

 4. NO HAY REVERSION AUTOMATICA DE RETENCIONES
    Si se cancela un payment group, se desconcilia pero no se
    genera un asiento de reversion de la retencion.
    Mejora: al cancelar, generar asiento inverso automaticamente.

 5. RECALCULO RETROACTIVO
    Si se modifica un pago anterior del mes, las retenciones
    acumuladas de pagos posteriores quedan inconsistentes.
    Mejora: metodo de recalculo masivo por periodo.

 6. MULTIMONEDA
    Todo se calcula en moneda de la empresa. No hay soporte para
    pagos en USD u otra moneda extranjera.

 7. VALIDACION DE CONDICION FISCAL
    El campo imp_ganancias_padron (AC/NI/EX/NC) se carga manual.
    Mejora: consulta automatica a AFIP para determinar la condicion
    fiscal del partner.
```

```
 RELACION CON SURTECNICA_CM
 ==================================================================

 surtecnica_cm CONSUME datos del modulo withholding:

 ┌───────────────────────────┐     ┌───────────────────────────┐
 │ l10n_ar_withholding       │     │ surtecnica_cm             │
 ├───────────────────────────┤     ├───────────────────────────┤
 │ Calcula retenciones       │────→│ Toma las tax lines con    │
 │ y percepciones en pagos   │     │ codigo IIBB ('07') y las  │
 │ y facturas                │     │ exporta en formato SIRCAR │
 │                           │     │ y SIFERE                  │
 │ Registra en account.move  │     │                           │
 │ y account.payment         │────→│ Las deducciones de la     │
 │                           │     │ liquidacion CM vienen de  │
 │                           │     │ ahi (percepciones/ret.    │
 │                           │     │ sufridas por jurisdiccion)│
 └───────────────────────────┘     └───────────────────────────┘

 En resumen:
   withholding → calcula y registra las percepciones/retenciones
   surtecnica_cm → las lee, las agrupa por jurisdiccion, y las
                   exporta en los formatos que piden COMARB y
                   las provincias
```

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
 Cliente:       Ferreteria Central SA
 Provincia:     Buenos Aires
 Jurisdiccion:  [902] Buenos Aires  ← se completo solo
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
5. **Auto-carga deducciones** desde datos contables:
   - **Percepciones sufridas:** busca tax lines IIBB ('07') en facturas de compra del periodo, agrupadas por jurisdiccion
   - **Retenciones sufridas:** busca retenciones IIBB en cobros inbound del periodo, resolviendo jurisdiccion desde la provincia del cliente
   - **Saldo anterior:** si el periodo anterior tiene saldo negativo (a favor), lo arrastra como deduccion
6. Incluye jurisdicciones que tienen deducciones aunque no tengan ventas en el periodo
7. Crea la liquidacion en estado **"Calculada"**

> Las deducciones pre-cargadas quedan **editables** — el contador puede corregir cualquier valor. Solo `recaudaciones_bancarias` queda manual (dato bancario, no esta en Odoo).

---

### Paso 7: Revisar deducciones y trazabilidad

**Menu:** Contabilidad > Contabilidad > Liquidacion CM

> **Vista kanban:** al abrir el menu, se ve un tablero kanban agrupado por estado (Borrador / Calculada / Confirmada) con resumen monetario de cada liquidacion. Tambien se puede cambiar a vista lista.

Se abre la liquidacion generada. Tiene una linea por cada jurisdiccion donde hubo ventas o deducciones:

```
 LIQUIDACION CM 2026/01 - Mi Empresa SA
 ═══════════════════════════════════════════════════════════════════════════════

 Jurisdiccion  │ Coef.  │ Base Gravada │ Base Distrib. │ Alic. │ Impuesto
 ──────────────┼────────┼──────────────┼───────────────┼───────┼──────────
 [913] Mendoza │ 0.4000 │ 1.000.000    │ 400.000       │ 3.00% │ 12.000
 [902] Bs. As. │ 0.3500 │ 1.000.000    │ 350.000       │ 4.00% │ 14.000
 [904] Cordoba │ 0.2500 │ 1.000.000    │ 250.000       │ 3.50% │  8.750
```

**La cuenta que se hace en cada linea:**

```
 Base Distribuida = Base Gravada × Coeficiente
                  = 1.000.000 × 0.4000
                  = 400.000

 Impuesto = Base Distribuida × Alicuota / 100
           = 400.000 × 3.00 / 100
           = 12.000
```

**Deducciones pre-cargadas:** el wizard auto-calcula estos valores desde la contabilidad. El usuario los puede ajustar:

| Campo | Que es | De donde sale |
|---|---|---|
| Retenciones sufridas | IIBB que te retuvieron tus clientes al cobrarte | Tax lines IIBB en cobros inbound |
| Percepciones sufridas | IIBB que te percibieron tus proveedores al facturarte | Tax lines IIBB en facturas de compra |
| Recaudaciones bancarias | IIBB que el banco te debito automaticamente | **Manual** (dato bancario) |
| Saldo anterior | Saldo a favor que arrastra del mes pasado | Liquidacion del periodo anterior |

**Trazabilidad (smart buttons):** cada linea tiene un boton `fa-external-link` que abre un formulario detallado con:

- **Boton "N Percepciones"** → abre las facturas de compra que originaron el monto de percepciones sufridas
- **Boton "N Retenciones"** → abre los cobros que originaron el monto de retenciones sufridas
- **Boton "Saldo Anterior"** → abre la liquidacion del periodo anterior de donde se arrastro el saldo

Esto permite al contador verificar de donde sale cada numero sin salir de la liquidacion.

**Recalcular deducciones:** si se registran nuevas facturas o cobros despues de generar la liquidacion, el boton **"Recalcular Deducciones"** en la cabecera re-ejecuta las queries de percepciones, retenciones y saldo anterior sin regenerar toda la liquidacion.

**El saldo final:**

```
 Saldo = Impuesto Determinado − Total Deducciones

 Si el saldo es positivo → hay que pagar
 Si el saldo es negativo → queda a favor para el mes siguiente
```

---

### Paso 8: Confirmar liquidacion

Una vez revisado todo, click en el boton **"Confirmar"** en la cabecera.

**Validaciones automaticas:** antes de confirmar, el sistema detecta situaciones a revisar:

- Jurisdiccion con coeficiente = 0
- Jurisdiccion sin deducciones cargadas (puede ser valido, pero avisa)
- Jurisdiccion con alicuota 0% pero base gravada > 0
- Suma de coeficientes distinta de 1.0000

Si hay advertencias, se abre un wizard mostrando la lista. El usuario puede:
- **"Confirmar Igual"** → confirma a pesar de las advertencias
- **"Cancelar"** → vuelve a la liquidacion para corregir

Si no hay advertencias, confirma directamente.

La liquidacion pasa a estado "Confirmada" y queda lista para exportar.

> Solo usuarios con rol **Responsable CM** pueden confirmar.
> Si hay que corregir algo, el boton **"Volver a Borrador"** permite reabrir.

---

### Paso 9: Exportar archivos

**Desde la liquidacion (recomendado):** en una liquidacion confirmada, aparecen 3 botones en la cabecera:

- **"Exportar CM03"** → abre el wizard CM03 pre-poblado con esta liquidacion
- **"Exportar SIRCAR"** → abre el wizard SIRCAR con las fechas del periodo
- **"Exportar SIFERE"** → abre el wizard SIFERE con las fechas del periodo

Esto permite exportar sin salir de la liquidacion ni buscar fechas manualmente.

**Desde el menu:** todos los exportadores tambien estan en **Contabilidad > Informes > Convenio Multilateral**.

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
| [913] Mendoza | [519000] Vta. mayor art. electricos | 3.00 | Art. 2 - General |
| [902] Buenos Aires | [519000] Vta. mayor art. electricos | 4.00 | Art. 2 - General |
| [904] Cordoba | [519000] Vta. mayor art. electricos | 3.50 | Art. 2 - General |

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
| 2026 | [913] Mendoza | 4.000.000 | 10.000.000 | 3.200.000 | 8.000.000 | 0.4000 |
| 2026 | [902] Bs. As. | 3.500.000 | 10.000.000 | 2.800.000 | 8.000.000 | 0.3500 |
| 2026 | [904] Cordoba | 2.500.000 | 10.000.000 | 2.000.000 | 8.000.000 | 0.2500 |

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
│   ├── cm_liquidation.py         # Liquidacion mensual + lineas + export + validaciones
│   ├── res_company.py            # Herencia: sede CM en la empresa
│   └── account_move.py           # Herencia: jurisdiccion CM en facturas
├── wizard/
│   ├── cm_coefficient_wizard.py  # Calculo automatico de CU
│   ├── cm_liquidation_wizard.py  # Generacion de liquidacion + auto-carga deducciones
│   ├── cm_sircar_wizard.py       # Export SIRCAR (CSV)
│   ├── cm_sifere_wizard.py       # Export SIFERE (TXT posicion fija)
│   ├── cm_cm03_wizard.py         # Export CM03 (XML)
│   ├── cm_cm05_wizard.py         # Export CM05 (Excel)
│   └── cm_confirm_wizard.py      # Wizard de confirmacion con advertencias
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
              cm.liquidation.line (mail.thread, tracking)
                    │  ├── percepciones_move_ids ──→ account.move (M2M)
                    │  ├── retenciones_payment_ids ──→ account.payment (M2M)
                    │  └── prev_liquidation_id ──→ cm.liquidation (M2O)
                    ▼
              cm.liquidation (mensual, mail.thread)
                    ├── action_export_cm03() → cm.cm03.wizard
                    ├── action_export_sircar() → cm.sircar.wizard
                    └── action_export_sifere() → cm.sifere.wizard

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
| `currency_id` | Many2one, related `company_id.currency_id` | Para widget monetary en vistas |
| `period` | Char(7) | Formato AAAA/MM |
| `date_from` / `date_to` | Date | Rango del periodo |
| `fiscal_year` | Char(4) | Ejercicio de coeficientes |
| `state` | Selection, tracking=True | `draft` → `calculated` → `confirmed` |
| `line_ids` | One2many `cm.liquidation.line` | Lineas por jurisdiccion |
| `total_*` | Float(16,2), computed stored | Sumas desde line_ids |

Hereda `mail.thread`. Unique: `(period, company_id)`.

Metodos de accion:

| Metodo | Que hace |
|---|---|
| `action_confirm()` | Si hay warnings → abre wizard confirmacion. Si no → confirma directo |
| `action_draft()` | Vuelve a borrador, borra lineas |
| `action_export_cm03()` | Abre wizard CM03 pre-poblado con esta liquidacion |
| `action_export_sircar()` | Abre wizard SIRCAR con fechas de la liquidacion |
| `action_export_sifere()` | Abre wizard SIFERE con fechas de la liquidacion |
| `action_recalculate_deductions()` | Re-ejecuta queries de deducciones sin regenerar lineas |
| `_get_confirmation_warnings()` | Detecta coeficiente=0, sin deducciones, alicuota=0, suma coef!=1 |

#### `cm.liquidation.line`

| Campo | Tipo | Descripcion |
|---|---|---|
| `liquidation_id` | Many2one (cascade) | Liquidacion padre |
| `jurisdiction_id` | Many2one (restrict) | Jurisdiccion |
| `currency_id` | Many2one, related | Para widget monetary |
| `coefficient` | Float(8,4) | CU aplicado |
| `base_gravada` | Float(16,2) | Base imponible total |
| `base_distribuida` | Float(16,2), computed stored | `base_gravada * coefficient` |
| `alicuota` | Float(6,4) | Tasa IIBB |
| `impuesto_determinado` | Float(16,2), computed stored | `base_distribuida * alicuota / 100` |
| `retenciones_sufridas` | Float(16,2), tracking | Ret. IIBB sufridas |
| `percepciones_sufridas` | Float(16,2), tracking | Perc. IIBB sufridas |
| `recaudaciones_bancarias` | Float(16,2), tracking | Rec. bancarias |
| `saldo_anterior` | Float(16,2), tracking | Arrastre periodo anterior |
| `total_deducciones` | Float(16,2), computed stored | Suma de deducciones |
| `saldo` | Float(16,2), computed stored | `impuesto - deducciones` |
| `percepciones_move_ids` | Many2many `account.move` | Facturas compra origen percepciones |
| `retenciones_payment_ids` | Many2many `account.payment` | Cobros origen retenciones |
| `prev_liquidation_id` | Many2one `cm.liquidation` | Liquidacion anterior (saldo arrastrado) |
| `percepciones_count` | Integer, computed | Cantidad de facturas vinculadas |
| `retenciones_count` | Integer, computed | Cantidad de cobros vinculados |

Hereda `mail.thread` (audit trail en campos de deduccion via tracking).

Smart buttons (formulario detallado de linea):

| Metodo | Que abre |
|---|---|
| `action_view_percepciones()` | Facturas de compra origen de percepciones |
| `action_view_retenciones()` | Cobros origen de retenciones |
| `action_view_prev_liquidation()` | Liquidacion anterior vinculada |
| `action_open_form()` | Formulario detallado de la linea (target=new) |

#### `cm.confirm.wizard`

| Campo | Tipo | Descripcion |
|---|---|---|
| `liquidation_id` | Many2one `cm.liquidation` | Liquidacion a confirmar |
| `warnings_text` | Text, readonly | Lista de advertencias detectadas |

Metodo `action_confirm_anyway()`: confirma la liquidacion a pesar de las advertencias.

### Herencias

**`res.company`:** agrega `cm_sede_jurisdiction_id` (Many2one → `cm.jurisdiction`).

**`account.move`:** agrega `cm_jurisdiction_id` (computed, stored, readonly=False). Se resuelve automaticamente desde `partner_shipping_id.state_id` o `partner_id.state_id`. Usa cache local para evitar N+1 queries.

#### `cm.liquidation.wizard` — metodos de auto-carga de deducciones

| Metodo | Que busca | Retorna |
|---|---|---|
| `_get_percepciones_sufridas(date_from, date_to, company_id)` | Tax lines IIBB ('07') en facturas de compra posted, agrupadas por `cm_jurisdiction_id` | `{jur_id: {'amount': float, 'move_ids': [int]}}` |
| `_get_retenciones_sufridas(date_from, date_to, company_id)` | Tax lines IIBB en cobros inbound, resolviendo jurisdiccion desde `partner_id.state_id` con cache | `{jur_id: {'amount': float, 'payment_ids': [int]}}` |
| `_get_saldo_anterior(period, company_id)` | Lineas con saldo negativo en liquidacion anterior confirmada/calculada | `{jur_id: {'amount': float, 'liquidation_id': int}}` |

Estos metodos se usan tanto en `action_generate()` como en `action_recalculate_deductions()` del modelo.

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
| `group_cm_manager` | `group_cm_user` | Todo: crear/editar/borrar maestros, calcular coeficientes, confirmar liquidaciones, wizard de confirmacion |

Wizards con acceso restringido a manager: `cm.coefficient.wizard`, `cm.confirm.wizard`.

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
| Auto-poblar deducciones editables | El wizard pre-carga valores verificables, el contador ajusta si es necesario |
| M2M para trazabilidad (`percepciones_move_ids`, `retenciones_payment_ids`) | Permite navegar desde la deduccion hasta el documento origen con smart buttons |
| Wizard intermedio de confirmacion | Evita confirmaciones accidentales sin bloquear el flujo (el usuario decide) |
| Botones de exportacion en la liquidacion | Evita ir a otro menu, pre-carga fechas y liquidacion automaticamente |
| Kanban como vista default de liquidaciones | Vista rapida del estado de cada periodo, agrupado por estado |
| `mail.thread` en `cm.liquidation.line` | Audit trail de cambios manuales en campos de deduccion |
| `currency_id` related en liquidacion y linea | Necesario para widget monetary en kanban y formularios |
| Recalcular deducciones sin regenerar | Permite actualizar datos si se cargaron facturas/cobros despues de generar |
| Jurisdicciones con deducciones sin ventas | Incluye lineas donde hay percepciones/retenciones pero no hubo ventas en el periodo |
