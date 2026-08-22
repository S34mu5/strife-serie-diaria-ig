# Serie diaria de Strife en Instagram · 29 posts + 2 carruseles

> **PAUSADO.** La automatizacion esta deshabilitada hasta que la app este en
> la store. Reactivar: pestana **Actions** > *Publicar serie diaria en Instagram*
> > **Enable workflow**. Manual completo en [MANUAL.md](../MANUAL.md).

Publica una vez al día, del **lunes 24 de agosto** al **miércoles 23 de septiembre de 2026**:
los 29 posts de imagen y, los dos últimos días, los carruseles-tutorial
(guía del alumno, 6 fotos; guía del club, 8 fotos). Lo ejecuta GitHub Actions
en la nube: no depende de que tu Mac esté encendido.

## Horas de publicación

- **L–V 19:30** (Madrid): el público de deportes de contacto entrena de tarde;
  scrollea justo antes y después.
- **S–D 11:30**: pico matinal de fin de semana, después del open mat.

Son horas basadas en estudios del sector — la cuenta aún no tiene audiencia que
medir. Cuando pase de ~100 seguidores, `medir_audiencia.py` (con las mismas
variables de entorno) imprime a qué hora están conectados **tus** seguidores y
el alcance de cada post publicado. Si contradice estas franjas, cambia `HORAS`
en `generar_calendario.py` y los `cron` del workflow.

## Piezas

| Archivo | Qué hace |
|---|---|
| `generar_calendario.py` | Lee `../pies-de-foto.txt` y genera `calendario.json`: 29 posts + 2 carruseles. Valida archivos, límites de caption y que los cierres caigan en domingo. |
| `medir_audiencia.py` | Horas de conexión reales de tus seguidores + alcance de cada post publicado, vía Insights. |
| `refrescar_token.py` | Renueva el token de 60 días por otros 60. No hace falta durante esta serie. |
| `calendario.json` | El calendario ya generado: día, fecha, archivo, pie, tags y caption final. |
| `publicar.py` | Publica el post que toca hoy vía Instagram Graph API. |
| `registro.json` | Se crea al primer post. Guarda qué días ya se publicaron para no duplicar nunca. |
| `.github/workflows/publicar-instagram.yml` | El cron diario en GitHub Actions. |

Si cambias un pie de foto, edita `../pies-de-foto.txt` y vuelve a lanzar
`python3 generar_calendario.py`.

## Vía usada: «Instagram API con Instagram Login»

Meta tiene dos vías para publicar. Usamos la de **Instagram Login**, que según su
documentación «no requiere que una página de Facebook esté vinculada a la cuenta
profesional de Instagram». Es bastante más corta que la vía de Facebook Login:
el token se genera con un botón en el propio panel de la app, sin Graph API
Explorer ni canjes de token.

| | Instagram Login (la que usamos) | Facebook Login (la antigua) |
|---|---|---|
| Página de Facebook | **no hace falta** | obligatoria |
| Host de la API | `graph.instagram.com` | `graph.facebook.com` |
| Permisos | `instagram_business_basic`, `instagram_business_content_publish` | `instagram_basic`, `instagram_content_publish`, `pages_read_engagement` |
| Token | 60 días, botón «Generate token» en el panel | canje `fb_exchange_token` → token de página |

Los permisos antiguos (`instagram_basic`, `instagram_content_publish`) quedaron
obsoletos el 27 de enero de 2025 para esta vía.

## Lo que tienes que preparar en Meta (una sola vez)

Ve paso a paso. Al final de cada bloque hay algo que apuntar.

### 1. La cuenta de Instagram tiene que ser Business

En la app de Instagram: **Ajustes → Tipo de cuenta y herramientas → Cambiar a cuenta
profesional → Empresa**. Si ya dice "Empresa", este paso está hecho.

*Por qué:* la Graph API no publica en cuentas personales. Es un requisito de Meta, no una
elección nuestra.

### 2. Una página de Facebook vinculada a esa cuenta

Toda cuenta de Instagram Business necesita una página de Facebook detrás, aunque no la uses.
Créala en facebook.com/pages/create (puedes dejarla sin publicar) y vincúlala desde
Instagram: **Ajustes → Herramientas empresariales → Página → Conectar**.

**Apunta:** el nombre de la página.

### 3. Una app en Meta Developers

Entra en developers.facebook.com, **Mis apps → Crear app**. Elige el caso de uso que
mencione Instagram (o el tipo "Empresa"). Ponle el nombre que quieras, p. ej. "Strife
Publicador".

Dentro de la app, añade el producto **Instagram** → *Configurar la API de Instagram*.

**Deja la app en modo Desarrollo.** Esto es importante y te ahorra semanas: en modo
Desarrollo puedes publicar en **tus propias** cuentas siendo administrador de la app, sin
pasar por la revisión de Meta. La revisión solo hace falta si terceros van a usar tu app.

**Apunta:** el ID de la app.

### 4. El token y el ID de la cuenta

Abre el **Graph API Explorer** (developers.facebook.com/tools/explorer). Selecciona tu app
arriba a la derecha y pide estos permisos con *Add permissions*:

- `instagram_basic`
- `instagram_content_publish`
- `instagram_manage_insights`  ← para medir la audiencia con `medir_audiencia.py`
- `pages_show_list`
- `pages_read_engagement`

Pulsa **Generate Access Token** y acepta. Ya tienes un token, pero dura 1 hora — lo
convertimos en el siguiente paso.

Con ese token, en el mismo Explorer, lanza estas dos consultas:

1. `me/accounts` → te devuelve tus páginas. Copia el `id` de la página del paso 2.
2. `{ID_DE_LA_PAGINA}?fields=instagram_business_account` → te devuelve el ID de la cuenta
   de Instagram.

**Apunta:** ese `instagram_business_account.id`. Ese es tu `IG_USER_ID` (es un número
largo, no tu @usuario).

### 5. Un token que no caduque

El token de 1 hora no sirve para un cron de 28 días. Hay que canjearlo:

```
GET /oauth/access_token
  ?grant_type=fb_exchange_token
  &client_id={ID_DE_LA_APP}
  &client_secret={CLAVE_SECRETA_DE_LA_APP}
  &fb_exchange_token={EL_TOKEN_DE_1_HORA}
```

Eso da un token de usuario de **60 días**. Con ese token, vuelve a lanzar `me/accounts`: el
`access_token` que viene ahí dentro es un **token de página que no caduca**. Ese es el que
usamos.

La clave secreta está en la app: **Configuración → Básica → Clave secreta de la app**.

**Apunta:** el token de página. Trátalo como una contraseña — quien lo tenga puede publicar
en tu cuenta.

## Los tres secretos de GitHub Actions

En el repo → **Settings → Secrets and variables → Actions → New repository secret**:

| Secreto | Valor |
|---|---|
| `IG_USER_ID` | el `instagram_business_account.id` del paso 4 |
| `IG_ACCESS_TOKEN` | el token de página del paso 5 |
| `IMAGE_BASE_URL` | `https://raw.githubusercontent.com/S34mu5/strife-serie-diaria-ig/main` |

Pega el token tú directamente ahí. Queda cifrado y no aparece en los logs.

## Comprobar antes de publicar de verdad

Ensayo, sin tocar Instagram:

```bash
python3 publicar.py --dia 1 --dry-run
```

Publicar un día concreto a mano, de verdad:

```bash
IG_USER_ID=... IG_ACCESS_TOKEN=... IMAGE_BASE_URL=... python3 publicar.py --dia 1
```

Los carruseles también se pueden lanzar por id:

```bash
python3 publicar.py --id guia-alumno --dry-run
```

## Notas de la API que conviene saber

- **Las imágenes necesitan URL pública HTTPS.** La Graph API no acepta subida de archivos:
  descarga la imagen desde una URL. De ahí que las imágenes vivan en el repositorio.
- **Instagram solo publica JPEG.** Los originales son PNG, así que `jpg/` contiene la
  conversión (calidad 92, mismas dimensiones) y es lo que se publica. Si añades o cambias
  una imagen, convierte el PNG con:
  `sips -s format jpeg -s formatOptions 92 dia-XX.png --out jpg/dia-XX.jpg`
- **La Graph API de Instagram no programa posts.** El `scheduled_publish_time` existe para
  páginas de Facebook, no para Instagram. El calendario lo pone el cron de Actions.
- **Límite de 100 publicaciones cada 24 horas.** Nosotros hacemos 1 al día.
- **Carruseles:** cada foto se sube como contenedor hijo (`is_carousel_item`),
  luego un contenedor `CAROUSEL` con los hijos y el pie, y se publica. Máximo
  10 fotos; las nuestras son 6 y 8. Un carrusel cuenta como UNA publicación.
  **Ojo:** Instagram recorta todas las fotos del carrusel a la proporción de la
  primera. Las nuestras son todas 1080×1350, así que no se recorta nada.
- **El token dura 60 días** y se renueva con `refrescar_token.py` (necesita tener
  al menos 24 h de vida). La serie dura 31 días, así que no hay que renovar nada
  durante la serie.
- El cron de GitHub Actions puede retrasarse unos minutos cuando hay mucha carga. Para una
  serie diaria da igual; si necesitaras la hora exacta, habría que otro planificador.
