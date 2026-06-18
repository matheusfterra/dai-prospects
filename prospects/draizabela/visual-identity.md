---
type: visual-identity
prospect: Dra. Izabela Rezende
slug: draizabela
instagram: "@draizabelarezende"
website: "https://bio.site/draizabelarezende"
segment: "Saúde — Ginecologia Endócrina, Estética Íntima, Lipedema, Reposição Hormonal, Emagrecimento"
extracted_at: "2026-06-18"
confidence: high
sources:
  - Instagram posts (img1–img5, img_sobre, hero)
  - bio.site/draizabelarezende (WebFetch)
  - LP existente (dra-izabela-rezende-ginecologia-endocrina/index.html)
conflict_note: "bio.site usa azul escuro #132442 como fundo — COERENTE com identidade real do Instagram. Posts do Instagram confirmam: azul marinho é a cor de marca, não template genérico."
---

# Identidade Visual — Dra. Izabela Rezende

## Análise Geral

**Estilo:** Premium feminino sofisticado. Paleta azul marinho + dourado + off-white champagne.
Posicionamento visual de marca médica premium — elegante, acolhedora, científica.

**Tom visual:** Clínica de alto padrão, médica jovem e moderna com autoridade científica.
Ambiente físico: consultório com madeira clara, iluminação aquecida âmbar, tons naturais.
Figurino: jaleco off-white/creme, blazer nude/camel, peças de roupa preta. Acessórios dourados.

**Conflito site vs mídias reais:** Nenhum conflito — o azul escuro #132442 do bio.site
é exatamente o mesmo usado nos posts do Instagram. Identidade coerente e confirmada.

---

## Paleta de Cores

| Token | Hex | Confiança | Fonte |
|-------|-----|-----------|-------|
| COLOR_PRIMARY | `#132442` | high | Instagram posts (fundo dominante em img2, img4, img5, img_sobre) |
| COLOR_PRIMARY_L | `#1A3260` | high | Variante ligeiramente mais clara do azul marinho |
| COLOR_PRIMARY_D | `#0C1A32` | medium | Variante escura derivada |
| COLOR_BG | `#F8F5F0` | high | Posts com fundo claro (img2), ambiente consultório |
| COLOR_SURFACE | `#F0EAE2` | high | Madeira clara do consultório, paredes do ambiente |
| COLOR_SURFACE_2 | `#E6DDD2` | medium | Terceiro tom derivado da superfície (mais escuro) |
| COLOR_BORDER | `rgba(19,36,66,0.18)` | high | LP existente (fundo #132442 com opacidade reduzida) |
| COLOR_DARK | `#132442` | high | Azul marinho — cor de texto escuro e fundos |
| COLOR_DARK_2 | `#1A3260` | high | Variante azul mais clara para hierarquia |
| COLOR_TEXT | `#132442` | high | Texto principal nos posts claros |
| COLOR_TEXT_MUTED | `#4A5A78` | medium | Texto secundário (derivado do azul) |
| COLOR_TEXT_SOFT | `#8A9BB8` | medium | Texto decorativo/suave (derivado do azul) |
| COLOR_GOLD | `#B58A5C` | high | Brincos e colar dourado nos posts, acento de marca |
| COLOR_GOLD_L | `#CDAA7A` | medium | Dourado claro (iluminação quente do consultório) |
| COLOR_GOLD_D | `#8A6638` | medium | Dourado escuro derivado |

### Notas de Cor

- **Azul marinho `#132442`** é a cor de marca principal — confirmada em 5+ posts do Instagram como fundo dominante
- **Dourado `#B58A5C`** aparece como acento premium (acessórios pessoais da médica, iluminação âmbar do consultório)
- **Off-white `#F8F5F0`** é o fundo limpo para layouts com foto — presente nos posts de fundo neutro (img2, img3)
- **Sequência de superfícies** (`F8F5F0 → F0EAE2 → E6DDD2`) simula o tom natural da madeira e linho do consultório

---

## Tipografia

### Fontes Identificadas

| Variável | Fonte | Fallback | Confiança | Fonte de dados |
|----------|-------|----------|-----------|----------------|
| FONT_HEADING | Cormorant Garamond | Georgia, serif | high | Visível nos posts do Instagram (img2, img_sobre, img5) — tipografia serif elegante com alternâncias itálico |
| FONT_BODY | DM Sans | system-ui, -apple-system, sans-serif | high | LP existente confirmada, coerente com estética clean dos posts |

### Google Fonts URLs

- **Heading:** `https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,500;0,600;0,700;1,300;1,400;1,600&display=swap`
- **Body:** `https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;1,9..40,400&display=swap`
- **Combinada:** `https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,500;0,600;0,700;1,300;1,400;1,600&family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;1,9..40,400&display=swap`

### Características Tipográficas

- **Heading:** Cormorant Garamond — serif editorial, peso 300–700, uso frequente de itálico nos posts. Evoca elegância médica premium.
- **Body:** DM Sans — sans-serif moderno e limpo, excelente legibilidade. Usado no bio.site como "Roboto", mas DM Sans é equivalente premium.
- **Tracking heading:** Espaçamento de letras wide em labels (ex: "DRA IZABELA REZENDE", "GINECOLOGISTA" em uppercase tracked)

---

## Logo

- **Forma:** Nome em tipografia — "Dra. Izabela Rezende | Ginecologia Endócrina"
- **URL pública:** Não identificado logo isolado
- **Tratamento:** Nome em Cormorant Garamond com subtítulo em DM Sans uppercase tracked

---

## CSS Tokens Completos

```css
:root {
  /* ── CORES PRIMÁRIAS ── */
  --color-primary:        #132442;   /* Azul marinho — cor de marca principal */
  --color-primary-light:  #1A3260;   /* Azul marinho variante clara */
  --color-primary-dark:   #0C1A32;   /* Azul marinho variante escura */

  /* ── ACENTO DOURADO ── */
  --color-accent:         #B58A5C;   /* Dourado — acento premium de marca */
  --color-accent-light:   #CDAA7A;   /* Dourado claro */
  --color-accent-dark:    #8A6638;   /* Dourado escuro */

  /* ── BACKGROUNDS E SUPERFÍCIES ── */
  --color-background:     #F8F5F0;   /* Off-white champagne — fundo principal */
  --color-surface:        #F0EAE2;   /* Bege linho — superfície cards */
  --color-surface-2:      #E6DDD2;   /* Bege escuro — terceiro tom */

  /* ── BORDAS ── */
  --color-border:         rgba(19,36,66,0.18); /* Azul marinho translúcido */

  /* ── TEXTOS ESCUROS ── */
  --color-dark:           #132442;   /* Azul marinho para texto escuro e fundos */
  --color-dark-2:         #1A3260;   /* Variante escura 2 */

  /* ── TEXTOS ── */
  --color-text:           #132442;   /* Texto principal */
  --color-text-muted:     #4A5A78;   /* Texto secundário */
  --color-text-soft:      #8A9BB8;   /* Texto suave/decorativo */

  /* ── UTILITÁRIOS ── */
  --color-white:          #FFFFFF;
  --color-gold:           #B58A5C;   /* Alias de acento */
  --color-gold-light:     #CDAA7A;
  --color-gold-dark:      #8A6638;

  /* ── TIPOGRAFIA ── */
  --font-heading:   'Cormorant Garamond', Georgia, serif;
  --font-body:      'DM Sans', system-ui, -apple-system, sans-serif;

  /* ── ESCALA TIPOGRÁFICA ── */
  --font-size-xs:   0.75rem;   /* 12px */
  --font-size-sm:   0.875rem;  /* 14px */
  --font-size-md:   1rem;      /* 16px */
  --font-size-lg:   1.125rem;  /* 18px */
  --font-size-xl:   1.375rem;  /* 22px */
  --font-size-2xl:  1.75rem;   /* 28px */
  --font-size-3xl:  2.25rem;   /* 36px */
  --font-size-4xl:  3rem;      /* 48px */

  /* ── ESPAÇAMENTOS ── */
  --spacing-xs:   0.375rem;   /* 6px */
  --spacing-sm:   0.75rem;    /* 12px */
  --spacing-md:   1.25rem;    /* 20px */
  --spacing-lg:   2rem;       /* 32px */
  --spacing-xl:   3rem;       /* 48px */
  --spacing-2xl:  4.5rem;     /* 72px */
  --spacing-3xl:  7rem;       /* 112px */

  /* ── BORDAS E RAIOS ── */
  --radius-sm:    6px;
  --radius-md:    12px;
  --radius-lg:    20px;
  --radius-full:  9999px;

  /* ── SOMBRAS ── */
  --shadow-sm:    0 1px 4px rgba(19,36,66,0.08);
  --shadow-md:    0 4px 16px rgba(19,36,66,0.12);
  --shadow-lg:    0 12px 40px rgba(19,36,66,0.18);
}
```

---

## Template Variables (para LP)

```
{{COLOR_PRIMARY}}:    #132442
{{COLOR_PRIMARY_L}}:  #1A3260
{{COLOR_PRIMARY_D}}:  #0C1A32
{{COLOR_BG}}:         #F8F5F0
{{COLOR_SURFACE}}:    #F0EAE2
{{COLOR_SURFACE_2}}:  #E6DDD2
{{COLOR_BORDER}}:     rgba(19,36,66,0.18)
{{COLOR_DARK}}:       #132442
{{COLOR_DARK_2}}:     #1A3260
{{COLOR_TEXT}}:       #132442
{{COLOR_TEXT_MUTED}}: #4A5A78
{{COLOR_TEXT_SOFT}}:  #8A9BB8
{{FONT_HEADING}}:     'Cormorant Garamond', Georgia, serif
{{FONT_BODY}}:        'DM Sans', system-ui, -apple-system, sans-serif
{{FONT_HEADING_URL}}: https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,500;0,600;0,700;1,300;1,400;1,600&family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;1,9..40,400&display=swap
```

---

## Diretrizes de Aplicação

### Combinações aprovadas
- **Fundo escuro:** `--color-primary` (#132442) + texto branco + acento dourado (#B58A5C) — estilo editorial dos posts
- **Fundo claro:** `--color-background` (#F8F5F0) + texto `--color-primary` + acento dourado — estilo clean premium
- **Cards:** `--color-surface` (#F0EAE2) com borda `--color-border` — superfície suave

### Tipografia
- **Títulos grandes:** Cormorant Garamond italic peso 400–600 — editorial e elegante
- **Labels uppercase:** DM Sans 400 com letter-spacing: 0.12em — tracking wide
- **Corpo:** DM Sans 400 tamanho 16px, linha 1.65

### Estilo visual geral
- Fotos sem filtro — alta qualidade, luz natural/âmbar
- Espaçamento generoso — não sobrecarregar o layout
- Elementos decorativos: linhas finas, não elementos pesados
- Ícones: linha fina (stroke), não preenchidos
