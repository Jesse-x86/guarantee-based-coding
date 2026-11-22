// 后端 HTTP 契约的薄封装。只收发,不做任何语义/路径处理。

export class ApiError extends Error {
  constructor(status, body) {
    super((body && body.error) || String(status));
    this.status = status;
    this.body = body || {};
  }
}

async function jsonOrThrow(res) {
  let body = null;
  try { body = await res.json(); } catch { /* 非 JSON 响应 */ }
  if (!res.ok) throw new ApiError(res.status, body || {});
  return body || {};
}

// GET /api/config -> {root, lang}
export async function getConfig() {
  return jsonOrThrow(await fetch("/api/config"));
}

// GET /api/tree-flat?root=... -> {root, name, tree:<flat map>}
export async function getTreeFlat(root) {
  return jsonOrThrow(await fetch("/api/tree-flat?root=" + encodeURIComponent(root || "")));
}

// GET /api/file-meta?root=...&path=... -> {meta|null}
export async function getFileMeta(root, path) {
  return jsonOrThrow(await fetch(
    "/api/file-meta?root=" + encodeURIComponent(root || "") + "&path=" + encodeURIComponent(path || "")
  ));
}

// POST /api/save body {root, base, current, force}
// 200 -> {written, deleted, count}; 409 -> {error:"conflict", conflicts, external_changes}
export async function saveTree(root, base, current, force) {
  return jsonOrThrow(await fetch("/api/save", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ root, base, current, force: !!force }),
  }));
}
