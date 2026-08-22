# Deploy del demo a Render — paso a paso

**Qué se publica:** el tenant `papasud`, con el dataset **sintético** de
`data-papasud/` (ver README — ningún número sale de un sistema real de
Papasud). `backend/.env` y las credenciales quedan afuera de la imagen por
`.dockerignore` **y** por la guardia del Dockerfile (el build falla si algo
se cuela).

**Cómo se dispara:** un push a `main` (osea, cada merge) corre
`.github/workflows/deploy.yml`. Ese pipeline:

1. **Smoke check** — instala el backend y corre `python -c "import main"`
   (si algo rompe un import, el contenedor tampoco va a levantar); instala el
   frontend y corre `npm run build` (el mismo build que corre el Dockerfile).
2. **Deploy** — solo si el smoke check pasó, pega contra el *Deploy Hook* de
   Render (`scripts/deploy_render.sh`), que dispara el build de la imagen.

`render.yaml` tiene `autoDeploy: false` a propósito: Render nunca redeploya
por su cuenta con cada push — el único gatillo es este pipeline. Así un merge
que rompe el backend o el build del frontend nunca llega a construir imagen
ni pisa el demo público.

## 1 · Crear el servicio en Render (una sola vez)

1. Cuenta en https://render.com (con GitHub).
2. **New +** → **Blueprint** → conectar este repo.
3. Render lee `render.yaml` (raíz del repo) y propone el servicio
   **papasud-polpilot** (Docker, plan Starter, `autoDeploy: false`).
   - Si el Blueprint no aparece: **New +** → **Web Service** → repo → Runtime
     **Docker** → Health Check Path `/api/health` → plan **Starter** (el Free
     se duerme tras 15 min de inactividad: mala primera impresión con un
     link compartido).

## 2 · Secrets (antes del primer deploy)

En el servicio → **Environment**:

| Variable | Valor |
|---|---|
| `AI_GATEWAY_API_KEY` | key del AI Gateway de Vercel — modo default (`LLM_MODE=gateway`, ya en `render.yaml`) |
| `ANTHROPIC_API_KEY` | alternativa directa si el gateway no responde (`LLM_MODE=anthropic`) |
| `POLPILOT_RESET_TOKEN` | string largo random (ej. de https://1password.com/password-generator) — candado del reset manual |

Sin ninguna de las dos keys de LLM, Ángela cae sola a `LLM_MODE=simulado`
(router determinista, sin modelo) — el sistema no se cae, responde con menos
lenguaje libre. Confirmalo en `/api/health` → `modo_angela`.

`LLM_MODE`, `GATEWAY_MODEL` y `ANGELA_MODEL` ya vienen declaradas en
`render.yaml` (no son secretos: son config, explícitas a propósito para no
depender de un default histórico del código). Si el servicio se creó a mano
(no por Blueprint), Render NO lee `render.yaml`: hay que agregarlas también
en **Environment**.

## 3 · Conectar el Deploy Hook al pipeline (una sola vez)

1. En el servicio → **Settings** → **Deploy Hook** → copiar la URL.
2. En GitHub → repo → **Settings** → **Secrets and variables** → **Actions**
   → **New repository secret** → nombre `RENDER_DEPLOY_HOOK_URL`, valor la
   URL copiada.

De acá en adelante, cada merge a `main` dispara el pipeline solo. Para un
redeploy manual sin esperar un push: pestaña **Actions** →
**Deploy a Render** → **Run workflow** — o, desde una terminal con la URL del
hook:

```bash
RENDER_DEPLOY_HOOK_URL="https://api.render.com/deploy/srv-xxx?key=yyy" \
  ./scripts/deploy_render.sh
```

## 4 · Checklist post-deploy (ventana de incógnito)

1. Abrir `https://papasud-polpilot.onrender.com` → entra DIRECTO como dueño
   (Ernesto), en castellano, Home completo con datos. Nada de pantalla de
   login (autologin del demo público).
2. Preguntarle algo a Ángela ("¿cuánto stock hay en el Galpón?") → responde
   con números reales.
3. **Movimientos** → dictar/cargar un movimiento → confirmar → aparece en el
   libro.
4. **Conciliación** → abrir una diferencia → leer la hipótesis con evidencia.
5. **Trazabilidad** → abrir un lote → ver el linaje (`lote_padre_id`).
6. **Exportación** → ver los documentos pre-completados (N03).
7. Abrir desde el **celular real** → el layout mobile-first.
8. Mandar mensajes hasta pasar 35 → el cap corta con el mensaje honesto.
9. `https://…/api/health` → `tenant: "papasud"`, `empresa: "Papasud S.A."`.

## 5 · Reset del demo público

- **Automático**: cada restart o redeploy vuelve al estado canónico (el
  filesystem de Render es efímero; el boot re-siembra).
- **Manual** (antes de compartir el link, o si alguien lo ensució):
  `curl -X POST "https://papasud-polpilot.onrender.com/api/admin/reset-demo?token=EL_RESET_TOKEN"`
  → `{"ok": true}`. Sin el token exacto responde 404 (ni revela que existe).
  Alternativa sin curl: **Manual Deploy → Restart** en el dashboard.

## 6 · Si algo falla

- **El pipeline de GitHub Actions falla en smoke-check**: el backend no
  importa o el frontend no compila — el log del step dice exactamente dónde.
  Arreglalo y volvé a mergear; el deploy a Render nunca llegó a dispararse.
- **El pipeline pasa pero Render no redeploya**: revisar que el secret
  `RENDER_DEPLOY_HOOK_URL` esté cargado y sea el de ESTE servicio.
- **Logs de Render**: servicio → pestaña **Logs**. El boot habla claro:
  `[boot] seed verificado` → `[boot] dataset ok: N artículos` → uvicorn.
  Un `[boot][X]` dice exactamente qué faltó.
- **Build falla en "guardia de privacidad"**: un `.env` o `credenciales.json`
  entró al contexto — revisar `.dockerignore`; es la guardia haciendo su
  trabajo.
- **PDF no genera**: mirar Logs por `OSError: cannot load library` → falta
  una lib de sistema (la lista vive en el Dockerfile; en local-Windows es el
  GTK3-Runtime, en la imagen ya están).
- **El chat no responde**: ninguna key de LLM cargada → Ángela cae al router
  simulado (funciona igual, con respuestas por reglas). Cargar
  `AI_GATEWAY_API_KEY` o `ANTHROPIC_API_KEY` y redeploy.

## Verificar el build local (opcional, recomendado antes del primer deploy)

```bash
docker build -t papasud-polpilot .
docker run --rm papasud-polpilot sh -c "test ! -e /app/backend/.env && echo GUARDIA-OK"
docker run --rm -p 8080:8000 -e LLM_MODE=simulado papasud-polpilot
```

`http://localhost:8080` → el checklist del punto 4 (incluida la exportación,
que prueba WeasyPrint en Linux).

## Nota sobre la suite de tests heredada

`backend/tests/` viene de un boilerplate previo a Papasud (ver CLAUDE.md,
"Reutilización de código") y una parte no fue portada al dominio actual:
~11 archivos fallan la *collection* de pytest por imports a módulos que ya no
existen (`core.cuentas`, `core.documentos`, etc. — de un tenant "piloto"
distinto que este fork no tiene). Por eso el pipeline **no** gatea el deploy
con la suite completa: el smoke check (`import main` + `npm run build`) es la
señal real de "esto no rompe el contenedor". Portar o podar esa suite es un
trabajo aparte, no bloquea el deploy.
