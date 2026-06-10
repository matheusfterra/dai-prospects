#!/usr/bin/env python3
"""
run_diagnostic.py — OpenAI Agents SDK Diagnostic Runner
- Instagram: instagram-browser MCP (SSE)
- Web/Google: crawl4prospect MCP (SSE)

Usage:
  python3 run_diagnostic.py \
    --slug odontoclinic-itumbiara \
    --ig-handle odontoclinicbr \
    --website-url https://odontoclinic.com.br \
    --brand-name "Odontoclinic" \
    --city "Itumbiara" \
    --sector "Odontologia" \
    [--callback-url https://webhook.digital-ai.tech/webhook/xxx]
"""

import asyncio
import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

import httpx
from agents import Agent, Runner
from agents.mcp import MCPServerSse


# ─── Config ────────────────────────────────────────────────────────────────────
TEMPLATE_PATH = Path("/workspace/dai-prospects/prospects/_template-health/template.html")
PROSPECTS_DIR  = Path("/workspace/dai-prospects/prospects")

IG_MCP_URL    = "https://agent-ig-browser-mcp.digital-ai.tech/sse"
IG_MCP_TOKEN  = "ig-mcp-2026-secret"
CRAWL_MCP_URL = "https://mcp-crawl4prospect.digital-ai.tech/sse"


# ─── Agent instructions ───────────────────────────────────────────────────────
AGENT_INSTRUCTIONS = """
Você é o Digital Presence Diagnostic Agent da Digital AI — empresa brasileira de AI-as-a-Service.

Seu trabalho: analisar a presença digital de um prospect e retornar um JSON estruturado
com TODAS as variáveis para preencher o template HTML de diagnóstico.

## Ferramentas disponíveis
- **Instagram MCP**: list_profile_posts, get_post_comments, get_profile_info — dados do Instagram
- **Crawl4Prospect MCP**: firecrawl_scrape(url), firecrawl_search(query) — scraping e busca na web

## Metodologia de Score (100 pts total)

### Instagram (40 pts):
- Engajamento: ER > 3% = 10pts | 1–3% = 7pts | <1% = 3pts
  ER = (média_likes + média_comments) / seguidores * 100
- Frequência (últimos 30d): >8 posts = 10pts | 4–8 = 7pts | 1–3 = 4pts | 0 = 0pts
- Sentimento (comentários top posts): >70% positivo = 10pts | 50–70% = 6pts | <50% = 3pts
- Consistência visual: consistente = 10pts | inconsistente = 5pts | muito fraca = 2pts

### Google (35 pts):
- Busca pelo nome (página 1): 5pts
- Busca especialidade+cidade (top 3): 10pts | página 1: 7pts | não encontrado: 0pts
- GMB existe: 10pts | não existe: 0pts
- Avaliação GMB ≥4.5: 5pts | ≥3.5: 3pts | <3.5: 1pt | sem GMB: 0pts
- Responde avaliações: sempre=5pts | raramente=2pts | nunca/sem GMB=0pts

### Website (25 pts):
- Existe: 10pts | não existe: 0pts
- Mobile-friendly: 5pts (viewport meta + layout responsivo)
- Velocidade OK: 5pts | lento: 2pts
- SEO básico (title, meta desc, H1): completo=5pts | parcial=3pts | ausente=0pts

## Grades: A=80–100 | B=60–79 | C=40–59 | D=20–39 | F=0–19

## Cores dos scores:
- IG_COLOR: var(--green) se IG_SCORE ≥ 30 | var(--yellow) se 20–29 | var(--red) se <20
- GOOGLE_COLOR: var(--green) se ≥ 26 | var(--yellow) se 17–25 | var(--red) se <17
- WEB_COLOR: var(--green) se ≥ 19 | var(--yellow) se 12–18 | var(--red) se <12
- GRADE_COLOR: var(--green) para A/B | var(--yellow) para C/D | var(--red) para F
- WEB_C*_COLOR: "#34D399" se passou | "#F87171" se falhou

## Labels: Excelente (verde) | Em Desenvolvimento (amarelo) | Crítico (vermelho)

## IMPORTANTE:
- Responda SOMENTE com o JSON puro. Sem markdown, sem ```json, sem texto adicional.
- Todas as strings em português (pt-BR) exceto URLs.
- Use dados reais coletados pelas ferramentas.
"""


def build_prompt(slug: str, ig_handle: str, website_url: str,
                 brand_name: str, city: str, sector: str) -> str:
    today = datetime.now().strftime("%d/%m/%Y")
    handle_clean = ig_handle.lstrip('@')
    brand_parts = brand_name.split(maxsplit=1)
    brand_first = brand_parts[0]
    brand_rest  = brand_parts[1] if len(brand_parts) > 1 else ''

    website_instruction = (
        f"Use web_scrape('{website_url}') para verificar: existência, viewport meta (mobile), "
        f"title tag, meta description, H1, velocidade estimada."
        if website_url
        else "Não foi fornecido website. Verifique se o GMB ou bio do Instagram menciona um. "
             "Se não encontrar nenhum, WEB_SCORE = 0."
    )

    ig_section = (
        f"## PASSO 1 — Instagram (use list_profile_posts e get_post_comments)\n"
        f"1. list_profile_posts para @{handle_clean} (limit=50)\n"
        f"2. Calcule: total de posts, seguidores, ER médio, posts nos últimos 30 dias\n"
        f"3. Identifique top 3 posts por likes\n"
        f"4. get_post_comments nos top 2 posts (limit=20 cada)\n"
        f"5. Analise sentimento: conte positivos, negativos, neutros, mistos\n"
        f"6. Identifique 3 categorias recorrentes de comentários\n"
        f"7. Escolha 4 comentários representativos reais"
        if handle_clean
        else "## PASSO 1 — Instagram\nNão foi fornecido handle do Instagram. "
             "Defina todos os campos IG_* como zero/vazio e IG_SCORE = 0."
    )

    return f"""Analise a presença digital deste prospect:

- Marca: {brand_name}
- Cidade: {city}, Brasil
- Setor: {sector}
- Instagram: {"@" + handle_clean if handle_clean else "não informado"}
- Website: {website_url or "não informado"}
- Slug: {slug}
- Hoje: {today}

{ig_section}

## PASSO 2 — Google/Local (use web_search)
1. web_search("{brand_name} {city}") — aparece na página 1?
2. web_search("{sector} {city}") — aparece no top 3? Maps pack?
3. web_search("{brand_name} {city} avaliações") — tem GMB? qual rating?
4. Verifique se tem GMB ativo com avaliações e se responde

## PASSO 3 — Website
{website_instruction}

## PASSO 4 — Calcule scores e retorne JSON

Retorne SOMENTE o JSON com TODOS os campos abaixo preenchidos com dados reais.
Substitua os valores entre [] pelos dados coletados.

{{
  "BRAND_NAME": "{brand_name}",
  "BRAND_NAME_FIRST": "{brand_first}",
  "BRAND_NAME_REST": "{brand_rest}",
  "BRAND_DIFFERENTIATOR": "[diferencial em 1 frase, ex: 'Especialista em saúde bucal']",
  "CITY": "{city}",
  "SECTOR": "{sector}",
  "SLUG": "{slug}",
  "ANALYSIS_DATE": "{today}",
  "WHATSAPP": "+55 64 99294-3740",
  "WEBSITE_URL": "[URL do site real, ou vazio]",

  "SCORE": 0,
  "GRADE": "F",
  "GRADE_COLOR": "var(--red)",

  "HERO_SUMMARY_TITLE": "[título impactante baseado nos achados]",
  "HERO_SUMMARY_DESC": "[2 frases resumindo os principais pontos]",
  "PILLARS_SUBTITLE": "[subtítulo descritivo para a seção dos 3 pilares]",

  "IG_HANDLE": "{handle_clean}",
  "IG_FOLLOWERS": "[número formatado, ex: '12.4K' ou '892']",
  "IG_POSTS": "[quantidade de posts]",
  "IG_ER": "[taxa de engajamento, ex: '3.2%']",
  "IG_SCORE": 0,
  "IG_COLOR": "var(--red)",
  "IG_LABEL": "Crítico",
  "IG_INTRO_TITLE": "[título da análise do Instagram]",
  "IG_INTRO_DESC": "[2 frases sobre a performance do Instagram]",
  "IG_DESC": "[1 linha sobre o desempenho no Instagram]",
  "IG_INSIGHT": "[insight chave, ex: 'Frequência crítica compromete o alcance orgânico']",
  "IG_SCORE_DESC": "[explicação do score do Instagram]",

  "POST1_URL": "[URL completa do post, ex: https://instagram.com/p/SHORTCODE]",
  "POST1_LIKES": "[número de likes]",
  "POST1_COMMENTS": "[número de comentários]",
  "POST1_DATE": "[DD/MM/YYYY]",
  "POST1_ER": "[ER deste post, ex: '4.1%']",
  "POST1_TYPE": "[Foto|Vídeo|Carrossel|Reel]",
  "POST1_CAPTION": "[primeiros 120 chars da legenda]",
  "POST1_ALT": "[descrição do conteúdo visual para alt text]",

  "POST2_URL": "",
  "POST2_LIKES": "",
  "POST2_COMMENTS": "",
  "POST2_DATE": "",
  "POST2_ER": "",
  "POST2_TYPE": "",
  "POST2_CAPTION": "",
  "POST2_ALT": "",

  "POST3_URL": "",
  "POST3_LIKES": "",
  "POST3_COMMENTS": "",
  "POST3_DATE": "",
  "POST3_ER": "",
  "POST3_TYPE": "",
  "POST3_CAPTION": "",
  "POST3_ALT": "",

  "COMMENT_1_TEXT": "[texto real de um comentário positivo]",
  "COMMENT_1_POST_URL": "[URL do post onde foi o comentário]",
  "COMMENT_1_CAT": "[categoria, ex: 'Elogio']",
  "COMMENT_2_TEXT": "[comentário real]",
  "COMMENT_2_POST_URL": "",
  "COMMENT_2_CAT": "[ex: 'Pergunta']",
  "COMMENT_3_TEXT": "[comentário real]",
  "COMMENT_3_POST_URL": "",
  "COMMENT_3_CAT": "[ex: 'Interesse em serviço']",
  "COMMENT_4_TEXT": "[comentário real]",
  "COMMENT_4_POST_URL": "",
  "COMMENT_4_CAT": "[ex: 'Indicação']",

  "SENT_HEADLINE": "[ex: 'Comunidade engajada e satisfeita']",
  "SENT_DESC": "[2 frases sobre sentimento geral dos comentários]",
  "SENT_BAR_TITLE": "Distribuição de Sentimentos",
  "SENT_TOTAL": 0,
  "SENT_POSTS_ANALYZED": 0,
  "SENT_COUNT_POSITIVE": 0,
  "SENT_COUNT_NEGATIVE": 0,
  "SENT_COUNT_MIXED": 0,
  "SENT_COUNT_NEUTRO": 0,
  "SENT_POSITIVE_PCT": 0,
  "SENT_POSITIVE": "0%",
  "SENT_CAT_1": "[categoria recorrente 1, ex: 'Elogios ao atendimento']",
  "SENT_CAT_1_COUNT": 0,
  "SENT_CAT_2": "[categoria recorrente 2]",
  "SENT_CAT_2_COUNT": 0,
  "SENT_CAT_3": "[categoria recorrente 3]",
  "SENT_CAT_3_COUNT": 0,
  "SENT_CAT_COMPLAINT_COUNT": 0,

  "GOOGLE_SCORE": 0,
  "GOOGLE_COLOR": "var(--red)",
  "GOOGLE_LABEL": "Crítico",
  "GOOGLE_HEADLINE": "[ex: 'Invisível para pacientes que buscam no Google']",
  "GOOGLE_DESC": "[2 frases sobre presença no Google]",
  "GOOGLE_LEVEL": "[Básico|Intermediário|Avançado]",
  "GOOGLE_GAP_TEXT": "[principal lacuna no Google, ex: 'Sem Google Meu Negócio']",

  "GOOGLE_CHECK_1_TITLE": "Busca pelo nome",
  "GOOGLE_CHECK_1_DESC": "[resultado da busca]",
  "GOOGLE_CHECK_1_ICON": "[✓ ou ✗]",
  "GOOGLE_CHECK_1_CLASS": "[check-pass ou check-fail]",
  "GOOGLE_CHECK_2_TITLE": "Busca por especialidade+cidade",
  "GOOGLE_CHECK_2_DESC": "[resultado]",
  "GOOGLE_CHECK_2_ICON": "[✓ ou ✗]",
  "GOOGLE_CHECK_2_CLASS": "[check-pass ou check-fail]",
  "GOOGLE_CHECK_3_TITLE": "Google Meu Negócio",
  "GOOGLE_CHECK_3_DESC": "[resultado]",
  "GOOGLE_CHECK_3_ICON": "[✓ ou ✗]",
  "GOOGLE_CHECK_3_CLASS": "[check-pass ou check-fail]",
  "GOOGLE_CHECK_4_TITLE": "Avaliações no Google",
  "GOOGLE_CHECK_4_DESC": "[resultado]",
  "GOOGLE_CHECK_4_ICON": "[✓ ou ✗]",
  "GOOGLE_CHECK_4_CLASS": "[check-pass ou check-fail]",
  "GOOGLE_CHECK_5_TITLE": "Resposta às avaliações",
  "GOOGLE_CHECK_5_DESC": "[resultado]",
  "GOOGLE_CHECK_5_ICON": "[✓ ou ✗]",
  "GOOGLE_CHECK_5_CLASS": "[check-pass ou check-fail]",

  "WEB_SCORE": 0,
  "WEB_COLOR": "var(--red)",
  "WEB_LABEL": "Crítico",
  "WEB_HEADLINE": "[ex: 'Site ausente — maior gap de conversão']",
  "WEB_DESC": "[2 frases sobre o website]",
  "WEB_MOCKUP_ICON": "⚠️",
  "WEB_MOCKUP_TEXT": "[texto curto para o mockup, ex: 'Site não encontrado']",

  "WEB_C1_TEXT": "Site Ativo",
  "WEB_C1_ICON": "[✓ ou ✗]",
  "WEB_C1_COLOR": "[#34D399 ou #F87171]",
  "WEB_C2_TEXT": "Mobile Friendly",
  "WEB_C2_ICON": "[✓ ou ✗]",
  "WEB_C2_COLOR": "[#34D399 ou #F87171]",
  "WEB_C3_TEXT": "SEO Básico",
  "WEB_C3_ICON": "[✓ ou ✗]",
  "WEB_C3_COLOR": "[#34D399 ou #F87171]",
  "WEB_C4_TEXT": "Velocidade OK",
  "WEB_C4_ICON": "[✓ ou ✗]",
  "WEB_C4_COLOR": "[#34D399 ou #F87171]",

  "REC1_TITLE": "[recomendação de maior impacto]",
  "REC1_DESC": "[descrição detalhada da ação necessária]",
  "REC1_IMPACT": "[ex: '+18 pts no score']",
  "REC1_GAIN": "[benefício principal, ex: 'Visibilidade local imediata']",
  "REC2_TITLE": "",
  "REC2_DESC": "",
  "REC2_IMPACT": "",
  "REC2_GAIN": "",
  "REC3_TITLE": "",
  "REC3_DESC": "",
  "REC3_IMPACT": "",
  "REC3_GAIN": "",
  "REC4_TITLE": "",
  "REC4_DESC": "",
  "REC4_IMPACT": "",
  "REC4_GAIN": "",
  "REC5_TITLE": "",
  "REC5_DESC": "",
  "REC5_IMPACT": "",
  "REC5_GAIN": "",

  "PROJ_SCORE": 0,
  "PROJ_GRADE": "B",
  "PROJ_GRADE_TARGET": "Grau B",
  "PROJ_DESC": "[o que será alcançado após implementar as recomendações]",
  "PROJ_NOTE": "Em 60 dias com suporte Digital AI",

  "CTA_TITLE_LINE1": "Pronto para transformar",
  "CTA_TITLE_ITALIC": "sua presença digital?",
  "CTA_DESC": "[descrição personalizada do CTA para o setor do prospect]",
  "WA_MSG": "Olá! Vi o diagnóstico da {brand_name} e quero saber mais sobre como melhorar minha presença digital."
}}"""


def fill_template(template: str, variables: dict) -> str:
    """Substitui todas as variáveis {{VAR}} no template."""
    result = template
    for key, value in variables.items():
        placeholder = "{{" + key + "}}"
        str_value = str(value) if value is not None else ""
        result = result.replace(placeholder, str_value)
    return result


def check_unfilled_vars(html: str) -> list:
    return re.findall(r"\{\{[^}]+\}\}", html)


async def run_diagnostic(slug: str, ig_handle: str, website_url: str,
                          brand_name: str, city: str, sector: str) -> dict:
    """Executa o agente e retorna dict com as variáveis do template."""

    ig_server = MCPServerSse(
        params={
            "url": IG_MCP_URL,
            "headers": {"Authorization": f"Bearer {IG_MCP_TOKEN}"}
        },
        cache_tools_list=True,
        name="instagram-browser",
        client_session_timeout_seconds=120,  # Instagram API pode demorar
    )

    crawl_server = MCPServerSse(
        params={"url": CRAWL_MCP_URL},
        cache_tools_list=True,
        name="crawl4prospect",
        client_session_timeout_seconds=60,
    )

    prompt = build_prompt(slug, ig_handle, website_url, brand_name, city, sector)

    print(f"[diagnostic] Conectando aos MCPs (Instagram + Crawl4Prospect)...", file=sys.stderr)

    async with ig_server, crawl_server:
        agent = Agent(
            name="DiagnosticAgent",
            model="gpt-4o",
            instructions=AGENT_INSTRUCTIONS,
            mcp_servers=[ig_server, crawl_server],
        )

        print(f"[diagnostic] Executando diagnóstico de @{ig_handle.lstrip('@')}...", file=sys.stderr)

        result = await Runner.run(
            agent,
            prompt,
            max_turns=80,
        )

    output = result.final_output
    if not output:
        raise ValueError("Agente retornou output vazio")

    # Limpar possível markdown wrapper
    clean = output.strip()
    if clean.startswith("```"):
        clean = re.sub(r"^```(?:json)?\s*", "", clean)
        clean = re.sub(r"\s*```$", "", clean)

    variables = json.loads(clean)
    return variables


def build_html(slug: str, variables: dict) -> Path:
    """Preenche o template e salva o HTML."""
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    filled   = fill_template(template, variables)

    unfilled = check_unfilled_vars(filled)
    if unfilled:
        print(f"[diagnostic] AVISO: {len(unfilled)} vars não preenchidas: {unfilled[:5]}", file=sys.stderr)

    output_dir = PROSPECTS_DIR / f"{slug}-health"
    output_dir.mkdir(parents=True, exist_ok=True)

    html_path = output_dir / "index.html"
    html_path.write_text(filled, encoding="utf-8")

    print(f"[diagnostic] HTML salvo: {html_path}", file=sys.stderr)
    return html_path


async def main():
    parser = argparse.ArgumentParser(description="Digital Health Diagnostic Agent")
    parser.add_argument("--slug",         required=True)
    parser.add_argument("--ig-handle",    required=True)
    parser.add_argument("--website-url",  default="")
    parser.add_argument("--brand-name",   required=True)
    parser.add_argument("--city",         required=True)
    parser.add_argument("--sector",       default="Saúde")
    parser.add_argument("--callback-url", default="")
    args = parser.parse_args()

    print(f"[diagnostic] Iniciando: {args.brand_name} | @{args.ig_handle} | {args.city}", file=sys.stderr)

    variables = await run_diagnostic(
        slug=args.slug,
        ig_handle=args.ig_handle,
        website_url=args.website_url,
        brand_name=args.brand_name,
        city=args.city,
        sector=args.sector,
    )

    html_path = build_html(args.slug, variables)

    result = {
        "score":         variables.get("SCORE", 0),
        "grade":         variables.get("GRADE", "N/A"),
        "html_path":     str(html_path),
        "url":           f"https://{args.slug}-health.digital-ai.tech",
        "opportunities": [
            variables.get("REC1_TITLE", ""),
            variables.get("REC2_TITLE", ""),
            variables.get("REC3_TITLE", ""),
        ],
    }

    # Callback ao n8n
    if args.callback_url:
        async with httpx.AsyncClient(timeout=30) as client:
            try:
                resp = await client.post(
                    args.callback_url,
                    json={
                        "score":         result["score"],
                        "grade":         result["grade"],
                        "opportunities": result["opportunities"],
                        "url":           result["url"],
                    }
                )
                print(f"[diagnostic] Callback: HTTP {resp.status_code}", file=sys.stderr)
            except Exception as e:
                print(f"[diagnostic] Erro callback: {e}", file=sys.stderr)

    # Stdout: JSON para o n8n ler
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
