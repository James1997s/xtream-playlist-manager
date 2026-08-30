"use strict";

const http = require("node:http");
const crypto = require("node:crypto");
const { URL } = require("node:url");

const PORT = Number(process.env.PORT || 7000);
const M3U_URL = process.env.M3U_URL || "https://raw.githubusercontent.com/James1997s/xtream-playlist-manager/main/playlist.m3u";
const REFRESH_MS = 60 * 60 * 1000;
let cache = { loadedAt: 0, entries: [] };

const COUNTRY_RULES = [
  ["United States", "North America", /^(usa|us|u\.s\.?)(?:\s|[-|:])/i],
  ["Canada", "North America", /^(canada|can)(?:\s|[-|:])/i],
  ["Mexico", "Latin America", /^(mexico|mex)(?:\s|[-|:])/i],
  ["Brazil", "Latin America", /^(brazil|bra)(?:\s|[-|:])/i],
  ["Argentina", "Latin America", /^(argentina|arg)(?:\s|[-|:])/i],
  ["Colombia", "Latin America", /^(colombia|col)(?:\s|[-|:])/i],
  ["United Kingdom", "Europe", /^(uk|u\.k\.?|united kingdom|british|england)(?:\s|[-|:])/i],
  ["Ireland", "Europe", /^(ireland|irish)(?:\s|[-|:])/i],
  ["France", "Europe", /^(france|french|fra)(?:\s|[-|:])/i],
  ["Germany", "Europe", /^(germany|german|deu)(?:\s|[-|:])/i],
  ["Italy", "Europe", /^(italy|italian|ita)(?:\s|[-|:])/i],
  ["Spain", "Europe", /^(spain|spanish|esp)(?:\s|[-|:])/i],
  ["Portugal", "Europe", /^(portugal|prt)(?:\s|[-|:])/i],
  ["Netherlands", "Europe", /^(netherlands|dutch|nl)(?:\s|[-|:])/i],
  ["Belgium", "Europe", /^(belgium|belgian|bel)(?:\s|[-|:])/i],
  ["Switzerland", "Europe", /^(switzerland|swiss|che)(?:\s|[-|:])/i],
  ["Austria", "Europe", /^(austria|aut)(?:\s|[-|:])/i],
  ["Turkey", "Europe / Middle East", /^(turkey|turkish|türkiye)(?:\s|[-|:])/i],
  ["Russia", "Europe / Asia", /^(russia|russian|rus)(?:\s|[-|:])/i],
  ["India", "Asia", /^(india|indian|ind)(?:\s|[-|:])/i],
  ["Pakistan", "Asia", /^(pakistan|pak)(?:\s|[-|:])/i],
  ["Bangladesh", "Asia", /^(bangladesh|bgd)(?:\s|[-|:])/i],
  ["Japan", "Asia", /^(japan|japanese|jpn)(?:\s|[-|:])/i],
  ["South Korea", "Asia", /^(korea|south korea|kor)(?:\s|[-|:])/i],
  ["China", "Asia", /^(china|chinese|chn)(?:\s|[-|:])/i],
  ["Philippines", "Asia", /^(philippines|phl)(?:\s|[-|:])/i],
  ["Indonesia", "Asia", /^(indonesia|idn)(?:\s|[-|:])/i],
  ["Malaysia", "Asia", /^(malaysia|mys)(?:\s|[-|:])/i],
  ["Singapore", "Asia", /^(singapore|sgp)(?:\s|[-|:])/i],
  ["Thailand", "Asia", /^(thailand|tha)(?:\s|[-|:])/i],
  ["United Arab Emirates", "Middle East", /^(uae|u\.a\.e\.?|dubai|emirates)(?:\s|[-|:])/i],
  ["Saudi Arabia", "Middle East", /^(saudi|saudi arabia|ksa)(?:\s|[-|:])/i],
  ["Israel", "Middle East", /^(israel|israeli|isr)(?:\s|[-|:])/i],
  ["Egypt", "Middle East / Africa", /^(egypt|egyptian|egy)(?:\s|[-|:])/i],
  ["South Africa", "Africa", /^(south africa|za|saf)(?:\s|[-|:])/i],
  ["Nigeria", "Africa", /^(nigeria|nga)(?:\s|[-|:])/i],
  ["Australia", "Oceania", /^(australia|aus)(?:\s|[-|:])/i],
  ["New Zealand", "Oceania", /^(new zealand|nz)(?:\s|[-|:])/i],
];

function locationFor(title, attrs) {
  const declaredCountry = clean(attrs.country || attrs["tvg-country"] || "");
  const declaredLanguage = clean(attrs.language || attrs["tvg-language"] || "");
  if (declaredCountry) {
    const found = COUNTRY_RULES.find(([country]) => country.toLocaleLowerCase() === declaredCountry.toLocaleLowerCase());
    return { country: declaredCountry, region: found ? found[1] : "Other", language: declaredLanguage || "Unknown" };
  }
  const found = COUNTRY_RULES.find(([, , pattern]) => pattern.test(title));
  return { country: found ? found[0] : "International", region: found ? found[1] : "International", language: declaredLanguage || "Unknown" };
}

function decode(value) {
  return Buffer.from(value, "base64url").toString("utf8");
}

function encode(value) {
  return Buffer.from(value, "utf8").toString("base64url");
}

function idFor(kind, value) {
  return `${kind}-${encode(value)}`;
}

function valueFromId(id, prefix) {
  const marker = `${prefix}-`;
  return id.startsWith(marker) ? decode(id.slice(marker.length)) : null;
}

function clean(value) {
  return String(value || "").replace(/[\r\n]/g, " ").trim();
}

function parseAttributes(header) {
  const attrs = {};
  for (const match of header.matchAll(/([\w-]+)="([^"]*)"/g)) attrs[match[1].toLowerCase()] = clean(match[2]);
  return attrs;
}

function is247Channel(title, attrs) {
  const text = `${title} ${attrs["group-title"] || ""} ${attrs["tvg-name"] || ""} ${attrs["channel-type"] || ""}`;
  return /(?:^|[\s|:_-])(?:24\s*[/.-]?\s*7|24\s*hours?|always[- ]?on|continuous|round[- ]?the[- ]?clock)(?:$|[\s|:_-])/i.test(text) || /24\s*\/\s*7/i.test(text);
}

function classify(attrs, title, streamUrl) {
  const group = `${attrs["group-title"] || ""} ${attrs.category || ""}`.toLowerCase();
  const episode = title.match(/(?:^|[ ._-])s(\d{1,2})[ ._-]*e(\d{1,3})(?:$|[ ._-])/i) || title.match(/(?:^|[ ._-])(\d{1,2})x(\d{1,3})(?:$|[ ._-])/i);
  if (episode || /tv show|tv shows|series|episodes/.test(group)) {
    const season = episode ? Number(episode[1]) : 1;
    const number = episode ? Number(episode[2]) : 0;
    const cleanTitle = title.replace(/[ ._-]*s\d{1,2}[ ._-]*e\d{1,3}/i, "").replace(/[ ._-]*\d{1,2}x\d{1,3}/i, "").trim();
    return { kind: "series", name: clean(attrs["tv-show"] || attrs["series-name"] || cleanTitle || title), season, episode: number };
  }
  if (/movie|movies|film|films|cinema/.test(group) || /\.(mkv|mp4|avi|mov)(?:\?|$)/i.test(streamUrl)) return { kind: "movie", name: clean(title), season: 0, episode: 0 };
  return { kind: "tv", name: clean(title), season: 0, episode: 0 };
}

function parseM3U(raw) {
  const entries = [];
  let pending = null;
  for (const rawLine of raw.split(/\r?\n/)) {
    const line = rawLine.trim().replace(/^\ufeff/, "");
    if (!line) continue;
    if (line.toUpperCase().startsWith("#EXTINF")) {
      const comma = line.indexOf(",");
      pending = { attrs: parseAttributes(comma >= 0 ? line.slice(0, comma) : line), title: clean(comma >= 0 ? line.slice(comma + 1) : "Untitled") };
      continue;
    }
    if (line.startsWith("#") || !pending) continue;
    const { attrs, title } = pending;
    const type = classify(attrs, title, line);
    const category = clean(attrs["group-title"] || "Uncategorised").replace(/^Movies\s*\/\s*/i, "").replace(/^TV Shows\s*\/\s*/i, "") || "Uncategorised";
    const location = locationFor(`${title} ${attrs["group-title"] || ""}`, attrs);
    entries.push({
      id: idFor("item", attrs["tvg-id"] || line), title, url: line, logo: attrs["tvg-logo"] || attrs.logo || "", poster: attrs.poster || attrs.cover || attrs["tvg-logo"] || "", fanart: attrs.fanart || attrs["tvg-fanart"] || attrs["tvg-logo"] || "", category, is247: type.kind === "tv" && is247Channel(title, attrs), ...location, ...type,
    });
    pending = null;
  }
  return entries;
}

async function loadEntries(force = false) {
  if (!force && cache.loadedAt && Date.now() - cache.loadedAt < REFRESH_MS) return cache.entries;
  const response = await fetch(M3U_URL, { headers: { "user-agent": "Xtream Playlist Stremio Addon/1.0" } });
  if (!response.ok) throw new Error(`M3U request failed: ${response.status}`);
  const entries = parseM3U(await response.text());
  cache = { loadedAt: Date.now(), entries };
  return entries;
}

function catalogItems(entries, kind, search = "", mode = "all") {
  const needle = search.toLocaleLowerCase();
  const filtered = entries.filter((entry) => entry.kind === kind && (mode === "247" ? entry.is247 : mode === "regular" ? !entry.is247 : true) && (!needle || `${entry.title} ${entry.name} ${entry.category} ${entry.region} ${entry.country} ${entry.language} ${entry.is247 ? "24/7 always on" : "regular"}`.toLocaleLowerCase().includes(needle)));
  const unique = kind === "series" ? [...new Map(filtered.map((entry) => [entry.name.toLocaleLowerCase(), entry])).values()] : filtered;
  return unique.sort((a, b) => a.region.localeCompare(b.region) || a.country.localeCompare(b.country) || a.category.localeCompare(b.category) || a.title.localeCompare(b.title)).map((entry) => ({
    id: entry.id,
    type: kind === "series" ? "series" : kind,
    name: kind === "tv" ? `${entry.region} · ${entry.country} · ${entry.title}` : kind === "series" ? entry.name : entry.title,
    poster: entry.poster || entry.logo,
    posterShape: kind === "tv" ? "landscape" : "poster",
    description: `${entry.is247 ? "24/7 / " : ""}${entry.region} / ${entry.country} / ${entry.category}${entry.language !== "Unknown" ? ` / ${entry.language}` : ""}`,
    genres: [entry.region, entry.country, entry.category, entry.language].filter((value) => value && value !== "Unknown"),
  }));
}

function itemMetas(entries, kind, category, search = "") {
  const needle = search.toLocaleLowerCase();
  return entries.filter((entry) => entry.kind === kind && (!category || entry.category.toLocaleLowerCase() === category.toLocaleLowerCase()) && (!needle || `${entry.title} ${entry.name} ${entry.category}`.toLocaleLowerCase().includes(needle)));
}

function metaFor(entries, type, id) {
  const item = entries.find((entry) => entry.id === id);
  if (item) {
    const videos = entries.filter((entry) => entry.kind === "series" && entry.name === item.name).sort((a, b) => a.season - b.season || a.episode - b.episode).map((entry) => ({ id: `${entry.id}:${entry.season}:${entry.episode}`, title: entry.title, season: entry.season, episode: entry.episode, thumbnail: entry.poster || entry.logo }));
    return { id, type, name: item.name || item.title, poster: item.poster || item.logo, background: item.fanart || item.poster || item.logo, description: item.category, ...(type === "series" ? { videos } : {}) };
  }
  const category = valueFromId(id, "category");
  if (category) {
    const [kind, categoryName] = category.split(":");
    return { id, type, name: categoryName, description: `Browse ${categoryName}`, posterShape: "landscape", _category: { kind, category: categoryName } };
  }
  return null;
}

function json(res, status, body) {
  const data = JSON.stringify(body);
  res.writeHead(status, { "content-type": "application/json; charset=utf-8", "access-control-allow-origin": "*", "cache-control": "no-store" });
  res.end(data);
}

const manifest = {
  id: "community.xtreamplaylistmanager",
  version: "1.0.0",
  name: "Xtream Playlist Manager",
  description: "Organised M3U live TV, movies and TV series with search.",
  resources: ["catalog", "meta", "stream"],
  types: ["tv", "movie", "series"],
  catalogs: [
    { type: "tv", id: "xtream-tv", name: "Live TV · Regional Channels", extra: [{ name: "search", isRequired: false }] },
    { type: "tv", id: "xtream-tv-247", name: "Live TV · 24/7 Channels", extra: [{ name: "search", isRequired: false }] },
    { type: "tv", id: "xtream-tv-all", name: "Live TV · All Channels", extra: [{ name: "search", isRequired: false }] },
    { type: "movie", id: "xtream-movies", name: "Movies", extra: [{ name: "search", isRequired: false }] },
    { type: "series", id: "xtream-series", name: "TV Shows", extra: [{ name: "search", isRequired: false }] },
  ],
};

async function handle(req, res) {
  const url = new URL(req.url, `http://${req.headers.host || "localhost"}`);
  try {
    if (url.pathname === "/manifest.json") return json(res, 200, manifest);
    const parts = url.pathname.split("/").filter(Boolean);
    if (parts.length && parts[parts.length - 1].endsWith(".json")) parts[parts.length - 1] = parts[parts.length - 1].slice(0, -5);
    const entries = await loadEntries();
    if (parts[0] === "catalog" && parts.length >= 3) {
      const type = parts[1] === "series" ? "series" : parts[1] === "movie" ? "movie" : "tv";
      const search = url.searchParams.get("search") || "";
      const catalogId = parts[2];
      const mode = catalogId === "xtream-tv-247" ? "247" : catalogId === "xtream-tv" ? "regular" : "all";
      return json(res, 200, { metas: catalogItems(entries, type, search, mode) });
    }
    if (parts[0] === "meta" && parts.length >= 3) return json(res, 200, { meta: metaFor(entries, parts[1], parts[2]) || {} });
    if (parts[0] === "stream" && parts.length >= 3) {
      const rawId = parts[2].split(":")[0];
      const entry = entries.find((candidate) => candidate.id === rawId);
      if (!entry && parts[1] === "series") return json(res, 200, { streams: [] });
      return json(res, 200, { streams: entry ? [{ name: "Xtream Playlist", title: entry.title, url: entry.url, behaviorHints: { bingeGroup: "xtream-playlist" } }] : [] });
    }
    return json(res, 404, { error: "Not found" });
  } catch (error) {
    return json(res, 502, { error: error.message });
  }
}

http.createServer(handle).listen(PORT, "0.0.0.0", () => console.log(`Xtream Stremio addon listening on port ${PORT}; refresh interval: 60 minutes`));

module.exports = { parseM3U, classify, is247Channel, REFRESH_MS };
