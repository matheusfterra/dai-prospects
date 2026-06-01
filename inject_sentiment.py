#!/usr/bin/env python3
"""
inject_sentiment.py
Lê sentiment_data/{slug}.json e injeta a seção "O que as pessoas estão dizendo"
nos health reports HTML correspondentes.

Uso:
  python3 inject_sentiment.py               # processa todos os slugs
  python3 inject_sentiment.py dra-thania-health  # processa slug específico
"""

import json
import sys
import re
from datetime import datetime, timezone
from html import escape
from pathlib import Path

BASE = Path(__file__).parent
SENTIMENT_DIR = BASE / "sentiment_data"
PROSPECTS_DIR = BASE / "prospects"

# Mapeamento slug → diretório do health report
SLUG_MAP = {
    "dra-thania-health": "dra-thania-health",
    "dra-anapaulapaludo-health": "dra-anapaulapaludo-health",
    "dra-danielaserafini-health": "dra-danielaserafini-health",
    "dra-luanamariano-health": "dra-luanamariano-health",
    "labexato-health": "labexato-health",
    "newlifeclinicas-health": "newlifeclinicas-health",
    "odontomad-health": "odontomad-health",
    "citti-imoveis-health": "citti-imoveis-health",
    "drameiriellyfedrigo-health": "drameiriellyfedrigo-health",
}

SENTIMENT_LABELS = {
    "positivo": "Positivo",
    "negativo": "Negativo",
    "misto": "Misto",
    "neutro": "Neutro",
}

CATEGORY_LABELS = {
    "elogio": "Elogio",
    "reclamacao": "Reclamação",
    "sugestao": "Sugestão",
    "duvida": "Dúvida",
}

SENTIMENT_EMOJI = {
    "positivo": "😊",
    "negativo": "😔",
    "misto": "😐",
    "neutro": "💬",
}

CATEGORY_EMOJI = {
    "elogio": "⭐",
    "reclamacao": "⚠️",
    "sugestao": "💡",
    "duvida": "❓",
}


def build_section_html(data: dict) -> str:
    # Validate required fields
    required = ["slug", "instagram_handle", "profile_url", "posts_analyzed",
                "total_comments", "sentiment", "categories"]
    missing = [k for k in required if k not in data]
    if missing:
        raise ValueError(f"JSON incompleto — campos obrigatorios faltando: {', '.join(missing)}")

    slug = data["slug"]
    handle = escape(data["instagram_handle"])
    raw_profile_url = data["profile_url"]
    _ig_domains = ("https://www.instagram.com/", "https://instagram.com/")
    profile_url = raw_profile_url if any(raw_profile_url.startswith(d) for d in _ig_domains) else "#"
    posts = data["posts_analyzed"]
    total = data["total_comments"]
    sent = data["sentiment"]
    cats = data["categories"]
    samples = data.get("sample_comments", [])
    note = escape(data.get("note", ""))
    collected_at = escape(data.get("collected_at", "2026-06-01"))
    chart_id = re.sub(r"[^a-z0-9]", "", slug)

    # Validate sentiment/category sub-fields
    for key in ["positivo", "negativo", "misto", "neutro"]:
        if key not in sent:
            raise ValueError(f"Campo sentiment.{key} faltando no JSON de {slug}")
    for key in ["elogio", "duvida", "sugestao", "reclamacao"]:
        if key not in cats:
            raise ValueError(f"Campo categories.{key} faltando no JSON de {slug}")

    # Sentiment percentages
    sent_total = sum(sent.values()) or 1
    pos_pct = round(sent["positivo"] / sent_total * 100)
    neg_pct = round(sent["negativo"] / sent_total * 100)
    mix_pct = round(sent["misto"] / sent_total * 100)
    neu_pct = round(sent["neutro"] / sent_total * 100)

    # Category percentages
    cat_total = sum(cats.values()) or 1

    # Dominant sentiment headline
    dominant_count = sent["positivo"]
    dominant_pct = pos_pct
    if dominant_pct >= 60:
        sentiment_headline = f"<em style=\"font-family:'Playfair Display',serif;font-style:italic\">{dominant_pct}% de positivos.</em>"
        sentiment_sub_color = "var(--green)"
        sentiment_icon = "💚"
    elif dominant_pct >= 40:
        sentiment_headline = f"<em style=\"font-family:'Playfair Display',serif;font-style:italic\">{dominant_pct}% de positivos.</em>"
        sentiment_sub_color = "var(--yellow)"
        sentiment_icon = "💛"
    else:
        sentiment_headline = f"<em style=\"font-family:'Playfair Display',serif;font-style:italic\">Atenção aos negativos.</em>"
        sentiment_sub_color = "var(--red)"
        sentiment_icon = "⚡"

    if total < 10:
        context_note = f"Volume baixo — apenas {total} comentários nas últimas {posts} publicações. O público ainda não interage com o conteúdo de forma significativa."
    else:
        context_note = f"{total} comentários analisados nas últimas {posts} publicações. {sentiment_icon} {dominant_pct}% do público responde de forma positiva ao conteúdo."

    # Build sample comments HTML
    comments_html = ""
    for c in samples[:5]:
        s = c["sentiment"]
        cat = c["category"]
        if s not in SENTIMENT_LABELS:
            raise ValueError(f"Sentiment inválido no JSON de {slug}: '{s}'")
        if cat not in CATEGORY_LABELS:
            raise ValueError(f"Category inválida no JSON de {slug}: '{cat}'")
        raw_text = c["text"][:180] + ("…" if len(c["text"]) > 180 else "")
        text = escape(raw_text)
        raw_post_url = c.get("post_url", "#")
        _ig_domains = ("https://www.instagram.com/", "https://instagram.com/")
        post_url = raw_post_url if any(raw_post_url.startswith(d) for d in _ig_domains) else "#"
        comments_html += f"""
          <div class="sent-comment-card reveal d2">
            <div class="sent-comment-badges">
              <span class="sent-badge sent-{s}">{SENTIMENT_EMOJI[s]} {SENTIMENT_LABELS[s]}</span>
              <span class="sent-badge sent-cat">{CATEGORY_EMOJI[cat]} {CATEGORY_LABELS[cat]}</span>
            </div>
            <p class="sent-comment-text">"{text}"</p>
            <a class="sent-comment-link" href="{post_url}" target="_blank" rel="noopener">Ver publicação ↗</a>
          </div>"""

    note_html = ""
    if note:
        note_html = f'<div class="sent-note reveal"><span class="sent-note-ico">ℹ️</span>{note}</div>'

    low_volume_warning = ""
    if total < 10:
        low_volume_warning = f"""
        <div class="sent-alert reveal">
          <strong>⚠️ Volume insuficiente</strong> — com apenas {total} comentário{"s" if total != 1 else ""}, os gráficos abaixo são meramente ilustrativos. Este perfil precisa de estratégia de engajamento antes de qualquer análise de sentimento significativa.
        </div>"""

    return f"""
<!-- SENTIMENT SECTION — gerado por inject_sentiment.py em {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} -->
<section class="sentiment-sec">
  <div class="wrap">
    <div class="sent-intro">
      <div class="sec-label reveal">Voz do Público · Instagram</div>
      <h2 class="reveal">O que as pessoas<br>estão dizendo.<br>{sentiment_headline}</h2>
      <p class="sub reveal">{context_note}</p>
      {note_html}
    </div>
    {low_volume_warning}
    <div class="sent-overview reveal d2">
      <div class="sent-overview-stat">
        <span class="sent-big-num" style="color:var(--gold)">{total}</span>
        <span class="sent-big-label">comentários analisados</span>
      </div>
      <div class="sent-overview-stat">
        <span class="sent-big-num" style="color:var(--green)">{sent['positivo']}</span>
        <span class="sent-big-label">positivos</span>
      </div>
      <div class="sent-overview-stat">
        <span class="sent-big-num" style="color:var(--muted)">{posts}</span>
        <span class="sent-big-label">publicações analisadas</span>
      </div>
    </div>

    <div class="sent-charts reveal d3">
      <div class="sent-chart-card">
        <h3 class="sent-chart-title">Sentimento</h3>
        <div class="sent-donut-wrap">
          <canvas id="sentDonut_{chart_id}"></canvas>
          <div class="sent-donut-center">
            <span class="sent-donut-pct" style="color:var(--green)">{pos_pct}%</span>
            <span class="sent-donut-sub">positivo</span>
          </div>
        </div>
        <div class="sent-legend">
          <div class="sent-leg-item"><span class="sent-leg-dot" style="background:var(--green)"></span><span>Positivo</span><strong>{sent['positivo']}</strong></div>
          <div class="sent-leg-item"><span class="sent-leg-dot" style="background:var(--muted2)"></span><span>Neutro</span><strong>{sent['neutro']}</strong></div>
          <div class="sent-leg-item"><span class="sent-leg-dot" style="background:var(--yellow)"></span><span>Misto</span><strong>{sent['misto']}</strong></div>
          <div class="sent-leg-item"><span class="sent-leg-dot" style="background:var(--red)"></span><span>Negativo</span><strong>{sent['negativo']}</strong></div>
        </div>
      </div>

      <div class="sent-chart-card">
        <h3 class="sent-chart-title">Categoria</h3>
        <div class="sent-bar-wrap"><canvas id="catBar_{chart_id}"></canvas></div>
        <div class="sent-legend">
          <div class="sent-leg-item"><span class="sent-leg-dot" style="background:var(--gold)"></span><span>Elogio</span><strong>{cats['elogio']}</strong></div>
          <div class="sent-leg-item"><span class="sent-leg-dot" style="background:rgba(201,169,110,0.45)"></span><span>Dúvida</span><strong>{cats['duvida']}</strong></div>
          <div class="sent-leg-item"><span class="sent-leg-dot" style="background:rgba(255,255,255,0.3)"></span><span>Sugestão</span><strong>{cats['sugestao']}</strong></div>
          <div class="sent-leg-item"><span class="sent-leg-dot" style="background:var(--red)"></span><span>Reclamação</span><strong>{cats['reclamacao']}</strong></div>
        </div>
      </div>
    </div>

    {'<div class="sent-comments-wrap"><h3 class="sent-comments-title reveal d2">Comentários em destaque</h3><div class="sent-comments-grid">' + comments_html + '</div></div>' if comments_html else ''}

    <div class="sent-footer reveal d3">
      <a class="sent-profile-link" href="{profile_url}" target="_blank" rel="noopener">
        Ver perfil @{handle} ↗
      </a>
      <span class="sent-date">Análise: {collected_at}</span>
    </div>
  </div>
</section>

<script>
(function() {{
  function initSentimentCharts_{chart_id}() {{
    if (typeof Chart === 'undefined') {{ setTimeout(initSentimentCharts_{chart_id}, 100); return; }}
    // Donut — Sentimento
    var dCtx = document.getElementById('sentDonut_{chart_id}');
    if (dCtx && !dCtx._chart) {{
      dCtx._chart = new Chart(dCtx, {{
        type: 'doughnut',
        data: {{
          labels: ['Positivo', 'Neutro', 'Misto', 'Negativo'],
          datasets: [{{ data: [{sent['positivo']}, {sent['neutro']}, {sent['misto']}, {sent['negativo']}], backgroundColor: ['#34D399','rgba(240,235,227,0.2)','#FBBF24','#F87171'], borderWidth: 0, hoverOffset: 6 }}]
        }},
        options: {{ responsive: true, maintainAspectRatio: true, cutout: '68%', plugins: {{ legend: {{ display: false }}, tooltip: {{ callbacks: {{ label: function(c) {{ return ' ' + c.label + ': ' + c.raw; }} }} }} }}, animation: {{ animateRotate: true, duration: 1000 }} }}
      }});
    }}
    // Bar — Categoria
    var bCtx = document.getElementById('catBar_{chart_id}');
    if (bCtx && !bCtx._chart) {{
      bCtx._chart = new Chart(bCtx, {{
        type: 'bar',
        data: {{
          labels: ['Elogio', 'Dúvida', 'Sugestão', 'Reclamação'],
          datasets: [{{ data: [{cats['elogio']}, {cats['duvida']}, {cats['sugestao']}, {cats['reclamacao']}], backgroundColor: ['#C9A96E','rgba(201,169,110,0.45)','rgba(255,255,255,0.3)','#F87171'], borderRadius: 4, borderWidth: 0 }}]
        }},
        options: {{
          responsive: true, maintainAspectRatio: false,
          indexAxis: 'y',
          plugins: {{ legend: {{ display: false }}, tooltip: {{ callbacks: {{ label: function(c) {{ return ' ' + c.raw + ' comentários'; }} }} }} }},
          scales: {{
            x: {{ grid: {{ color: 'rgba(255,255,255,0.05)' }}, ticks: {{ color: 'rgba(240,235,227,0.45)', font: {{ size: 11 }} }} }},
            y: {{ grid: {{ display: false }}, ticks: {{ color: 'rgba(240,235,227,0.6)', font: {{ size: 12 }} }} }}
          }},
          animation: {{ duration: 900 }}
        }}
      }});
    }}
  }}
  initSentimentCharts_{chart_id}();
}})();
</script>
<!-- END SENTIMENT SECTION -->
"""


SENTIMENT_CSS_START = "/* SENTIMENT CSS START */"
SENTIMENT_CSS_END = "/* SENTIMENT CSS END */"

SENTIMENT_CSS = """/* SENTIMENT CSS START */
    /* ── Sentiment Section ── */
    .sentiment-sec{padding:6rem 2rem;background:var(--bg);}
    .sentiment-sec .sub{font-size:.88rem;color:var(--muted);max-width:560px;line-height:1.75;margin-top:.6rem;}
    .sent-intro{margin-bottom:3rem;}
    .sent-alert{padding:1rem 1.25rem;background:rgba(248,113,113,.07);border-left:3px solid var(--red);font-size:.82rem;color:var(--muted);line-height:1.6;margin-bottom:2rem;}
    .sent-alert strong{color:var(--text);}
    .sent-note{display:flex;align-items:flex-start;gap:.6rem;padding:.85rem 1.1rem;background:var(--surface2);border:1px solid var(--border);font-size:.78rem;color:var(--muted);line-height:1.6;margin-top:1rem;margin-bottom:2rem;}
    .sent-note-ico{flex-shrink:0;}
    .sent-overview{display:flex;gap:0;margin-bottom:3.5rem;}
    .sent-overview-stat{flex:1;padding:1.75rem 1.5rem;background:var(--surface);border:1px solid var(--border);text-align:center;}
    .sent-overview-stat+.sent-overview-stat{border-left:0;}
    .sent-big-num{display:block;font-family:'Playfair Display',serif;font-size:2.8rem;font-weight:700;line-height:1;}
    .sent-big-label{display:block;font-size:.65rem;text-transform:uppercase;letter-spacing:.16em;color:var(--muted);margin-top:.4rem;}
    .sent-charts{display:grid;grid-template-columns:1fr 1.5fr;gap:2rem;margin-bottom:3.5rem;align-items:start;}
    @media(max-width:700px){.sent-charts{grid-template-columns:1fr;} .sent-overview{flex-direction:column;}}
    .sent-chart-card{background:var(--surface);border:1px solid var(--border);padding:1.75rem;min-width:0;}
    .sent-chart-card canvas{display:block;max-width:100%;}
    .sent-chart-title{font-size:.75rem;font-weight:600;letter-spacing:.14em;text-transform:uppercase;color:var(--gold);margin-bottom:1.25rem;}
    .sent-donut-wrap{position:relative;width:160px;height:160px;margin:0 auto 1.25rem;}
    @media(max-width:480px){.sent-donut-wrap{width:130px;height:130px;}}
    .sent-donut-center{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;pointer-events:none;}
    .sent-donut-pct{font-family:'Playfair Display',serif;font-size:1.75rem;font-weight:700;line-height:1;}
    @media(max-width:480px){.sent-donut-pct{font-size:1.4rem;}}
    .sent-donut-sub{font-size:.6rem;color:var(--muted);text-transform:uppercase;letter-spacing:.12em;}
    .sent-bar-wrap{position:relative;width:100%;height:190px;}
    @media(max-width:480px){.sent-bar-wrap{height:160px;}}
    .sent-legend{display:flex;flex-direction:column;gap:.45rem;margin-top:1rem;}
    .sent-leg-item{display:flex;align-items:center;gap:.6rem;font-size:.78rem;color:var(--muted);}
    .sent-leg-item span:nth-child(2){flex:1;}
    .sent-leg-item strong{color:var(--text);font-size:.82rem;}
    .sent-leg-dot{width:8px;height:8px;border-radius:50%;flex-shrink:0;}
    .sent-comments-wrap{margin-bottom:2.5rem;}
    .sent-comments-title{font-family:'Playfair Display',serif;font-size:1.3rem;font-weight:400;margin-bottom:1.5rem;color:var(--text);}
    .sent-comments-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:1.25rem;}
    @media(max-width:480px){.sent-comments-grid{grid-template-columns:1fr;}}
    .sent-comment-card{background:var(--surface);border:1px solid var(--border);padding:1.25rem;}
    .sent-comment-badges{display:flex;gap:.5rem;flex-wrap:wrap;margin-bottom:.75rem;}
    .sent-badge{font-size:.67rem;font-weight:600;letter-spacing:.08em;padding:.25rem .65rem;border-radius:2px;}
    .sent-positivo{background:rgba(52,211,153,.1);color:var(--green);border:1px solid rgba(52,211,153,.2);}
    .sent-negativo{background:rgba(248,113,113,.1);color:var(--red);border:1px solid rgba(248,113,113,.2);}
    .sent-misto{background:rgba(251,191,36,.1);color:var(--yellow);border:1px solid rgba(251,191,36,.2);}
    .sent-neutro{background:rgba(240,235,227,.07);color:var(--muted);border:1px solid var(--border);}
    .sent-cat{background:rgba(201,169,110,.08);color:var(--gold);border:1px solid rgba(201,169,110,.2);}
    .sent-comment-text{font-size:.82rem;color:var(--muted);line-height:1.65;margin-bottom:.75rem;font-style:italic;}
    .sent-comment-link{font-size:.72rem;color:var(--gold);text-decoration:none;letter-spacing:.06em;}
    .sent-comment-link:hover{text-decoration:underline;}
    .sent-footer{display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:1rem;padding-top:2rem;border-top:1px solid var(--border);}
    .sent-profile-link{display:inline-flex;align-items:center;gap:.5rem;background:rgba(201,169,110,.08);border:1px solid rgba(201,169,110,.25);padding:.6rem 1.25rem;font-size:.75rem;font-weight:600;color:var(--gold);text-decoration:none;letter-spacing:.1em;transition:background .2s;}
    .sent-profile-link:hover{background:rgba(201,169,110,.15);}
    .sent-date{font-size:.68rem;color:var(--muted2);letter-spacing:.1em;}
/* SENTIMENT CSS END */"""

CHARTJS_TAG = '<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>'


def inject_into_html(html_path: Path, data: dict) -> bool:
    content = html_path.read_text(encoding="utf-8")

    # Skip if already injected
    if "SENTIMENT SECTION" in content:
        print(f"  ⚡ Já injetado, re-injetando (atualizando)…")
        # Remove existing section
        content = re.sub(
            r"\n<!-- SENTIMENT SECTION.*?<!-- END SENTIMENT SECTION -->\n",
            "\n",
            content,
            flags=re.DOTALL,
        )
        # Remove existing CSS (marker-based, reliable across versions)
        content = re.sub(
            r"/\* SENTIMENT CSS START \*/.*?/\* SENTIMENT CSS END \*/",
            "",
            content,
            flags=re.DOTALL,
        )

    # Add/re-add CSS before </style>
    if SENTIMENT_CSS_START not in content:
        content = content.replace("</style>", SENTIMENT_CSS + "\n  </style>", 1)

    # Add Chart.js before </head> if not present
    if "chart.js" not in content.lower():
        content = content.replace("</head>", f"  {CHARTJS_TAG}\n</head>", 1)

    # Build and inject section
    section_html = build_section_html(data)
    # Inject before <section class="google-sec">
    injected = re.sub(
        r'(\n<section class="google-sec">)',
        "\n" + section_html + r'\1',
        content,
        count=1,
    )

    if injected == content:
        print(f"  ⚠️  Anchor '<section class=\"google-sec\">' não encontrado em {html_path.name}")
        return False

    html_path.write_text(injected, encoding="utf-8")
    return True


def process_slug(slug: str):
    if not re.match(r"^[a-z0-9-]+$", slug):
        print(f"⚠️  Slug inválido (caracteres não permitidos): {slug!r}")
        return
    json_path = SENTIMENT_DIR / f"{slug}.json"
    if not json_path.exists():
        print(f"⚠️  JSON não encontrado: {json_path}")
        return

    data = json.loads(json_path.read_text())
    dir_name = SLUG_MAP.get(slug, slug)
    html_path = PROSPECTS_DIR / dir_name / "index.html"

    if not html_path.exists():
        print(f"⚠️  HTML não encontrado: {html_path}")
        return

    print(f"→ Processando {slug}…")
    ok = inject_into_html(html_path, data)
    if ok:
        print(f"  ✅ Injetado com sucesso ({data['total_comments']} comentários, {data['posts_analyzed']} posts)")
    else:
        print(f"  ❌ Falha na injeção")


def main():
    targets = sys.argv[1:] if len(sys.argv) > 1 else list(SLUG_MAP.keys())
    print(f"\n🔬 Injetando seção de sentimentos em {len(targets)} relatório(s)…\n")
    for slug in targets:
        process_slug(slug)
    print("\n✨ Concluído!")


if __name__ == "__main__":
    main()
