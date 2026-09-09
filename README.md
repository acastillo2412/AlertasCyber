# AlertaCyber

Vigila vulnerabilidades (CVE) de MikroTik, Altai, Fortinet (FortiOS/FortiSwitch/FortiAP), Huawei,
SonicWall, Ubiquiti/UniFi, TP-Link, Cambium Networks, Ruijie, Windows (10/11), Windows Server,
Debian y Ubuntu, y envía alertas nuevas a un grupo de Telegram. Además manda un resumen de
críticas cada 12 horas y un resumen semanal los lunes.

Para Windows, Windows Server, Debian y Ubuntu solo se avisa de vulnerabilidades **CRITICAL**
(campo `severities` en `config/vendors.json`) — el volumen de CVEs de sistemas operativos es muy
superior al de los fabricantes de red (p. ej. Windows Server tiene ~70 CVEs/mes, de las que
normalmente 3-4 son críticas). Las no críticas ni siquiera se registran: se descartan antes de
guardarse en `data/seen.json` o `data/alert_log.jsonl`, así que tampoco aparecen en los
resúmenes.

## Fuentes de datos

- **NVD (NIST) CVE API 2.0**: búsqueda por palabra clave de cada fabricante. Es la fuente
  principal para todos los fabricantes.
- **RSS de fabricante**: solo se incluye el feed de FortiGuard (Fortinet), que es el único de
  esta lista con un RSS público estable verificado. Se filtra por las mismas palabras clave del
  fabricante (`nvd_keywords`) para no traer avisos de productos Fortinet fuera de alcance. El
  resto de fabricantes no publican un feed RSS fiable; si encuentras uno, añádelo en
  `config/vendors.json` bajo `rss_feeds`.
- **CISA KEV** (catálogo de vulnerabilidades explotadas activamente): se usa solo en los
  resúmenes, para marcar qué críticas requieren acción inmediata.

Los avisos ya enviados se registran en `data/seen.json` para no duplicar alertas entre
ejecuciones. Cada alerta enviada también queda en `data/alert_log.jsonl` (histórico de 40 días),
que es lo que alimenta los resúmenes periódicos.

> **Nota sobre "Unify"**: se ha interpretado como Ubiquiti/UniFi (fabricante de redes), no como
> Unify/Atos (comunicaciones unificadas), por ser coherente con el resto de fabricantes de
> networking de la lista. Si te referías a otro fabricante, edita las `nvd_keywords` de la
> entrada `unifi` en `config/vendors.json`.

## Resúmenes periódicos

Además de la alerta individual de cada CVE nuevo, `src/summary.py` manda al mismo grupo:

- **Cada 12 horas**: cuántas alertas se enviaron, cuántas son críticas, y si alguna consta como
  explotada activamente (CISA KEV) — con una recomendación explícita de si conviene actuar ya o
  no es urgente.
- **Semanal (lunes 9:00)**: lo mismo pero sobre los últimos 7 días, con el desglose de alertas
  por fabricante.

```powershell
python src\summary.py               # resumen de las ultimas 12h (por defecto)
python src\summary.py --hours 24    # resumen de un periodo custom
python src\summary.py --weekly      # resumen semanal (7 dias)
```

## Instalación (entorno local de desarrollo, Windows)

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

> **Importante**: si ya tienes una instancia corriendo en el servidor de producción, no ejecutes
> `main.py` también en local — cada instancia lleva su propio `data/seen.json` y duplicará
> alertas en el grupo.

## Crear el bot de Telegram y obtener el chat_id

1. En Telegram, habla con **@BotFather** → `/newbot` → sigue los pasos → copia el token.
2. En **@BotFather** (no en el bot) → `/setprivacy` → elige tu bot → `Disable` (para que pueda
   leer mensajes normales del grupo, no solo comandos).
3. Crea el grupo de Telegram y añade el bot como miembro.
4. Envía cualquier mensaje al grupo.
5. Visita `https://api.telegram.org/bot<TOKEN>/getUpdates` en el navegador y busca la entrada con
   `"type":"group"` o `"supergroup"` — el `"chat":{"id": -100...}` (número negativo) es tu
   `TELEGRAM_CHAT_ID`.

## Probar manualmente

```powershell
venv\Scripts\activate
python src\main.py
python src\summary.py --hours 12
```

## Despliegue en servidor (producción, Linux/Ubuntu)

Setup actual: usuario de servicio dedicado `alertacyber` (sin shell de login, sin sudo), código
en `/opt/alertacyber/app`, clonado por SSH con una Deploy Key de solo lectura del repo de GitHub.

```bash
sudo useradd --system --create-home --home-dir /opt/alertacyber --shell /usr/sbin/nologin alertacyber
sudo -u alertacyber ssh-keygen -t ed25519 -f /opt/alertacyber/.ssh/id_ed25519 -N ''
# Añadir /opt/alertacyber/.ssh/id_ed25519.pub como Deploy Key (solo lectura) en GitHub

sudo -u alertacyber bash -c '
  GIT_SSH_COMMAND="ssh -i /opt/alertacyber/.ssh/id_ed25519 -o IdentitiesOnly=yes" \
  git clone git@github.com:acastillo2412/AlertasCyber.git /opt/alertacyber/app
  cd /opt/alertacyber/app
  python3 -m venv venv
  venv/bin/pip install -r requirements.txt
'
# Crear /opt/alertacyber/app/.env manualmente (no se clona, esta en .gitignore)
sudo chmod 600 /opt/alertacyber/app/.env
```

Cron del usuario `alertacyber` (`crontab -u alertacyber -e` o `sudo -u alertacyber crontab -e`):

```cron
# Alertas de CVE nuevos, cada hora
0 * * * * cd /opt/alertacyber/app && venv/bin/python src/main.py >> /opt/alertacyber/app/run.log 2>&1

# Resumen de criticas cada 12 horas (00:00 y 12:00)
0 */12 * * * cd /opt/alertacyber/app && venv/bin/python src/summary.py --hours 12 >> /opt/alertacyber/app/run.log 2>&1

# Resumen semanal, lunes a las 9:00
0 9 * * 1 cd /opt/alertacyber/app && venv/bin/python src/summary.py --weekly >> /opt/alertacyber/app/run.log 2>&1
```

Para actualizar el código tras un cambio: `sudo -u alertacyber git -C /opt/alertacyber/app pull`.

## Estructura del proyecto

```
config/vendors.json    Fabricantes: palabras clave para NVD y feeds RSS
src/sources/nvd.py      Cliente NVD CVE API 2.0
src/sources/rss.py      Lector generico de RSS (con filtro opcional por keywords)
src/store.py            Registro de alertas ya enviadas (evita duplicados)
src/alertlog.py         Historial de alertas enviadas (alimenta los resumenes)
src/kev.py              Catalogo CISA KEV (vulnerabilidades explotadas activamente)
src/translate.py        Traduccion de descripciones al espanol (MyMemory)
src/telegram.py         Formateo y envio de mensajes a Telegram
src/main.py             Orquestador de alertas individuales (punto de entrada)
src/summary.py          Resumen periodico/semanal de criticas
data/seen.json           Se crea automaticamente en la primera ejecucion
data/alert_log.jsonl     Historico de alertas enviadas (40 dias), usado por summary.py
data/run.log             Log de ejecuciones
```

## Añadir o quitar fabricantes

Edita `config/vendors.json`. Cada entrada admite:

```json
"clave": {
  "label": "Nombre mostrado en las alertas",
  "nvd_keywords": ["palabra1", "palabra2"],
  "rss_feeds": ["https://.../feed.xml"],
  "severities": ["CRITICAL"]
}
```

Las `nvd_keywords` tambien se usan para filtrar los `rss_feeds` de ese mismo fabricante, asi que
mantenlas especificas al producto que te interesa (evita palabras genericas como el nombre del
fabricante si solo quieres un subconjunto de sus productos, como pasa con Fortinet).

`severities` es opcional (por defecto se avisa de todas). Si se indica, solo se envian y registran
los CVE cuya severidad este en esa lista (valores validos: `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`).
Se usa en Windows/Windows Server/Debian/Ubuntu porque su volumen de CVEs es demasiado alto para
avisar de todo.
