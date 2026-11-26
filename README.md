# DOL Engine Pro · Draw on Liquidity (versión 1m)

**Archivo:** [`DOL_Engine_Pro.pine`](./DOL_Engine_Pro.pine). Es la versión principal. El original `DOL_Engine.pine` se mantiene como v1.

Diseñado para usarse en el **gráfico de 1 minuto**. Los objetivos de liquidez se calculan en **1H** y **15m**, además de los niveles diarios, semanales y de sesión. El DOL **solo aparece cuando la Confirmación es ≥ 80%** (ajustable en *Quality Gates*).

### Qué muestra (estilo TradeAxis DOL Pro)
- **DOL activo**: línea ámbar gruesa dentro de una banda de tolerancia con borde discontinuo, una etiqueta central `1. PDH · 122 bars` y una etiqueta a la derecha `◆ A PDH / 1D 58.3%`. Una línea punteada une el precio con el objetivo.
- **HUD** (arriba a la derecha): `◆ A PDH | precio` · `PoT 120b ████░░ %` · `Confirmation ████ %` · `Distance × 15m ATR ↑` · `Engines 1H · 15m` · `Session ▲ UP → LON-H` · `Order Flow` · **TIMEFRAME BIAS** (4H / 1H / 15m) · **CANDIDATE LADDER** (los siguientes objetivos con su puntuación).
- Si ningún objetivo llega al 80%, el HUD muestra `◇ WAITING ≥ 80%` junto con el mejor candidato del momento.
- **Niveles de liquidez**: PDH/PDL, PWH/PWL, ASIA-H/L, LON-H/L, NY-H/L, BSL/SSL y EQH/EQL de 1H y 15m.
- **Zonas FVG** de 1H y 15m (BFVG alcista, SFVG bajista), con relleno parcial, y el **+ ANCHOR FVG** en el lado opuesto al objetivo.
- **Señales coherentes con el DOL**: solo hay BUY si el DOL activo está **arriba** y SELL si está **abajo**. El **TP es el DOL** y lo sigue mientras mantenga la dirección. La señal y sus líneas **desaparecen** al tocar el DOL (TP), al tocar el SL o si el DOL se gira en contra. Solo hay una señal abierta a la vez. Alertas: *Signal TP*, *Signal SL hit* y *Signal invalidated*.
- **Señales BUY / SELL en el DOL** (detalle) (ámbar): cuando el precio alcanza un DOL **arriba** se prepara una **SELL** (barrida de liquidez compradora); si el DOL está **abajo**, una **BUY**. La señal sale cuando una vela cierra de vuelta al otro lado del nivel (rechazo), dentro de las 15 velas siguientes, y queda opcionalmente filtrada por desplazamiento. Marca la entrada, el **SL** (extremo de la barrida más un margen) y el **TP** (siguiente liquidez del lado contrario o 2R), con el RR en la etiqueta. Tiene alertas *BUY at DOL* y *SELL at DOL*.
- **Filtros de seguridad** (internos, sin dibujar nada nuevo):
  - Killzones: solo hay señales en Londres (2–5), NY AM (8:30–11) y NY PM (13:30–16).
  - Ventanas de noticias bloqueadas: 8:25–8:40, 9:55–10:05 y 13:55–14:10.
  - Confirmación por **MSS en 1m**: después de la barrida, una vela tiene que cerrar más allá del último swing de 1m.
  - Filtro **premium / discount** (rango de 2 días): SELL solo en premium, BUY solo en discount.
  - **RR mínimo** de 1.5.
  - **Divergencia SMT** opcional, comparando con otro símbolo (por ejemplo ES1! para NQ1!).
  - **PoT conservador**: no cuenta la deriva a favor, recorta la volatilidad un 15% y la reduce fuera de las killzones.
  - La etiqueta muestra `★n/5`: cuántas confluencias se cumplieron (killzone, MSS, desplazamiento, premium/discount, SMT).
- Opcional: BOS / MSS en el gráfico y barras de desequilibrio de order flow.

### 📈 Instrumentos: Nasdaq y Oro
Preset **Auto**: el indicador reconoce el activo del gráfico y ajusta killzones y par SMT (hora de Nueva York).

| | Nasdaq (NQ, MNQ, NAS100, US100, USTEC) | Oro (XAUUSD, GOLD, GC, MGC) |
|---|---|---|
| Killzone Londres | 02:00–05:00 | 02:00–05:00 |
| Killzone NY AM | 08:30–11:00 (datos + apertura cash) | 08:20–11:00 (apertura COMEX) |
| Killzone NY PM | 13:30–16:00 | 13:30–15:00 |
| Par SMT | ES1! (futuros) / OANDA:SPX500USD (CFD) | SI1! (futuros) / OANDA:XAGUSD (spot) |

El par SMT se puede cambiar en *Safety Filters*. Usa un símbolo con datos en tiempo real: los futuros CME sin suscripción llegan con 10 minutos de retraso. Si no hay datos del par, el SMT simplemente no suma.

### ⚡ Rendimiento
- `calc_bars_count = 7000`: el indicador calcula solo las últimas ~7000 velas, unos 5 días en 1m.
- **Performance Mode** (por defecto **Fast**): funciona en todos los planes. El plan Basic tiene ~20 s de cálculo. *Balanced* y *Full* aprenden de más historia, pero necesitan un plan pago.
- La volatilidad del PoT se calcula de forma incremental, con un solo cálculo de horario para killzones y otro para noticias.
- SMT apagado por defecto, porque carga un segundo gráfico de 1m. Se activa en *Safety Filters*.

### 🎯 Precisión del DOL (algoritmos)
| Algoritmo | Qué hace |
|---|---|
| **Histéresis / compromiso** | Una vez activo, el DOL se mantiene mientras siga dentro de 10 puntos del umbral. Solo lo reemplaza un objetivo con al menos 10 puntos más de probabilidad. Así no salta ni parpadea |
| **Contador honesto** | Cada DOL activado hoy cuenta como tocado si el precio llega aunque ya no sea el activo. Si un nivel se reactiva, no se cuenta dos veces. La fila muestra `✓ 17 / 22 · 77%` |
| **ADR (rango diario promedio de 10 días)** | Filtro y 8.ª confirmación: descarta objetivos que exigirían más rango del normal en el día |
| **Volatilidad por hora del día** | El PoT usa el perfil de volatilidad por hora de NY (EWMA) a lo largo del horizonte, en vez de una volatilidad fija |
| **Kaufman Efficiency Ratio** | Fuerza de la tendencia hacia el objetivo, usada como dato para la IA |
| **PoT AI (regresión logística en línea, SGD)** | Aprende con cada resultado real qué combinación de PoT, confirmación, confirmaciones, distancia, ADR, tendencia, tipo de nivel, killzone y temporalidad predice el toque. Arranca igual al PoT matemático y se corrige solo, con una regularización que lo mantiene estable |

Por defecto, el DOL aparece solo con **PoT AI ≥ 60%**, **≥ 5 de 8 confirmaciones**, **dentro del ADR** y con la confirmación por encima del umbral automático.

### 📏 Cómo leer los números (importante)
| En el panel | Qué es | Qué NO es |
|---|---|---|
| **Score ≥90 · 85/100** | Puntuación de cuántas condiciones se cumplen | No es una probabilidad de ganar |
| **PoT AI 67%** | Probabilidad de que el precio **toque** el DOL en las próximas 120 velas. Mientras la IA tenga pocos datos dice `learning · n 14` | No dice si tu SL se toca antes |
| **TP before SL ≈ 38%** (en la señal) / **My trade** | Probabilidad de tocar el **TP antes que el SL**, con la volatilidad y la deriva actuales. Sin deriva es SL ÷ (SL + TP): con un 2R gana ~33% de las veces por puro azar | No es una garantía |

**📌 My Trade (manual):** activa *Analyze My Trade* y escribe tu entrada, SL y TP. El panel muestra `My trade ▲ · TP first 41% · RR 2.0`, o `TP reached` / `SL reached`.

### ⚠ Conflicto de dirección
Si un objetivo **del lado contrario**, con confirmación ≥ 60 y a más de la distancia mínima, tiene **igual o más PoT AI** que el DOL activo:
- La fila *Engines* del panel cambia a `⚠ CONFLICT ↓ BFVG 1H 85%`.
- La línea del DOL se atenúa y su etiqueta muestra `⚠`.
- Se **bloquean las señales** BUY/SELL en la dirección del DOL mientras dure el conflicto.
- Hay una alerta *DOL conflict*.
- La IA aprende de esto: la probabilidad del lado contrario es su 11.º dato.

### 🧠 Auto-aprendizaje (retroalimentación)
El indicador **mide sus propios resultados en tu gráfico** (por defecto, las últimas 4000 velas) y se calibra solo:

| Qué aprende | Cómo lo usa |
|---|---|
| Cada 10 velas registra el mejor objetivo y comprueba si el precio lo tocó dentro del horizonte del PoT | **PoT calibrado**: mezcla el modelo con la tasa de acierto real (bayesiano: el modelo cuenta como 10 muestras y luego mandan los datos) |
| % de acierto por nivel de Confirmación (≥70, ≥80, ≥90) | **Umbral automático**: elige el nivel más bajo que alcanza el acierto objetivo (70%). Con pocos datos usa 80 y, si ninguno llega, 90 |
| 7 confirmaciones independientes: sesgo 1H, sesgo 15m, sesgo 4H, order flow, camino libre, confluencia entre temporalidades, killzone | El DOL solo aparece con **≥ 4 de 7** confirmaciones (ajustable) |
| Resultado en R de cada señal según sus estrellas (★0–5), aunque no se muestre | Las configuraciones con **expectativa negativa se ocultan** cuando hay ≥ 8 casos. La etiqueta muestra el % histórico |

El HUD tiene además la fila **DOL today**: `✓ 3 touched / 4 active` muestra cuántos DOL se tocaron y cuántos se activaron desde la apertura. Se reinicia en la apertura del día de trading o, si se elige, a las 09:30 NY, y en ese caso cuenta solo de 09:30 a 16:00. El HUD agrega 2 filas: `DOL hit ≥80 auto · 74% · n 120` y `Signals · 58% · +0.31R · n 12`.

### 📚 Investigación usada
- Los extremos del día anterior se alcanzan en ~90% de las sesiones de NQ, y el rango overnight se rompe ~94% de los días. Por eso se subió la profundidad de PDH/PDL y de las sesiones.
- Las reversiones tras barrida con TP fijo a 2R ganaron entre 26% y 41% en un backtest independiente (sin ventaja), y la ventaja tras barrer el PDH es pequeña (46.9% frente a 43.6%). Por eso el TP es el DOL y no un R fijo, y las configuraciones se filtran por su expectativa medida.
- Los % de acierto publicados por vendedores no son verificables. Por eso el indicador mide en **tu** activo.

### Confirmación (0–100)
| Pilar | Peso | Lógica |
|---|---|---|
| Profundidad de liquidez | 25 | PWH/PWL 22 · PDH/PDL 20 · Sesión 14–15 · EQH/EQL +5 por toque · FVG según tamaño · +5 por cada nivel fusionado entre temporalidades |
| Alineación HTF | 25 | Sesgo 1H (12) + 15m (8) + 4H (5) a favor del objetivo |
| Order flow | 15 | % de compradores/vendedores estimado (delta acumulado) a favor |
| Proximidad | 20 | Distancia en ATR de 15m (máximo 12 ATR) |
| Camino libre | 15 | −5 por cada FVG que bloquea el camino hasta el objetivo |

**PoT** (probabilidad de toque): modelo de difusión con deriva sobre las últimas 200 velas de 1m. Horizonte de 120 velas, con tope del 95%.

---

# DOL Engine · Liquidity Compass

Indicador para TradingView (Pine Script v6) que detecta, puntúa y sigue el **Draw on Liquidity (DOL)**, es decir, el nivel de liquidez hacia el que es más probable que se mueva el precio. Usa conceptos **ICT / Smart Money** y una estimación de **order flow**.

Toma como referencia de diseño y funciones los scripts públicos de [tradeaxis_systems](https://es.tradingview.com/u/tradeaxis_systems/#published-scripts), sobre todo *TradeAxis DOL (Draw on Liquidity)*. Esos scripts son *invite-only* (código cerrado), así que **este código es una implementación propia**, hecha a partir de las descripciones públicas y de la teoría ICT.

> ⚠️ Es una herramienta educativa y de confluencia, no una señal de compra o venta.

---

## 🚀 Cómo verlo en TradingView

1. Abre TradingView y luego el **Editor Pine** (abajo, *Pine Editor*).
2. Copia todo el contenido de [`DOL_Engine.pine`](./DOL_Engine.pine).
3. Pégalo en el editor y reemplaza el código que haya.
4. Pulsa **Guardar** y después **Añadir al gráfico**.
5. Usa un timeframe igual o menor que el de ejecución del modo elegido: Day Trading → 15m o menos, Scalping → 5m o menos, Swing → 1H o menos.

---

## 📚 Conceptos estudiados y cómo se usan

### 1. ICT (Inner Circle Trader)
| Concepto | Qué es | En el indicador |
|---|---|---|
| **BSL / SSL** (Buy/Sell-Side Liquidity) | Stops acumulados por encima de máximos y por debajo de mínimos | Línea en cada pivot high/low sin barrer. Si es barrida, queda punteada y gris |
| **EQH / EQL** | Máximos o mínimos iguales: liquidez "obvia" | Se fusionan dentro de la tolerancia (×ATR) y suben la *densidad* |
| **DOL** (Draw on Liquidity) | El imán del precio, el objetivo institucional | Candidato con la mayor puntuación de 0 a 100 |
| **FVG** (Fair Value Gap) | Desequilibrio de 3 velas | Caja que se va **encogiendo** con el relleno parcial y se elimina con el relleno total |
| **iFVG** (Inversion FVG) | FVG atravesado por un cierre de cuerpo que cambia de polaridad | Cambia de color y el borde pasa a discontinuo. Tiene alerta propia |
| **Order Block** | Última vela opuesta antes del desplazamiento que rompe estructura | Vela con el mínimo (o máximo) más extremo del tramo que hizo el BOS |
| **Breaker Block** | OB invalidado que cambia de polaridad | El OB se convierte en ±BRK cuando un cierre lo atraviesa |
| **BOS / CHoCH** | Ruptura de estructura y cambio de carácter | Confirmados por **cierre de cuerpo**, no por mecha |
| **Premium / Discount** | Encima o debajo del 50% del rango (equilibrium) | Línea EQ + % de posición en el dashboard |
| **PDH / PDL, PWH / PWL** | Máximo y mínimo del día y de la semana anteriores | Candidatos DOL (PDH/PDL) y confluencia (todos) |
| **Sesgo multi-timeframe** | HTF → MTF → LTF alineados | Tabla con el sesgo en 3 temporalidades según el modo |

### 2. Order Flow
TradingView no da datos de *footprint* en Pine estándar, así que el flujo se **estima** por vela:
- **Delta estimado** = volumen × posición del cierre dentro del rango (compradores frente a vendedores).
- **CVD móvil** = suma del delta de las últimas *N* velas, mostrada como "% de compradores".
- **RVOL**: volumen relativo frente a la media de 20 velas.
- **Barras de desequilibrio** (▲ ▼): RVOL ≥ 2 con un delta de más del 50% hacia un lado. Indican agresión institucional.

### 3. Otros enfoques famosos (para próximas mejoras)
- **SMC** (Smart Money Concepts): misma base que ICT (estructura, OB, FVG, liquidez).
- **Wyckoff**: acumulación y distribución, *spring* y *upthrust* (equivalentes a barridas de liquidez).
- **Volume Profile**: POC, VAH, VAL, LVN y HVN (TradeAxis usa LVN de 1H).
- **VWAP y bandas**: valor justo intradía.
- **Killzones ICT**: Londres, NY AM, NY PM y Asia.

---

## 🎯 Motor de puntuación (0 – 100)

| Pilar | Peso | Lógica |
|---|---|---|
| **Proximidad** | 35 | `35 × (1 − distancia/MaxATR)`. Los niveles más lejos de *Max ATR Distance* se excluyen |
| **Frescura** | 25 | Decaimiento exponencial con vida media configurable: `25 × 0.5^(edad/half-life)` |
| **Confluencia** | 25 | +10 alineado con el sesgo HTF · +7 cerca de PDH/PDL/PWH/PWL · +4 lógica premium/discount · +4 order flow a favor |
| **Densidad** | 15 | EQH/EQL (+5 por toque) · tamaño del FVG en ATR · RVOL de la vela del OB |

**PoT % (Probability of Touch)**: estimación heurística, con tope del 95%. Se calcula con la distancia en ATR, la alineación con el sesgo HTF y el order flow. Se recalcula en tiempo real.

El candidato con la mayor puntuación es el **DOL principal** (caja o línea dorada, flecha y etiqueta). El mejor del lado contrario aparece como **alt**.
Cuando el precio alcanza el DOL, queda un **ghost trail** (`✓ DOL`) como registro histórico.

---

## 🎨 Diseño
Estilo "terminal" oscuro y minimalista, con fuente monoespaciada:
- Cian `#00E5FF` para lado comprador y zonas alcistas · Magenta `#FF2E88` para lado vendedor y zonas bajistas.
- Ámbar `#FFC400` para el DOL activo · Gris `#5D6B82` para lo mitigado o neutral.
- Las zonas tocadas se atenúan; las invertidas (iFVG/BRK) tienen borde discontinuo.
- Todos los colores se pueden cambiar en *Theme*.

## 🔔 Alertas
`New DOL Target Active` · `DOL Target Swept` · `New iFVG Formed` · `BOS / CHoCH`
Las alertas dinámicas usan `alert()` e incluyen tipo, nivel, puntuación y PoT.

## 🧭 Anti-repaint
- La estructura, las zonas y los eventos solo se procesan en velas **cerradas** (`barstate.isconfirmed`).
- Los datos HTF se piden con `[1]` + `lookahead_on`, el patrón estándar sin repintado.
- Solo la puntuación y el PoT se actualizan en vivo.

## 🗺️ Roadmap (siguientes mejoras)
- [ ] Killzones / sesiones (Asia, Londres, NY) como confluencia y como liquidez (máximo y mínimo de sesión).
- [ ] Volume Profile: LVN/HVN y POC por zona (estilo *heatmap*).
- [ ] Detección de *inducement* y barridas (Turtle Soup).
- [ ] OTE (Optimal Trade Entry, Fibonacci 62–79%).
- [ ] SMT divergence entre activos correlacionados.
- [ ] Backtest de tasa de acierto del DOL (para calibrar los pesos y el PoT).


---

## 🔌 MetaTrader MCP Server (carpeta `metatrader-mcp-server/`)

Copia del proyecto open source [ariadng/metatrader-mcp-server](https://github.com/ariadng/metatrader-mcp-server) (licencia MIT, commit `bd2ff59`). Es un **puente entre Claude y MetaTrader 5**: permite consultar la cuenta y los precios y **ejecutar operaciones reales** desde lenguaje natural.

- **Requisitos:** Windows con MetaTrader 5 instalado y abierto, y Python 3.10+. No funciona en Mac/Linux ni en la nube.
- **Credenciales:** van en un archivo `.env` (ver `.env.example`) **solo en tu PC**. Nunca lo subas a GitHub; el `.gitignore` de la carpeta ya lo excluye.
- **Cambios respecto al original:** no se incluyeron `build/` ni `dist/` (archivos compilados), ni el enlace `.claude/skills`, que activaba automáticamente un skill que ejecuta órdenes **sin pedir confirmación**. El skill sigue disponible como texto en `claude-skill/trading/SKILL.md`.
- ⚠️ Con esto una IA puede abrir y cerrar operaciones con dinero real. Pruébalo primero en una **cuenta demo**.
