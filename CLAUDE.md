# DAI Prospects — Instruções do Projeto

## Checklist OBRIGATÓRIO para cada nova LP de prospect

**Ao criar uma nova LP, TODOS os passos abaixo DEVEM ser executados, nesta ordem:**

```
[ ] 1. Criar pasta: prospects/<slug>/img/
[ ] 2. Baixar imagens do Instagram (hero sem texto, about, casos clínicos)
[ ] 3. Criar index.html na pasta do prospect
[ ] 4. Adicionar entrada em workers/subdomain-router/worker.js  → ROUTING map
[ ] 5. Adicionar entrada em workers/subdomain-router/routing.json
[ ] 6. Adicionar rota em workers/subdomain-router/wrangler.toml
[ ] 7. *** CRIAR DNS CNAME *** via Cloudflare API (ver comando abaixo)
[ ] 8. Deploy do Worker: CLOUDFLARE_API_TOKEN=$CF_API_TOKEN_WORKERS npx wrangler deploy --no-bundle
[ ] 9. Commit + push (git add + git commit + git push origin main)
```

### Passo 7 — Criar DNS CNAME (NÃO PULAR!)

```bash
source /cortex/secrets/org/cloudflare.env
ZONE_ID="82ac933764b2f11edeee34ee88d5a82d"
SLUG="<nome-do-subdominio>"   # ex: drameiriellyfedrigo

curl -s -X POST \
  "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records" \
  -H "Authorization: Bearer $CF_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"type\": \"CNAME\",
    \"name\": \"$SLUG\",
    \"content\": \"prospects.digital-ai.tech\",
    \"proxied\": true,
    \"comment\": \"LP prospect\"
  }"
```

> Erro 81053 = CNAME já existe. Isso é OK — prosseguir normalmente.
> Sem o CNAME: o subdomínio não resolve → SSL falha → página inacessível.

---

## Stack do projeto

- **Hospedagem:** GitHub Pages → `prospects.digital-ai.tech`
- **Roteamento:** Cloudflare Worker `dai-prospects-router`
- **Cada subdomínio:** `<slug>.digital-ai.tech` → `prospects.digital-ai.tech/<pasta>/`
- **Secrets:** `/cortex/secrets/org/cloudflare.env`
  - `CF_API_TOKEN` → DNS + Worker read
  - `CF_API_TOKEN_WORKERS` → Wrangler deploy

## Estrutura de pastas

```
prospects/
  <slug>/
    index.html
    img/
      dra_xxx_hero.jpg    # foto sem texto, fundo limpo
      dra_xxx_about.jpg   # segunda foto (jaleco, clínica)
      resultado_xxx.jpg   # casos clínicos (1-2 imagens)
workers/
  subdomain-router/
    worker.js             # ROUTING map
    routing.json          # índice de rotas
    wrangler.toml         # rotas explícitas Cloudflare
```

## Regras de design

- Hero: **foto SEM texto/escrita sobreposta** e fundo limpo (regra de memória: `feedback_lp_hero_photo.md`)
- Cada seção usa foto **única** — sem repetição entre seções (`feedback_lp_no_duplicate_photos.md`)
- LP é **brinde para pacientes da prospect**, não pitch B2B da Digital AI (`feedback_leadkit_lp_purpose.md`)
- Botão flutuante: **WhatsApp verde** (#25D366, círculo 58px, ícone SVG)
- `html { background: var(--dark) }` para overscroll escuro; `body` mantém background claro
- Footer sem `padding` e `text-align: center` — inner divs gerenciam próprio layout

## Gotchas conhecidos

Ver: `/cortex/projects/dai-prospects/gotchas.md`
