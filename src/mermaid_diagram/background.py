from __future__ import annotations

import html


def background_css(background: str) -> str:
    if background == "transparent":
        return "transparent"
    if background == "white":
        return "#ffffff"
    return background


def inject_svg_background(svg: str, color: str) -> str:
    insert_at = svg.find(">")
    if insert_at == -1:
        return svg
    rect = f'<rect width="100%" height="100%" fill="{html.escape(color, quote=True)}"/>'
    return svg[: insert_at + 1] + rect + svg[insert_at + 1 :]
