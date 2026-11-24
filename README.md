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
