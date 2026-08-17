// 单一可变状态(三态:loaded / current / disk)+ 深拷贝助手。无依赖。

export const state = {
  root: "",        // 项目路径(展示层,不含 .gbc)
  name: "",        // 项目名(根节点语义名)
  lang: "en",
  loaded: null,    // 加载/保存时的快照,不随编辑变化
  current: null,   // 正在编辑的工作副本
  disk: null,      // 最近一次从硬盘读到的内容(load 后 = loaded;切硬盘比较/保存时刷新)
  diskChecked: false, // 是否在 load 之后重新读过硬盘
  selectedPath: "",
  compareMode: "current-loaded", // current-loaded | current-disk | loaded-disk
  drawerOpen: false,
  collapsed: new Set(),
};

export function clone(value) {
  return JSON.parse(JSON.stringify(value));
}
