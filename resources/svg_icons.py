"""内置常用线性图标；由基本几何构成，不依赖字体、网络或外部资源。"""

from __future__ import annotations

from dataclasses import dataclass
import math
import re
from xml.etree import ElementTree


@dataclass(frozen=True, slots=True)
class SvgIcon:
    key: str
    label: str
    category: str
    keywords: str
    body: str


# 统一使用 24 × 24 坐标、圆端点和圆连接，便于组合成同一套界面。
ICONS = (
    SvgIcon("home", "主页", "导航", "首页 房子 house", '<path d="M3 11 12 3 21 11M5 10v11h5v-7h4v7h5V10"/>'),
    SvgIcon("menu", "菜单", "导航", "目录 汉堡 bars", '<path d="M4 6h16M4 12h16M4 18h16"/>'),
    SvgIcon("search", "搜索", "导航", "查找 放大镜 find", '<circle cx="10" cy="10" r="6"/><path d="m15 15 6 6"/>'),
    SvgIcon("arrow-left", "向左", "导航", "返回 后退 back", '<path d="M21 12H3m7-7-7 7 7 7"/>'),
    SvgIcon("arrow-right", "向右", "导航", "前进 下一步 next", '<path d="M3 12h18m-7-7 7 7-7 7"/>'),
    SvgIcon("arrow-up", "向上", "导航", "顶部 top", '<path d="M12 21V3M5 10l7-7 7 7"/>'),
    SvgIcon("arrow-down", "向下", "导航", "底部 bottom", '<path d="M12 3v18m-7-7 7 7 7-7"/>'),
    SvgIcon("external-link", "外部链接", "导航", "跳转 新窗口 open", '<path d="M13 3h8v8M21 3 10 14M10 5H4v15h15v-6"/>'),
    SvgIcon("plus", "新增", "操作", "增加 添加 add", '<path d="M12 4v16M4 12h16"/>'),
    SvgIcon("minus", "减少", "操作", "移除 subtract", '<path d="M4 12h16"/>'),
    SvgIcon("edit", "编辑", "操作", "修改 铅笔 pencil", '<path d="m4 15 12-12 5 5L9 20l-6 1 1-6Zm9-9 5 5"/>'),
    SvgIcon("trash", "删除", "操作", "垃圾桶 清空 delete", '<path d="M3 6h18M9 6V3h6v3M5 6l1 15h12l1-15M10 10v7M14 10v7"/>'),
    SvgIcon("copy", "复制", "操作", "拷贝 duplicate", '<rect x="8" y="8" width="13" height="13" rx="2"/><path d="M16 8V3H3v13h5"/>'),
    SvgIcon("refresh", "刷新", "操作", "重新加载 同步 reload sync", '<path d="M20 9a8 8 0 0 0-14-3L3 9m0-6v6h6M4 15a8 8 0 0 0 14 3l3-3m0 6v-6h-6"/>'),
    SvgIcon("undo", "撤销", "操作", "回退 restore", '<path d="M3 4v7h7M3 11l5-5a8 8 0 1 1 4 15"/>'),
    SvgIcon("filter", "筛选", "操作", "过滤 漏斗 funnel", '<path d="M3 4h18l-7 8v7l-4 2v-9L3 4Z"/>'),
    SvgIcon("file", "文件", "文件", "文档 document", '<path d="M5 3h9l5 5v13H5V3Zm9 0v6h5M8 13h8M8 17h6"/>'),
    SvgIcon("folder", "文件夹", "文件", "目录 directory", '<path d="M3 6V3h7l3 3h8v15H3V6Zm0 3h18"/>'),
    SvgIcon("save", "保存", "文件", "存储 磁盘 disk", '<path d="M3 3h15l3 3v15H3V3Zm4 0v6h10V3M7 21v-8h10v8M14 5v2"/>'),
    SvgIcon("download", "下载", "文件", "导出 export", '<path d="M12 3v12m-5-5 5 5 5-5M3 16v5h18v-5"/>'),
    SvgIcon("upload", "上传", "文件", "导入 import", '<path d="M12 15V3M7 8l5-5 5 5M3 16v5h18v-5"/>'),
    SvgIcon("image", "图片", "文件", "相册 照片 picture photo", '<rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8" cy="8" r="2"/><path d="m3 18 6-6 4 4 4-6 4 6"/>'),
    SvgIcon("clipboard", "剪贴板", "文件", "粘贴 paste", '<path d="M8 5H4v16h16V5h-4M8 11h8M8 15h6"/><rect x="8" y="3" width="8" height="4" rx="1"/>'),
    SvgIcon("link", "链接", "文件", "连接 附件 url", '<path d="m9 7 3-3a5 5 0 0 1 8 8l-3 3M7 9l-3 3a5 5 0 0 0 8 8l3-3M8 16l8-8"/>'),
    SvgIcon("user", "用户", "用户", "账号 个人 头像 account profile", '<circle cx="12" cy="7" r="4"/><path d="M4 21v-2a8 8 0 0 1 16 0v2"/>'),
    SvgIcon("users", "用户组", "用户", "团队 多人 group team", '<circle cx="9" cy="7" r="3"/><path d="M3 21v-3a6 6 0 0 1 12 0v3M16 4a3 3 0 0 1 0 6M18 13a6 6 0 0 1 3 5v3"/>'),
    SvgIcon("user-plus", "添加用户", "用户", "注册 邀请 register invite", '<circle cx="9" cy="7" r="4"/><path d="M2 21v-2a7 7 0 0 1 14 0v2M19 7v8M15 11h8"/>'),
    SvgIcon("login", "登录", "用户", "进入 sign in", '<path d="M14 3h7v18h-7M3 12h13m-5-5 5 5-5 5"/>'),
    SvgIcon("logout", "退出", "用户", "注销 sign out", '<path d="M10 3H3v18h7M8 12h13m-5-5 5 5-5 5"/>'),
    SvgIcon("lock", "锁定", "用户", "密码 加密 安全 password", '<rect x="4" y="10" width="16" height="11" rx="2"/><path d="M7 10V7a5 5 0 0 1 10 0v3M12 14v3"/>'),
    SvgIcon("unlock", "解锁", "用户", "开放 密码 open", '<rect x="4" y="10" width="16" height="11" rx="2"/><path d="M7 10V7a5 5 0 0 1 10 0M12 14v3"/>'),
    SvgIcon("shield", "安全", "用户", "保护 盾牌 security", '<path d="M12 2 3 6v6c0 5 9 10 9 10s9-5 9-10V6l-9-4ZM8 12l3 3 5-6"/>'),
    SvgIcon("message", "消息", "消息", "评论 聊天 对话 comment chat", '<path d="M3 3h18v14H9l-6 4V3ZM7 8h10M7 12h7"/>'),
    SvgIcon("mail", "邮件", "消息", "信封 私信 email inbox", '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 6 9 7 9-7"/>'),
    SvgIcon("send", "发送", "消息", "提交 纸飞机 submit", '<path d="m2 3 20 9-20 9 4-9-4-9Zm4 9h16"/>'),
    SvgIcon("bell", "通知", "消息", "铃铛 提醒 notification", '<path d="M4 17h16l-2-4V9a6 6 0 0 0-12 0v4l-2 4ZM9 21h6M12 1v2"/>'),
    SvgIcon("phone", "电话", "消息", "通话 联系 call", '<path d="m4 3 4-1 3 5-3 3a17 17 0 0 0 6 6l3-3 5 3-1 4C12 23 1 12 4 3Z"/>'),
    SvgIcon("share", "分享", "消息", "转发 share", '<circle cx="5" cy="12" r="3"/><circle cx="19" cy="5" r="3"/><circle cx="19" cy="19" r="3"/><path d="m8 11 8-5M8 13l8 5"/>'),
    SvgIcon("heart", "喜欢", "消息", "收藏 爱心 like favorite", '<path d="M12 21 3 12a6 6 0 0 1 9-8 6 6 0 0 1 9 8l-9 9Z"/>'),
    SvgIcon("star", "星标", "消息", "收藏 评分 favorite rating", '<path d="m12 2 3 7 7 1-5 5 1 7-6-3-6 3 1-7-5-5 7-1 3-7Z"/>'),
    SvgIcon("check", "完成", "状态", "确认 成功 对勾 ok success", '<path d="m3 12 6 6L21 5"/>'),
    SvgIcon("close", "关闭", "状态", "取消 叉号 cancel x", '<path d="m5 5 14 14M19 5 5 19"/>'),
    SvgIcon("info", "信息", "状态", "提示 说明 information", '<circle cx="12" cy="12" r="10"/><path d="M12 11v6M12 7v.1"/>'),
    SvgIcon("help", "帮助", "状态", "问号 问题 question", '<circle cx="12" cy="12" r="10"/><path d="M9 8a3 3 0 1 1 5 2c-2 1-2 2-2 3M12 17v.1"/>'),
    SvgIcon("warning", "警告", "状态", "注意 感叹号 alert", '<path d="M12 2 1 21h22L12 2ZM12 9v5M12 18v.1"/>'),
    SvgIcon("error", "错误", "状态", "失败 禁止 failure", '<circle cx="12" cy="12" r="10"/><path d="m8 8 8 8m0-8-8 8"/>'),
    SvgIcon("clock", "时钟", "状态", "时间 历史 time history", '<circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 3"/>'),
    SvgIcon("calendar", "日历", "状态", "日期 排期 date schedule", '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M7 2v6M17 2v6M3 10h18M7 14h2m3 0h2m3 0h.1M7 18h2m3 0h2"/>'),
    SvgIcon("play", "播放", "媒体", "开始 运行 start run", '<path d="m6 3 15 9-15 9V3Z"/>'),
    SvgIcon("pause", "暂停", "媒体", "停止 pause", '<path d="M6 3h4v18H6V3Zm8 0h4v18h-4V3Z"/>'),
    SvgIcon("stop", "停止", "媒体", "结束 stop", '<rect x="4" y="4" width="16" height="16" rx="1"/>'),
    SvgIcon("volume", "音量", "媒体", "声音 喇叭 sound", '<path d="M3 9h4l5-5v16l-5-5H3V9Zm13-1a6 6 0 0 1 0 8m3-11a10 10 0 0 1 0 14"/>'),
    SvgIcon("camera", "相机", "媒体", "拍照 截图 capture", '<path d="M3 6h4l2-3h6l2 3h4v15H3V6Z"/><circle cx="12" cy="13" r="4"/>'),
    SvgIcon("video", "视频", "媒体", "录像 会议 movie", '<rect x="2" y="5" width="13" height="14" rx="2"/><path d="m15 9 7-4v14l-7-4"/>'),
    SvgIcon("music", "音乐", "媒体", "音符 歌曲 audio", '<path d="M9 18V5l12-3v13M9 9l12-3"/><ellipse cx="5" cy="18" rx="4" ry="3"/><ellipse cx="17" cy="15" rx="4" ry="3"/>'),
    SvgIcon("microphone", "麦克风", "媒体", "语音 录音 mic record", '<rect x="9" y="2" width="6" height="13" rx="3"/><path d="M5 10v2a7 7 0 0 0 14 0v-2M12 19v3M8 22h8"/>'),
    SvgIcon("settings", "设置", "工具", "参数 调节 配置 config", '<path d="M3 6h4m6 0h8M3 12h10m6 0h2M3 18h4m6 0h8"/><circle cx="10" cy="6" r="3"/><circle cx="16" cy="12" r="3"/><circle cx="10" cy="18" r="3"/>'),
    SvgIcon("chart", "统计", "工具", "数据 图表 分析 analytics", '<path d="M3 3v18h18M7 17v-5M12 17V7M17 17V4"/>'),
    SvgIcon("grid", "网格", "工具", "应用 九宫格 dashboard", '<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>'),
    SvgIcon("database", "数据库", "工具", "数据 存储 storage", '<ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M3 5v14c0 4 18 4 18 0V5M3 12c0 4 18 4 18 0"/>'),
    SvgIcon("globe", "网络", "工具", "全球 网站 地球 web internet", '<circle cx="12" cy="12" r="10"/><ellipse cx="12" cy="12" rx="4" ry="10"/><path d="M2 12h20M4 6h16M4 18h16"/>'),
    SvgIcon("location", "位置", "工具", "定位 地图 map pin", '<path d="M12 22S4 14 4 9a8 8 0 0 1 16 0c0 5-8 13-8 13Z"/><circle cx="12" cy="9" r="3"/>'),
    SvgIcon("code", "代码", "工具", "开发 编程 program", '<path d="m7 6-5 6 5 6M17 6l5 6-5 6M14 3l-4 18"/>'),
    SvgIcon("eye", "查看", "工具", "预览 可见 显示 preview visible", '<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8S1 12 1 12Z"/><circle cx="12" cy="12" r="3"/>'),
)

ICON_BY_KEY = {icon.key: icon for icon in ICONS}
CATEGORIES = tuple(dict.fromkeys(icon.category for icon in ICONS))


def search_icons(query: str = "", category: str = "") -> tuple[SvgIcon, ...]:
    terms = query.casefold().split()
    return tuple(icon for icon in ICONS if (not category or icon.category == category)
                 and all(term in f"{icon.key} {icon.label} {icon.category} {icon.keywords}".casefold()
                         for term in terms))


def icon_svg(key: str, color: str = "#cccccc", stroke_width: float = 1.8) -> str:
    icon = ICON_BY_KEY[key]
    if not re.fullmatch(r"#[0-9a-fA-F]{6}", color):
        raise ValueError("图标颜色必须是六位十六进制颜色。")
    if not math.isfinite(stroke_width) or not 0.5 <= stroke_width <= 4:
        raise ValueError("图标线宽必须在 0.5 到 4 之间。")
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" '
            f'fill="none" stroke="{color.lower()}" stroke-width="{stroke_width:g}" '
            f'stroke-linecap="round" stroke-linejoin="round" data-uiplay-icon="{key}">'
            f'{icon.body}</svg>')


def identify_icon(data: str) -> tuple[str, str, float] | None:
    """只认完整匹配的内置内容，手改过的图形保持为自定义 SVG。"""
    if len(data) > 100_000 or "<!DOCTYPE" in data.upper() or "<!ENTITY" in data.upper():
        return None
    try:
        root = ElementTree.fromstring(data)
        key, color = root.get("data-uiplay-icon", ""), root.get("stroke", "")
        width = float(root.get("stroke-width", "0"))
        if key in ICON_BY_KEY and data == icon_svg(key, color, width):
            return key, color, width
    except (ElementTree.ParseError, ValueError):
        pass
    return None
