"""SVG 编辑器和项目校验共用的文本边界。"""

from xml.etree import ElementTree

from .errors import require


def validate_svg(data: str) -> None:
    require(isinstance(data, str) and len(data) <= 100_000, "SVG 内容必须是长度合理的文本。")
    require("<!DOCTYPE" not in data.upper() and "<!ENTITY" not in data.upper(), "SVG 不支持文档类型或实体声明。")
    try:
        root = ElementTree.fromstring(data)
        require(root.tag in {"svg", "{http://www.w3.org/2000/svg}svg"}, "SVG 内容必须以 svg 元素为根。")
    except (ElementTree.ParseError, UnicodeError):
        require(False, "SVG 内容不是有效的 XML。")
