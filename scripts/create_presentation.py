from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_AUTO_SHAPE_TYPE, MSO_CONNECTOR
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "VendorLens_AI_20_Minute_Presentation.pptx"

NAVY = RGBColor(12, 35, 64)
DEEP = RGBColor(18, 60, 105)
BLUE = RGBColor(42, 127, 158)
TEAL = RGBColor(22, 154, 151)
VIOLET = RGBColor(112, 73, 190)
ORANGE = RGBColor(224, 126, 39)
GREEN = RGBColor(45, 134, 89)
RED = RGBColor(190, 62, 62)
INK = RGBColor(23, 32, 51)
MUTED = RGBColor(82, 104, 116)
PALE = RGBColor(243, 247, 249)
PALE_BLUE = RGBColor(232, 245, 248)
PALE_ORANGE = RGBColor(255, 245, 231)
WHITE = RGBColor(255, 255, 255)
LINE = RGBColor(184, 201, 211)

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
BLANK = prs.slide_layouts[6]


def shape(slide, x, y, w, h, fill, rounded=False, line_color=None, line_width=1):
    kind = MSO_AUTO_SHAPE_TYPE.ROUNDED_RECTANGLE if rounded else MSO_AUTO_SHAPE_TYPE.RECTANGLE
    item = slide.shapes.add_shape(kind, Inches(x), Inches(y), Inches(w), Inches(h))
    item.fill.solid()
    item.fill.fore_color.rgb = fill
    item.line.color.rgb = line_color or fill
    item.line.width = Pt(line_width)
    if rounded:
        item.adjustments[0] = 0.12
    return item


def line(slide, x1, y1, x2, y2, color=LINE, width=1.5):
    item = slide.shapes.add_connector(
        MSO_CONNECTOR.STRAIGHT,
        Inches(x1), Inches(y1), Inches(x2), Inches(y2),
    )
    item.line.color.rgb = color
    item.line.width = Pt(width)
    return item


def add_text(
    slide,
    value,
    x,
    y,
    w,
    h,
    size=18,
    color=INK,
    bold=False,
    align=PP_ALIGN.LEFT,
    font="Aptos",
    valign=MSO_ANCHOR.TOP,
):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    frame = box.text_frame
    frame.clear()
    frame.word_wrap = True
    frame.margin_left = Inches(0.04)
    frame.margin_right = Inches(0.04)
    frame.margin_top = Inches(0.02)
    frame.margin_bottom = Inches(0.02)
    frame.vertical_anchor = valign
    paragraph = frame.paragraphs[0]
    paragraph.alignment = align
    run = paragraph.add_run()
    run.text = value
    run.font.name = font
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    return box


def bullets(slide, items, x, y, w, h, size=15, color=INK, gap=0.0):
    box = add_text(slide, "", x, y, w, h, size=size, color=color)
    frame = box.text_frame
    frame.clear()
    for index, item in enumerate(items):
        paragraph = frame.paragraphs[0] if index == 0 else frame.add_paragraph()
        paragraph.text = f"•  {item}"
        paragraph.font.name = "Aptos"
        paragraph.font.size = Pt(size)
        paragraph.font.color.rgb = color
        paragraph.space_after = Pt(gap)
    return box


def footer(slide, number, timing):
    shape(slide, 0, 7.1, 13.333, 0.4, NAVY)
    add_text(slide, "VendorLens AI", 0.65, 7.18, 2.2, 0.16, 8.5, RGBColor(199, 220, 232), True)
    add_text(slide, timing, 4.4, 7.18, 4.5, 0.16, 8.5, RGBColor(199, 220, 232), False, PP_ALIGN.CENTER)
    add_text(slide, f"{number:02d}", 12.05, 7.18, 0.6, 0.16, 9, RGBColor(143, 207, 226), True, PP_ALIGN.RIGHT)


def title(slide, kicker, heading, subtitle, number, timing):
    shape(slide, 0, 0, 13.333, 7.5, WHITE)
    shape(slide, 0, 0, 13.333, 0.14, BLUE)
    add_text(slide, kicker.upper(), 0.7, 0.43, 3.9, 0.22, 10.5, BLUE, True)
    add_text(slide, heading, 0.7, 0.76, 11.9, 0.58, 28, NAVY, True, font="Aptos Display")
    add_text(slide, subtitle, 0.72, 1.45, 11.7, 0.42, 13, MUTED)
    footer(slide, number, timing)


def label(slide, value, x, y, w, color=BLUE):
    shape(slide, x, y, w, 0.34, color, True)
    add_text(slide, value.upper(), x, y + 0.08, w, 0.15, 9.5, WHITE, True, PP_ALIGN.CENTER)


def card(slide, x, y, w, h, heading, body, accent=BLUE, fill=PALE):
    shape(slide, x, y, w, h, fill, True, RGBColor(214, 226, 232))
    shape(slide, x, y, 0.08, h, accent, True, accent)
    add_text(slide, heading, x + 0.25, y + 0.22, w - 0.45, 0.27, 16, NAVY, True)
    add_text(slide, body, x + 0.25, y + 0.62, w - 0.45, h - 0.78, 11.2, MUTED)


# 1 — opening
slide = prs.slides.add_slide(BLANK)
shape(slide, 0, 0, 13.333, 7.5, NAVY)
shape(slide, 0, 0, 13.333, 0.16, ORANGE)
shape(slide, 8.8, 0.16, 4.533, 7.34, RGBColor(16, 53, 88))
add_text(slide, "VendorLens AI", 0.82, 1.08, 7.25, 0.72, 42, WHITE, True, font="Aptos Display")
add_text(
    slide,
    "Evidence-led supplier onboarding\nwith human approval",
    0.86, 2.02, 7.5, 1.18, 28, RGBColor(218, 235, 245), True, font="Aptos Display",
)
add_text(slide, "From application and documents to an auditable ERP record", 0.88, 3.55, 7.25, 0.32, 15.5, ORANGE, True)
add_text(
    slide,
    "React 19  •  FastAPI  •  PostgreSQL 18  •  ChromaDB  •  Tesseract  •  OpenRouter / Azure OpenAI",
    0.88, 5.77, 7.55, 0.45, 10.5, RGBColor(177, 207, 225),
)
add_text(slide, "As-built demo baseline  •  September 2026", 0.88, 6.28, 6.5, 0.22, 10, RGBColor(177, 207, 225))
for index, (name, color, note) in enumerate([
    ("SUPPLIER", BLUE, "apply + upload"),
    ("REVIEWER", VIOLET, "verify + decide"),
    ("ADMIN", ORANGE, "observe + maintain"),
    ("ERP", GREEN, "validate + create"),
]):
    y = 1.05 + index * 1.27
    shape(slide, 9.38, y, 3.05, 0.82, color, True)
    add_text(slide, name, 9.38, y + 0.14, 3.05, 0.22, 15, WHITE, True, PP_ALIGN.CENTER)
    add_text(slide, note, 9.38, y + 0.48, 3.05, 0.16, 9.2, RGBColor(229, 242, 249), False, PP_ALIGN.CENTER)
footer(slide, 1, "Opening | 0:00–0:40")


# 2 — product and users
slide = prs.slides.add_slide(BLANK)
title(
    slide,
    "Product",
    "One workflow, three workspaces, one accountable decision",
    "VendorLens replaces disconnected forms, files, searches, and handoffs with a traceable case record.",
    2,
    "Problem + product | 0:40–2:30",
)
roles = [
    (0.72, "Supplier portal", "Register • classify service\nUpload dynamic checklist\nSubmit • correct • resubmit\nAsk scoped onboarding questions", BLUE),
    (4.49, "Reviewer workbench", "Inspect originals + history\nVerify/correct AI fields\nRun policy checks + case chat\nApprove or reject", VIOLET),
    (8.26, "Administrator", "Manage demo profiles\nReset access safely\nInspect AI, OCR, RAG and ERP\noperational metrics", ORANGE),
]
for x, head, body, accent in roles:
    shape(slide, x, 2.18, 3.42, 3.34, WHITE, True, accent, 1.6)
    shape(slide, x, 2.18, 3.42, 0.62, accent, True)
    add_text(slide, head, x + 0.14, 2.38, 3.14, 0.22, 17, WHITE, True, PP_ALIGN.CENTER)
    bullets(slide, body.split("\n"), x + 0.28, 3.08, 2.95, 1.9, 13, INK, 7)
label(slide, "Non-negotiable", 5.15, 5.83, 1.55, RED)
add_text(slide, "AI assists; the reviewer remains the decision-maker.", 3.18, 6.31, 6.95, 0.28, 16, NAVY, True, PP_ALIGN.CENTER)


# 3 — lifecycle
slide = prs.slides.add_slide(BLANK)
title(
    slide,
    "Lifecycle",
    "The complete as-built supplier journey",
    "Readability, AI processing, evidence review, compliance, and approval are separate states—not one opaque score.",
    3,
    "Workflow | 2:30–4:10",
)
steps = [
    ("1", "Classify", "8 categories\n24 subcategories", BLUE),
    ("2", "Collect", "3 baseline +\npolicy evidence", TEAL),
    ("3", "Read", "native text +\nselective OCR", ORANGE),
    ("4", "Understand", "redact • extract\nembed • cite", VIOLET),
    ("5", "Review", "originals • fields\nchecks • feedback", DEEP),
    ("6", "Decide", "all checks PASS\nexplicit reviewer", GREEN),
    ("7", "Create", "idempotent\nERP record", NAVY),
]
for index, (num, head, body, accent) in enumerate(steps):
    x = 0.46 + index * 1.82
    shape(slide, x, 2.35, 1.48, 2.2, WHITE, True, accent, 1.4)
    shape(slide, x + 0.48, 2.1, 0.52, 0.52, accent, True)
    add_text(slide, num, x + 0.48, 2.24, 0.52, 0.16, 11, WHITE, True, PP_ALIGN.CENTER)
    add_text(slide, head, x + 0.08, 2.86, 1.32, 0.23, 14.5, NAVY, True, PP_ALIGN.CENTER)
    add_text(slide, body, x + 0.1, 3.38, 1.28, 0.63, 10.2, MUTED, False, PP_ALIGN.CENTER)
    if index < len(steps) - 1:
        add_text(slide, "→", x + 1.51, 3.14, 0.3, 0.28, 17, LINE, True, PP_ALIGN.CENTER)
shape(slide, 1.14, 5.15, 4.65, 0.95, PALE_ORANGE, True, ORANGE)
add_text(slide, "Correction loop", 1.38, 5.36, 1.45, 0.22, 15, ORANGE, True)
add_text(slide, "flag evidence → supplier replaces → resubmit", 2.8, 5.36, 2.65, 0.25, 11.2, MUTED)
shape(slide, 6.4, 5.15, 5.75, 0.95, PALE_BLUE, True, BLUE)
add_text(slide, "Submission survives AI failure", 6.68, 5.36, 2.72, 0.22, 15, BLUE, True)
add_text(slide, "safe failure state + reviewer retry", 9.45, 5.36, 2.3, 0.25, 11.2, MUTED)


# 4 — architecture
slide = prs.slides.add_slide(BLANK)
title(
    slide,
    "Architecture",
    "Application components with explicit trust boundaries",
    "Compose runs frontend, backend, PostgreSQL and mock ERP; Chroma is embedded persistence and AI is external.",
    4,
    "Architecture | 4:10–6:20",
)
components = [
    (0.72, 2.28, 2.2, "React / Nginx", "role UI\n/api reverse proxy", BLUE),
    (3.65, 2.08, 2.6, "FastAPI", "auth • workflow • OCR\nAI • policy • audit", TEAL),
    (9.92, 2.08, 2.45, "AI provider", "OpenRouter or Azure\nexternal boundary", ORANGE),
    (1.7, 4.18, 2.48, "PostgreSQL", "business source of truth\ncases • runs • audit", DEEP),
    (5.08, 4.18, 2.48, "ChromaDB", "embedded persistent client\nsupplier-filtered vectors", VIOLET),
    (8.46, 4.18, 2.48, "Mock ERP MCP", "separate JSON-RPC service\nvalidate • create • get • list", GREEN),
]
for x, y, w, head, body, accent in components:
    shape(slide, x, y, w, 1.32, accent, True)
    add_text(slide, head, x, y + 0.22, w, 0.24, 15, WHITE, True, PP_ALIGN.CENTER)
    add_text(slide, body, x + 0.08, y + 0.62, w - 0.16, 0.42, 9.2, RGBColor(230, 243, 249), False, PP_ALIGN.CENTER)
add_text(slide, "→", 3.05, 2.58, 0.36, 0.28, 20, BLUE, True, PP_ALIGN.CENTER)
add_text(slide, "→", 7.92, 2.5, 0.36, 0.28, 20, ORANGE, True, PP_ALIGN.CENTER)
line(slide, 6.25, 2.73, 7.88, 2.73, TEAL, 2)
line(slide, 4.95, 3.42, 2.95, 4.12, DEEP, 2)
line(slide, 4.95, 3.42, 6.32, 4.12, VIOLET, 2)
line(slide, 4.95, 3.42, 9.68, 4.12, GREEN, 2)
shape(slide, 0.86, 5.77, 1.55, 0.38, NAVY, True)
add_text(slide, "UPLOAD VOLUME", 0.86, 5.88, 1.55, 0.15, 9.1, WHITE, True, PP_ALIGN.CENTER)
add_text(slide, "UUID files • SHA-256 • revisions", 2.58, 5.86, 2.58, 0.19, 10.2, MUTED)
label(slide, "Provider rule", 6.18, 5.79, 1.32, ORANGE)
add_text(slide, "No silent cross-provider failover.", 7.72, 5.84, 4.05, 0.24, 12.3, NAVY, True)


# 5 — document AI
slide = prs.slides.add_slide(BLANK)
title(
    slide,
    "Document AI + RAG",
    "Readable evidence in; traceable facts and answers out",
    "OCR provenance, typed PII placeholders, page-local chunks, and citation validation make model output inspectable.",
    5,
    "AI pipeline | 6:20–8:10",
)
pipeline = [
    (0.65, "READ", "PDF / PNG / JPEG / TXT\nnative • mixed • OCR", ORANGE),
    (3.05, "REDACT", "GSTIN • PAN • CIN\nemail • phone • bank", RED),
    (5.45, "EXTRACT", "allow-listed fields\npage • confidence • conflicts", TEAL),
    (7.85, "INDEX", "500 tokens • 75 overlap\nnever crosses a page", VIOLET),
    (10.25, "ANSWER", "top 4 • distance 0.72\ncitation or exact not-found", BLUE),
]
for index, (x, head, body, accent) in enumerate(pipeline):
    shape(slide, x, 2.18, 2.05, 1.78, WHITE, True, accent, 1.5)
    label(slide, head, x + 0.42, 2.42, 1.21, accent)
    add_text(slide, body, x + 0.17, 3.08, 1.71, 0.53, 10.2, MUTED, False, PP_ALIGN.CENTER)
    if index < len(pipeline) - 1:
        add_text(slide, "→", x + 2.07, 2.9, 0.28, 0.28, 17, LINE, True, PP_ALIGN.CENTER)
card(slide, 0.78, 4.52, 3.68, 1.24, "Supplier isolation", "Every vector query filters by supplier ID before similarity ranking.", VIOLET, PALE)
card(slide, 4.82, 4.52, 3.68, 1.24, "Human-readable provenance", "Original filename, page, OCR method, confidence, review state and citation.", TEAL, PALE)
card(slide, 8.86, 4.52, 3.68, 1.24, "Versioned behavior", "extraction-v4 • rag-answer-v3 • supplier-assistant-v2", BLUE, PALE)
add_text(slide, "AI failure is diagnosable by document, stage, model, prompt, tokens and latency.", 1.15, 6.25, 11.05, 0.26, 14, NAVY, True, PP_ALIGN.CENTER)


# 6 — review, policy and ERP
slide = prs.slides.add_slide(BLANK)
title(
    slide,
    "Controls",
    "Calculated findings remain visible; reviewers own the outcome",
    "The policy engine separates model evidence, deterministic checks, reviewer verification, and downstream creation.",
    6,
    "Review + ERP | 8:10–10:05",
)
shape(slide, 0.78, 2.13, 3.52, 3.7, PALE_BLUE, True, BLUE)
add_text(slide, "Policy catalogue", 1.08, 2.46, 2.6, 0.3, 20, BLUE, True, font="Aptos Display")
add_text(slide, "8", 1.1, 3.06, 0.85, 0.5, 30, NAVY, True)
add_text(slide, "categories", 1.72, 3.19, 1.3, 0.22, 12, MUTED)
add_text(slide, "24", 1.1, 3.77, 0.85, 0.5, 30, NAVY, True)
add_text(slide, "subcategories", 1.92, 3.9, 1.45, 0.22, 12, MUTED)
add_text(slide, "22", 1.1, 4.48, 0.85, 0.5, 30, NAVY, True)
add_text(slide, "reusable requirements", 1.92, 4.61, 1.83, 0.22, 12, MUTED)
add_text(slide, "Checklist is frozen at first submission", 1.08, 5.32, 2.85, 0.25, 11.2, BLUE, True)
shape(slide, 4.72, 2.13, 3.7, 3.7, WHITE, True, VIOLET, 1.5)
add_text(slide, "Approval gate", 5.02, 2.46, 2.6, 0.3, 20, VIOLET, True, font="Aptos Display")
bullets(slide, [
    "required readable evidence exists",
    "numbered policy checks verified",
    "no disputed documents or fields",
    "all extracted values reviewed",
    "every compliance result = PASS",
], 5.04, 3.06, 3.05, 2.13, 12.2, INK, 7)
add_text(slide, "Reviewer clicks Approve", 5.04, 5.34, 2.95, 0.25, 12, VIOLET, True, PP_ALIGN.CENTER)
shape(slide, 8.84, 2.13, 3.7, 3.7, PALE, True, GREEN)
add_text(slide, "ERP handoff", 9.14, 2.46, 2.6, 0.3, 20, GREEN, True, font="Aptos Display")
bullets(slide, [
    "reviewed values preferred",
    "validate required data + duplicates",
    "case ID is idempotency key",
    "safe retry if service is unavailable",
    "sanitized attempt audit",
], 9.16, 3.06, 3.05, 2.13, 12.2, INK, 7)
add_text(slide, "APPROVED only after ERP create/replay", 9.06, 5.34, 3.3, 0.25, 11.2, GREEN, True, PP_ALIGN.CENTER)
add_text(slide, "AI match → NEEDS REVIEW     •     Reviewer verification → PASS", 2.0, 6.29, 9.3, 0.26, 14.5, NAVY, True, PP_ALIGN.CENTER)


# 7 — live demo handoff
slide = prs.slides.add_slide(BLANK)
title(
    slide,
    "Live demo",
    "Follow one case across all trust boundaries",
    "The walkthrough proves both the happy path and the controls that prevent unsupported automation.",
    7,
    "Live walkthrough | 10:05–15:40",
)
demo = [
    ("01", "Supplier", "Register or sign in; complete India-based details and choose a subcategory.", BLUE),
    ("02", "Evidence", "Show dynamic checklist; upload native and scanned evidence; open OCR provenance.", ORANGE),
    ("03", "Submit", "Freeze the checklist and observe background extraction/index status.", TEAL),
    ("04", "Reviewer", "Open original/page, inspect mismatch, ask the case assistant, verify/correct evidence.", VIOLET),
    ("05", "Compliance", "Run checks; show why unresolved items block approval; verify to reach all PASS.", DEEP),
    ("06", "ERP + admin", "Approve, retrieve the ERP record, then show AI/OCR/ERP observability.", GREEN),
]
for index, (num, head, body, accent) in enumerate(demo):
    row = index // 2
    col = index % 2
    x = 0.78 + col * 6.15
    y = 2.08 + row * 1.34
    shape(slide, x, y, 5.66, 1.03, WHITE, True, accent, 1.3)
    shape(slide, x + 0.2, y + 0.22, 0.56, 0.56, accent, True)
    add_text(slide, num, x + 0.2, y + 0.39, 0.56, 0.16, 10.5, WHITE, True, PP_ALIGN.CENTER)
    add_text(slide, head, x + 0.96, y + 0.18, 1.3, 0.24, 15, NAVY, True)
    add_text(slide, body, x + 2.12, y + 0.16, 3.2, 0.55, 10.5, MUTED)
shape(slide, 1.3, 6.2, 10.75, 0.46, PALE_ORANGE, True, ORANGE)
add_text(slide, "Fallback: use the evaluation report if an external provider is slow; never bypass the review controls.", 1.45, 6.33, 10.45, 0.19, 11.2, ORANGE, True, PP_ALIGN.CENTER)


# 8 — quality and operations
slide = prs.slides.add_slide(BLANK)
title(
    slide,
    "Evidence",
    "Measured quality plus operational visibility",
    "The repository includes a controlled multi-supplier corpus; the admin workspace exposes current runtime evidence.",
    8,
    "Quality + operations | 15:40–17:30",
)
metrics = [
    ("36/36", "field checks", "historical v3 evaluation", BLUE),
    ("24/24", "Q&A cases", "answers + expected terms", TEAL),
    ("100%", "citations + not-found", "including isolation", VIOLET),
    ("2,035 ms", "average Q&A", "2,439 ms maximum", ORANGE),
]
for index, (value, name, note, accent) in enumerate(metrics):
    x = 0.7 + index * 3.13
    shape(slide, x, 2.08, 2.78, 1.38, PALE, True, LINE)
    shape(slide, x, 2.08, 0.08, 1.38, accent, True)
    add_text(slide, value, x + 0.23, 2.3, 2.3, 0.35, 24, NAVY, True, font="Aptos Display")
    add_text(slide, name, x + 0.23, 2.76, 2.35, 0.2, 11.5, NAVY, True)
    add_text(slide, note, x + 0.23, 3.08, 2.35, 0.16, 9.1, MUTED)
ops = [
    (0.82, "Admin observability", "success/failure • model/prompt • tokens • avg/P95 latency\nRAG grounding • OCR methods/pages • ERP attempts/latency", BLUE),
    (4.77, "Langfuse", "privacy-safe correlated traces and cost analysis\ncontent capture disabled by default", VIOLET),
    (8.72, "Prometheus + Promptfoo", "traffic • errors • dependencies • decisions\ngrounding • citations • isolation • refusals", ORANGE),
]
for x, head, body, accent in ops:
    card(slide, x, 4.08, 3.78, 1.58, head, body, accent, WHITE)
add_text(slide, "Controlled synthetic results are evidence—not production guarantees; rerun them for every release candidate.", 0.95, 6.27, 11.45, 0.28, 12.2, RED, True, PP_ALIGN.CENTER)


# 9 — security and production readiness
slide = prs.slides.add_slide(BLANK)
title(
    slide,
    "Security + readiness",
    "Strong prototype controls; explicit production prerequisites",
    "The demo makes privacy and accountability visible while remaining honest about operational hardening.",
    9,
    "Readiness | 17:30–19:10",
)
shape(slide, 0.78, 2.1, 5.7, 4.15, PALE_BLUE, True, BLUE)
add_text(slide, "Implemented now", 1.1, 2.43, 2.7, 0.31, 20, BLUE, True, font="Aptos Display")
bullets(slide, [
    "role-enforced API routes; scrypt supplier passwords",
    "hashed, expiring bearer sessions",
    "UUID paths, MIME/size limits and SHA-256 verification",
    "PII redaction before external AI calls",
    "supplier-filtered retrieval and privacy-safe telemetry",
    "human decision, immutable revision metadata and audit trail",
], 1.1, 3.04, 4.92, 2.54, 12.2, INK, 7)
shape(slide, 6.84, 2.1, 5.7, 4.15, PALE_ORANGE, True, ORANGE)
add_text(slide, "Before production", 7.16, 2.43, 2.9, 0.31, 20, ORANGE, True, font="Aptos Display")
bullets(slide, [
    "SSO/MFA, secure HttpOnly sessions and enterprise RBAC",
    "TLS, secrets manager and private docs/metrics",
    "encrypted object storage, malware/DLP and retention",
    "durable worker queue, retries and managed persistence",
    "policy governance, privacy impact and provider agreements",
    "browser E2E, load, accessibility, security and DR tests",
], 7.16, 3.04, 4.92, 2.54, 12.2, INK, 7)
add_text(slide, "Current deployment profile: local development and capstone demonstration—not a production procurement service.", 1.0, 6.57, 11.35, 0.26, 12.5, RED, True, PP_ALIGN.CENTER)


# 10 — close
slide = prs.slides.add_slide(BLANK)
shape(slide, 0, 0, 13.333, 7.5, NAVY)
shape(slide, 0, 0, 13.333, 0.16, VIOLET)
add_text(slide, "VendorLens AI", 0.82, 0.86, 3.8, 0.48, 25, RGBColor(191, 221, 234), True, font="Aptos Display")
add_text(slide, "Evidence in.\nAccountable decision out.", 0.82, 1.7, 7.75, 1.38, 38, WHITE, True, font="Aptos Display")
summary = [
    ("TRACEABLE", "page sources • citations • revisions", BLUE),
    ("CONTROLLED", "policy gates • human approval", VIOLET),
    ("OPERABLE", "metrics • traces • safe retries", ORANGE),
]
for index, (head, body, accent) in enumerate(summary):
    x = 0.86 + index * 3.96
    shape(slide, x, 4.2, 3.48, 1.12, RGBColor(20, 55, 90), True, accent, 1.5)
    add_text(slide, head, x + 0.18, 4.47, 3.1, 0.22, 14, accent, True, PP_ALIGN.CENTER)
    add_text(slide, body, x + 0.18, 4.83, 3.1, 0.18, 9.7, RGBColor(210, 230, 241), False, PP_ALIGN.CENTER)
add_text(slide, "Q&A", 0.82, 6.07, 3.2, 0.5, 28, WHITE, True, font="Aptos Display")
footer(slide, 10, "Questions + discussion | 19:10–20:00")


prs.core_properties.title = "VendorLens AI - 20 Minute Demo Presentation"
prs.core_properties.subject = "As-built supplier onboarding, document AI, policy review, ERP integration, and observability"
prs.core_properties.author = "VendorLens AI"
prs.core_properties.comments = "Updated for the September 2026 as-built project baseline."
prs.save(OUT)
print(OUT)
