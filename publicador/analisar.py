"""Puxa dados de um perfil (posts, métricas, público) e grava em status/analise-<perfil>.json.

O perfil vem do arquivo status/analisar-agora (uma linha com o nome).
"""
import json
import pathlib
import sys
import time
from datetime import datetime, timedelta, timezone

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from meta import MetaErro, chamar  # noqa: E402

RAIZ = pathlib.Path(__file__).resolve().parent.parent


def tentar(*variantes):
    """Tenta chamadas alternativas (a API muda nomes de métricas entre versões)."""
    erros = []
    for metodo, caminho, params in variantes:
        try:
            r = chamar(metodo, caminho, params)
            r.pop("paging", None)  # links de paginação trazem o token
            return r
        except MetaErro as e:
            erros.append(str(e))
    return {"erro": erros}


def insights_post(mid, tipo):
    base = "reach,saved,shares,total_interactions"
    extra = ",views" if tipo != "CAROUSEL_ALBUM" else ""
    r = tentar(("GET", f"{mid}/insights", {"metric": base + extra}),
               ("GET", f"{mid}/insights", {"metric": base}),
               ("GET", f"{mid}/insights", {"metric": "reach,saved"}))
    if "data" not in r:
        return r
    return {m["name"]: (m.get("values") or [{}])[0].get("value") for m in r["data"]}


def main():
    nome = (RAIZ / "status" / "analisar-agora").read_text().split()[0].lstrip("@").lower()
    ig = json.loads((RAIZ / "perfis.json").read_text())[nome]
    out = {"perfil": nome, "gerado_em": datetime.now(timezone.utc).isoformat(timespec="seconds")}

    out["conta"] = tentar(("GET", ig, {"fields": "username,name,biography,website,followers_count,"
                                                 "follows_count,media_count"}))

    posts = []
    url_params = {"fields": "id,caption,media_type,media_product_type,timestamp,permalink,"
                            "like_count,comments_count", "limit": "50"}
    pagina = tentar(("GET", f"{ig}/media", url_params))
    for p in pagina.get("data", [])[:50]:
        p["insights"] = insights_post(p["id"], p.get("media_type"))
        if p.get("caption"):
            p["caption"] = p["caption"][:400]
        posts.append(p)
        time.sleep(0.3)
    out["posts"] = posts

    agora = datetime.now(timezone.utc)
    desde = int((agora - timedelta(days=28)).timestamp())
    ate = int(agora.timestamp())
    out["conta_28d"] = tentar(("GET", f"{ig}/insights", {
        "metric": "reach,views,accounts_engaged,total_interactions,profile_links_taps,follows_and_unfollows",
        "period": "day", "metric_type": "total_value", "since": desde, "until": ate}),
        ("GET", f"{ig}/insights", {"metric": "reach,accounts_engaged,total_interactions",
                                   "period": "day", "metric_type": "total_value",
                                   "since": desde, "until": ate}))

    publico = {}
    for quebra in ("age", "gender", "city"):
        publico[quebra] = tentar(
            ("GET", f"{ig}/insights", {"metric": "follower_demographics", "period": "lifetime",
                                       "metric_type": "total_value", "breakdown": quebra,
                                       "timeframe": "this_month"}),
            ("GET", f"{ig}/insights", {"metric": "follower_demographics", "period": "lifetime",
                                       "metric_type": "total_value", "breakdown": quebra}))
    publico["horarios_online"] = tentar(("GET", f"{ig}/insights", {"metric": "online_followers",
                                                                   "period": "lifetime"}))
    out["publico"] = publico

    saida = RAIZ / "status" / f"analise-{nome}.json"
    saida.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n")
    print("ok", saida, len(posts), "posts")


if __name__ == "__main__":
    main()
