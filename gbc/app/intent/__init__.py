# Copyright 2026 Jesse-x86
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""意图文档(gbc.md)子系统。

与保证引擎(core + interface)对称:`base` 是唯一 IO/编排点(路径解析、gbc.md
读写、父子投影、一致性、整树读写);`cli`/`editor` 都是薄表面,只调 base、不碰磁盘。
gbc.md 解析单源复用 gbc.app.utils.gbc_md。
"""
