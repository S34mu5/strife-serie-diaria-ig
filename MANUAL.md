# Manual de la serie diaria

Cómo funciona la publicación automática y qué tocar para cambiar cada cosa.

> **⏸ PAUSADO.** La automatización está deshabilitada a propósito: no se publica
> nada hasta que la app esté en la store. Para reactivarla, ve a la pestaña
> **Actions** del repositorio, entra en *Publicar serie diaria en Instagram* y
> pulsa **Enable workflow**. Mientras siga deshabilitada, el cron no dispara y
> tampoco se puede lanzar a mano.

## 1. La cadena

Cinco piezas en fila. Cada una coge lo de la anterior y produce lo de la siguiente.

| Pieza | Qué hace |
|---|---|
| `pies-de-foto.txt` | **Lo que escribes tú.** Los textos de los 31 posts, en crudo. Única fuente de verdad del contenido. |
| `automatizacion/generar_calendario.py` | **El que reparte las fechas.** Les pone fecha empezando por el lunes que le digas y comprueba que no falte ninguna imagen. |
| `automatizacion/calendario.json` | **El plan.** Qué día sale cada post, con qué imagen y qué texto. No se edita a mano: se regenera. |
| `automatizacion/publicar.py` | **El que publica.** Mira qué día es hoy, busca si hay algo para hoy, y lo publica. Si no toca nada, no hace nada. |
| `.github/workflows/publicar-instagram.yml` | **El despertador.** Vive en GitHub, en la nube. Decide **a qué hora** se ejecuta. Por eso no depende de tu ordenador. |

Hay un sexto fichero, `registro.json`, que se crea solo: apunta lo que ya se
publicó para no repetirlo nunca, aunque el despertador se dispare dos veces.

## 2. La hora no está donde parece

⚠️ En `calendario.json` cada post tiene un campo `"hora": "19:30"`. **Ese campo no
hace nada** — es informativo. `publicar.py` solo mira el **día**, nunca la hora.

La hora real la decide únicamente el cron del despertador. Si cambias `HORAS` en
`generar_calendario.py` y no tocas el cron, no cambia nada en la realidad.

El cron se lee al revés (primero minuto, luego hora) y va en **UTC**, que en
verano español son dos horas menos:

```
- cron: "30 17 * * 1-5"    →  17:30 UTC = 19:30 Madrid, lunes a viernes
- cron: "30  9 * * 0,6"    →  09:30 UTC = 11:30 Madrid, sábado y domingo
```

Días: `1-5` lunes a viernes, `0` domingo, `6` sábado.

**Cambio de hora:** el 25 de octubre de 2026 España pasa a UTC+1, así que ese
mismo cron dispararía a las 18:30 en vez de a las 19:30.

## 3. Qué puedes cambiar

| Qué | Dónde | Cómo |
|---|---|---|
| Día de inicio | ningún fichero | `python3 generar_calendario.py 2026-09-21` — tiene que ser **lunes** |
| Textos y hashtags | `pies-de-foto.txt` | como un documento normal; respeta `Pie:` y `Tags:` |
| Hora de publicación | `publicar-instagram.yml` | cambia el cron |
| Imágenes | carpeta `jpg/` | solo **JPEG**: `sips -s format jpeg -s formatOptions 92 dia-XX.png --out jpg/dia-XX.jpg` |

## 4. Probar sin publicar

```bash
cd automatizacion
python3 publicar.py --dia 1 --dry-run
```

| Quiero… | Comando |
|---|---|
| ver qué saldría hoy | `python3 publicar.py --dry-run` |
| ver un día concreto | `python3 publicar.py --dia 7 --dry-run` |
| publicar un día a mano | `python3 publicar.py --dia 7` |
| rehacer el plan | `python3 generar_calendario.py` |
| renovar el token | `python3 refrescar_token.py` |

## 5. La única regla que importa

Cambies lo que cambies, **regenera y sube**, en ese orden:

```bash
cd ~/Downloads/export/ig/serie-diaria/automatizacion
python3 generar_calendario.py
cd .. && git add -A && git commit -m "lo que has cambiado" && git push
```

Quien publica no es tu ordenador, es GitHub. Si el cambio no está subido, **no
existe**: puedes editar todo lo que quieras en local, que la serie seguiría
saliendo como estaba.

## 6. El token

Se genera en el panel de Meta: **Instagram → API setup with Instagram business
login → Generate token**. Dura **60 días**.

Ojo con dos cosas:

- **Generar un token nuevo NO invalida el anterior.** Conviven. Para matar uno
  filtrado hay que revocar el acceso de la app en
  [instagram.com/accounts/manage_access](https://instagram.com/accounts/manage_access),
  lo que invalida *todos* los tokens de esa app; después se vuelve a añadir la
  cuenta en el panel y se genera uno nuevo.
- **Nunca lo pegues en un chat, un correo o un commit.** Va directo al almacén de
  secretos de GitHub: *Settings → Secrets and variables → Actions*, con el nombre
  `IG_ACCESS_TOKEN`.
