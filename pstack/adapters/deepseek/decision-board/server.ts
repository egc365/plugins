import { readFile } from "node:fs/promises";
import { createServer } from "node:http";
import { extname, join, resolve } from "node:path";
import { buildSnapshot, parseConfig } from "./projection.ts";

const args = process.argv.slice(2);
const arg = (name: string): string | undefined => { const index = args.indexOf(name); return index < 0 ? undefined : args[index + 1]; };
const configPathValue = arg("--config") ?? process.env.DECISION_BOARD_CONFIG;
if (!configPathValue) throw new Error("Pass --config /absolute/path/config.json or set DECISION_BOARD_CONFIG");
const configPath = configPathValue;
const port = Number(arg("--port") ?? process.env.PORT ?? "0");
if (!Number.isSafeInteger(port) || port < 0 || port > 65535) throw new Error("port must be an integer from 0 to 65535");
const publicDir = resolve(import.meta.dirname, "public");
const mime: Record<string, string> = { ".html": "text/html; charset=utf-8", ".css": "text/css; charset=utf-8", ".js": "text/javascript; charset=utf-8" };
async function config() { return parseConfig(JSON.parse(await readFile(resolve(configPath), "utf8"))); }
const server = createServer(async (request, response) => {
  const url = new URL(request.url ?? "/", "http://localhost");
  if (request.method !== "GET") { response.writeHead(405).end("Method not allowed"); return; }
  if (url.pathname === "/api/snapshot") {
    try { const body = JSON.stringify(await buildSnapshot(await config())); response.writeHead(200, { "content-type": "application/json", "cache-control": "no-store" }).end(body); }
    catch (error) { response.writeHead(500, { "content-type": "application/json", "cache-control": "no-store" }).end(JSON.stringify({ error: String(error), observedAt: new Date().toISOString() })); }
    return;
  }
  const name = url.pathname === "/" ? "index.html" : url.pathname.slice(1);
  if (!/^[a-zA-Z0-9._-]+$/.test(name)) { response.writeHead(404).end("Not found"); return; }
  try { const body = await readFile(join(publicDir, name)); response.writeHead(200, { "content-type": mime[extname(name)] ?? "application/octet-stream", "cache-control": "no-store" }).end(body); }
  catch { response.writeHead(404).end("Not found"); }
});
server.listen(port, "127.0.0.1", () => { const address = server.address(); if (typeof address === "object" && address) console.log("Decision board: http://127.0.0.1:" + address.port); });
