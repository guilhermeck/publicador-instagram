"""Chamadas à Graph API da Meta (só biblioteca padrão)."""
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request

API = "https://graph.facebook.com/v21.0"


class MetaErro(Exception):
    pass


def _token():
    t = os.environ.get("INSTAGRAM_TOKEN", "").strip()
    if not t:
        raise MetaErro("Segredo INSTAGRAM_TOKEN não configurado no GitHub.")
    return t


def chamar(metodo, caminho, params=None):
    params = dict(params or {})
    params["access_token"] = _token()
    dados = urllib.parse.urlencode(params).encode()
    url = f"{API}/{caminho}"
    if metodo == "GET":
        req = urllib.request.Request(f"{url}?{dados.decode()}")
    else:
        req = urllib.request.Request(url, data=dados, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        corpo = e.read().decode(errors="replace")
        try:
            msg = json.loads(corpo).get("error", {}).get("message", corpo)
        except ValueError:
            msg = corpo
        raise MetaErro(f"HTTP {e.code}: {msg}") from None


def esperar_container(container_id, limite_seg=600):
    """Vídeos (Reels/stories) precisam ser processados antes de publicar."""
    inicio = time.time()
    while True:
        st = chamar("GET", container_id, {"fields": "status_code,status"})
        code = st.get("status_code")
        if code == "FINISHED":
            return
        if code in ("ERROR", "EXPIRED"):
            raise MetaErro(f"Processamento falhou: {st.get('status')}")
        if time.time() - inicio > limite_seg:
            raise MetaErro("Tempo esgotado esperando a Meta processar a mídia.")
        time.sleep(10)


def publicar(ig_id, tipo, urls, legenda=""):
    """Cria o container e publica. Retorna o id da mídia publicada."""
    tipo = tipo.lower()
    eh_video = lambda u: u.lower().split("?")[0].endswith((".mp4", ".mov"))

    if tipo in ("foto", "imagem", "image"):
        c = chamar("POST", f"{ig_id}/media", {"image_url": urls[0], "caption": legenda})
        cid = c["id"]
        esperar_container(cid, 120)

    elif tipo in ("carrossel", "carousel"):
        if not 2 <= len(urls) <= 10:
            raise MetaErro("Carrossel precisa de 2 a 10 mídias.")
        filhos = []
        for u in urls:
            p = {"is_carousel_item": "true"}
            if eh_video(u):
                p.update(media_type="VIDEO", video_url=u)
            else:
                p["image_url"] = u
            f = chamar("POST", f"{ig_id}/media", p)["id"]
            esperar_container(f)
            filhos.append(f)
        c = chamar("POST", f"{ig_id}/media",
                   {"media_type": "CAROUSEL", "children": ",".join(filhos), "caption": legenda})
        cid = c["id"]
        esperar_container(cid, 300)

    elif tipo in ("reels", "reel", "video"):
        c = chamar("POST", f"{ig_id}/media",
                   {"media_type": "REELS", "video_url": urls[0], "caption": legenda,
                    "share_to_feed": "true"})
        cid = c["id"]
        esperar_container(cid)

    elif tipo in ("story", "stories"):
        p = {"media_type": "STORIES"}
        if eh_video(urls[0]):
            p["video_url"] = urls[0]
        else:
            p["image_url"] = urls[0]
        cid = chamar("POST", f"{ig_id}/media", p)["id"]
        esperar_container(cid)

    else:
        raise MetaErro(f"Tipo de post desconhecido: {tipo}")

    pub = chamar("POST", f"{ig_id}/media_publish", {"creation_id": cid})
    return pub["id"]
