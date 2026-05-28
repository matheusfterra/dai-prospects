// Cloudflare Worker — Subdomain Router para prospects Digital AI
// Mapeia <slug>.digital-ai.tech → prospects.digital-ai.tech/<prospect-slug>/
// Deploy: PUT /accounts/:id/workers/scripts/dai-prospects-router

// Routing map: chave = subdomínio, valor = pasta em dai-prospects
const ROUTING = {
  "labexato": "laboratorio-exato-itumbiara",
  // LeadKit adiciona entradas aqui automaticamente via Fase 4 do pipeline
};

const ORIGIN = "https://prospects.digital-ai.tech";

addEventListener("fetch", (event) => {
  event.respondWith(handleRequest(event.request));
});

async function handleRequest(request) {
  const url = new URL(request.url);
  const hostname = url.hostname; // ex: labexato.digital-ai.tech

  // Extrair subdomínio
  const parts = hostname.split(".");
  if (parts.length < 3) {
    return new Response("Not Found", { status: 404 });
  }

  const subdomain = parts[0];
  const prospectSlug = ROUTING[subdomain];

  if (!prospectSlug) {
    return new Response(`Prospect '${subdomain}' não encontrado`, { status: 404 });
  }

  // Mapear caminho: / → /<slug>/  |  /asset.js → /<slug>/asset.js
  const pathSuffix = url.pathname === "/" ? "/" : url.pathname;
  const newUrl = `${ORIGIN}/${prospectSlug}${pathSuffix}${url.search}`;

  // Proxy da request preservando método e headers
  const proxyRequest = new Request(newUrl, {
    method: request.method,
    headers: request.headers,
    body: ["GET", "HEAD"].includes(request.method) ? undefined : request.body,
  });

  const response = await fetch(proxyRequest);

  // Retornar response com headers ajustados
  const newHeaders = new Headers(response.headers);
  newHeaders.set("Access-Control-Allow-Origin", "*");
  newHeaders.delete("x-frame-options"); // permite embed

  return new Response(response.body, {
    status: response.status,
    headers: newHeaders,
  });
}
