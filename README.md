# AlertaCyber

Vigila vulnerabilidades (CVE) de los fabricantes MikroTik, Altai, Fortinet/FortiGate, Huawei,
SonicWall, Ubiquiti/UniFi, TP-Link y Cambium Networks, y envía alertas nuevas a un grupo de Telegram.

## Fuentes de datos

- **NVD (NIST) CVE API 2.0**: búsqueda por palabra clave de cada fabricante. Es la fuente
  principal para los 8 fabricantes.
- **RSS de fabricante**: solo se incluye el feed de FortiGuard (Fortinet), que es el único de
  esta lista con un RSS público estable verificado. El resto de fabricantes no publican un feed
  RSS fiable; si encuentras uno, añádelo en `config/vendors.json` bajo `rss_feeds`.

Los avisos ya enviados se registran en `data/seen.json` para no duplicar alertas entre
ejecuciones.

> **Nota sobre "Unify"**: se ha interpretado como Ubiquiti/UniFi (fabricante de redes), no como
> Unify/Atos (comunicaciones unificadas), por ser coherente con el resto de fabricantes de
> networking de la lista. Si te referías a otro fabricante, edita las `nvd_keywords` de la
> entrada `unifi` en `config/vendors.json`.

## Instalación

```powershell
cd "AlertaCyber"
py -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Edita `.env` y completa:

- `TELEGRAM_BOT_TOKEN`: token del bot (ver abajo).
- `TELEGRAM_CHAT_ID`: ID del grupo de Telegram (ver abajo).
- `NVD_API_KEY` (opcional): sube el límite de peticiones a NVD. Se pide gratis en
  https://nvd.nist.gov/developers/request-an-api-key
- `LOOKBACK_DAYS`: días hacia atrás a revisar en cada ejecución (por defecto 3, para tener
  margen si alguna ejecución falla).

## Crear el bot de Telegram y obtener el chat_id

1. En Telegram, habla con **@BotFather** → `/newbot` → sigue los pasos → copia el token.
2. Crea el grupo de Telegram y añade el bot como miembro.
3. Envía cualquier mensaje al grupo.
4. Visita `https://api.telegram.org/bot<TOKEN>/getUpdates` en el navegador y busca
   `"chat":{"id": -1001234567890, ...}` — ese número (con el signo negativo si lo tiene) es tu
   `TELEGRAM_CHAT_ID`.

## Probar manualmente

```powershell
venv\Scripts\activate
python src\main.py
```

Revisa `data\run.log` y la consola para ver el resumen de alertas enviadas/errores.

## Programar la ejecución automática (Task Scheduler)

Opción rápida por línea de comandos (ejecuta cada hora):

```powershell
schtasks /create /tn "AlertaCyber" /tr "\"%CD%\run_alertacyber.bat\"" /sc hourly /f
```

O manualmente desde el Programador de tareas de Windows:

1. Crear tarea básica → nombre `AlertaCyber`.
2. Desencadenador: diario/cada hora, según la frecuencia deseada.
3. Acción: iniciar un programa → selecciona `run_alertacyber.bat` dentro de esta carpeta.
4. En opciones avanzadas, marca "Ejecutar tanto si el usuario inició sesión como si no" si
   quieres que funcione con la sesión bloqueada.

## Estructura del proyecto

```
config/vendors.json   Fabricantes: palabras clave para NVD y feeds RSS
src/sources/nvd.py     Cliente NVD CVE API 2.0
src/sources/rss.py     Lector genérico de RSS
src/store.py           Registro de alertas ya enviadas (evita duplicados)
src/telegram.py        Formateo y envío de mensajes a Telegram
src/main.py            Orquestador (punto de entrada)
data/seen.json          Se crea automáticamente en la primera ejecución
data/run.log            Log de ejecuciones (usado por el .bat)
```

## Añadir o quitar fabricantes

Edita `config/vendors.json`. Cada entrada admite:

```json
"clave": {
  "label": "Nombre mostrado en las alertas",
  "nvd_keywords": ["palabra1", "palabra2"],
  "rss_feeds": ["https://.../feed.xml"]
}
```
