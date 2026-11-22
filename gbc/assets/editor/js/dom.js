// 极小的 DOM 帮手(零依赖)。视图层共用:escapeHtml / el / qs / on。

export function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (c) => (
    { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]
  ));
}

// 声明式建元素:el("button", { class, onclick, dataset, disabled, value }, ...kids)
export function el(tag, props, ...kids) {
  const n = document.createElement(tag);
  for (const k in (props || {})) {
    const v = props[k];
    if (v == null) continue;
    if (k === "class") n.className = v;
    else if (k === "dataset") Object.assign(n.dataset, v);
    else if (k.startsWith("on")) n.addEventListener(k.slice(2), v);
    else if (k === "value") n.value = v;
    else if (k === "disabled") { if (v) n.disabled = true; }
    else n.setAttribute(k, v);
  }
  for (const c of kids.flat()) {
    if (c == null || c === false) continue;
    n.append(c.nodeType ? c : document.createTextNode(String(c)));
  }
  return n;
}

export function qs(sel, root) {
  return (root || document).querySelector(sel);
}

export function qsAll(sel, root) {
  return Array.from((root || document).querySelectorAll(sel));
}

// 空安全的事件绑定:元素缺失时静默跳过。
export function on(sel, event, fn) {
  const target = typeof sel === "string" ? qs(sel) : sel;
  if (target) target.addEventListener(event, fn);
  return target;
}
