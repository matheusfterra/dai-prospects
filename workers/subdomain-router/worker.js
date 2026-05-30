// Cloudflare Worker — Subdomain Router para prospects Digital AI
// Mapeia <slug>.digital-ai.tech → prospects.digital-ai.tech/<prospect-slug>/
// Deploy: PUT /accounts/:id/workers/scripts/dai-prospects-router
// IMPORTANTE: NÃO usar rota wildcard *.digital-ai.tech — usar rotas explícitas por prospect

// Routing map: chave = subdomínio, valor = pasta em dai-prospects
const ROUTING = {
  "labexato": "laboratorio-exato-itumbiara",
  "lab-exato": "laboratorio-exato-itumbiara",
  "citti": "citti-imoveis",
  "newlife": "newlife-clinicas",
  "peb": "peb-groups",
  "dr-thania": "dra-thania-rego",
  "odonto-mad": "clinica-odonto-mad",
  "dra-danielaserafini": "dra-daniela-serafini",
  // LeadKit adiciona entradas aqui automaticamente via Fase 4 do pipeline
};

const ORIGIN = "https://prospects.digital-ai.tech";

addEventListener("fetch", (event) => {
  event.respondWith(handleRequest(event.request));
});

async function handleRequest(request) {
  const url = new URL(request.url);
  const hostname = url.hostname;

  // Extrair subdomínio
  const parts = hostname.split(".");
  if (parts.length < 3) {
    // Não é subdomínio — pass-through ao origin
    return fetch(request);
  }

  const subdomain = parts[0];
  const prospectSlug = ROUTING[subdomain];

  if (!prospectSlug) {
    // Subdomínio não é prospect — pass-through ao origin (Pages, Traefik, etc.)
    // NUNCA retornar 404 aqui — outros serviços usam subdomínios de digital-ai.tech
    return fetch(request);
  }

  // Mapear caminho: / → /prospects/<slug>/  |  /asset.js → /prospects/<slug>/asset.js
  const pathSuffix = url.pathname === "/" ? "/" : url.pathname;
  const newUrl = `${ORIGIN}/prospects/${prospectSlug}${pathSuffix}${url.search}`;

  const proxyRequest = new Request(newUrl, {
    method: request.method,
    headers: request.headers,
    body: ["GET", "HEAD"].includes(request.method) ? undefined : request.body,
  });

  const response = await fetch(proxyRequest);

  const newHeaders = new Headers(response.headers);
  newHeaders.set("Access-Control-Allow-Origin", "*");
  newHeaders.delete("x-frame-options");

  return new Response(response.body, {
    status: response.status,
    headers: newHeaders,
  });
}