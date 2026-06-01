#!/usr/bin/env python3
"""
collect_sentiment.py
Pipeline completo de coleta e classificação de sentimentos via Instagram Browser MCP.

Etapas:
  1. Conecta no MCP instagram-browser (SSE/HTTP)
  2. Coleta últimas 20 publicações de cada perfil via list_profile_posts
  3. Coleta comentários de cada publicação via get_post_comments
  4. Classifica via OpenAI GPT-4.1-mini em lotes
  5. Salva em sentiment_data/{slug}.json
  6. (Opcional) Chama inject_sentiment.py para atualizar os HTMLs

Uso:
  python3 collect_sentiment.py                    # todos os prospects
  python3 collect_sentiment.py dra-thania-health  # prospect específico
  python3 collect_sentiment.py --dry-run          # exibe dados sem classificar
  python3 collect_sentiment.py --inject           # injeta HTMLs após coletar

Dependências:
  pip install requests openai sseclient-py
"""

import json
import os
import sys
import time
import uuid
import subprocess
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

import requests

# ── Configuração ─────────────────────────────────────────────────
BASE = Path(__file__).parent
SENTIMENT_DIR = BASE / "sentiment_data"
SENTIMENT_DIR.mkdir(exist_ok=True)

MCP_SSE_URL = "https://agent-ig-browser-mcp.digital-ai.tech/sse"
MCP_BEARER = "ig-mcp-2026-secret"
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
if not OPENAI_API_KEY:
    # Tenta carregar do Cortex secrets (ambiente interno Digital AI)
    _secrets_file = Path("/cortex/secrets/org/media-apis.env")
    if _secrets_file.exists():
        for _line in _secrets_file.read_text().splitlines():
            if _line.startswith("OPENAI_API_KEY="):
                OPENAI_API_KEY = _line.split("=", 1)[1].strip()
                break
OPENAI_MODEL = "gpt-4.1-mini"

# Prospects configurados
PROSPECTS = {
    "dra-thania-health": {
        "instagram_handle": "dra.thaniarego",
        "profile_url": "https://www.instagram.com/dra.thaniarego/",
    },
    "dra-anapaulapaludo-health": {
        "instagram_handle": "dra.anapaulapaludo",
        "profile_url": "https://www.instagram.com/dra.anapaulapaludo/",
    },
    "dra-danielaserafini-health": {
        "instagram_handle": "dra_danielacostaserafini",
        "profile_url": "https://www.instagram.com/dra_danielacostaserafini/",
    },
    "dra-luanamariano-health": {
        "instagram_handle": "draluanamariano",
        "profile_url": "https://www.instagram.com/draluanamariano/",
    },
    "labexato-health": {
        "instagram_handle": "laboratorioexatoitumbiara",
        "profile_url": "https://www.instagram.com/laboratorioexatoitumbiara/",
    },
    "newlifeclinicas-health": {
        "instagram_handle": "newlife_clinicasiub",
        "profile_url": "https://www.instagram.com/newlife_clinicasiub/",
    },
    "odontomad-health": {
        "instagram_handle": "clinicaodontomad",
        "profile_url": "https://www.instagram.com/clinicaodontomad/",
    },
    "citti-imoveis-health": {
        "instagram_handle": "cittiimoveis",
        "profile_url": "https://www.instagram.com/cittiimoveis/",
    },
    "drameiriellyfedrigo-health": {
        "instagram_handle": "drameiriellyfedrigo",
        "profile_url": "https://www.instagram.com/drameiriellyfedrigo/",
    },
}


# ── MCP HTTP Client ───────────────────────────────────────────────
class MCPClient:
    """
    Cliente MCP sobre HTTP/SSE.
    Protocolo: GET /sse (SSE stream) + POST /message?sessionId=... (JSON-RPC)
    """

    def __init__(self, sse_url: str, bearer: str):
        self.sse_url = sse_url
        self.bearer = bearer
        self.session_id: Optional[str] = None
        self.message_url: Optional[str] = None
        self._session = requests.Session()
        self._session.headers["Authorization"] = f"Bearer {bearer}"

    def connect(self, timeout: int = 15) -> bool:
        """Abre a conexão SSE e extrai o endpoint de mensagens."""
        try:
            resp = self._session.get(
                self.sse_url, stream=True, timeout=timeout, headers={"Accept": "text/event-stream"}
            )
            resp.raise_for_status()
            for line in resp.iter_lines(decode_unicode=True):
                if line.startswith("data:"):
                    payload = line[5:].strip()
                    try:
                        data = json.loads(payload)
                        if "endpoint" in data or "sessionId" in data:
                            self.session_id = data.get("sessionId") or str(uuid.uuid4())
                            self.message_url = data.get("endpoint") or self.sse_url.replace("/sse", "/message")
                            resp.close()
                            return True
                    except json.JSONDecodeError:
                        # Pode ser apenas o URL do endpoint como string
                        if payload.startswith("http") or payload.startswith("/"):
                            self.message_url = payload
                            self.session_id = str(uuid.uuid4())
                            resp.close()
                            return True
                if self.session_id:
                    break
        except Exception as e:
            print(f"  ⚠️  Erro ao conectar no MCP: {e}")
        return False

    def call_tool(self, tool_name: str, params: dict, timeout: int = 30) -> Optional[dict]:
        """Executa uma tool via JSON-RPC e retorna o resultado."""
        if not self.message_url:
            return None

        payload = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": params},
        }
        url = self.message_url
        if self.session_id and "sessionId" not in url:
            url = f"{url}?sessionId={self.session_id}"

        try:
            resp = self._session.post(url, json=payload, timeout=timeout)
            resp.raise_for_status()
            data = resp.json()
            if "result" in data:
                # MCP retorna result.content[0].text (texto JSON ou string)
                content = data["result"].get("content", [])
                if content and isinstance(content, list):
                    text = content[0].get("text", "")
                    try:
                        return json.loads(text)
                    except json.JSONDecodeError:
                        return {"raw": text}
                return data["result"]
            if "error" in data:
                print(f"  ⚠️  MCP error: {data['error']}")
        except Exception as e:
            print(f"  ⚠️  Erro na chamada {tool_name}: {e}")
        return None


# ── Coleta de posts e comentários ────────────────────────────────
def collect_posts(mcp: MCPClient, handle: str, limit: int = 20) -> list[dict]:
    """Coleta lista de posts do perfil."""
    result = mcp.call_tool("list_profile_posts", {"username": handle, "limit": limit})
    if not result:
        return []
    posts = result.get("posts") or result.get("items") or (result if isinstance(result, list) else [])
    return posts


def collect_comments(mcp: MCPClient, post_url: str, limit: int = 30) -> list[dict]:
    """Coleta comentários de um post."""
    result = mcp.call_tool("get_post_comments", {"post_url": post_url, "limit": limit})
    if not result:
        return []
    comments = result.get("comments") or result.get("items") or (result if isinstance(result, list) else [])
    return comments


# ── Classificação via OpenAI ─────────────────────────────────────
CLASSIFY_SYSTEM = """
Você é um classificador de comentários de Instagram para perfis profissionais brasileiros.
Para cada comentário receba e retorne um JSON com a classificação.

Sentimento:
- positivo: elogio, satisfação, entusiasmo, gratidão
- negativo: reclamação clara, frustração, crítica sem ressalva
- misto: tem pontos positivos E negativos
- neutro: pergunta simples, agendamento, emojis apenas, spam

Categoria:
- elogio: elogio ao profissional, resultado ou conteúdo
- reclamacao: reclamação sobre serviço, atendimento, preço ou resultado
- sugestao: pedido de novo conteúdo, nova especialidade, melhoria
- duvida: pergunta sobre preço, agendamento, tratamento, disponibilidade

Retorne JSON array com: [{"text": "...", "sentiment": "...", "category": "..."}]
Ignore comentários que são spam, emojis sozinhos ou resposta a outros comentários com @menção.
"""


def classify_comments(comments: list[str]) -> list[dict]:
    """Classifica uma lista de comentários via OpenAI."""
    if not comments:
        return []

    from openai import OpenAI
    client = OpenAI(api_key=OPENAI_API_KEY)

    # Processa em lotes de 30
    results = []
    batch_size = 30
    for i in range(0, len(comments), batch_size):
        batch = comments[i : i + batch_size]
        prompt = json.dumps(batch, ensure_ascii=False)
        try:
            resp = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": CLASSIFY_SYSTEM},
                    {"role": "user", "content": f"Classifique estes comentários:\n{prompt}"},
                ],
                response_format={"type": "json_object"},
                temperature=0,
                max_tokens=2000,
            )
            raw = resp.choices[0].message.content
            parsed = json.loads(raw)
            # Pode retornar {"results": [...]} ou direto [...]
            items = parsed if isinstance(parsed, list) else parsed.get("results") or parsed.get("comments") or []
            results.extend(items)
            time.sleep(0.5)
        except Exception as e:
            print(f"  ⚠️  Erro na classificação (lote {i}): {e}")
            # Fallback: marca como neutro
            for text in batch:
                results.append({"text": text, "sentiment": "neutro", "category": "duvida"})

    return results


# ── Agrega resultados ────────────────────────────────────────────
def aggregate(classified: list[dict]) -> dict:
    sent = {"positivo": 0, "negativo": 0, "misto": 0, "neutro": 0}
    cats = {"elogio": 0, "reclamacao": 0, "sugestao": 0, "duvida": 0}
    for item in classified:
        s = item.get("sentiment", "neutro")
        c = item.get("category", "duvida")
        if s in sent:
            sent[s] += 1
        if c in cats:
            cats[c] += 1
    return {"sentiment": sent, "categories": cats}


def pick_samples(classified: list[dict], post_map: dict[str, str], n: int = 3) -> list[dict]:
    """
    Seleciona n comentários representativos.
    post_map: {comment_text → post_url}
    """
    # Prioriza: 1 positivo/elogio, 1 neutro/duvida, 1 misto ou negativo
    priority = [
        lambda x: x.get("sentiment") == "positivo" and x.get("category") == "elogio",
        lambda x: x.get("sentiment") in ("neutro", "misto") and x.get("category") in ("duvida", "sugestao"),
        lambda x: x.get("sentiment") in ("negativo", "misto"),
    ]
    selected = []
    used = set()
    for pred in priority:
        if len(selected) >= n:
            break
        for item in classified:
            if len(selected) >= n:
                break
            text = item.get("text", "")
            if text in used:
                continue
            if pred(item) and len(text) > 20:
                selected.append({
                    "text": text,
                    "sentiment": item.get("sentiment"),
                    "category": item.get("category"),
                    "post_url": post_map.get(text, ""),
                })
                used.add(text)
    return selected


# ── Pipeline principal ───────────────────────────────────────────
def process_prospect(slug: str, mcp: MCPClient, dry_run: bool = False) -> Optional[dict]:
    info = PROSPECTS.get(slug)
    if not info:
        print(f"⚠️  Prospect desconhecido: {slug}")
        return None

    handle = info["instagram_handle"]
    print(f"\n→ {slug} (@{handle})")

    # Coleta posts
    print(f"  📋 Coletando posts de @{handle}…")
    posts = collect_posts(mcp, handle, limit=20)
    if not posts:
        print(f"  ⚠️  Nenhum post retornado. MCP pode estar offline.")
        return None
    print(f"  ✓ {len(posts)} posts encontrados")

    # Coleta comentários
    all_comments = []  # list of (text, post_url)
    for post in posts:
        # O MCP retorna estruturas variadas; tenta diferentes keys
        shortcode = (
            post.get("shortcode")
            or post.get("code")
            or post.get("id")
            or ""
        )
        post_url = (
            post.get("url")
            or post.get("permalink")
            or (f"https://www.instagram.com/p/{shortcode}/" if shortcode else "")
        )
        comment_count = post.get("comment_count") or post.get("comments_count") or 0

        if not post_url or comment_count == 0:
            continue

        print(f"  💬 Coletando comentários de {post_url} ({comment_count} esperados)…")
        comments = collect_comments(mcp, post_url, limit=30)
        for c in comments:
            text = c.get("text") or c.get("comment") or c.get("content") or ""
            text = text.strip()
            if text and len(text) > 5:
                all_comments.append((text, post_url))
        time.sleep(0.3)

    total = len(all_comments)
    print(f"  ✓ {total} comentários coletados no total")

    if dry_run:
        print(f"  🔍 Dry-run: {total} comentários, primeiros 5:")
        for text, url in all_comments[:5]:
            print(f"    - {text[:80]} [{url}]")
        return None

    if total == 0:
        print(f"  ⚠️  Sem comentários para classificar")
        return None

    # Classifica
    print(f"  🤖 Classificando {total} comentários via OpenAI {OPENAI_MODEL}…")
    texts = [t for t, _ in all_comments]
    post_map = {t: u for t, u in all_comments}
    classified = classify_comments(texts)
    print(f"  ✓ {len(classified)} comentários classificados")

    # Agrega
    agg = aggregate(classified)
    samples = pick_samples(classified, post_map, n=3)

    data = {
        "slug": slug,
        "instagram_handle": handle,
        "profile_url": info["profile_url"],
        "posts_analyzed": len(posts),
        "total_comments": total,
        "collected_at": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "sentiment": agg["sentiment"],
        "categories": agg["categories"],
        "sample_comments": samples,
        "google_reviews": None,
    }

    # Salva JSON
    out_path = SENTIMENT_DIR / f"{slug}.json"
    out_path.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    print(f"  💾 Salvo em {out_path}")
    return data


def main():
    args = sys.argv[1:]
    dry_run = "--dry-run" in args
    do_inject = "--inject" in args
    args = [a for a in args if not a.startswith("--")]

    slugs = args if args else list(PROSPECTS.keys())
    print(f"\n🔬 Iniciando coleta de sentimentos para {len(slugs)} prospect(s)…")
    print(f"   MCP: {MCP_SSE_URL}")
    print(f"   OpenAI: {OPENAI_MODEL}")
    if dry_run:
        print("   ⚠️  Dry-run ativo — não classifica")

    # Conecta no MCP
    mcp = MCPClient(MCP_SSE_URL, MCP_BEARER)
    print(f"\n🔌 Conectando no Instagram MCP…")
    connected = mcp.connect(timeout=10)
    if not connected:
        print("  ❌ Falha na conexão com o MCP.")
        print("  ℹ️  Verifique se o serviço está rodando: https://agent-ig-browser-mcp.digital-ai.tech/")
        print("  ℹ️  Para usar dados seed existentes, rode apenas: python3 inject_sentiment.py")
        sys.exit(1)
    print("  ✅ Conectado!")

    for slug in slugs:
        try:
            process_prospect(slug, mcp, dry_run=dry_run)
        except KeyboardInterrupt:
            print("\n⚡ Interrompido pelo usuário")
            break
        except Exception as e:
            print(f"  ❌ Erro em {slug}: {e}")

    if do_inject:
        print("\n🎨 Executando inject_sentiment.py…")
        subprocess.run([sys.executable, str(BASE / "inject_sentiment.py")] + slugs)

    print("\n✨ Coleta concluída!")


if __name__ == "__main__":
    main()
