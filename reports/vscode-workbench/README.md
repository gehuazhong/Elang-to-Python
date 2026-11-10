# 本轮验证产物

日期：2026-11-09。修改前截图为 before.png，最终截图位于 scale-1、scale-1.5、scale-2。文件名含 initial 的截图为调试中间态。

- regression.xml：868 项全量回归通过。
- workbench-tests.xml：最终 26 项专项通过，其中 7 项为新增导航与命令搜索回归。
- release-check.json / release-check.png：Windows 源码交付检查与截图。
- scale-*/verification.json：各 DPI 档的桌面检查结果与截图清单。

最终核心源码与资源指纹（scripts/source_fingerprint.py）：

`753afc75fedcd27e8fca77c404f4cdfde2a36465b8642c3bcc48a9f5a12d8a17`

本轮未重新构建历史便携包。界面改动、操作方法和验证边界见 ../../docs/VSCode风格工作台.md。
