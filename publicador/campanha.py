"""Cria uma campanha de anúncios SEMPRE pausada, ou ativa uma já criada (só com pedido explícito).

status/campanha.json:
  {"id": "...", "acao": "criar", "conta": "act_...", "campanha": {...}, "conjunto": {...}, "criativo": {...}, "anuncio": {...}}
  {"id": "...", "acao": "ativar", "ids": ["<campanha>", "<conjunto>", "<anuncio>"]}
Grava status/campanha-<id>.json (o workflow criptografa).
"""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from meta import MetaErro, chamar  # noqa: E402

RAIZ = pathlib.Path(__file__).resolve().parent.parent


def campos(d):
    return {k: (json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v) for k, v in d.items()}


def criar(p, out):
    conta = p["conta"]
    camp = dict(p["campanha"], status="PAUSED")
    try:
        out["campanha_id"] = chamar("POST", f"{conta}/campaigns", campos(camp))["id"]
    except MetaErro as e:
        if "is_adset_budget_sharing_enabled" not in str(e) and "budget sharing" not in str(e).lower():
            raise
        camp["is_adset_budget_sharing_enabled"] = False
        out["campanha_id"] = chamar("POST", f"{conta}/campaigns", campos(camp))["id"]

    conj = dict(p["conjunto"], campaign_id=out["campanha_id"], status="PAUSED")
    out["conjunto_id"] = chamar("POST", f"{conta}/adsets", campos(conj))["id"]

    cri = dict(p["criativo"])
    try:
        out["criativo_id"] = chamar("POST", f"{conta}/adcreatives", campos(cri))["id"]
    except MetaErro as e:
        if "instagram_user_id" not in cri:
            raise
        out["aviso_criativo"] = str(e)
        cri["instagram_actor_id"] = cri.pop("instagram_user_id")
        out["criativo_id"] = chamar("POST", f"{conta}/adcreatives", campos(cri))["id"]

    ad = dict(p["anuncio"], adset_id=out["conjunto_id"], creative={"creative_id": out["criativo_id"]}, status="PAUSED")
    out["anuncio_id"] = chamar("POST", f"{conta}/ads", campos(ad))["id"]

    out["conferencia"] = {
        "campanha": chamar("GET", out["campanha_id"], {"fields": "name,objective,status,effective_status"}),
        "conjunto": chamar("GET", out["conjunto_id"], {"fields": "name,status,effective_status,lifetime_budget,start_time,"
                                                                  "end_time,optimization_goal,destination_type,promoted_object,targeting"}),
        "anuncio": chamar("GET", out["anuncio_id"], {"fields": "name,status,effective_status,preview_shareable_link"}),
    }


def ativar(p, out):
    out["ativados"] = {}
    for i in p["ids"]:
        chamar("POST", i, {"status": "ACTIVE"})
        out["ativados"][i] = chamar("GET", i, {"fields": "name,status,effective_status"})


def main():
    p = json.loads((RAIZ / "status" / "campanha.json").read_text())
    out = {"id": p["id"], "acao": p["acao"]}
    try:
        {"criar": criar, "ativar": ativar}[p["acao"]](p, out)
        out["ok"] = True
    except MetaErro as e:
        out["ok"] = False
        out["erro"] = str(e)
        out["etapa"] = ("campanha" if "campanha_id" not in out else "conjunto" if "conjunto_id" not in out
                        else "criativo" if "criativo_id" not in out else "anuncio")
    (RAIZ / "status" / f"campanha-{p['id']}.json").write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n")
    print("ok" if out["ok"] else "erro")


if __name__ == "__main__":
    main()
