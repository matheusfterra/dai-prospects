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
  "dra-luanamariano": "dra-luana-mariano",
  "dra-anapaulapaludo": "dra-ana-paula-paludo",
  "drameiriellyfedrigo": "dra-meirielly-fedrigo",
  "drameiriellyfedrigo-health": "drameiriellyfedrigo-health",
  "dra-anapaulapaludo-health": "dra-anapaulapaludo-health",
  "citti-imoveis-health": "citti-imoveis-health",
  "dra-danielaserafini-health": "dra-danielaserafini-health",
  "dra-luanamariano-health": "dra-luanamariano-health",
  "dra-thania-health": "dra-thania-health",
  "labexato-health": "labexato-health",
  "newlifeclinicas-health": "newlifeclinicas-health",
  "odontomad-health": "odontomad-health",
  "ituaco-ferro": "ituaco-ferro",
  "dra-arianesantana": "dra-arianesantana",
  "magab-wear": "magab-wear",
  "magabwear": "magab-wear",
  "magabwear-health": "magabwear-health",
  "yooufit-academia-health": "yooufit-academia-health",
  "noma-medicina-health": "noma-medicina-health",
  "odontoclinic-health": "odontoclinic-health",
  "kion-dental-technology-health": "kion-dental-technology-health",
  "mari-saraiva-acessorios-health": "mari-saraiva-acessorios-health",
  "mari-saraiva-acessorios": "mari-saraiva-acessorios",
  "dra-mariajuliaoliv": "dra-mariajuliaoliv",
  "dra-izabela": "dra-izabela",
  "dra-izabela-rezende-ginecologia-endocrina-health": "dra-izabela-rezende-ginecologia-endocrina-health",
  "dra-izabela-rezende-ginecologia-endocrina": "dra-izabela-rezende-ginecologia-endocrina",
  "dra-izabela-health": "dra-izabela-rezende-ginecologia-endocrina-health",
"otica-itumbiara-maria-optica-health": "otica-itumbiara-maria-optica-health",
  "otica-itumbiara-maria-optica": "otica-itumbiara-maria-optica",
  "sorrifacil-clinicas-odontologicas-health": "sorrifacil-clinicas-odontologicas-health",
  "sorrifacil-clinicas-odontologicas": "sorrifacil-clinicas-odontologicas",
  "yooufit-academia": "yooufit-academia",
  "draizabela": "dra-izabela-rezende-ginecologia-endocrina",
  "kion-dental-technology": "kion-dental-technology",
  "clinicas-sorrifacil": "clinicas-sorrifacil",
  "jennefer-anunciato-health": "jennefer-anunciato-health",
  "jennefer-anunciato": "jennefer-anunciato",
  "oral-center": "oral-center",
  "regivel-ford": "regivel-ford",
  "dra-viviane": "dra-viviane",
  "cartorio-dualibi-health": "cartorio-dualibi-health",
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