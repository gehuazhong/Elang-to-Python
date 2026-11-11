# 0.10.3 SVG 图标库验证

本轮为 SVG 属性增加 64 个内置图标、八类分类、中英文搜索、颜色与线宽设置、双色背景预览及源码编辑。图标按完整 SVG 保存，独立导出不依赖设计器图标库。

## 验证范围

- 新增 84 项回归：64 个图标分别检查 XML、Qt 渲染、透明背景、颜色及项目校验；其他用例覆盖搜索、无效输入、草稿保留、取消、一次撤销/重做、保存重开与隔离导出。
- Windows 平台下完成 100% 和 200% 缩放检查，包括分类弹层、鼠标搜索选择、颜色对话框、所有操作控件完整可见，以及每档连续重开十二次。
- [示例项目](../../examples/常用SVG图标.uipro) 已通过运行时构建并核对全部 64 个图标。
- 全量 **1,380 项全部通过**，其中本轮新增 84 项；耗时 1,342.62 秒（22 分 22 秒）。完整结果见 [JUnit XML](full.xml)。

全量测试命令：

```powershell
python -X utf8 -m pytest -q --tb=short --junitxml=reports/svg-icons/full.xml
```

实际窗口检查使用 [check_svg_icons.py](../../scripts/check_svg_icons.py)。结果见 [100% 记录](native.json) 和 [200% 记录](scale-200/native.json)。

## 截图

- [图标选择器](icon-picker.png)
- [SVG 源码编辑](svg-source.png)
- [全部图标示例](icon-gallery.png)
- [200% 缩放选择器](scale-200/icon-picker.png)

源码指纹：`5146e7a2c5a8cd9f527b1ae0bddc100502e476400de6446fca0b4844d05d95f0`。

本次验证源码运行和独立 Python 导出，没有重新打包 EXE。
