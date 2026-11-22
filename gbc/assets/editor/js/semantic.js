// 项目语义路径与扁平树(flat map)的纯函数。零 DOM、零副作用。
//
// 扁平树契约(与 /api/tree-flat 一致):
//   ""            -> 根文件夹
//   文件夹路径以 "/" 结尾, 文件路径无尾 "/"
//   folder = {kind:"folder", intent, constraints}
//   file   = {kind:"file",   desc}
// 本模块只按「路径形状」判定 folder/file;kind 字段用于展示兜底,不作为唯一依据。

import { t } from "../i18n.js";

export function isFolderPath(path) {
  return path === "" || path.endsWith("/");
}

export function pathKind(path, node) {
  if (node && node.kind === "file") return "file";
  if (node && node.kind === "folder") return "folder";
  return isFolderPath(path) ? "folder" : "file";
}

// 父文件夹路径("" 为根)。根返回 null。
export function parentPath(path) {
  if (!path) return null;
  const clean = path.endsWith("/") ? path.slice(0, -1) : path;
  const at = clean.lastIndexOf("/");
  return at < 0 ? "" : clean.slice(0, at + 1);
}

// 语义名:文件 "main.py"、文件夹 "core/"、根为项目名。
export function baseName(path, projectName) {
  if (!path) return projectName || "";
  const clean = path.endsWith("/") ? path.slice(0, -1) : path;
  return clean.slice(clean.lastIndexOf("/") + 1) + (path.endsWith("/") ? "/" : "");
}

// 子节点完整路径:parent 为 "" 或 "app/";kind 决定尾 "/"。
export function childPath(parent, name, kind) {
  const clean = String(name || "").trim();
  return parent + clean + (kind === "folder" ? "/" : "");
}

// 直接子节点路径(文件夹优先,同种按字典序)。
export function childrenOf(map, path) {
  const out = [];
  for (const k of Object.keys(map || {})) {
    if (!k) continue;
    if (parentPath(k) === path) out.push(k);
  }
  out.sort((a, b) => {
    const af = isFolderPath(a) ? 1 : 0;
    const bf = isFolderPath(b) ? 1 : 0;
    if (af !== bf) return bf - af;
    return a.localeCompare(b);
  });
  return out;
}

// 某节点在 diff/导出里展示的语义文本(folder=意图+约束, file=描述)。
export function semanticText(node, path) {
  if (!node) return "";
  if (!isFolderPath(path)) return t("diffFieldDesc") + "\n" + (node.desc || "");
  const blocks = [t("diffFieldIntent") + "\n" + (node.intent || "")];
  if ((node.constraints || "").trim()) {
    blocks.push(t("diffFieldConstraints") + "\n" + node.constraints);
  }
  return blocks.join("\n\n");
}

// 稳定语义签名:不含 i18n,仅按 kind + 意图/约束(folder)或 desc(file)。
// changedPaths/pathChange/classify 用它做相等性判断,语言切换不会造成假「已修改」。
export function nodeSignature(node, path) {
  if (!node) return "";
  if (!isFolderPath(path)) return "file|" + (node.desc || "");
  const c = (node.constraints || "").trim();
  return "folder|" + (node.intent || "") + (c ? "|" + c : "");
}

// before/after(flat map)之间语义发生变化的路径列表。
export function changedPaths(before, after) {
  const keys = new Set([...Object.keys(before || {}), ...Object.keys(after || {})]);
  return [...keys]
    .filter((k) => nodeSignature((before || {})[k], k) !== nodeSignature((after || {})[k], k))
    .sort();
}

// 单路径的变化类型:"" | "added" | "modified" | "deleted"。
export function pathChange(path, before, after) {
  const b = before ? before[path] : undefined;
  const a = after ? after[path] : undefined;
  if (!b && a) return "added";
  if (b && !a) return "deleted";
  if (nodeSignature(b, path) !== nodeSignature(a, path)) return "modified";
  return "";
}

// 把 before/after 分成 added / modified / deleted 三组。
export function classify(before, after) {
  const keys = new Set([...Object.keys(before || {}), ...Object.keys(after || {})]);
  const result = { added: [], modified: [], deleted: [] };
  [...keys].sort().forEach((path) => {
    const b = (before || {})[path];
    const a = (after || {})[path];
    if (!b && a) result.added.push({ path, before: null, after: a });
    else if (b && !a) result.deleted.push({ path, before: b, after: null });
    else if (nodeSignature(b, path) !== nodeSignature(a, path)) {
      result.modified.push({ path, before: b, after: a });
    }
  });
  return result;
}

// 名称校验:返回错误 key(errEmpty/errSlash/errDot/errDup)或 null。
// 同父重复按「去尾斜杠」归一比较——"foo/" 与 "foo" 视为同名。
export function validateName(name, map, parent, kind) {
  const clean = String(name || "").trim();
  if (!clean) return "errEmpty";
  if (/[\/\\]/.test(clean)) return "errSlash";
  if (clean === "." || clean === "..") return "errDot";
  const key = childPath(parent || "", clean, kind);
  const norm = isFolderPath(key) ? key.slice(0, -1) : key;
  for (const k of Object.keys(map || {})) {
    if (!k) continue;
    const normK = isFolderPath(k) ? k.slice(0, -1) : k;
    if (normK === norm) return "errDup";
  }
  return null;
}

// 新增一个节点(返回新 flat map;不动原 map 的共享引用之外的键)。
export function addInMap(map, parent, name, kind) {
  const out = { ...map };
  const key = childPath(parent, name, kind);
  out[key] = kind === "folder"
    ? { kind: "folder", intent: "", constraints: "" }
    : { kind: "file", desc: "" };
  return out;
}

// 改名:folder 重写整棵前缀子树的所有 key;file 为单 key 改名。
export function renameInMap(map, oldPath, newPath) {
  const out = {};
  const isFolder = isFolderPath(oldPath);
  for (const k of Object.keys(map)) {
    if (isFolder && (k === oldPath || k.startsWith(oldPath))) {
      out[newPath + (k === oldPath ? "" : k.slice(oldPath.length))] = map[k];
    } else if (!isFolder && k === oldPath) {
      out[newPath] = map[k];
    } else {
      out[k] = map[k];
    }
  }
  return out;
}

// 删除:folder 删除整棵前缀子树;file 删单 key。根("")不可删(由调用方拦截)。
export function deleteInMap(map, path) {
  const out = {};
  const isFolder = isFolderPath(path);
  for (const k of Object.keys(map)) {
    if (isFolder && (k === path || k.startsWith(path))) continue;
    if (!isFolder && k === path) continue;
    out[k] = map[k];
  }
  return out;
}
