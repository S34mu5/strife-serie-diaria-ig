#!/usr/bin/env python3
"""Renueva el token de 60 dias por otros 60.

El token de Instagram Login caduca a los 60 dias. La serie dura 31, asi que no
hace falta durante la serie — esto es para despues, o si la alargas.

Requisitos de Meta: el token debe tener al menos 24 horas y no haber caducado.

Uso:  IG_ACCESS_TOKEN=... python3 refrescar_token.py
Imprime solo la fecha de caducidad nueva; el token va al fichero token-nuevo.txt
para que lo pegues tu en GitHub (nunca se imprime en pantalla ni en logs).
"""
import json, os, urllib.parse, urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

HOST = os.environ.get("GRAPH_HOST", "graph.instagram.com")


def main():
    token = os.environ.get("IG_ACCESS_TOKEN")
    if not token:
        raise SystemExit("exporta IG_ACCESS_TOKEN")

    url = f"https://{HOST}/refresh_access_token?" + urllib.parse.urlencode({
        "grant_type": "ig_refresh_token", "access_token": token,
    })
    try:
        with urllib.request.urlopen(url, timeout=60) as r:
            d = json.load(r)
    except urllib.error.HTTPError as e:
        raise SystemExit(f"error al refrescar ({e.code}):\n{e.read().decode('utf-8', 'replace')}")

    nuevo = d.get("access_token")
    if not nuevo:
        raise SystemExit(f"respuesta inesperada: {d}")

    segundos = int(d.get("expires_in", 0))
    caduca = datetime.now(timezone.utc) + timedelta(seconds=segundos)
    destino = Path(__file__).resolve().parent / "token-nuevo.txt"
    destino.write_text(nuevo + "\n", encoding="utf-8")
    destino.chmod(0o600)

    print(f"token renovado. caduca el {caduca:%Y-%m-%d} ({segundos // 86400} dias)")
    print(f"esta en {destino.name} — pegalo en GitHub como IG_ACCESS_TOKEN y borra el fichero")


if __name__ == "__main__":
    main()
