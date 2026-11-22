// 差异抽屉:比较 tab、diff 内容、导出文本。纯渲染 + 纯函数,不 import actions/state。

import { escapeHtml } from "./dom.js";
import * as sem from "./semantic.js";
import { diffLines } from "./diff.js";
import { t } from "../i18n.js";

const MODES = [
  ["current-loaded", "tabCurrentLoaded"],
  ["current-disk", "tabCurrentDisk"],
  ["loaded-disk", "tabLoadedDisk"],
];

// ctx: { compareMode, onChangeMode }
export function renderTabs(host, ctx) {
  host.innerHTML = MODES.map(([mode, key]) =>
    `<button class="compare-tab${ctx.compareMode === mode ? " active" : ""}" data-mode="${mode}">${escapeHtml(t(key))}</button>`
  ).join("");
  host.querySelectorAll(".compare-tab").forEach((btn) => {
    btn.addEventListener("click", () => ctx.onChangeMode(btn.dataset.mode));
  });
}

// ctx: { before, after, diskChecked, external, totalEl, alertEl }
export function renderDiff(host, ctx) {
  const groups = sem.classify(ctx.before, ctx.after);
  const total = groups.added.length + groups.modified.length + groups.deleted.length;
  ctx.totalEl.textContent = t("totalChanges", { n: total });

  if (ctx.diskChecked && ctx.external.length) {
    ctx.alertEl.classList.add("show");
    ctx.alertEl.textContent = t("externalAlert", {
      n: ctx.external.length,
      paths: ctx.external.map((p) => p || t("rootPath")).join(", "),
    });
  } else {
    ctx.alertEl.classList.remove("show");
  }

  const titles = { added: t("sectionAdded"), modified: t("sectionModified"), deleted: t("sectionDeleted") };
  host.innerHTML =
    sectionHtml(titles.added, "added", groups.added) +
    sectionHtml(titles.modified, "modified", groups.modified) +
    sectionHtml(titles.deleted, "deleted", groups.deleted);
}

function sectionHtml(title, kind, items) {
  return `<section class="change-section">` +
    `<div class="change-section-head"><span class="section-title">${escapeHtml(title)}</span><span class="count ${kind}">${items.length}</span></div>` +
    (items.length
      ? items.map((x) => diffCard(kind, x)).join("")
      : `<div class="section-empty">${escapeHtml(t("emptySection", { title }))}</div>`) +
  `</section>`;
}

function diffCard(kind, item) {
  const oldText = sem.semanticText(item.before, item.path);
  const newText = sem.semanticText(item.after, item.path);
  const lines = kind === "added"
    ? newText.split("\n").map((text) => ({ type: "add", text }))
    : kind === "deleted"
      ? oldText.split("\n").map((text) => ({ type: "del", text }))
      : diffLines(oldText, newText);
  const isFolder = sem.isFolderPath(item.path);
  return `<article class="diff-card ${kind}">` +
    `<div class="diff-card-head"><span>${isFolder ? "▰" : "▤"}</span><span class="diff-path">${escapeHtml(item.path || t("rootPath"))}</span><span class="diff-kind">${escapeHtml(isFolder ? t("folderKind") : t("fileKind"))}</span></div>` +
    `<pre class="diff-code">${lines.map((l) =>
      `<span class="diff-line ${l.type}"><span class="diff-prefix">${l.type === "add" ? "+" : l.type === "del" ? "−" : " "}</span>${escapeHtml(l.text)}</span>`
    ).join("")}</pre>` +
  `</article>`;
}

// 统一 diff 文本:包含项目、比较模式、项目语义路径,给 LLM/agent 直接阅读。
// ctx: { before, after, compareLabel, projectName }
export function buildExportText(ctx) {
  const groups = sem.classify(ctx.before, ctx.after);
  const lines = [
    t("exportTitle"),
    t("exportProject", { name: ctx.projectName || "" }),
    t("exportComparison", { label: ctx.compareLabel }),
    t("exportHint"),
    "",
  ];
  const addGroup = (title, kind, items) => {
    if (!items.length) return;
    lines.push("## " + title);
    items.forEach((item) => {
      const path = item.path || "(root)";
      const oldText = sem.semanticText(item.before, item.path);
      const newText = sem.semanticText(item.after, item.path);
      lines.push("",
        `diff --gbc a/${path} b/${path}`,
        `--- ${kind === "added" ? "/dev/null" : `a/${path}`}`,
        `+++ ${kind === "deleted" ? "/dev/null" : `b/${path}`}`,
        "@@");
      const ds = kind === "added"
        ? newText.split("\n").map((text) => ({ type: "add", text }))
        : kind === "deleted"
          ? oldText.split("\n").map((text) => ({ type: "del", text }))
          : diffLines(oldText, newText);
      ds.forEach((l) => lines.push((l.type === "add" ? "+" : l.type === "del" ? "-" : " ") + l.text));
    });
    lines.push("");
  };
  addGroup(t("sectionAdded"), "added", groups.added);
  addGroup(t("sectionModified"), "modified", groups.modified);
  addGroup(t("sectionDeleted"), "deleted", groups.deleted);
  if (!(groups.added.length + groups.modified.length + groups.deleted.length)) lines.push(t("exportNoChanges"));
  return lines.join("\n");
}
