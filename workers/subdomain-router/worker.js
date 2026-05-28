// Cloudflare Worker — Subdomain Router para prospects Digital AI
// Mapeia <slug>.digital-ai.tech → prospects.digital-ai.tech/<prospect-slug>/

// Routing map: chave = subdomínio, valor = pasta em dai-prospects
const ROUTING = {
  "labexato": "laboratorio-exato-itumbiara",
  // LeadKit adiciona entradas aqui automaticamente
};

const ORIGIN = "https://prospects.digital-ai.tech";

export default {
  async fetch(request) {
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

    // Redirecionar caminho: / → /<slug>/
    const newPath = `/${prospectSlug}${url.pathname === "/" ? "/" : url.pathname}`;
    const newUrl = `${ORIGIN}${newPath}${url.search}`;

    // Proxy da request
    const proxyRequest = new Request(newUrl, {
      method: request.method,
      headers: request.headers,
      body: request.body,
    });

    const response = await fetch(proxyRequest);

    // Retornar response com headers CORS
    return new Response(response.body, {
      status: response.status,
      headers: {
        ...Object.fromEntries(response.headers),
        "Access-Control-Allow-Origin": "*",
      },
    });
  },
};
