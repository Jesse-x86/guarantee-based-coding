// GBC 意图编辑器 —— 启动与顶层接线。零构建、零依赖、原生 ES modules。
// 所有编排都在 js/actions.js;这里只负责拉 /api/config、切语言、启动。

import * as actions from "./js/actions.js";

actions.init();
