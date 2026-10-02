"""Build the study-guide PDF from the Markdown docs and the source files.

DRY: the PDFs have no content of their own. They render docs/*.md and append the
real source files, so they can never drift from the repository. Rebuild after any change:

    pip install reportlab svglib
    python scripts/build_pdf.py            # every edition
    python scripts/build_pdf.py hinglish   # one edition (see EDITIONS)
"""
import datetime
import re
import subprocess
import sys
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    KeepTogether, PageBreak, Paragraph, Preformatted, SimpleDocTemplate, Spacer, Table, TableStyle,
)
from reportlab.platypus.tableofcontents import TableOfContents
from svglib.svglib import svg2rlg

ROOT = Path(__file__).resolve().parent.parent
TITLE = "Kubernetes-Based Application Deployment and Monitoring"
EDITIONS = {
    "english": {
        "output": "docs/k8s-flask-monitoring-guide.pdf",
        "chapters": ["docs/guide.md", "docs/troubleshooting.md", "docs/interview-prep.md"],
        "subtitle": "Study guide: build, operate, monitor, troubleshoot and explain the project",
        "contents": "Contents",
        "appendix": ("Appendix - Source Files",
                     "Every file below is included directly from the repository, so it always matches "
                     "the code you run. The guide chapters explain why each part exists."),
    },
    "hinglish": {
        "output": "docs/k8s-flask-monitoring-guide-hinglish.pdf",
        "chapters": sorted(str(p.relative_to(ROOT)) for p in (ROOT / "docs" / "hinglish").glob("*.md")),
        "subtitle": "Hinglish study guide: basics se lekar interview tak, sab kuch",
        "contents": "Vishay Suchi (Contents)",
        "appendix": ("Appendix - Poora Source Code",
                     "Neeche ki har file seedha repository se li gayi hai, isliye yeh hamesha asli code se "
                     "match karti hai. Har file ka matlab Part 5 mein samjhaya gaya hai."),
    },
}
SOURCE_FILES = [
    "app/config.py", "app/app.py", "app/gunicorn.conf.py", "app/requirements.txt",
    "Dockerfile", ".dockerignore",
    "k8s/configmap.yaml", "k8s/deployment.yaml", "k8s/service.yaml",
    "monitoring/00-namespace.yaml", "monitoring/10-prometheus.yaml", "monitoring/20-grafana.yaml",
    "monitoring/dashboards/flask-app.json",
    "scripts/deploy.sh", "scripts/load.sh", "scripts/teardown.sh",
    "tests/test_app.py", "tests/test_manifests.py",
]
PAGE_W, PAGE_H = A4
MARGIN = 18 * mm
CONTENT_W = PAGE_W - 2 * MARGIN
CODE_WRAP = 92
CODE_CHUNK = 60  # lines per code box


# ---------- fonts (use Windows/Linux TrueType fonts when present for wider character support)
def register_fonts():
    candidates = {
        "Body": ["C:/Windows/Fonts/arial.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"],
        "Body-Bold": ["C:/Windows/Fonts/arialbd.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"],
        "Mono": ["C:/Windows/Fonts/consola.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"],
    }
    fallback = {"Body": "Helvetica", "Body-Bold": "Helvetica-Bold", "Mono": "Courier"}
    names = {}
    for name, paths in candidates.items():
        path = next((p for p in paths if Path(p).exists()), None)
        if path:
            pdfmetrics.registerFont(TTFont(name, path))
            names[name] = name
        else:
            names[name] = fallback[name]
    pdfmetrics.registerFontFamily("Body", normal=names["Body"], bold=names["Body-Bold"],
                                  italic=names["Body"], boldItalic=names["Body-Bold"])
    return names


FONTS = register_fonts()
BLUE = colors.HexColor("#1f6feb")
INK = colors.HexColor("#24292f")
MUTED = colors.HexColor("#57606a")
CODE_BG = colors.HexColor("#f6f8fa")
RULE = colors.HexColor("#d0d7de")

base = getSampleStyleSheet()


def style(name, parent="BodyText", **kw):
    kw.setdefault("fontName", FONTS["Body"])
    kw.setdefault("textColor", INK)
    return ParagraphStyle(name, parent=base[parent], **kw)


S = {
    "body": style("body", fontSize=10, leading=14.5, spaceAfter=5),
    "h1": style("h1", "Heading1", fontName=FONTS["Body-Bold"], fontSize=22, leading=27,
                textColor=BLUE, spaceAfter=10),
    "h2": style("h2", "Heading2", fontName=FONTS["Body-Bold"], fontSize=15, leading=19,
                spaceBefore=14, spaceAfter=6, textColor=BLUE, keepWithNext=1),
    "h3": style("h3", "Heading3", fontName=FONTS["Body-Bold"], fontSize=12, leading=15,
                spaceBefore=10, spaceAfter=4, keepWithNext=1),
    "bullet": style("bullet", fontSize=10, leading=14, leftIndent=14, bulletIndent=4, spaceAfter=2),
    "quote": style("quote", fontSize=10, leading=14, leftIndent=10, textColor=MUTED,
                   borderColor=BLUE, borderWidth=0, borderPadding=4),
    "cell": style("cell", fontSize=8.5, leading=11),
    "cellhead": style("cellhead", fontName=FONTS["Body-Bold"], fontSize=8.5, leading=11),
    "code": ParagraphStyle("code", fontName=FONTS["Mono"], fontSize=8, leading=10.2, textColor=INK),
    "cover_title": style("cover_title", "Title", fontName=FONTS["Body-Bold"], fontSize=26, leading=32,
                         textColor=BLUE, alignment=TA_CENTER),
    "cover_sub": style("cover_sub", fontSize=13, leading=18, alignment=TA_CENTER, textColor=MUTED),
    "toc_title": style("toc_title", "Heading1", fontName=FONTS["Body-Bold"], fontSize=20, textColor=BLUE),
}


# ---------- inline Markdown -> ReportLab mini-HTML
def inline(text):
    parts = re.split(r"(`[^`]+`)", text)
    out = []
    for part in parts:
        if part.startswith("`") and part.endswith("`") and len(part) > 1:
            code = escape(part[1:-1])
            out.append(f'<font name="{FONTS["Mono"]}" color="#953800">{code}</font>')
            continue
        part = escape(part)
        part = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", part)
        part = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", link, part)
        out.append(part)
    return "".join(out)


def escape(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def link(match):
    text, target = match.groups()
    if target.startswith("http"):
        return f'<link href="{target}" color="#1f6feb">{text}</link>'
    return text  # in-repo links: the content is already inside this PDF


# ---------- block-level Markdown
class Heading(Paragraph):
    """Paragraph that registers itself in the table of contents."""

    def __init__(self, text, level):
        self.level = level
        super().__init__(inline(text), S[f"h{min(level, 2) + 1}"])
        self.toc_text = text.replace("`", "")


def code_block(lines):
    wrapped = []
    for line in lines:
        line = line.expandtabs(4)
        while len(line) > CODE_WRAP:
            wrapped.append(line[:CODE_WRAP])
            line = "    " + line[CODE_WRAP:]
        wrapped.append(line)
    # A table cell cannot break across pages, so long listings become several boxes.
    chunks = [wrapped[i:i + CODE_CHUNK] for i in range(0, len(wrapped), CODE_CHUNK)] or [[" "]]
    blocks = []
    for chunk in chunks:
        table = Table([[Preformatted("\n".join(chunk), S["code"])]], colWidths=[CONTENT_W])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), CODE_BG),
            ("BOX", (0, 0), (-1, -1), 0.5, RULE),
            ("LEFTPADDING", (0, 0), (-1, -1), 6), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        blocks.append(table)
    return blocks + [Spacer(1, 6)]


def md_table(rows):
    # Split on "|" but not on an escaped "\|" (a literal pipe inside a cell).
    cells = [[c.strip().replace(r"\|", "|") for c in re.split(r"(?<!\\)\|", row.strip().strip("|"))]
             for row in rows]
    header, body = cells[0], [r for r in cells[2:]]
    widths = [max(len(r[i]) if i < len(r) else 0 for r in cells[:1] + body) for i in range(len(header))]
    widths = [min(max(w, 10), 60) for w in widths]
    col_w = [CONTENT_W * w / sum(widths) for w in widths]
    data = [[Paragraph(inline(c), S["cellhead"]) for c in header]]
    data += [[Paragraph(inline(c), S["cell"]) for c in r] for r in body]
    table = Table(data, colWidths=col_w, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#ddf4ff")),
        ("GRID", (0, 0), (-1, -1), 0.4, RULE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#fafbfc")]),
        ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return [table, Spacer(1, 8)]


def image(path, max_w=CONTENT_W, max_h=150 * mm):
    drawing = svg2rlg(str(path))
    scale = min(max_w / drawing.width, max_h / drawing.height)
    drawing.width, drawing.height = drawing.width * scale, drawing.height * scale
    drawing.scale(scale, scale)
    return drawing


def markdown(path):
    lines = path.read_text(encoding="utf-8").splitlines()
    story, para, i = [], [], 0

    def flush():
        if para:
            story.append(Paragraph(inline(" ".join(para)), S["body"]))
            para.clear()

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if stripped.startswith("```"):
            flush()
            j = i + 1
            while j < len(lines) and not lines[j].strip().startswith("```"):
                j += 1
            story += code_block(lines[i + 1:j])
            i = j + 1
            continue
        if stripped.startswith("|"):
            flush()
            j = i
            while j < len(lines) and lines[j].strip().startswith("|"):
                j += 1
            story += md_table(lines[i:j])
            i = j
            continue
        heading = re.match(r"(#{1,4}) (.+)", stripped)
        image_ref = re.match(r"!\[[^\]]*\]\(([^)]+)\)", stripped)
        bullet = re.match(r"[-*] (.+)", stripped)
        numbered = re.match(r"(\d+)\. (.+)", stripped)
        if heading:
            flush()
            level = len(heading.group(1)) - 1
            story.append(Heading(heading.group(2), level))
        elif image_ref:
            flush()
            story += [image(path.parent / image_ref.group(1)), Spacer(1, 8)]
        elif bullet:
            flush()
            story.append(Paragraph(inline(bullet.group(1)), S["bullet"], bulletText="\u2022"))
        elif numbered:
            flush()
            story.append(Paragraph(inline(numbered.group(2)), S["bullet"], bulletText=f"{numbered.group(1)}."))
        elif stripped.startswith(">"):
            flush()
            story.append(Paragraph(inline(stripped.lstrip("> ")), S["quote"]))
        elif not stripped:
            flush()
        else:
            para.append(stripped)
        i += 1
    flush()
    return story


# ---------- document assembly
class GuideDoc(SimpleDocTemplate):
    def afterFlowable(self, flowable):
        if isinstance(flowable, Heading) and flowable.level <= 1:
            key = f"h{id(flowable)}"
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(flowable.toc_text, key, level=flowable.level)
            self.notify("TOCEntry", (flowable.level, flowable.toc_text, self.page, key))


def decorate(canvas, doc):
    if doc.page == 1:
        return
    canvas.saveState()
    canvas.setFont(FONTS["Body"], 8)
    canvas.setFillColor(MUTED)
    canvas.drawString(MARGIN, 10 * mm, TITLE)
    canvas.drawRightString(PAGE_W - MARGIN, 10 * mm, f"Page {doc.page}")
    canvas.setStrokeColor(RULE)
    canvas.line(MARGIN, 13 * mm, PAGE_W - MARGIN, 13 * mm)
    canvas.restoreState()


def git_author():
    try:
        return subprocess.run(["git", "config", "user.name"], cwd=ROOT, capture_output=True,
                              text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return ""


def cover(edition):
    author = git_author()
    story = [
        Spacer(1, 30 * mm),
        Paragraph(TITLE, S["cover_title"]),
        Spacer(1, 6 * mm),
        Paragraph("Docker &middot; Minikube &middot; Prometheus &middot; Grafana &middot; Python Flask", S["cover_sub"]),
        Spacer(1, 4 * mm),
        Paragraph(edition["subtitle"], S["cover_sub"]),
        Spacer(1, 14 * mm),
        image(ROOT / "docs" / "architecture.svg", max_h=110 * mm),
        Spacer(1, 14 * mm),
    ]
    if author:
        story.append(Paragraph(author, S["cover_sub"]))
    story += [Paragraph(datetime.date.today().strftime("%B %Y"), S["cover_sub"]), PageBreak()]
    return story


def contents(edition):
    toc = TableOfContents()
    toc.levelStyles = [
        style("toc0", fontName=FONTS["Body-Bold"], fontSize=11, leading=16, spaceBefore=6),
        style("toc1", fontSize=9.5, leading=13, leftIndent=14),
    ]
    return [Paragraph(edition["contents"], S["toc_title"]), toc, PageBreak()]


def appendix(edition):
    title, intro = edition["appendix"]
    story = [Heading(title, 0), Paragraph(intro, S["body"])]
    for rel in SOURCE_FILES:
        text = (ROOT / rel).read_text(encoding="utf-8")
        first, *rest = code_block(text.splitlines())
        story += [KeepTogether([Heading(rel, 2), first]), *rest]
    return story


def build(name):
    edition = EDITIONS[name]
    story = cover(edition) + contents(edition)
    for chapter in edition["chapters"]:
        story += markdown(ROOT / chapter) + [PageBreak()]
    story += appendix(edition)
    output = ROOT / edition["output"]
    doc = GuideDoc(str(output), pagesize=A4, leftMargin=MARGIN, rightMargin=MARGIN,
                   topMargin=MARGIN, bottomMargin=20 * mm,
                   title=f"{TITLE} - Study Guide ({name})", author=git_author())
    doc.multiBuild(story, onFirstPage=decorate, onLaterPages=decorate)
    print(f"Wrote {output.relative_to(ROOT)}")


if __name__ == "__main__":
    for edition_name in sys.argv[1:] or EDITIONS:
        build(edition_name)
