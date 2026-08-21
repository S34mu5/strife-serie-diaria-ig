#!/usr/bin/env python3
"""Convierte pies-de-foto.txt en calendario.json (28 posts, uno al dia)."""
import json, re, unicodedata
from datetime import date, timedelta
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
FUENTE = RAIZ / "pies-de-foto.txt"
DESTINO = Path(__file__).resolve().parent / "calendario.json"

INICIO = date(2026, 8, 24)   # lunes
HORA = "10:00"               # Europe/Madrid
DIAS_ES = ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"]


def sin_tildes(texto):
    return "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn")


def parsear():
    texto = FUENTE.read_text(encoding="utf-8")
    bloques = re.split(r"^D[ÍI]A\s+(\d+)\s*·\s*(.+?)$", texto, flags=re.MULTILINE)[1:]
    posts = []
    for i in range(0, len(bloques), 3):
        numero = int(bloques[i])
        cabecera = bloques[i + 1].strip()
        cuerpo = bloques[i + 2]

        archivo = re.search(r"^Archivo:\s*(\S+\.png)", cuerpo, re.MULTILINE)
        pie = re.search(r"^Pie:\s*(.+)$", cuerpo, re.MULTILINE)
        tags = re.search(r"^Tags:\s*(.+)$", cuerpo, re.MULTILINE)
        if not (archivo and pie):
            raise SystemExit(f"DIA {numero}: falta Archivo o Pie en pies-de-foto.txt")

        publica = INICIO + timedelta(days=numero - 1)
        etiquetas = tags.group(1).strip() if tags else ""
        # audiencia: "para el alumno" / "para el club" / "cierre"
        audiencia = cabecera.split("—")[-1].strip() if "—" in cabecera else cabecera

        posts.append({
            "dia": numero,
            "fecha": publica.isoformat(),
            "dia_semana": DIAS_ES[publica.weekday()],
            "hora": HORA,
            "audiencia": audiencia,
            "archivo": archivo.group(1),
            "pie": pie.group(1).strip(),
            "tags": etiquetas,
            "caption": f"{pie.group(1).strip()}\n\n{etiquetas}".strip(),
        })
    return posts


def validar(posts):
    errores = []
    if len(posts) != 28:
        errores.append(f"se esperaban 28 posts, hay {len(posts)}")
    if [p["dia"] for p in posts] != list(range(1, len(posts) + 1)):
        errores.append("los numeros de dia no son consecutivos del 1 al 28")
    for p in posts:
        if not (RAIZ / p["archivo"]).exists():
            errores.append(f"DIA {p['dia']}: no existe el archivo {p['archivo']}")
        if len(p["caption"]) > 2200:
            errores.append(f"DIA {p['dia']}: caption de {len(p['caption'])} caracteres (limite 2200)")
        # el guion marca los cierres en domingo
        if "cierre" in sin_tildes(p["audiencia"]).lower() and p["dia_semana"] != "domingo":
            errores.append(f"DIA {p['dia']}: es un cierre pero cae en {p['dia_semana']}")
    return errores


if __name__ == "__main__":
    posts = parsear()
    errores = validar(posts)
    DESTINO.write_text(json.dumps(posts, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{len(posts)} posts -> {DESTINO.name}")
    print(f"del {posts[0]['fecha']} ({posts[0]['dia_semana']}) al {posts[-1]['fecha']} ({posts[-1]['dia_semana']}) a las {HORA}")
    if errores:
        print("\nAVISOS:")
        for e in errores:
            print(f"  - {e}")
        raise SystemExit(1)
    print("validacion OK: 28 archivos presentes, captions dentro de limite, cierres en domingo")
