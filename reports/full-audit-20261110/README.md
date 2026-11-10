# 全量审计验证

环境：Windows，Python 3.11.8，PySide6 / Qt 6.11.1。日期：2026-11-10。

[修复说明](../../docs/全量审计与修复_20261110.md) 记录四项已复现问题及修复方式。

## 已完成检查

- `pytest.xml`：最终全量回归 **1,139 项通过**，0 失败、0 跳过，用时 1,066.15 秒。期间另有压力与生命周期检查并行运行，耗时不用于单独性能比较。
- `reproduced.xml`：修复前，新增回归中 9 项失败、3 项通过，覆盖四类问题。
- `targeted.xml`：修复后 172 项针对性回归全部通过。
- `desktop.json`：Windows 原生窗口和隔离导出均通过。四种模型视图保留选中状态与运行时编辑；每种连续替换内容 20 次后，选择模型仍为 1 个。
- `lifecycle.json`：三轮预热及 40 轮一百控件创建销毁，43 个原生根窗口均收到销毁信号。原始私有内存序列保留在报告中，不据此声称不存在任何泄漏。
- `soak.json`：修复后混合编辑压力检查通过，实际运行 314.125 秒、完成 8 轮。包含 177 次命令提交与撤销重做、45 次整树复制与撤销、59 次删除与撤销、5,957 次滚轮值保持检查，以及 8 次保存期间继续编辑、备份和完整历史还原；独立预览及导出运行各 1 次。异常和错误日志均为空。

`soak-initial.json` 是修复前的混合流程基线，运行 128.469 秒、完成 3 轮，通过。它未覆盖本轮针对性复现条件，因此不能用该基线替代故障回归。

## 重现命令

```powershell
python -X utf8 -m pytest tests/test_full_audit.py tests/test_advanced_components.py tests/test_property_completion.py tests/test_workbench_settings.py -q --disable-warnings --junitxml=reports/full-audit-20261110/targeted.xml
python -X utf8 scripts/check_full_audit.py
python -X utf8 -m tests.soak_designer --seconds 300 --seed 20261110 --report reports/full-audit-20261110/soak.json
python -X utf8 -m pytest -q --disable-warnings --junitxml=reports/full-audit-20261110/pytest.xml
```

所有检查只使用测试项目、临时配置和本报告目录。历史报告、用户项目及已发布 EXE 保留。

## 核心源码指纹

`scripts/source_fingerprint.py` 计算的 SHA-256：

```text
118404f3c5993aea05d16105faa9fe1d897c64bdce1dc325ab4d04452aad0ca2
```

该指纹覆盖核心 Python 源码及资源，不包含文档、测试和历史 EXE。压力工具另有不包含资源的源码摘要，两者用途不同。
