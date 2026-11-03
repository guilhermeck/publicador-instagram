"""Confere se o token enxerga cada perfil e grava o resultado em status/teste.json."""
import json
import pathlib
import sys
from datetime import datetime, timezone

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from meta import MetaErro, chamar  # noqa: E402

RAIZ = pathlib.Path(__file__).resolve().parent.parent


def main():
    perfis = json.loads((RAIZ / "perfis.json").read_text())
    resultado = {"testado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                 "perfis": {}}
    for nome, ig_id in perfis.items():
        try:
            d = chamar("GET", ig_id, {"fields": "username,followers_count,media_count"})
            resultado["perfis"][nome] = {"ok": True, "username": d.get("username"),
                                         "seguidores": d.get("followers_count")}
        except MetaErro as e:
            resultado["perfis"][nome] = {"ok": False, "erro": str(e)}
        print(nome, resultado["perfis"][nome])
    saida = RAIZ / "status" / "teste.json"
    saida.parent.mkdir(exist_ok=True)
    saida.write_text(json.dumps(resultado, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
