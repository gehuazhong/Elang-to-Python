# 0.10.2 验证记录

环境：Windows、Python 3.11.8、PySide6/Qt 6.11.1、pytest 8.3.4。对应改动见 [迭代说明](../../docs/0.10.2迭代与验证.md)。

## 故障复现与回归

新增 33 项测试，覆盖通用对话框六种模式、回调重开、销毁和配置失败，导出版本复用、事件初始化失败与恢复，标签状态保留，以及接受和取消窗口关闭。

| 记录 | 结果 | 含义 |
| --- | --- | --- |
| [第一批故障复现](reproduced.xml) | 12 失败、1 通过 | 修复前的导出和通用对话框缺陷 |
| [标签栏故障复现](tabbar-reproduced.xml) | 3 失败、1 通过 | 修复前的选择、顺序和业务数据丢失 |
| [退出流程故障复现](window-reproduced.xml) | 4 失败 | 修复前的对话框残留、时钟继续运行和取消关闭误清理 |
| [相关回归](focused.xml) | 346 通过 | 新增 33 项和现有导出、事件、基础及高级组件测试 |
| [完整回归](pytest.xml) | 1296 通过 | 全部测试及架构检查，无失败、错误或跳过，约 509.89 秒 |

失败记录是修复前的证据，不能当作当前源码的测试结果。完整回归在最终 0.10.2 源码上执行，退出码为 0；完成后未再修改产品源码。

## Windows 与独立导出

[runtime.json](runtime.json) 记录 Windows 后端的原生运行时和 `python -I` 隔离导出进程检查：每条路径的六种通用对话框均完成 6 次接受、6 次取消和 12 次回调重开，共 72 次；每次验证旧对象释放、当前对象保留、结果正确和无迟到信号串扰。

每条路径还执行 50 次标签栏配置更新，核对选择、顺序和业务数据保留；关闭主窗口后确认对话框释放、时钟停止。导出子进程先制造事件语法错误、检查窗口及事件模块释放，再修复文件并成功重试；同时确认未导入设计器的 `core`、`designer`、`panels` 模块。保存并重新加载的项目复用相同导出版本。

[启动截图](startup.png) 来自实际 Windows 设计器窗口，源码启动检查通过。本轮未重建 EXE。原有演示项目未纳入本次修复提交。

[现有项目兼容性](projects.json) 覆盖 `examples` 和 `uidemo` 中的 22 个项目：全部成功加载并生成构建计划，21 个能够生成导出文件。最早的“中文界面示例”仍声明不支持的导出模板；与 `d9bb3c1` 基线逐项对照，所有项目的成功结果或拒绝原因一致。检查前后文件 SHA-256 一致，没有写回项目。

## 复现命令

```powershell
python -X utf8 -m pytest -q --tb=short --junitxml=reports/iteration-0102/pytest.xml
python -X utf8 -m pytest tests/test_window_component_lifecycle.py tests/test_tab_bar_refresh.py tests/test_export_stability.py tests/test_common_dialog_lifecycle.py tests/test_runtime_dialog_lifecycle.py tests/test_codegen.py tests/test_easy_widgets.py tests/test_events.py tests/test_advanced_components.py -q --tb=short --junitxml=reports/iteration-0102/focused.xml
python -X utf8 -m scripts.check_iteration_0102
python -X utf8 main.py --smoke-test --screenshot reports/iteration-0102/startup.png
```

全量 pytest 默认使用离屏 Qt 后端；运行脚本验证 Windows 后端，通用对话框使用 Qt 实现。没有将结果外推至所有 Qt 版本、平台或系统原生文件选择器。
