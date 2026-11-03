# Publicador Instagram

Publica e agenda posts nos perfis do Instagram usando o token permanente do
usuário do sistema "Robo Publicacao" (portfólio lestenewstb). Gratuito: roda no
GitHub Actions.

## Como funciona

1. Cada post é uma pasta em `posts/`, com as mídias e um `post.json`.
2. A cada 15 minutos o GitHub confere a fila e publica o que já chegou na hora.
3. Depois de publicar, o `status` do post muda para `publicado` (ou `erro`, com o motivo).

## post.json

```json
{
  "perfil": "gcharneski",
  "tipo": "foto",
  "midias": ["1.jpg"],
  "legenda": "Texto do post #hashtag",
  "publicar_em": "2026-11-06T19:00:00-03:00",
  "status": "agendado"
}
```

- `tipo`: `foto`, `carrossel` (2 a 10 mídias), `reels` (vídeo .mp4) ou `story`.
- Imagens em **JPEG**, proporção entre 4:5 e 1.91:1 (1080x1350 é o ideal).
- O horário pode atrasar alguns minutos (o GitHub confere a fila a cada 15 min).

## Perfis

Listados em `perfis.json` (nome → ID do Instagram). Para um perfil novo: coloque-o
no portfólio lestenewstb, atribua ao Robo Publicacao e adicione aqui.

## Configuração

- Segredo do repositório `INSTAGRAM_TOKEN` = token do Robo Publicacao
  (Settings → Secrets and variables → Actions).
- Teste: aba Actions → "Testar conexão com os perfis" → Run workflow.
  O resultado fica em `status/teste.json`.
