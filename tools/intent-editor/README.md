# GBC 意图树编辑器 / Intent-Tree Editor

把 GBC 意图树(`.gbc/<path>/gbc.md`)当**单一事实源**来可视化编辑:一个节点的意图只写一次,保存时工具同步投影到父/子两处,免去手维护双份导致的漂移。人做架构判断,工具担机械维护——与 GBC 哲学一致。

Visually edit the GBC intent tree (`.gbc/<path>/gbc.md`) as a **single source of truth**: write a node's intent once, and on save the tool projects it into both the parent and child docs — no hand-maintained duplication, no drift. Humans make the architectural calls; the tool handles the mechanical upkeep.

## 跑起来 / Run

```bash
cd backend
python3 server.py                       # 127.0.0.1:8765
python3 server.py --root /path/to/.gbc  # 预填并自动加载 / prefill & auto-load
# 另可加 / also: --port / --host
```

浏览器打开 / open http://localhost:8765 。

## 完整文档 / Full docs

Web 编辑器用法、意图 CLI(`gbc_doc.py`)、把 CLI 包成 skill、以及 gbc.md 三段式写法,见 /
For web-editor usage, the intent CLI (`gbc_doc.py`), wrapping it as a skill, and how to write gbc.md, see:

- 中文:[../../docs/intent-editor-and-skills.md](../../docs/intent-editor-and-skills.md)
- English: [../../docs/intent-editor-and-skills_EN.md](../../docs/intent-editor-and-skills_EN.md)
