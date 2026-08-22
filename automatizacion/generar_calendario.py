#!/usr/bin/env python3
"""Convierte pies-de-foto.txt en calendario.json.

Serie: 29 posts de imagen (uno al dia desde INICIO) + 2 carruseles-tutorial
que se publican los dos dias siguientes al dia 29.
"""
import json, os, re, sys, unicodedata
from datetime import date, timedelta
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
FUENTE = RAIZ / "pies-de-foto.txt"
DESTINO = Path(__file__).resolve().parent / "calendario.json"

# Fecha de arranque. Se puede cambiar sin tocar el codigo, por orden de prioridad:
#   python3 generar_calendario.py 2026-09-21     (argumento)
#   FECHA_INICIO=2026-09-21 python3 generar_calendario.py   (variable de entorno)
# Tiene que ser LUNES: la serie alterna publico por dia de semana, los cierres
# caen en domingo y las horas cambian entre semana y fin de semana.
INICIO_POR_DEFECTO = date(2026, 8, 24)


def leer_inicio():
    crudo = (sys.argv[1] if len(sys.argv) > 1 else "") or os.environ.get("FECHA_INICIO", "")
    if not crudo:
        return INICIO_POR_DEFECTO
    try:
        d = date.fromisoformat(crudo.strip())
    except ValueError:
        raise SystemExit(f"fecha no valida: {crudo!r} — usa el formato AAAA-MM-DD")
    if d.weekday() != 0:
        siguiente = d + timedelta(days=(7 - d.weekday()) % 7)
        raise SystemExit(
            f"{d.isoformat()} es {DIAS_ES[d.weekday()]}, y la serie tiene que empezar en LUNES.\n"
            f"El lunes siguiente es {siguiente.isoformat()}."
        )
    return d


INICIO = None  # se fija en main()
# Hora por dia de semana (Europe/Madrid). Publico de deportes de contacto:
# L-V 19:30 (ventana de entreno de tarde), S-D 11:30 (post open mat).
# Cuando la cuenta pase de 100 seguidores, medir_audiencia.py da las horas reales.
HORAS = ["19:30", "19:30", "19:30", "19:30", "19:30", "11:30", "11:30"]
DIAS_ES = ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"]

# Los carruseles no llevan fecha en pies-de-foto.txt: siguen la cadencia diaria
# tras el dia 29 (alumno primero, club despues).
CARRUSELES = {
    "TU PRIMER DÍA": {"id": "guia-alumno", "carpeta": "guia-alumno", "offset": 1},
    "ABRE TU CLUB": {"id": "guia-club", "carpeta": "guia-club", "offset": 2},
}


def sin_tildes(texto):
    return "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn")


def campo(cuerpo, nombre):
    m = re.search(rf"^{nombre}:\s*(.+)$", cuerpo, re.MULTILINE)
    return m.group(1).strip() if m else None


def parsear():
    texto = FUENTE.read_text(encoding="utf-8")
    posts = []

    # posts diarios de imagen
    for m in re.finditer(r"^D[ÍI]A\s+(\d+)\s*·\s*(.+?)$([\s\S]*?)(?=^D[ÍI]A\s|\ZCARRUSEL|^CARRUSEL|\Z)", texto, re.MULTILINE):
        numero, cabecera, cuerpo = int(m.group(1)), m.group(2).strip(), m.group(3)
        archivo = campo(cuerpo, "Archivo")
        pie, tags = campo(cuerpo, "Pie"), campo(cuerpo, "Tags") or ""
        if not (archivo and pie):
            raise SystemExit(f"DIA {numero}: falta Archivo o Pie")
        archivo = re.sub(r"\s*\(.*\)$", "", archivo)  # quitar "(1080×1350)"
        publica = INICIO + timedelta(days=numero - 1)
        posts.append({
            "id": f"dia-{numero:02d}", "tipo": "imagen", "dia": numero,
            "fecha": publica.isoformat(), "dia_semana": DIAS_ES[publica.weekday()], "hora": HORAS[publica.weekday()],
            "audiencia": cabecera.split("—")[-1].strip() if "—" in cabecera else cabecera,
            "archivo": f"jpg/{archivo[:-4]}.jpg",
            "origen_png": archivo,
            "caption": f"{pie}\n\n{tags}".strip(),
        })

    ultimo = max(p["dia"] for p in posts)

    # carruseles
    for m in re.finditer(r"^CARRUSEL\s*·\s*(.+?)$([\s\S]*?)(?=^CARRUSEL\s|^D[ÍI]A\s|\Z)", texto, re.MULTILINE):
        cabecera, cuerpo = m.group(1).strip(), m.group(2)
        clave = next((k for k in CARRUSELES if k in cabecera.upper() or k in sin_tildes(cabecera).upper()), None)
        if clave is None:
            raise SystemExit(f"carrusel no reconocido: {cabecera}")
        c = CARRUSELES[clave]
        pie, tags = campo(cuerpo, "Pie"), campo(cuerpo, "Tags") or ""
        archivos = sorted((RAIZ / "jpg" / c["carpeta"]).glob("*.jpg"))
        publica = INICIO + timedelta(days=ultimo - 1 + c["offset"])
        posts.append({
            "id": c["id"], "tipo": "carrusel", "dia": ultimo + c["offset"],
            "fecha": publica.isoformat(), "dia_semana": DIAS_ES[publica.weekday()], "hora": HORAS[publica.weekday()],
            "audiencia": cabecera,
            "archivos": [f"jpg/{c['carpeta']}/{a.name}" for a in archivos],
            "caption": f"{pie}\n\n{tags}".strip(),
        })

    posts.sort(key=lambda p: p["fecha"])
    return posts


def validar(posts):
    errores = []
    imagenes = [p for p in posts if p["tipo"] == "imagen"]
    carruseles = [p for p in posts if p["tipo"] == "carrusel"]
    if len(imagenes) != 29:
        errores.append(f"se esperaban 29 posts de imagen, hay {len(imagenes)}")
    if len(carruseles) != 2:
        errores.append(f"se esperaban 2 carruseles, hay {len(carruseles)}")
    fechas = [p["fecha"] for p in posts]
    if len(set(fechas)) != len(fechas):
        errores.append("hay fechas duplicadas")
    for p in posts:
        archivos = p.get("archivos") or [p["archivo"]]
        if not (2 <= len(archivos) <= 10) and p["tipo"] == "carrusel":
            errores.append(f"{p['id']}: carrusel con {len(archivos)} fotos (Instagram: 2-10)")
        for a in archivos:
            if not (RAIZ / a).exists():
                errores.append(f"{p['id']}: no existe {a}")
        if len(p["caption"]) > 2200:
            errores.append(f"{p['id']}: caption de {len(p['caption'])} caracteres (limite 2200)")
        if "cierre" in sin_tildes(p["audiencia"]).lower() and p["dia_semana"] != "domingo":
            errores.append(f"{p['id']}: es un cierre pero cae en {p['dia_semana']}")
    return errores


if __name__ == "__main__":
    INICIO = leer_inicio()
    posts = parsear()
    errores = validar(posts)
    DESTINO.write_text(json.dumps(posts, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{len(posts)} publicaciones -> {DESTINO.name}")
    print(f"del {posts[0]['fecha']} ({posts[0]['dia_semana']}) al {posts[-1]['fecha']} ({posts[-1]['dia_semana']}) · L-V {HORAS[0]} · S-D {HORAS[5]}")
    for p in posts[-3:]:
        extra = f" · {len(p['archivos'])} fotos" if p["tipo"] == "carrusel" else ""
        print(f"  {p['fecha']} {p['dia_semana']:9s} {p['id']}{extra}")
    if errores:
        print("\nAVISOS:")
        for e in errores:
            print(f"  - {e}")
        raise SystemExit(1)
    print("validacion OK")
