import html
import re

BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
ITALIC_RE = re.compile(r"(?<!\*)\*([^*\n]+)\*(?!\*)")
CODE_RE = re.compile(r"`([^`\n]+)`")
LINK_RE = re.compile(r"\[([^\]\n]+)\]\((https?://[^)\s]+)\)")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+)$")
LIST_RE = re.compile(r"^\s*[-*•]\s+(.+)$")


def _inline(text: str) -> str:
    text = CODE_RE.sub(r"<code>\1</code>", text)
    text = BOLD_RE.sub(r"<b>\1</b>", text)
    text = ITALIC_RE.sub(r"<i>\1</i>", text)
    text = LINK_RE.sub(r'<a href="\2">\1</a>', text)
    return text


def md_to_html(text: str) -> str:
    if not text:
        return ""
    escaped = html.escape(text, quote=False)
    code_blocks = []

    def stash_code_block(match):
        code_blocks.append(match.group(1).strip("\n"))
        return f"\x00{len(code_blocks) - 1}\x00"

    escaped = re.sub(r"```[^\n]*\n(.*?)```", stash_code_block, escaped, flags=re.S)

    lines = escaped.split("\n")
    out = []
    in_list = False
    for line in lines:
        heading = HEADING_RE.match(line)
        list_item = LIST_RE.match(line)
        if list_item:
            if not in_list:
                out.append("• " + _inline(list_item.group(1)))
                in_list = True
            else:
                out.append("• " + _inline(list_item.group(1)))
            continue
        in_list = False
        if heading:
            out.append("<b>" + _inline(heading.group(2).strip()) + "</b>")
        elif line.strip() == "":
            out.append("")
        else:
            out.append(_inline(line))

    result = "<br>".join(out)
    result = re.sub(r"(<br>){3,}", "<br><br>", result)

    def unstash(match):
        code = code_blocks[int(match.group(1))]
        return f"<pre>{code}</pre>"

    return re.sub(r"\x00(\d+)\x00", unstash, result)
