import os
import re
import sys
from pathlib import Path

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, HRFlowable
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.colors import HexColor
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.units import mm
from reportlab.pdfgen.canvas import Canvas
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
SRC = Path(os.environ.get("EI_SOURCE", ROOT / "paper.md"))
OUT = Path(os.environ.get("EI_OUTPUT", ROOT / "dist" / "Execution_Intelligence_Judgement_Carried_into_Execution_v1.0.pdf"))
DOI = os.environ.get("PUBLICATION_DOI", "Pending reservation")
PUBLICATION_DATE = os.environ.get("PUBLICATION_DATE", "August 2026")

OUT.parent.mkdir(parents=True, exist_ok=True)

font_candidates = {
    "Serif": ["/usr/share/fonts/truetype/noto/NotoSerif-Regular.ttf", "/usr/share/fonts/opentype/noto/NotoSerif-Regular.ttf"],
    "SerifBold": ["/usr/share/fonts/truetype/noto/NotoSerif-Bold.ttf", "/usr/share/fonts/opentype/noto/NotoSerif-Bold.ttf"],
    "SerifItalic": ["/usr/share/fonts/truetype/noto/NotoSerif-Italic.ttf", "/usr/share/fonts/opentype/noto/NotoSerif-Italic.ttf"],
    "Sans": ["/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf", "/usr/share/fonts/opentype/noto/NotoSans-Regular.ttf"],
    "SansBold": ["/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf", "/usr/share/fonts/opentype/noto/NotoSans-Bold.ttf"],
}

for name, candidates in font_candidates.items():
    match = next((p for p in candidates if Path(p).exists()), None)
    if not match:
        raise RuntimeError(f"Required Noto font not found for {name}. Install fonts-noto-core.")
    pdfmetrics.registerFont(TTFont(name, match))

ACCENT = HexColor("#9B6B43")
INK = HexColor("#191919")
MUTED = HexColor("#66615D")
LIGHT = HexColor("#D8D2CB")

styles = {
    "body": ParagraphStyle("body", fontName="Serif", fontSize=9.85, leading=12.35, textColor=INK, spaceAfter=5.3, allowWidows=0, allowOrphans=0),
    "h2": ParagraphStyle("h2", fontName="SansBold", fontSize=16.2, leading=18.6, textColor=INK, spaceBefore=1, spaceAfter=6, keepWithNext=True),
    "h3": ParagraphStyle("h3", fontName="SansBold", fontSize=11.2, leading=13.6, textColor=INK, spaceBefore=6, spaceAfter=3, keepWithNext=True),
    "quote": ParagraphStyle("quote", fontName="SerifBold", fontSize=11.0, leading=13.8, textColor=INK, leftIndent=8 * mm, rightIndent=4 * mm, borderColor=ACCENT, borderWidth=1.3, borderPadding=(2, 0, 2, 7), spaceBefore=4, spaceAfter=7),
    "bullet": ParagraphStyle("bullet", fontName="Serif", fontSize=9.75, leading=12.1, textColor=INK, leftIndent=6 * mm, firstLineIndent=-3 * mm, spaceAfter=1.8),
    "num": ParagraphStyle("num", fontName="Serif", fontSize=9.75, leading=12.1, textColor=INK, leftIndent=6.5 * mm, firstLineIndent=-4 * mm, spaceAfter=2),
    "ref": ParagraphStyle("ref", fontName="Serif", fontSize=9.0, leading=11.25, textColor=INK, spaceAfter=5),
}


def inline(text: str) -> str:
    text = text.strip().replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = re.sub(r"(https?://[^\s<]+)", r'<link href="\1" color="#6E4E36">\1</link>', text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"(?<!\*)\*([^*]+?)\*(?!\*)", r"<i>\1</i>", text)
    return text


def parse(md: str, ref: bool = False):
    lines = md.strip().splitlines()
    out = []
    i = 0
    while i < len(lines):
        st = lines[i].strip()
        if not st or st == "---":
            i += 1
            continue
        if st.startswith("## "):
            out.append(Paragraph(inline(st[3:]), styles["h2"]))
            i += 1
            continue
        if st.startswith("### "):
            out.append(Paragraph(inline(st[4:]), styles["h3"]))
            i += 1
            continue
        if st.startswith("> "):
            q = []
            while i < len(lines) and lines[i].strip().startswith("> "):
                q.append(lines[i].strip()[2:])
                i += 1
            out.append(Paragraph(inline(" ".join(q)), styles["quote"]))
            continue
        if st.startswith("- "):
            while i < len(lines) and lines[i].strip().startswith("- "):
                out.append(Paragraph("• " + inline(lines[i].strip()[2:]), styles["bullet"]))
                i += 1
            continue
        if re.match(r"^\d+\. ", st):
            while i < len(lines) and re.match(r"^\d+\. ", lines[i].strip()):
                m = re.match(r"^(\d+)\.\s+(.*)$", lines[i].strip())
                out.append(Paragraph(m.group(1) + ". " + inline(m.group(2)), styles["num"]))
                i += 1
            continue
        para = [st]
        i += 1
        while i < len(lines):
            nxt = lines[i].strip()
            if not nxt or nxt == "---" or nxt.startswith("## ") or nxt.startswith("### ") or nxt.startswith("> ") or nxt.startswith("- ") or re.match(r"^\d+\. ", nxt):
                break
            para.append(nxt)
            i += 1
        out.append(Paragraph(inline(" ".join(para)), styles["ref"] if ref else styles["body"]))
    return out


raw = SRC.read_text(encoding="utf-8")
parts = re.split(r"(?m)^## ", raw)
sec = {}
for part in parts[1:]:
    lines = part.splitlines()
    title = lines[0].strip()
    sec[title] = "## " + part.strip()

required = [
    "Abstract",
    "1. The question underneath execution",
    "2. Working definition",
    "3. Terminology and contribution boundary",
    "4. Judgement continuity",
    "5. A connected lens for execution",
    "6. Execution drift and deliberate adaptation",
    "7. Three tensions inside intelligent execution",
    "8. Relationship to established organisational thinking",
    "9. Technology as a particularly useful context",
    "10. Relationship to Reflection Core",
    "11. What Execution Intelligence is not",
    "12. Initial propositions for research",
    "13. Research agenda and methods",
    "14. Evidence and limitations",
    "15. Conclusion",
    "Publication note",
    "About Cralgo Research",
    "References",
]
missing = [x for x in required if x not in sec]
if missing:
    raise RuntimeError(f"paper.md is missing required sections: {missing}")


def split_at(text: str, marker: str):
    a, b = text.split(marker, 1)
    return a, marker + b


s4a, s4b = split_at(sec["4. Judgement continuity"], "The proposed object of attention is **judgement continuity**")
s5a, s5b = split_at(sec["5. A connected lens for execution"], "### Structure")
s8a, s8b = split_at(sec["8. Relationship to established organisational thinking"], "### 8.3 Organisational learning")

pages = [
    sec["Abstract"],
    sec["1. The question underneath execution"] + "\n\n" + sec["2. Working definition"],
    sec["3. Terminology and contribution boundary"] + "\n\n" + s4a,
    "## 4. Judgement continuity\n\n" + s4b + "\n\n" + s5a,
    "## 5. A connected lens for execution\n\n" + s5b + "\n\n" + sec["6. Execution drift and deliberate adaptation"],
    sec["7. Three tensions inside intelligent execution"] + "\n\n" + s8a,
    "## 8. Relationship to established organisational thinking\n\n" + s8b + "\n\n" + sec["9. Technology as a particularly useful context"],
    sec["10. Relationship to Reflection Core"] + "\n\n" + sec["11. What Execution Intelligence is not"] + "\n\n" + sec["12. Initial propositions for research"],
    sec["13. Research agenda and methods"] + "\n\n" + sec["14. Evidence and limitations"],
    sec["15. Conclusion"] + "\n\n" + sec["Publication note"] + "\n\n" + sec["About Cralgo Research"],
    sec["References"] + f"\n\n## Citation and release status\n\n**Version:** 1.0  \n**DOI:** {DOI}  \n**Licence:** CC BY-NC-ND 4.0\n\nThe DOI shown above identifies the v1.0 publication record on Zenodo.\n\n© 2026 Cralgo Innovations (OPC) Pvt. Ltd.",
]

story = [
    Spacer(1, 18 * mm),
    Paragraph("CRALGO RESEARCH", ParagraphStyle("ey", fontName="SansBold", fontSize=9.3, leading=11, textColor=ACCENT, tracking=1.5, spaceAfter=12)),
    HRFlowable(width=28 * mm, thickness=1.2, color=ACCENT, spaceAfter=15),
    Paragraph("Execution Intelligence", ParagraphStyle("ct", fontName="SansBold", fontSize=30, leading=33, textColor=INK, spaceAfter=5)),
    Paragraph("Judgement Carried into Execution", ParagraphStyle("cs", fontName="Serif", fontSize=20, leading=24, textColor=INK, spaceAfter=16)),
    Paragraph("A Cralgo Concept Paper", ParagraphStyle("ci", fontName="SerifItalic", fontSize=11.5, leading=14, textColor=MUTED, spaceAfter=22)),
    Spacer(1, 47 * mm),
    Paragraph("<b>Anil Kabir Kumar</b><br/>Cralgo<br/>Cralgo Innovations (OPC) Pvt. Ltd.", ParagraphStyle("cm", fontName="Sans", fontSize=9.3, leading=13, textColor=INK, spaceAfter=14)),
    Paragraph(f"Version 1.0  |  {PUBLICATION_DATE}<br/><b>DOI:</b> {DOI}", ParagraphStyle("cm2", fontName="Sans", fontSize=8.8, leading=12, textColor=MUTED)),
    PageBreak(),
]

for idx, page in enumerate(pages):
    story.extend(parse(page, ref=(idx == 10)))
    if idx < len(pages) - 1:
        story.append(PageBreak())


class NumCanvas(Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.saved = []

    def showPage(self):
        self.saved.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total = len(self.saved)
        for state in self.saved:
            self.__dict__.update(state)
            self.footer(total)
            Canvas.showPage(self)
        Canvas.save(self)

    def footer(self, total):
        n = self._pageNumber
        w, h = A4
        if n == 1:
            self.setFont("Sans", 7.5)
            self.setFillColor(MUTED)
            self.drawString(20 * mm, 11 * mm, "Cralgo Research")
            self.drawRightString(w - 20 * mm, 11 * mm, "Execution Intelligence")
        else:
            self.setStrokeColor(LIGHT)
            self.setLineWidth(0.35)
            self.line(18 * mm, 14 * mm, w - 18 * mm, 14 * mm)
            self.setFont("Sans", 7.4)
            self.setFillColor(MUTED)
            self.drawString(18 * mm, 9.3 * mm, "EXECUTION INTELLIGENCE  /  CRALGO RESEARCH")
            self.drawRightString(w - 18 * mm, 9.3 * mm, f"{n:02d}")


doc = SimpleDocTemplate(
    str(OUT),
    pagesize=A4,
    leftMargin=20 * mm,
    rightMargin=20 * mm,
    topMargin=18 * mm,
    bottomMargin=19 * mm,
    title="Execution Intelligence: Judgement Carried into Execution",
    author="Anil Kabir Kumar",
    subject="A Cralgo Concept Paper",
)
doc.build(story, canvasmaker=NumCanvas)

reader = PdfReader(str(OUT))
if len(reader.pages) != 12:
    raise RuntimeError(f"Publication PDF must be exactly 12 pages; generated {len(reader.pages)}")

print(f"Built {OUT} with 12 pages and DOI {DOI}")
