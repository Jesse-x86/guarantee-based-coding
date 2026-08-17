// 主内容区渲染:folder 页(意图/约束/子节点)与 file 页(描述/只读接口文档)。
// 纯渲染:接收 ctx(数据 + 回调),不 import actions/state。

import { escapeHtml } from "./dom.js";
import * as sem from "./semantic.js";
import { t } from "../i18n.js";

// ctx: { current, loaded, selectedPath, projectName,
//        onSelect, onInput, onAdd, onRename, onDelete, onNeedMeta }
export function renderEditor(host, ctx) {
  const { current, selectedPath, loaded, projectName } = ctx;
  const node = current[selectedPath];
  const isFolder = sem.isFolderPath(selectedPath);
  const change = sem.pathChange(selectedPath, loaded, current);
  const name = sem.baseName(selectedPath, projectName);

  host.innerHTML =
    `<div class="breadcrumbs">${breadcrumbs(selectedPath, projectName)}</div>` +
    `<div class="page-head">` +
      `<div class="page-icon">${isFolder ? "▰" : "▤"}</div>` +
      `<div>` +
        `<h1 class="page-title">${escapeHtml(name)}</h1>` +
        `<div class="page-subtitle">${escapeHtml(selectedPath || t("rootSubtitle"))}</div>` +
      `</div>` +
      `<div class="spacer"></div>` +
      (change
        ? `<span class="badge unsaved">${escapeHtml(change === "added" ? t("badgeNew") : t("badgeUnsaved"))}</span>`
        : "") +
      `<span class="badge ${isFolder ? "folder" : "file"}">${escapeHtml(isFolder ? t("badgeFolder") : t("badgeFile"))}</span>` +
      (selectedPath ? pageActions(selectedPath) : "") +
    `</div>` +
    (isFolder ? folderEditor(selectedPath, node, ctx) : fileEditor(selectedPath, node, ctx));

  // 面包屑导航
  host.querySelectorAll("[data-breadcrumb-path]").forEach((x) => {
    x.addEventListener("click", () => ctx.onSelect(x.dataset.breadcrumbPath));
  });
  // 子节点行 → 打开该节点
  host.querySelectorAll("[data-open-path]").forEach((x) => {
    x.addEventListener("click", (ev) => {
      if (ev.target.closest("[data-action]")) return;
      ctx.onSelect(x.dataset.openPath);
    });
  });
  // 行内 / 页头动作按钮(改名 / 删除 / 新增)
  host.querySelectorAll("[data-action]").forEach((btn) => {
    btn.addEventListener("click", (ev) => {
      ev.stopPropagation();
      const action = btn.dataset.action;
      const path = btn.dataset.path;
      if (action === "rename") ctx.onRename(path);
      else if (action === "delete") ctx.onDelete(path);
      else if (action === "add-file") ctx.onAdd("file", selectedPath);
      else if (action === "add-folder") ctx.onAdd("folder", selectedPath);
    });
  });
  // 文本框 → 直接改 current(不重渲染编辑器,保住焦点)
  const intent = host.querySelector("[data-field='intent']");
  if (intent) intent.addEventListener("input", (e) => ctx.onInput(selectedPath, "intent", e.target.value));
  const constraints = host.querySelector("[data-field='constraints']");
  if (constraints) constraints.addEventListener("input", (e) => ctx.onInput(selectedPath, "constraints", e.target.value));
  const desc = host.querySelector("[data-field='desc']");
  if (desc) desc.addEventListener("input", (e) => ctx.onInput(selectedPath, "desc", e.target.value));

  // file 页:异步拉取只读接口文档
  if (!isFolder) {
    const metaHost = host.querySelector("[data-meta]");
    if (metaHost) ctx.onNeedMeta(selectedPath, metaHost);
  }
}

function breadcrumbs(path, projectName) {
  const parts = path ? path.replace(/\/$/, "").split("/") : [];
  let built = "";
  const out = [`<span data-breadcrumb-path="">${escapeHtml(projectName || t("rootCrumb"))}</span>`];
  parts.forEach((part, i) => {
    built += part + (i < parts.length - 1 || path.endsWith("/") ? "/" : "");
    out.push(`<span class="crumb-sep">/</span><span data-breadcrumb-path="${escapeHtml(built)}">${escapeHtml(part)}</span>`);
  });
  return out.join("");
}

function pageActions(path) {
  return `<div class="page-actions">` +
    `<button class="btn small" data-action="rename" data-path="${escapeHtml(path)}">${escapeHtml(t("rename"))}</button>` +
    `<button class="btn small danger" data-action="delete" data-path="${escapeHtml(path)}">${escapeHtml(t("delete"))}</button>` +
    `</div>`;
}

function folderEditor(path, node, ctx) {
  const children = sem.childrenOf(ctx.current, path);
  return `<section class="card">` +
    `<div class="card-head"><span class="card-title">${escapeHtml(t("intentCardTitle"))}</span><span class="card-hint">${escapeHtml(t("intentCardHint"))}</span></div>` +
    `<div class="card-body">` +
      `<div class="field-label">${escapeHtml(t("intentLabel"))} <span class="field-help">${escapeHtml(t("intentHelp", { name: sem.baseName(path, ctx.projectName) }))}</span></div>` +
      `<textarea class="textarea" data-field="intent">${escapeHtml(node.intent || "")}</textarea>` +
      (path ? `<div class="projection-note"><strong>${escapeHtml(t("singleSource"))}</strong><span>${escapeHtml(t("singleSourceNote"))}</span></div>` : "") +
    `</div></section>` +
    `<section class="card">` +
      `<div class="card-head"><span class="card-title">${escapeHtml(t("constraintsCardTitle"))}</span><span class="card-hint">${escapeHtml(t("constraintsCardHint"))}</span></div>` +
      `<div class="card-body"><textarea class="textarea compact" data-field="constraints" placeholder="${escapeHtml(t("constraintsPlaceholder"))}">${escapeHtml(node.constraints || "")}</textarea></div>` +
    `</section>` +
    `<section class="card">` +
      `<div class="card-head">` +
        `<span class="card-title">${escapeHtml(t("contentsCardTitle"))}</span><span class="card-hint">${escapeHtml(t("contentsCardHint"))}</span>` +
        `<div class="card-actions">` +
          `<button class="btn small" data-action="add-file">${escapeHtml(t("addFile"))}</button>` +
          `<button class="btn small" data-action="add-folder">${escapeHtml(t("addFolder"))}</button>` +
        `</div>` +
      `</div>` +
      `<div class="card-body">` +
        (children.length
          ? `<div class="content-list">${children.map((p) => contentRow(p, ctx)).join("")}</div>`
          : `<div class="empty-state">${escapeHtml(t("emptyDir"))}</div>`) +
      `</div>` +
    `</section>`;
}

function contentRow(path, ctx) {
  const n = ctx.current[path];
  const isFolder = sem.isFolderPath(path);
  const meta = isFolder
    ? t("entriesCount", { n: sem.childrenOf(ctx.current, path).length })
    : t("fileKind");
  return `<div class="content-row" data-open-path="${escapeHtml(path)}">` +
    `<div class="content-name"><span>${isFolder ? "▰" : "▤"}</span>${escapeHtml(sem.baseName(path, ctx.projectName))}</div>` +
    `<div class="content-desc">${escapeHtml(isFolder ? (n.intent || "") : (n.desc || ""))}</div>` +
    `<div class="content-meta">${escapeHtml(meta)}</div>` +
    `<div class="row-actions">` +
      `<button class="btn subtle small" data-action="rename" data-path="${escapeHtml(path)}">${escapeHtml(t("rename"))}</button>` +
      `<button class="btn subtle small danger" data-action="delete" data-path="${escapeHtml(path)}">${escapeHtml(t("delete"))}</button>` +
    `</div>` +
  `</div>`;
}

function fileEditor(path, node, ctx) {
  return `<section class="card">` +
    `<div class="card-head"><span class="card-title">${escapeHtml(t("descCardTitle"))}</span><span class="card-hint">${escapeHtml(t("descCardHint"))}</span></div>` +
    `<div class="card-body">` +
      `<div class="field-label">${escapeHtml(t("descLabel"))} <span class="field-help">${escapeHtml(t("descHelp"))}</span></div>` +
      `<textarea class="textarea compact" data-field="desc">${escapeHtml(node.desc || "")}</textarea>` +
    `</div></section>` +
    `<section class="card">` +
      `<div class="card-head"><span class="card-title">${escapeHtml(t("interfaceCardTitle"))}</span><span class="card-hint">${escapeHtml(t("interfaceCardHint", { path }))}</span></div>` +
      `<div class="card-body" data-meta><div class="meta-loading">${escapeHtml(t("metaLoading"))}</div></div>` +
    `</section>`;
}

// 文件 .gbc json 只读视图(异步结果回填)。meta 为 null=无元数据;err 非空=加载失败。
export function renderFileMeta(host, path, meta, err) {
  if (err) {
    host.innerHTML = `<div class="empty-state">${escapeHtml(t("metaLoadError", { err }))}</div>`;
    return;
  }
  if (!meta) {
    host.innerHTML = `<div class="empty-state">${escapeHtml(t("metaEmpty"))}</div>`;
    return;
  }
  const provides = normalizeProvides(meta.provides);
  const depends = normalizeDependsOn(meta.depends_on);
  host.innerHTML =
    `<div class="readonly-note"><span>◉</span><span>${escapeHtml(t("metaReadonly"))}</span></div>` +
    `<div class="interface-summary">` +
      `<div class="summary-tile"><div class="summary-number">${provides.length}</div><div class="summary-label">${escapeHtml(t("providesSummary"))}</div></div>` +
      `<div class="summary-tile"><div class="summary-number">${depends.length}</div><div class="summary-label">${escapeHtml(t("dependsSummary"))}</div></div>` +
    `</div>` +
    `<div class="field-label">${escapeHtml(t("providesLabel"))}</div>` +
    (provides.length ? provides.map(provideRow).join("") : `<div class="empty-state">${escapeHtml(t("noGuarantees"))}</div>`) +
    `<div class="field-label" style="margin-top:18px">${escapeHtml(t("dependsOnLabel"))}</div>` +
    (depends.length ? depends.map(dependRow).join("") : `<div class="empty-state">${escapeHtml(t("noDeps"))}</div>`);
}

function normalizeProvides(p) {
  if (!p) return [];
  if (Array.isArray(p)) {
    return p.map((x) => ({
      id: x && x.id,
      desc: (x && x.desc) || "",
      disabled: !!(x && x.disabled),
      dependents: (x && x.dependents) || [],
    }));
  }
  if (typeof p === "object") {
    return Object.keys(p).map((id) => {
      const v = p[id] || {};
      return { id, desc: v.desc || "", disabled: !!v.disabled, dependents: v.dependents || [] };
    });
  }
  return [];
}

function normalizeDependsOn(d) {
  if (!Array.isArray(d)) return [];
  return d.map((x) => ({
    symbol: (x && x.symbol) || "",
    guarantees: (x && x.guarantees) || [],
  }));
}

function provideRow(p) {
  const depCount = (p.dependents || []).length;
  return `<div class="api-item">` +
    `<div class="api-id">${escapeHtml(p.id || "")}${p.disabled ? ` <span class="badge disabled-badge">${escapeHtml(t("disabledLabel"))}</span>` : ""}</div>` +
    (p.desc ? `<div class="api-desc">${escapeHtml(p.desc)}</div>` : "") +
    `<div class="api-foot">${depCount
      ? escapeHtml(t("dependentsCount", { n: depCount })) + ": " + p.dependents.map((d) => escapeHtml(String(d))).join(", ")
      : escapeHtml(t("noDependents"))}</div>` +
  `</div>`;
}

function dependRow(d) {
  return `<div class="api-item">` +
    `<span class="api-symbol">${escapeHtml(d.symbol || "")}</span>` +
    `<div class="api-foot">${(d.guarantees && d.guarantees.length)
      ? escapeHtml(t("guaranteesLabel")) + ": " + d.guarantees.map((g) => escapeHtml(String(g))).join(" · ")
      : escapeHtml(t("symbolOnly"))}</div>` +
  `</div>`;
}
