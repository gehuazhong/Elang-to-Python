# 全量优化验证记录

环境：Windows，Python 3.11.8，PySide6 / Qt 6.11.1。日期：2026-11-11。

修复说明见 [本轮审计](../../docs/全量审计与修复_20261111.md)。

## 检查结果

| 记录 | 结果 |
| --- | --- |
| `reproduced.xml` | 修复前新增回归 15 项失败、4 项通过，覆盖集合状态丢失、无效目录和恢复服务退出 |
| `targeted-initial.xml` | 第一批修复后 77 项通过 |
| `pytest.xml` | 全量 1,190 项通过，0 失败、0 跳过，用时 536.62 秒 |
| `targeted.xml` | 最终源码 246 项专项复测通过，0 失败、0 跳过，用时 57.68 秒 |
| `desktop.json` | Windows 原生窗口和 `python -I` 隔离导出通过；五类控件各刷新外观 20 次，模型重置均为 0，保留选择、编辑和勾选，并验证实际内容替换 |
| `lifecycle.json` | 3 轮预热及 40 轮一百控件创建销毁，43 个原生根窗口均正常销毁，保留完整私有内存序列 |
| `soak.json` | 混合编辑压力检查运行 301.922 秒、16 轮，通过；异常和错误日志为空 |
| `soak-final.json` | 最终源码补充混合编辑检查运行 128.672 秒、8 轮，通过；异常和错误日志为空 |

应用启动命令 `python -X utf8 main.py --smoke-test` 通过。

全量批次启动后，最后校正了超级列表框勾选状态的 Qt 值类型，并保护没有设计行号的运行时新增行。这一末次修改通过 `targeted.xml` 和 `desktop.json` 复测；`pytest.xml` 是该末次修改前的完整批次，不包含随后新增的一个边界用例。`soak-final.json` 另记录最终源码的混合编辑复测。

压力工具使用包含 72 类组件、89 个节点的项目。五分钟批次执行 362 次命令与撤销重做、98 次整树复制与撤销、97 次删除与撤销、12,164 次滚轮值保持检查、16 次异步保存期间继续编辑及备份，以及各 2 次独立预览和导出。此前原有测试的基线批次也完成，1,166 项通过；它不替代新增故障回归。

## 重现命令

在项目根目录执行：

```powershell
python -X utf8 -m pytest -q --junitxml=reports/full-audit-20261111/pytest.xml
python -X utf8 -m pytest tests/test_audit_20261111.py tests/test_full_audit.py tests/test_column_widths.py tests/test_easy_widgets.py tests/test_standard_widgets.py tests/test_property_completion.py tests/test_storage.py tests/test_project_file_dialog.py tests/test_codegen.py -q --junitxml=reports/full-audit-20261111/targeted.xml
python -X utf8 scripts/check_item_refresh.py
python -X utf8 -m tests.soak_designer --seconds 300 --seed 20261111 --report reports/full-audit-20261111/soak.json
python -X utf8 -m tests.soak_designer --seconds 120 --seed 20261112 --report reports/full-audit-20261111/soak-final.json
python -X utf8 -c "from tests.check_lifecycle import main; main(report_name='full-audit-20261111/lifecycle.json')"
python -X utf8 main.py --smoke-test
```

`scripts/check_item_refresh.py` 每次生成单独的 `item-export-*` 目录，不覆盖旧的导出项目。最近一次成功导出的入口记录在 `desktop.json`，窗口截图为 `item-views.png`。

## 最终源码指纹

`scripts/source_fingerprint.py` 计算的 SHA-256：

```text
4b6ca5f9883cfa3726cea31c5d3460f401037c363e591c9eb80027c1171ddff6
```

该指纹覆盖应用核心源码和资源；不包含测试、报告和历史 EXE。压力工具记录的是另一种不含资源的源码摘要。

这些检查记录当前环境的指定运行范围。测试项目和导出文件均位于临时目录或本报告目录，用户设计项目和历史 EXE 未修改。
