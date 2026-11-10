# 侧栏导航验证记录

本次增加控件层级操作、按钮关联页面、侧栏交互样式。操作说明见 [侧栏导航与控件层级](../../docs/侧栏导航与控件层级.md)。

## 可直接打开的结果

- [万金油UI 导航增强副本](../../uidemo/08_万金油UI/万金油UI_导航增强.uipro)：前三个导航按钮置顶，关联原有前三页，隐藏选择夹表头。
- [独立导出入口](export/main.py)：用 Python 和 PySide6 运行。
- [机器可读验证结果](result.json)：含原生、F5 预览子进程、隔离导出结果及原始项目 SHA-256。

原始“万金油UI”和“兔子工具个人中心”文件未改动。数字占位按钮没有增加业务行为，页面内容也沿用原项目。

## 自动与原生验证

完整功能实现的全量回归 **1217 项通过**，耗时 856.28 秒，见 [测试日志](pytest.log) 和 [JUnit 结果](pytest.xml)。

新增功能回归覆盖层级、属性面板、三类按钮与三类页面容器、撤销、删除、复制、保存、动态页签排序、解除关联、样式恢复和快捷键。已有多选、输入扩展与选择夹相关回归 **112 项通过**。

最后精简了菜单可用状态计算：仅检查选中控件与相邻层级，不再为了刷新菜单构造候选模型。1000 个控件、选中其中 500 个的本机测量中，四个动作的可用状态计算从约 26.52 毫秒降到 1.44 毫秒。新增测试枚举五个控件的全部 31 种非空选集，核对菜单状态与实际命令结果；最终源码的层级专项 **7 项通过**。

菜单优化后，最终源码的导航、层级、多选及命令面板联合复测 **97 项通过，0 失败、0 跳过**，耗时 361.93 秒。见 [最终复测日志](menu-final.log) 和 [JUnit 结果](menu-final.xml)。

Windows 原生运行时、正式预览协议的独立子进程、Python `-I` 隔离的导出进程均完成：

- 在每个导航按钮的左侧、文字区和右侧点击，累计检查 12 个位置。
- 连续切换 60 次，验证当前页与唯一高亮同步。
- 保持选择夹表头隐藏，且重复应用构建计划不会重复触发切页。

隔离导出不加载 `core` 或 `designer` 模块。发布清单已包含新增 `runtime/navigation.py`，并核对全部 14 个导出运行模块；本次未重建 Windows EXE。

## 截图

| 运行路径 | 用户中心 | 任务中心 | 软件设置 |
| --- | --- | --- | --- |
| Windows 原生 | [页面 1](native/page-1.png) | [页面 2](native/page-2.png) | [页面 3](native/page-3.png) |
| F5 子进程 | [页面 1](preview/page-1.png) | [页面 2](preview/page-2.png) | [页面 3](preview/page-3.png) |
| 独立导出 | [页面 1](exported/page-1.png) | [页面 2](exported/page-2.png) | [页面 3](exported/page-3.png) |

## 复现命令

```powershell
python -m pytest tests/test_navigation.py tests/test_stacking.py -q
python -m pytest tests/test_navigation.py tests/test_stacking.py tests/test_multiselect.py tests/test_workbench_commands.py -q
python -m pytest -q --tb=short --junitxml=reports/navigation-20261111/pytest.xml
$env:QT_QPA_PLATFORM = 'windows'
python -X utf8 -m scripts.check_navigation
```

全量回归源码指纹：`f74beca36c7df5b70d3aeff408c10343864b08051294c83499dcb5f0e4099add`。

最后菜单计算优化后的核心源码指纹：`d255af9e9269fd19e436b8990a5ee63626f3127da137b25382012bb205d0ead0`。
