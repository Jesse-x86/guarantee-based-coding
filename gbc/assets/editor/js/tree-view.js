// 左侧统一项目语义树。folder 与 file 都是一等节点。
// 纯渲染:接收 ctx(数据 + 回调),不 import actions/state,避免循环依赖。

import { escapeHtml } from "./dom.js";
import * as sem from "./semantic.js";
import { t } from "../i18n.js";

// ctx: { current, loaded, selectedPath, collapsed, projectName, onSelect, onToggle }
export function renderTree(host, ctx) {
  const { current, loaded, selectedPath, collapsed, projectName, onSelect, onToggle } = ctx;
  host.innerHTML = "";
  const build = (path, depth) => {
    const node = current[path];
    if (!node) return;
    const isFolder = sem.isFolderPath(path);
    const kids = isFolder ? sem.childrenOf(current, path) : [];
    const open = !collapsed.has(path);
    const change = sem.pathChange(path, loaded, current);
    const row = document.createElement("div");
    row.className = "tree-row" + (isFolder ? " folder" : " file") +
      (selectedPath === path ? " selected" : "");
    row.style.paddingLeft = `${8 + depth * 8}px`;
    const twisty = kids.length ? (open ? "⌄" : "›") : "";
    row.innerHTML =
      `<span class="twisty">${twisty}</span>` +
      `<span class="node-icon">${isFolder ? "▰" : "▤"}</span>` +
      `<span class="node-name">${escapeHtml(sem.baseName(path, projectName))}</span>` +
      (change === "added"
        ? `<span class="new-tag">${escapeHtml(t("badgeNew"))}</span>`
        : (change ? `<span class="change-mark ${change}"></span>` : ""));
    row.addEventListener("click", (ev) => {
      if (kids.length && ev.target.classList.contains("twisty")) {
        ev.stopPropagation();
        onToggle(path);
      } else {
        onSelect(path);
      }
    });
    host.append(row);
    if (isFolder && open) kids.forEach((child) => build(child, depth + 1));
  };
  build("", 0);
}
