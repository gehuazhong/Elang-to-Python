# 0.10.1 迭代验证记录

验证环境：Windows，Python 3.11.8，PySide6/Qt 6.11.1，pytest 8.3.4。

## 修复依据

首次对已有实现运行十项新增测试，十项均失败，记录保留在 [reproduced.xml](reproduced.xml)。失败包含组内对话框触发关联未映射、带事件时复制失败、外部引用未清理、非可视组被错误要求画布层级、结果回调中新窗口丢失、重复完成、取消后迟到完成、忙碌状态误报、重新打开初始进度错误。

随后扩展了真实对象树 Ctrl 多选、代码名称避重、事件声明、锁定、非法片段、撤销重做、原生窗口销毁、Esc/关闭/拒绝/取消按钮、消息按钮结果、输入模式快照、模态进度框处理事件时的回调重入等覆盖。

新增专项回归 **45 项全部通过**，耗时 9.34 秒，见 [targeted.xml](targeted.xml)。

最终全量回归 **1263 项全部通过，0 失败、0 错误、0 跳过**，耗时 1292.55 秒。见 [完整日志](pytest.log) 和 [JUnit 结果](pytest.xml)。全量运行期间未再修改应用源码；随后只补充报告和发布文本。

最终应用源码指纹为 `bda7fb2e951ab208cf1b65f1fe2f8c09c643f89eb8d7deb97c9f7ce8161d05d6`，与 Windows、预览、独立导出及最终性能采样记录一致。

## Windows 与独立导出

[runtime.json](runtime.json) 记录 Windows 平台上的运行结果：

| 检查 | 设计器 | 原生运行时 | F5 子进程 | 隔离导出 |
| --- | --- | --- | --- | --- |
| 对象树 Ctrl 多选、复制粘贴快捷键、整组撤销重做 | 通过 | 不适用 | 不适用 | 不适用 |
| 两组按钮独立触发各自复制的对话框 | 不适用 | 通过 | 通过 | 通过 |
| 输入结果回调连续重开 12 次 | 不适用 | 通过 | 通过 | 通过 |
| 自动关闭与自动重置四种组合 | 不适用 | 通过 | 通过 | 通过 |
| 完成／取消只报告一次，忙碌状态不误报 | 不适用 | 通过 | 通过 | 通过 |

运行时反复应用同一构建计划四次后再检查触发。预览使用正式 `PreviewService` 协议，确认进程与设计器不同；导出在 `python -I` 下运行，确认未导入 `core`、`designer`、`panels`。同时核对临时项目保存加载的一致性。

原有 07 兔子工具个人中心、08 万金油 UI 及其导航增强版均通过加载和构建计划检查；检查前后的 SHA-256 一致，具体节点数和摘要见 `runtime.json`。

[启动截图](startup.png) 和 [非可视组件多选截图](nonvisual-selection.png) 来自实际 Windows 窗口。源码启动检查通过，本次没有重新打包 EXE。

## 性能采样

[优化前](performance-before.json) 与 [优化后](performance-after.json) 使用同形状的 500 个按钮项目，各预热两次，采样七次。比较指标为 `compile_plan` 的耗时中位数，不包含画布渲染、窗口显示、项目读写或 Python 导出。

| 采样 | 中位数 | 最小值 | 最大值 |
| --- | --- | --- | --- |
| 优化前 | 195.101 ms | 181.166 ms | 213.017 ms |
| 最终源码 | 76.862 ms | 75.173 ms | 79.649 ms |

本机采样中位数降低约 **60.6%**。最终采样在全量测试退出后执行；这些是本机短时测量值，仍会受机器负载与缓存状态影响，不作为其他机器的性能保证。

注册表指纹保持为 `78ea756544a4d77c0188d0f4dda2f78e194c55543cdbff7a0feb38651aeeb3d8`。原始采样与对应源码指纹均保存在 JSON 中。

## 复现命令

```powershell
python -X utf8 -m pytest -q --tb=short --junitxml=reports/iteration-20261111/pytest.xml
python -X utf8 -m pytest tests/test_clipboard_references.py tests/test_runtime_dialog_lifecycle.py tests/test_metadata_defaults.py -q --tb=short --junitxml=reports/iteration-20261111/targeted.xml
python -X utf8 -m scripts.check_iteration_runtime
python -X utf8 -m scripts.check_iteration_performance after
python -X utf8 main.py --smoke-test --screenshot reports/iteration-20261111/startup.png
```

性能基线 `before` 在优化前生成；当前源码重新运行 `before` 只会覆盖标签文件，不能重现旧实现的耗时。各报告用于本机验证，不表示所有 Qt 版本和平台均已通过。
