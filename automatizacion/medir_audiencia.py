#!/usr/bin/env python3
"""Mide con datos reales de la cuenta cuando publicar.

1. online_followers: a que hora estan conectados TUS seguidores (histograma
   por hora, ultimos 30 dias). Instagram exige 100+ seguidores para servirlo.
2. rendimiento por publicacion: alcance y likes de cada post ya publicado,
   cruzado con su hora, para ver que franjas funcionan.

Uso:  IG_USER_ID=... IG_ACCESS_TOKEN=... python3 medir_audiencia.py
Si las franjas reales contradicen las HORAS de generar_calendario.py,
cambia HORAS y el cron de .github/workflows/publicar-instagram.yml.
"""
import json, os, urllib.parse, urllib.request
from collections import Counter
from pathlib import Path

VERSION = os.environ.get("GRAPH_VERSION", "v21.0")


def api(ruta, datos):
    url = f"https://graph.facebook.com/{VERSION}/{ruta}?" + urllib.parse.urlencode(datos)
    try:
        with urllib.request.urlopen(url, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        return {"error": json.loads(e.read().decode("utf-8", "replace")).get("error", {})}


def main():
    ig_user = os.environ.get("IG_USER_ID")
    token = os.environ.get("IG_ACCESS_TOKEN")
    if not (ig_user and token):
        raise SystemExit("exporta IG_USER_ID e IG_ACCESS_TOKEN")

    print("== ¿A qué hora están conectados tus seguidores? (UTC) ==")
    r = api(f"{ig_user}/insights", {"metric": "online_followers", "period": "lifetime", "access_token": token})
    if "error" in r:
        print(f"  sin datos todavía: {r['error'].get('message', r['error'])}")
        print("  (Instagram lo sirve a partir de ~100 seguidores)")
    else:
        horas = Counter()
        for serie in r.get("data", []):
            for punto in serie.get("values", []):
                for h, n in (punto.get("value") or {}).items():
                    horas[int(h)] += n
        if horas:
            tope = max(horas.values())
            for h in range(24):
                n = horas.get(h, 0)
                print(f"  {h:02d}h UTC ({(h + 2) % 24:02d}h Madrid) {'█' * int(n / tope * 40):40s} {n}")
            mejores = [f"{(h + 2) % 24:02d}h Madrid" for h, _ in horas.most_common(3)]
            print(f"  mejores franjas: {', '.join(mejores)}")

    print("\n== Rendimiento de lo ya publicado ==")
    registro = Path(__file__).resolve().parent / "registro.json"
    if not registro.exists():
        print("  aún no hay publicaciones registradas")
        return
    for clave, fila in json.loads(registro.read_text()).items():
        m = api(f"{fila['post_id']}/insights", {"metric": "reach,likes,saved,shares", "access_token": token})
        if "error" in m:
            print(f"  {clave}: {m['error'].get('message', 'sin metricas')}")
            continue
        valores = {d["name"]: d["values"][0]["value"] for d in m.get("data", [])}
        print(f"  {clave} ({fila['fecha_programada']}): " + " · ".join(f"{k} {v}" for k, v in valores.items()))


if __name__ == "__main__":
    main()
