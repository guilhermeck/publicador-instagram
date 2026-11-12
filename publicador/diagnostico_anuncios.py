"""Diagnóstico para anúncios: permissões do token, contas de anúncio, páginas/WhatsApp e mídia do Reels.

Lê status/diagnosticar-agora: linha 1 = perfil, linha 2 = shortcode do post (opcional).
Grava status/diagnostico-<perfil>.json (o workflow criptografa).
"""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from meta import MetaErro, chamar  # noqa: E402

RAIZ = pathlib.Path(__file__).resolve().parent.parent


def tentar(metodo, caminho, params=None):
    try:
        r = chamar(metodo, caminho, params or {})
        r.pop("paging", None)
        return r
    except MetaErro as e:
        return {"erro": str(e)}


def main():
    linhas = (RAIZ / "status" / "diagnosticar-agora").read_text().split()
    nome = linhas[0].lstrip("@").lower()
    codigo = linhas[1] if len(linhas) > 1 else ""
    ig = json.loads((RAIZ / "perfis.json").read_text())[nome]
    out = {"perfil": nome}

    out["permissoes"] = tentar("GET", "me/permissions")
    out["eu"] = tentar("GET", "me", {"fields": "id,name"})
    out["contas_anuncio"] = tentar("GET", "me/adaccounts", {
        "fields": "id,account_id,name,account_status,currency,timezone_name,disable_reason,"
                  "business{id,name},funding_source_details,amount_spent,spend_cap",
        "limit": "50"})
    out["paginas"] = tentar("GET", "me/accounts", {
        "fields": "id,name,instagram_business_account{id,username},whatsapp_number,"
                  "connected_instagram_account{id,username}", "limit": "50"})

    midia = None
    if codigo:
        url = {"fields": "id,caption,media_type,media_product_type,permalink,timestamp,like_count,"
                         "comments_count,boost_eligibility_info", "limit": "50"}
        lista = tentar("GET", f"{ig}/media", url)
        for m in lista.get("data", []):
            if codigo in (m.get("permalink") or ""):
                midia = m
                break
        if midia is None and "erro" in lista:
            url["fields"] = url["fields"].replace(",boost_eligibility_info", "")
            lista = tentar("GET", f"{ig}/media", url)
            midia = next((m for m in lista.get("data", []) if codigo in (m.get("permalink") or "")), None)
        if midia and midia.get("caption"):
            midia["caption"] = midia["caption"][:600]
    out["midia"] = midia or {"erro": f"post {codigo} não encontrado nos 50 mais recentes"}

    saida = RAIZ / "status" / f"diagnostico-{nome}.json"
    saida.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n")
    print("ok")


if __name__ == "__main__":
    main()
