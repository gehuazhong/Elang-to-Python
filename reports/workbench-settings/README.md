# 工作台设置验证

Windows，Python 3.11.8，PySide6 / Qt 6.11.1。验证日期：2026-11-10。

## 已验证

- `pytest.xml`：最终全量回归 **1,127 项全部通过**，0 失败、0 跳过，用时 422.15 秒。
- `settings.xml`：12 项设置专项测试通过，包含即时预览、取消、应用后再取消、重启恢复、配置损坏回退、面板锁定、默认布局、保存失败恢复及回车确认。
- `regression.xml`：86 项相关回归通过，覆盖工作台命令、设计器主题、布局恢复、属性交互、字体属性及设置。这份报告早于最后的按钮默认行为调整，按钮行为由上述最新专项覆盖。
- `desktop.json`：Windows 实机检查通过。实际预览工作台字体、保存并重新创建窗口核对字体和布局、还原默认设置，并验证小窗口滚动及底部按钮可用。

字体变化前后对照设计文档、运行控件字体和生成代码，确认工作台设置未改变项目。字号放大和取消恢复后，核对属性编辑器实际位置都位于所属行内，避免只检查建议行高而遗漏显示重叠。

首轮相关测试发现 Qt 样式表保留子控件旧字体，已改用限定在工作台的字体样式。Windows 截图检查发现滚动区底色和持久属性编辑器位置问题，已补齐背景及行布局刷新。`initial.xml` 保留修复前结果，不作为最终验收。

## 重现

```powershell
python -X utf8 -m pytest tests/test_workbench_settings.py -q --disable-warnings --junitxml=reports/workbench-settings/settings.xml
python -X utf8 scripts/check_workbench_settings.py
python -X utf8 -m pytest -q --disable-warnings --junitxml=reports/workbench-settings/pytest.xml
```

截图：`settings-dialog.png` 为设置窗口，`font-preview.png` 为字体预览后的工作台，`custom-layout.png` 为右侧组件箱布局，`compact-dialog.png` 为小窗口。

检查使用临时配置，未改写用户配置或项目文件。交付为当前源码，未重新打包历史 EXE。

## 核心源码指纹

由 `scripts/source_fingerprint.py` 对核心 Python 源码及资源计算的 SHA-256：

```text
923b46be55eeaaef65fb41aa623c3b003bc9c3ca4c9aac0b275e9c7eacdce520
```

指纹不包含文档、测试和历史 EXE。当前结果对应本轮工作台设置源码。
