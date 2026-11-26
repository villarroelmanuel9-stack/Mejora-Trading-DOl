# Capital.com → Claude (solo lectura)

Conector MCP para que **Claude Desktop** vea tu cuenta de **Capital.com**: saldo, disponible, P/L, posiciones abiertas, órdenes pendientes, historial y precios.

🔒 **Solo lectura por diseño.** Capital.com no tiene claves API de solo lectura (todas permiten operar), así que el propio conector lo garantiza: solo hace consultas (`GET`) y el inicio de sesión. Cualquier intento de abrir, modificar o cerrar operaciones se bloquea **antes** de enviarse (probado en `tests/`).

## Qué le puedes preguntar a Claude
- "Muéstrame mi cuenta de Capital.com" → `get_account_summary`
- "¿Qué posiciones tengo abiertas y cuánto van ganando o perdiendo?" → `get_positions`
- "¿Tengo órdenes pendientes?" → `get_working_orders`
- "¿Qué operaciones hice hoy?" → `get_activity_history` / `get_transactions`
- "¿A cuánto está el oro?" → `search_markets` + `get_market`

## Instalación (computadora Windows o Mac + Claude Desktop)
1. **Crea la clave API** en Capital.com, en la web o la app: *Configuración → Integraciones API → Generar clave*. Necesitas la verificación en dos pasos activada. Pon una **contraseña propia** para la clave y guárdala. La clave **se muestra una sola vez**.
   Recomendado: empieza con tu **cuenta demo** (`CAPITAL_ENV=demo`).
2. **Instala Python 3.10+** (en Windows marca *Add Python to PATH*).
3. Descarga este repositorio (*Code → Download ZIP*) y en la carpeta `capital-mcp` ejecuta:
   ```
   pip install -r requirements.txt
   ```
4. **Configura Claude Desktop.** Abre el archivo de configuración: en Windows `%APPDATA%\Claude\claude_desktop_config.json`, en Mac `~/Library/Application Support/Claude/claude_desktop_config.json`. Agrega:
   ```json
   {
     "mcpServers": {
       "capital": {
         "command": "python",
         "args": ["C:\\Trading\\Mejora-Trading-DOl\\capital-mcp\\capital_mcp.py"],
         "env": {
           "CAPITAL_API_KEY": "TU_CLAVE_API",
           "CAPITAL_IDENTIFIER": "TU_EMAIL_DE_CAPITAL",
           "CAPITAL_PASSWORD": "CONTRASEÑA_DE_LA_CLAVE_API",
           "CAPITAL_ENV": "demo"
         }
       }
     }
   }
   ```
   Cambia la ruta a donde descomprimiste el repo. En Mac usa `python3` y una ruta como `/Users/tu_usuario/...`. Para la cuenta real pon `"CAPITAL_ENV": "live"`.
5. **Reinicia Claude Desktop** y pregunta: *"Muéstrame mi cuenta de Capital.com"*.

⚠️ Tus datos van **solo** en ese archivo de tu computadora (o en un `.env` junto a `capital_mcp.py`, ver `.env.example`). **Nunca** los pegues en un chat ni los subas a GitHub. Si crees que alguien vio tu clave, **pausala o bórrala** en Capital.com y genera otra.

## Notas
- La sesión de Capital.com caduca a los 10 minutos sin uso; el conector se reconecta solo.
- Historial: la API permite como máximo 24 horas por consulta.
- El celular solo no puede ejecutar este conector. Necesita una computadora con Claude Desktop.

## Pruebas
`pip install pytest` y luego `python -m pytest tests`. Las pruebas usan un servidor falso que imita la API de Capital.com: no tocan ninguna cuenta real.
