"""Publica os posts da fila (posts/*/post.json) cujo horário já chegou.

Formato de posts/<id>/post.json:
{
  "perfil": "gcharneski",
  "tipo": "foto" | "carrossel" | "reels" | "story",
  "midias": ["1.jpg", "2.jpg"],          # arquivos dentro da pasta do post
  "legenda": "texto...",
  "publicar_em": "2026-11-06T19:00:00-03:00",
  "status": "agendado"                    # o robô troca para publicado/erro
}
"""
import json
import pathlib
import sys
from datetime import datetime, timezone

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from meta import MetaErro, publicar  # noqa: E402

RAIZ = pathlib.Path(__file__).resolve().parent.parent
REPO = "guilhermeck/publicador-instagram"
RAW = f"https://raw.githubusercontent.com/{REPO}/main"
MAX_TENTATIVAS = 3


def agora():
    return datetime.now(timezone.utc)


def main():
    perfis = json.loads((RAIZ / "perfis.json").read_text())
    alterou = False
    for arq in sorted((RAIZ / "posts").glob("*/post.json")):
        post = json.loads(arq.read_text())
        if post.get("status") != "agendado":
            continue
        quando = datetime.fromisoformat(post["publicar_em"])
        if quando > agora():
            continue

        pasta = arq.parent.name
        nome = post["perfil"].lstrip("@").lower()
        print(f"[{pasta}] publicando em @{nome} ({post['tipo']})...")
        try:
            ig_id = perfis[nome]
        except KeyError:
            post.update(status="erro", erro=f"Perfil @{nome} não está em perfis.json")
        else:
            urls = [f"{RAW}/posts/{pasta}/{m}" for m in post["midias"]]
            try:
                mid = publicar(ig_id, post["tipo"], urls, post.get("legenda", ""))
                post.update(status="publicado", media_id=mid,
                            publicado_em=agora().isoformat(timespec="seconds"))
                post.pop("erro", None)
                print(f"[{pasta}] OK, mídia {mid}")
            except MetaErro as e:
                post["tentativas"] = post.get("tentativas", 0) + 1
                post["erro"] = str(e)
                if post["tentativas"] >= MAX_TENTATIVAS:
                    post["status"] = "erro"
                print(f"[{pasta}] ERRO: {e}")
        arq.write_text(json.dumps(post, ensure_ascii=False, indent=2) + "\n")
        alterou = True

    if not alterou:
        print("Nada para publicar agora.")


if __name__ == "__main__":
    main()
