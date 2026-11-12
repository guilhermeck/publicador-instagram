"""Consultas de leitura (somente GET) na API da Meta.

Lê status/consulta.json: {"id": "...", "chamadas": [{"nome": "...", "caminho": "...", "params": {...}}]}
Grava status/consulta-<id>.json (o workflow criptografa). Nunca faz POST/DELETE.
"""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from meta import MetaErro, chamar  # noqa: E402

RAIZ = pathlib.Path(__file__).resolve().parent.parent


def main():
    pedido = json.loads((RAIZ / "status" / "consulta.json").read_text())
    out = {"id": pedido["id"], "resultados": {}}
    for c in pedido["chamadas"]:
        try:
            r = chamar("GET", c["caminho"], c.get("params", {}))
            r.pop("paging", None)
        except MetaErro as e:
            r = {"erro": str(e)}
        out["resultados"][c["nome"]] = r
    saida = RAIZ / "status" / f"consulta-{pedido['id']}.json"
    saida.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n")
    print("ok", saida.name)


if __name__ == "__main__":
    main()
