// 重渲染编排 + 数据动作。唯一 import 视图层/状态/API 的模块;
// 视图层通过 ctx 里的 callback 触发这里的动作,不反向 import(无循环依赖)。

import { setLang, t } from "../i18n.js";
import * as dom from "./dom.js";
import * as api from "./api.js";
import * as sem from "./semantic.js";
import { state, clone } from "./state.js";
import * as treeView from "./tree-view.js";
import * as editorView from "./editor-view.js";
import * as reviewView from "./review-view.js";

// ---- 历史(项目路径) --------------------------------------------------------
const HIST_KEY = "gbc_dir_history";
function getHistory() {
  try { return JSON.parse(localStorage.getItem(HIST_KEY)) || []; } catch { return []; }
}
function pushHistory(p) {
  if (!p) return;
  const h = getHistory().filter((x) => x !== p);
  h.unshift(p);
  localStorage.setItem(HIST_KEY, JSON.stringify(h.slice(0, 12)));
}

// ---- 状态 / 渲染 ------------------------------------------------------------
function setStatus(text) {
  const el = dom.qs("#statusMessage");
  if (el) el.textContent = text;
}

let toastTimer;
function toast(text) {
  const el = dom.qs("#toast");
  if (!el) return;
  el.textContent = text;
  el.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.classList.remove("show"), 1800);
}

function applyStaticText() {
  dom.qsAll("[data-i18n]").forEach((el) => { el.textContent = t(el.dataset.i18n); });
  dom.qsAll("[data-i18n-title]").forEach((el) => { el.title = t(el.dataset.i18nTitle); });
  document.title = t("title");
  document.documentElement.lang = state.lang;
}

function normalizeSelection() {
  if (state.current && state.current[state.selectedPath]) return state.selectedPath;
  return "";
}

function renderTree() {
  const host = dom.qs("#tree");
  if (!host) return;
  if (!state.current) {
    host.innerHTML = `<div class="tree-empty">${dom.escapeHtml(t("empty"))}</div>`;
    return;
  }
  treeView.renderTree(host, {
    current: state.current,
    loaded: state.loaded,
    selectedPath: state.selectedPath,
    collapsed: state.collapsed,
    projectName: state.name,
    onSelect,
    onToggle,
  });
}

function renderEditor() {
  const host = dom.qs("#editor");
  if (!host) return;
  if (!state.current) {
    host.innerHTML =
      `<div class="empty-state big"><div>${dom.escapeHtml(t("empty"))}</div>` +
      `<button class="btn primary" id="chooseProjectBtn">${dom.escapeHtml(t("chooseProject"))}</button></div>`;
    const btn = host.querySelector("#chooseProjectBtn");
    if (btn) btn.addEventListener("click", chooseProject);
    return;
  }
  if (!state.current[state.selectedPath]) state.selectedPath = "";
  editorView.renderEditor(host, {
    current: state.current,
    loaded: state.loaded,
    selectedPath: state.selectedPath,
    projectName: state.name,
    onSelect,
    onInput,
    onAdd,
    onRename,
    onDelete,
    onNeedMeta,
  });
}

function renderChrome() {
  const hasProject = !!state.current;
  const dirtyCount = state.loaded ? sem.changedPaths(state.loaded, state.current).length : 0;

  const dirtyChip = dom.qs("#dirtyChip");
  const dirtyText = dom.qs("#dirtyText");
  if (dirtyChip) dirtyChip.classList.toggle("dirty", dirtyCount > 0);
  if (dirtyText) dirtyText.textContent = dirtyCount ? t("dirtyCount", { n: dirtyCount }) : t("noUnsaved");

  const resetBtn = dom.qs("#resetBtn");
  const drawerResetBtn = dom.qs("#drawerResetBtn");
  if (resetBtn) resetBtn.disabled = !hasProject || dirtyCount === 0;
  if (drawerResetBtn) drawerResetBtn.disabled = !hasProject || dirtyCount === 0;
  for (const id of ["#saveBtn", "#reviewBtn", "#reloadBtn"]) {
    const b = dom.qs(id);
    if (b) b.disabled = !hasProject;
  }

  const diskChip = dom.qs("#diskChip");
  const diskText = dom.qs("#diskText");
  if (diskChip) diskChip.classList.toggle("checked", state.diskChecked);
  if (diskText) {
    diskText.textContent = !state.diskChecked ? t("diskUnchecked")
      : (state.loaded && sem.changedPaths(state.loaded, state.disk).length ? t("diskChanged") : t("diskClean"));
  }

  const pathEl = dom.qs("#projectPath");
  if (pathEl) pathEl.textContent = state.root || t("chooseProject");
  const langEl = dom.qs("#langLabel");
  if (langEl) langEl.textContent = t("langLabel");
}

function renderReview() {
  if (!state.drawerOpen) return;
  const cmp = comparison();
  const external = state.diskChecked ? sem.changedPaths(state.loaded, state.disk) : [];
  reviewView.renderTabs(dom.qs("#compareTabs"), { compareMode: state.compareMode, onChangeMode });
  reviewView.renderDiff(dom.qs("#diffContent"), {
    before: cmp.before,
    after: cmp.after,
    diskChecked: state.diskChecked,
    external,
    totalEl: dom.qs("#totalChanges"),
    alertEl: dom.qs("#externalAlert"),
  });
}

function comparison() {
  if (state.compareMode === "current-disk") {
    return { before: state.disk, after: state.current, label: t("compareLabelCurrentDisk") };
  }
  if (state.compareMode === "loaded-disk") {
    return { before: state.loaded, after: state.disk, label: t("compareLabelLoadedDisk") };
  }
  return { before: state.loaded, after: state.current, label: t("compareLabelCurrentLoaded") };
}

// ---- 数据动作 ---------------------------------------------------------------
async function load() {
  const root = state.root.trim();
  if (!root) { renderEditor(); renderTree(); renderChrome(); return; }
  setStatus(t("msgLoading"));
  try {
    const data = await api.getTreeFlat(root);
    state.name = data.name || "";
    state.disk = data.tree;
    state.loaded = clone(data.tree);
    state.current = clone(data.tree);
    state.diskChecked = false;
    state.selectedPath = "";
    state.collapsed.clear();
    pushHistory(root);
    renderTree(); renderEditor(); renderChrome();
    setStatus(t("msgLoaded"));
  } catch (err) {
    setStatus(t("msgLoadFailed", { err: err.message }));
    toast(t("msgLoadFailed", { err: err.message }));
  }
}

async function refreshDisk() {
  setStatus(t("msgCheckingDisk"));
  try {
    const data = await api.getTreeFlat(state.root);
    state.disk = data.tree;
    state.name = data.name || state.name;
    state.diskChecked = true;
  } catch (err) {
    state.diskChecked = false;
    setStatus(t("msgDiskCheckFailed", { err: err.message }));
    toast(t("msgDiskCheckFailed", { err: err.message }));
  }
  renderChrome();
}

async function save(force = false) {
  setStatus(t("msgSaving"));
  let res;
  try {
    res = await api.saveTree(state.root, state.loaded, state.current, force);
  } catch (err) {
    if (err instanceof api.ApiError && err.status === 409 && !force) {
      showConflict(err.body);
      return;
    }
    setStatus(t("msgSaveFailed", { err: err.message }));
    toast(t("msgSaveFailed", { err: err.message }));
    return;
  }

  // 保存已成功;刷新硬盘状态与保存结果分开——刷新失败不等于保存失败。
  let refreshErr = null;
  try {
    const data = await api.getTreeFlat(state.root);
    state.name = data.name || state.name;
    state.disk = data.tree;
    state.loaded = clone(data.tree);
    state.current = clone(data.tree);
    state.diskChecked = true;
  } catch (err) {
    refreshErr = err;
    // 把已保存内容标记为 loaded,避免下次保存把自己的变化误判为外部冲突。
    state.loaded = clone(state.current);
    state.diskChecked = false;
  }
  state.selectedPath = normalizeSelection();
  closeModal();
  closeReview();
  renderTree(); renderEditor(); renderChrome();
  if (refreshErr) {
    setStatus(t("msgSavedRefreshFailed", { err: refreshErr.message }));
    toast(t("msgSavedRefreshFailed", { err: refreshErr.message }));
  } else {
    setStatus(t("msgSaved", { count: res.count || 0 }));
    toast(t("toastSaved", { count: res.count || 0 }));
  }
}

function showConflict(body) {
  const conflicts = body.conflicts || [];
  const listHtml = conflicts
    .map((c) => `<li>${dom.escapeHtml((c && c.path) || t("rootPath"))}</li>`)
    .join("");
  openModal({
    title: t("conflictTitle"),
    bodyHtml:
      `<div>${dom.escapeHtml(t("conflictBody"))}</div>` +
      `<div class="modal-callout">${dom.escapeHtml(t("conflictPathsLabel"))}<ul class="conflict-list">${listHtml}</ul></div>`,
    confirmLabel: t("confirmOverwrite"),
    confirmKind: "danger",
    onConfirm: () => { save(true); return true; },
    cancelLabel: t("cancel"),
  });
}

function resetToLoaded() {
  const n = sem.changedPaths(state.loaded, state.current).length;
  if (!n) return;
  openModal({
    title: t("confirmResetTitle"),
    bodyHtml: `<div>${dom.escapeHtml(t("confirmResetBody", { n }))}</div>`,
    confirmLabel: t("confirmRevert"),
    confirmKind: "danger",
    onConfirm: () => {
      state.current = clone(state.loaded);
      state.selectedPath = normalizeSelection();
      closeModal();
      closeReview();
      renderTree(); renderEditor(); renderChrome();
      setStatus(t("msgReverted"));
      toast(t("toastReverted"));
      return true;
    },
    cancelLabel: t("cancel"),
  });
}

function reloadDisk() {
  const n = sem.changedPaths(state.loaded, state.current).length;
  const act = async () => {
    try {
      const data = await api.getTreeFlat(state.root);
      state.name = data.name || state.name;
      state.disk = data.tree;
      state.loaded = clone(data.tree);
      state.current = clone(data.tree);
      state.diskChecked = true;
      state.selectedPath = "";
      closeModal();
      closeReview();
      renderTree(); renderEditor(); renderChrome();
      setStatus(t("msgReloaded"));
      toast(t("toastLoaded"));
    } catch (err) {
      closeModal();
      setStatus(t("msgLoadFailed", { err: err.message }));
      toast(t("msgLoadFailed", { err: err.message }));
    }
  };
  if (!n) { act(); return; }
  openModal({
    title: t("confirmLoadTitle"),
    bodyHtml: `<div>${dom.escapeHtml(t("confirmLoadBody", { n }))}</div>`,
    confirmLabel: t("confirmLoad"),
    confirmKind: "danger",
    onConfirm: () => { act(); return true; },
    cancelLabel: t("cancel"),
  });
}

function chooseProject() {
  openModal({
    title: t("chooseProject"),
    input: {
      value: state.root,
      label: t("projectPathLabel"),
      placeholder: t("rootPlaceholder"),
      hint: t("projectPathHint"),
      datalist: getHistory(),
    },
    confirmLabel: t("loadProject"),
    confirmKind: "primary",
    onConfirm: (value) => {
      const root = String(value || "").trim();
      if (!root) { toast(t("errEmpty")); return false; }
      state.root = root;
      load();
      return true;
    },
    cancelLabel: t("cancel"),
  });
}

// ---- 视图回调 ---------------------------------------------------------------
function onSelect(path) {
  state.selectedPath = path;
  renderTree();
  renderEditor();
}

function onToggle(path) {
  if (state.collapsed.has(path)) state.collapsed.delete(path);
  else state.collapsed.add(path);
  renderTree();
}

function onCollapseAll() {
  for (const k of Object.keys(state.current || {})) {
    if (sem.isFolderPath(k) && sem.childrenOf(state.current, k).length) state.collapsed.add(k);
  }
  renderTree();
}

function onInput(path, field, value) {
  const node = state.current && state.current[path];
  if (!node) return;
  node[field] = value;
  renderChrome();
  renderTree();
}

function onAdd(kind, parent) {
  openModal({
    title: kind === "folder" ? t("addFolderTitle") : t("addFileTitle"),
    input: {
      value: "",
      label: t("addNameLabel"),
      placeholder: t("namePlaceholder"),
      hint: kind === "folder" ? t("addFolderHint") : t("addFileHint"),
    },
    confirmLabel: t("confirmAdd"),
    confirmKind: "primary",
    onConfirm: (name) => {
      const err = sem.validateName(name, state.current, parent, kind);
      if (err) { toast(t(err)); return false; }
      state.current = sem.addInMap(state.current, parent, name, kind);
      state.selectedPath = sem.childPath(parent, name, kind);
      renderTree(); renderEditor(); renderChrome();
      return true;
    },
    cancelLabel: t("cancel"),
  });
}

function onRename(path) {
  const kind = sem.isFolderPath(path) ? "folder" : "file";
  const cleanName = sem.baseName(path, state.name).replace(/\/$/, "");
  const parent = sem.parentPath(path);
  openModal({
    title: t("renameTitle", { name: sem.baseName(path, state.name) }),
    input: {
      value: cleanName,
      label: t("renameLabel"),
      placeholder: t("namePlaceholder"),
      hint: t("renameHint"),
    },
    confirmLabel: t("confirmRename"),
    confirmKind: "primary",
    onConfirm: (name) => {
      const clean = String(name || "").trim();
      const newPath = sem.childPath(parent, clean, kind);
      if (newPath === path) return true; // 未改 → 直接关
      const err = sem.validateName(clean, state.current, parent, kind);
      if (err) { toast(t(err)); return false; }
      const wasSelected = state.selectedPath === path;
      state.current = sem.renameInMap(state.current, path, newPath);
      if (wasSelected) state.selectedPath = newPath;
      renderTree(); renderEditor(); renderChrome();
      return true;
    },
    cancelLabel: t("cancel"),
  });
}

function onDelete(path) {
  if (!path) { toast(t("errRootReadonly")); return; }
  const isFolder = sem.isFolderPath(path);
  const name = sem.baseName(path, state.name);
  openModal({
    title: t("deleteTitle", { name }),
    bodyHtml: `<div>${dom.escapeHtml(isFolder ? t("deleteFolderBody", { path }) : t("deleteFileBody", { path }))}</div>`,
    confirmLabel: t("confirmDelete"),
    confirmKind: "danger",
    onConfirm: () => {
      const wasSelected = state.selectedPath === path;
      state.current = sem.deleteInMap(state.current, path);
      if (wasSelected) state.selectedPath = sem.parentPath(path) || "";
      renderTree(); renderEditor(); renderChrome();
      return true;
    },
    cancelLabel: t("cancel"),
  });
}

async function onNeedMeta(path, host) {
  try {
    const data = await api.getFileMeta(state.root, path);
    if (!host.isConnected) return; // 已切页,丢弃过期结果
    editorView.renderFileMeta(host, path, data.meta, null);
  } catch (err) {
    if (!host.isConnected) return;
    editorView.renderFileMeta(host, path, null, err.message);
  }
}

// ---- 差异抽屉 ---------------------------------------------------------------
async function openReview() {
  state.drawerOpen = true;
  dom.qs("#drawerScrim").classList.add("open");
  dom.qs("#reviewDrawer").classList.add("open");
  await refreshForCompare();
  renderReview();
}

function closeReview() {
  state.drawerOpen = false;
  dom.qs("#drawerScrim").classList.remove("open");
  dom.qs("#reviewDrawer").classList.remove("open");
}

async function refreshForCompare() {
  if (state.compareMode === "current-loaded") return;
  await refreshDisk();
}

async function onChangeMode(mode) {
  state.compareMode = mode;
  await refreshForCompare();
  renderReview();
}

function exportCtx() {
  const cmp = comparison();
  return {
    before: cmp.before,
    after: cmp.after,
    compareMode: state.compareMode,
    compareLabel: cmp.label,
    projectName: state.name,
  };
}

async function copyExport() {
  const text = reviewView.buildExportText(exportCtx());
  try {
    await navigator.clipboard.writeText(text);
  } catch {
    const ta = document.createElement("textarea");
    ta.value = text;
    document.body.append(ta);
    ta.select();
    document.execCommand("copy");
    ta.remove();
  }
  toast(t("toastCopied"));
}

function downloadExport() {
  const text = reviewView.buildExportText(exportCtx());
  const url = URL.createObjectURL(new Blob([text], { type: "text/plain;charset=utf-8" }));
  const a = document.createElement("a");
  a.href = url;
  a.download = "gbc-intent-diff.txt";
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 0);
  toast(t("toastDownloaded"));
}

// ---- 弹窗 -------------------------------------------------------------------
let modalInputEl = null;

function openModal({ title, bodyHtml, input, confirmLabel, confirmKind = "primary", onConfirm, cancelLabel, onCancel }) {
  dom.qs("#modalTitle").textContent = title;
  let body = bodyHtml || "";
  if (input) {
    body += `<div class="modal-field">` +
      `<div class="field-label">${dom.escapeHtml(input.label || "")}</div>` +
      `<input class="text-input" id="modalInput" list="__modal_datalist" value="${dom.escapeHtml(input.value || "")}" placeholder="${dom.escapeHtml(input.placeholder || "")}" />` +
      (input.datalist && input.datalist.length
        ? `<datalist id="__modal_datalist">${input.datalist.map((v) => `<option value="${dom.escapeHtml(v)}"></option>`).join("")}</datalist>`
        : "") +
      (input.hint ? `<div class="field-help">${dom.escapeHtml(input.hint)}</div>` : "") +
    `</div>`;
  }
  dom.qs("#modalBody").innerHTML = body;
  modalInputEl = input ? dom.qs("#modalInput") : null;

  const foot = dom.qs("#modalFoot");
  foot.innerHTML = "";
  if (onConfirm) {
    const btn = dom.el("button", {
      class: "btn " + (confirmKind || "primary"),
      onclick: () => {
        const value = modalInputEl ? modalInputEl.value : "";
        const close = onConfirm(value);
        if (close !== false) closeModal();
      },
    }, confirmLabel || t("confirm"));
    foot.append(btn);
  }
  foot.append(dom.el("button", {
    class: "btn",
    onclick: () => { closeModal(); if (onCancel) onCancel(); },
  }, cancelLabel || t("cancel")));

  dom.qs("#modalScrim").classList.add("open");
  if (modalInputEl) { modalInputEl.focus(); modalInputEl.select(); }
}

function closeModal() {
  dom.qs("#modalScrim").classList.remove("open");
  modalInputEl = null;
}

// ---- 静态接线 / 启动 ---------------------------------------------------------
function wireStatic() {
  dom.on("#reloadBtn", "click", reloadDisk);
  dom.on("#resetBtn", "click", resetToLoaded);
  dom.on("#reviewBtn", "click", openReview);
  dom.on("#saveBtn", "click", () => save(false));
  dom.on("#projectSwitcher", "click", chooseProject);
  dom.on("#collapseAllBtn", "click", onCollapseAll);
  dom.on("#drawerScrim", "click", closeReview);
  dom.on("#cancelReviewBtn", "click", closeReview);
  dom.on("#drawerResetBtn", "click", resetToLoaded);
  dom.on("#drawerSaveBtn", "click", () => save(false));
  dom.on("#copyBtn", "click", copyExport);
  dom.on("#downloadBtn", "click", downloadExport);
  dom.on("#modalScrim", "click", (ev) => { if (ev.target === dom.qs("#modalScrim")) closeModal(); });
  document.addEventListener("keydown", (ev) => {
    if (ev.key === "Escape") {
      if (dom.qs("#modalScrim").classList.contains("open")) closeModal();
      else if (state.drawerOpen) closeReview();
    }
  });
}

export async function init() {
  wireStatic();
  setLang("");
  applyStaticText();
  renderChrome();
  renderTree();
  renderEditor();
  try {
    const cfg = await api.getConfig();
    setLang(cfg.lang);
    applyStaticText();
    if (cfg.root) {
      state.root = cfg.root;
      renderChrome();
      await load();
      return;
    }
  } catch (err) {
    setStatus(t("msgConfigFailed", { err: err.message }));
  }
  renderChrome();
  renderTree();
  renderEditor();
}
