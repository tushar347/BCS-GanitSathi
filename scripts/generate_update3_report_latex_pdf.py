"""Generate the ACML 2026 Result Analysis Update Report 3 as a publication-grade PDF.

Uses ReportLab and Arial Unicode to produce an IEEE one-column format PDF that
mirrors the LaTeX source in update_3_report.tex, containing 5 result analysis
tables combining the legacy 202-dataset and expanded 411-dataset evaluations.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
    PageBreak,
)
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


FONT_PATH = "C:/Windows/Fonts/ARIALUNI.ttf"
if os.path.exists(FONT_PATH):
    pdfmetrics.registerFont(TTFont("ArialUnicode", FONT_PATH))
    MAIN_FONT = "ArialUnicode"
else:
    MAIN_FONT = "Helvetica"


class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas for 'Page X of Y' and running headers."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count: int):
        self.saveState()
        self.setFont(MAIN_FONT, 8)
        self.setFillColor(colors.HexColor("#64748B"))

        if self._pageNumber > 1:
            self.drawString(
                54, 11 * 72 - 36,
                "GonitSathi — Update Report 3: ACML 2026 Result Analysis",
            )
            self.drawRightString(
                8.5 * 72 - 54, 11 * 72 - 36,
                "September 23, 2026",
            )
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.5)
            self.line(54, 11 * 72 - 42, 8.5 * 72 - 54, 11 * 72 - 42)

        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawString(
            54, 34,
            "CONFIDENTIAL — GonitSathi Research Team (North South University)",
        )
        self.drawRightString(8.5 * 72 - 54, 34, page_str)
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.5)
        self.line(54, 44, 8.5 * 72 - 54, 44)
        self.restoreState()


def generate_charts(assets_dir: Path) -> dict[str, Path]:
    """Generate high-resolution matplotlib charts for the ACML result analysis."""
    assets_dir.mkdir(parents=True, exist_ok=True)
    chart_paths = {}

    plt.rcParams["font.sans-serif"] = "DejaVu Sans"
    plt.rcParams["axes.edgecolor"] = "#CBD5E1"
    plt.rcParams["axes.linewidth"] = 0.8

    # ── Chart 1: Topic Distribution across 411 Problem Families ──
    fig, ax = plt.subplots(figsize=(6.6, 2.1), dpi=300)
    topics = [
        "Algebra & Number Systems",
        "Percentages, Profit & Loss",
        "Arithmetic & Mental Ability",
        "Ratios & Proportions",
        "Speed, Distance & Work/Time",
        "Averages & Mixtures",
        "Geometry & Mensuration",
    ]
    counts = [236, 56, 40, 29, 26, 17, 7]
    total = sum(counts)
    bar_colors = [
        "#1E3A8A", "#2563EB", "#0284C7", "#0D9488",
        "#10B981", "#6366F1", "#8B5CF6",
    ]

    y_pos = np.arange(len(topics))
    bars = ax.barh(y_pos, counts, color=bar_colors, height=0.60, edgecolor="none")
    ax.set_yticks(y_pos)
    ax.set_yticklabels(topics, fontsize=7.8, fontweight="medium", color="#1E293B")
    ax.invert_yaxis()
    ax.set_xlabel(
        "Number of BCS Problem Families (Total = 411 across BCS 10–50)",
        fontsize=7.5, color="#475569",
    )
    ax.set_title(
        "BCS Math Benchmark: Topic Distribution (411 Families, 7 Domains)",
        fontsize=8.5, fontweight="bold", color="#0F172A", pad=6,
    )
    ax.grid(axis="x", linestyle="--", alpha=0.5, color="#E2E8F0")

    for bar in bars:
        w = bar.get_width()
        pct = (w / total) * 100
        ax.text(
            w + 2.5, bar.get_y() + bar.get_height() / 2,
            f"{w} ({pct:.1f}%)",
            ha="left", va="center", fontsize=7, fontweight="bold", color="#334155",
        )

    ax.set_xlim(0, 280)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    plt.tight_layout()

    chart1_path = assets_dir / "topic_distribution_411.png"
    plt.savefig(chart1_path, dpi=300, bbox_inches="tight")
    plt.close()
    chart_paths["topic_dist"] = chart1_path

    # ── Chart 2: Benchmark Results (Risk + Latency-Accuracy Frontier) ──
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(6.6, 2.3), dpi=300)

    systems = [
        "B0\nRule", "B1\nPrompt", "B2\nVerify", "B3\nBayes",
        "B4\nIntelli", "B5\nScaffold", "B6\nSLOW", "G\n(Ours)",
    ]

    # Test split risk values
    risk_pct = [0.0, 56.5, 0.0, 0.0, 71.4, 71.4, 71.4, 0.0]
    risk_colors = [
        "#10B981", "#EF4444", "#10B981", "#10B981",
        "#DC2626", "#DC2626", "#DC2626", "#047857",
    ]

    x = np.arange(len(systems))
    bars = ax1.bar(x, risk_pct, color=risk_colors, width=0.55)
    ax1.set_ylabel("Unsupported Risk R_commit (%)", fontsize=7.5, color="#475569")
    ax1.set_title(
        "(a) False-Attribution Risk on Test Split",
        fontsize=8, fontweight="bold", color="#0F172A",
    )
    ax1.set_xticks(x)
    ax1.set_xticklabels(systems, fontsize=6.2)
    ax1.grid(axis="y", linestyle="--", alpha=0.5, color="#E2E8F0")
    ax1.set_ylim(0, 88)
    ax1.spines["top"].set_visible(False)
    ax1.spines["right"].set_visible(False)

    for bar in bars:
        h = bar.get_height()
        ax1.text(
            bar.get_x() + bar.get_width() / 2, h + 1.5,
            f"{h:.1f}%", ha="center", va="bottom",
            fontsize=6.2, fontweight="bold", color="#1E293B",
        )

    # (b) Frontier plot: Latency vs First-Error Accuracy (Test split)
    ax2.scatter([0.01], [32.9], color="#64748B", s=40, marker="o", label="B0 (Rule)")
    ax2.scatter([0.07], [32.9], color="#EF4444", s=40, marker="s", label="B1 (Prompt)")
    ax2.scatter([151.37], [31.4], color="#3B82F6", s=40, marker="^", label="B2 (Verify)")
    ax2.scatter([166.82], [31.4], color="#8B5CF6", s=40, marker="D", label="B3 (Bayes)")
    ax2.scatter([127.03], [0.0], color="#9CA3AF", s=30, marker="x", label="B4-B6 (Memory)")
    ax2.scatter([127.18], [0.0], color="#9CA3AF", s=30, marker="x")
    ax2.scatter([132.72], [0.0], color="#9CA3AF", s=30, marker="x")
    ax2.scatter([162.00], [35.7], color="#047857", s=80, marker="*", label="GonitSathi (Ours)")

    ax2.set_xlabel("Mean Latency per Turn (ms)", fontsize=7.5, color="#475569")
    ax2.set_ylabel("First-Error Accuracy (%)", fontsize=7.5, color="#475569")
    ax2.set_title(
        "(b) Latency vs Accuracy (Test Split)",
        fontsize=8, fontweight="bold", color="#0F172A",
    )
    ax2.set_xlim(-10, 200)
    ax2.set_ylim(-3, 44)
    ax2.grid(True, linestyle="--", alpha=0.5, color="#E2E8F0")
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_visible(False)
    ax2.legend(fontsize=5.8, loc="lower right", framealpha=0.85)
    ax2.annotate(
        "GonitSathi [35.7% Acc, 0% Risk]",
        xy=(162.0, 35.7), xytext=(30, 40.0),
        arrowprops=dict(arrowstyle="->", color="#047857", lw=0.8),
        fontsize=6.5, fontweight="bold", color="#047857",
    )

    plt.tight_layout()
    chart2_path = assets_dir / "eval_metrics_summary_411.png"
    plt.savefig(chart2_path, dpi=300, bbox_inches="tight")
    plt.close()
    chart_paths["eval_metrics"] = chart2_path

    # ── Chart 3: Scaling Risk Comparison (202 vs 411) ──
    fig, ax3 = plt.subplots(figsize=(6.6, 2.3), dpi=300)

    systems_short = ["B0", "B1", "B2", "B3", "B4", "B5", "B6", "G (Ours)"]
    risk_202 = [0.0, 41.7, 0.0, 0.0, 56.3, 56.3, 56.3, 0.0]
    risk_411 = [0.0, 56.5, 0.0, 0.0, 71.4, 71.4, 71.4, 0.0]

    x3 = np.arange(len(systems_short))
    w3 = 0.32
    ax3.bar(x3 - w3 / 2, risk_202, w3, color="#93C5FD", label="202-Dataset (Update 2)", edgecolor="white", linewidth=0.5)
    ax3.bar(x3 + w3 / 2, risk_411, w3, color="#1E3A8A", label="411-Dataset (Update 3)", edgecolor="white", linewidth=0.5)

    ax3.set_ylabel("Risk R_commit (%)", fontsize=7.5, color="#475569")
    ax3.set_title(
        "Scaling Effect on False-Attribution Risk: 202 vs 411 Families",
        fontsize=8.5, fontweight="bold", color="#0F172A", pad=8,
    )
    ax3.set_xticks(x3)
    ax3.set_xticklabels(systems_short, fontsize=7.5)
    ax3.set_ylim(0, 95)
    ax3.grid(axis="y", linestyle="--", alpha=0.5, color="#E2E8F0")
    ax3.spines["top"].set_visible(False)
    ax3.spines["right"].set_visible(False)
    ax3.legend(fontsize=7, loc="upper left", ncol=2, framealpha=0.92, columnspacing=1.0)

    # Annotate the increase for B1 and B4-B6
    for i, (r2, r4) in enumerate(zip(risk_202, risk_411)):
        if r4 > 0 and r4 > r2:
            diff = r4 - r2
            ax3.annotate(
                f"+{diff:.1f}pp",
                xy=(x3[i] + w3 / 2, r4),
                xytext=(0, 4),
                textcoords="offset points",
                ha="center", fontsize=6.2, fontweight="bold", color="#DC2626",
            )

    plt.tight_layout()
    chart3_path = assets_dir / "scaling_risk_comparison.png"
    plt.savefig(chart3_path, dpi=300, bbox_inches="tight")
    plt.close()
    chart_paths["scaling_risk"] = chart3_path

    return chart_paths


def build_pdf_report(output_pdf_path: Path):
    """Build the ACML 2026 result analysis report PDF."""
    output_pdf_path.parent.mkdir(parents=True, exist_ok=True)
    assets_dir = output_pdf_path.parent / "report_assets"
    charts = generate_charts(assets_dir)

    doc = SimpleDocTemplate(
        str(output_pdf_path),
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=44,
        bottomMargin=44,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "DocTitle", parent=styles["Normal"],
        fontName=MAIN_FONT, fontSize=15, leading=18,
        textColor=colors.HexColor("#0F172A"), spaceAfter=2,
    )
    subtitle_style = ParagraphStyle(
        "DocSubtitle", parent=styles["Normal"],
        fontName=MAIN_FONT, fontSize=9.5, leading=13,
        textColor=colors.HexColor("#1E3A8A"), spaceAfter=6,
    )
    meta_style = ParagraphStyle(
        "Meta", parent=styles["Normal"],
        fontName=MAIN_FONT, fontSize=7.2, leading=9.5,
        textColor=colors.HexColor("#334155"),
    )
    h1_style = ParagraphStyle(
        "H1", parent=styles["Normal"],
        fontName=MAIN_FONT, fontSize=10.5, leading=13.5,
        textColor=colors.HexColor("#1E3A8A"),
        spaceBefore=5, spaceAfter=3, keepWithNext=True,
    )
    h2_style = ParagraphStyle(
        "H2", parent=styles["Normal"],
        fontName=MAIN_FONT, fontSize=8.5, leading=11.5,
        textColor=colors.HexColor("#0F172A"),
        spaceBefore=4, spaceAfter=2, keepWithNext=True,
    )
    body_style = ParagraphStyle(
        "Body", parent=styles["Normal"],
        fontName=MAIN_FONT, fontSize=7.3, leading=10.2,
        textColor=colors.HexColor("#334155"), spaceAfter=3,
    )
    callout_text = ParagraphStyle(
        "Callout", parent=styles["Normal"],
        fontName=MAIN_FONT, fontSize=7.2, leading=10.0,
        textColor=colors.HexColor("#1E293B"),
    )
    caption_style = ParagraphStyle(
        "Caption", parent=styles["Normal"],
        fontName=MAIN_FONT, fontSize=7.0, leading=9.5,
        textColor=colors.HexColor("#475569"), spaceAfter=4,
    )

    def cell(
        text: str,
        is_header: bool = False,
        align: str = "left",
        color_hex: Optional[str] = None,
    ) -> Paragraph:
        p_color = color_hex or ("#FFFFFF" if is_header else "#1E293B")
        align_code = 0 if align == "left" else (1 if align == "center" else 2)
        style = ParagraphStyle(
            "Cell",
            fontName=MAIN_FONT,
            fontSize=7.0 if not is_header else 7.3,
            leading=9.5 if not is_header else 10.0,
            textColor=colors.HexColor(p_color),
            alignment=align_code,
        )
        return Paragraph(text, style)

    def make_ieee_table(data, col_widths, has_highlight_last=True):
        t = Table(data, colWidths=col_widths)
        style_cmds = [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E3A8A")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CBD5E1")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -2 if has_highlight_last else -1),
             [colors.HexColor("#FFFFFF"), colors.HexColor("#F8FAFC")]),
            ("TOPPADDING", (0, 0), (-1, -1), 2.5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ]
        if has_highlight_last:
            style_cmds.extend([
                ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#ECFDF5")),
                ("BOX", (0, -1), (-1, -1), 1.0, colors.HexColor("#059669")),
            ])
        t.setStyle(TableStyle(style_cmds))
        return t

    story = []

    # =====================================================================
    # PAGE 1: TITLE, RECAP, TABLE I (DATASET SCALING), TABLE II (TOPICS)
    # =====================================================================
    story.append(Paragraph("<b>Update Report 3: GonitSathi</b>", title_style))
    story.append(Paragraph(
        "Neuro-Symbolic Diagnostic Tutoring for Ambiguous Bengali Mathematics",
        subtitle_style,
    ))
    story.append(Paragraph(
        "<b>Research Assistants:</b> RA1, RA2, RA3, RA4 &nbsp;|&nbsp; "
        "<b>Lab:</b> GonitSathi Research Lab, North South University<br/>"
        "<b>Target Venue:</b> OE-Agent Workshop @ ACML 2026 &nbsp;|&nbsp; "
        "<b>Date:</b> September 23, 2026",
        meta_style,
    ))
    story.append(Spacer(1, 4))

    # Section I header
    story.append(Paragraph("I. Update 3 Progress & Verification Report", h1_style))

    # What was done previously (concise)
    story.append(Paragraph("<b>A. What was done in the previous update</b>", h2_style))
    story.append(Paragraph(
        "In Update 2 (September 21, 2026), the team: "
        "(1) implemented the bilingual Bengali normalizer and AST symbolic verifier, "
        "(2) built the evidence admission controller with the 2-observation corroboration rule, "
        "(3) created the baseline suite (B0–B6), "
        "(4) conducted the initial pilot evaluation on a flat 202-question subset, "
        "and (5) passed all 112 automated tests. "
        "GonitSathi achieved 0.0% risk, 31.25% first-error accuracy, and 55.84 ms latency on the 202 pilot.",
        body_style,
    ))

    # What is done in this update
    story.append(Paragraph("<b>B. What is done in this update</b>", h2_style))
    story.append(Paragraph(
        "Update 3 scales the evaluation from the preliminary 202-dataset pilot to the complete "
        "<b>411 authentic BCS problem families</b> (1,536 student solving steps across 41 exams, BCS 10–50). "
        "Tasks completed: "
        "(1) Benchmark split freezing (Train: 207, Dev: 102, Test: 102) with zero family overlap, "
        "(2) Full 411-family diagnostic evaluation, "
        "(3) 8-architecture comparative evaluation on frozen dev and test splits, "
        "(4) Result analysis comparing 202-pilot vs 411-full dataset performance.",
        body_style,
    ))
    story.append(Spacer(1, 2))

    # ── TABLE I: Dataset Scaling ──
    story.append(Paragraph(
        "<b>Table I: Dataset Scaling — 202-Pilot (Update 2) vs. 411-Full (Update 3)</b>",
        h2_style,
    ))
    scaling_data = [
        [
            cell("<b>Metric</b>", is_header=True),
            cell("<b>Update 2 (202)</b>", is_header=True, align="center"),
            cell("<b>Update 3 (411)</b>", is_header=True, align="center"),
            cell("<b>Change</b>", is_header=True, align="center"),
        ],
        [cell("Exam Sessions"), cell("22 (BCS 10–31)", align="center"), cell("41 (BCS 10–50)", align="center"), cell("+86.4%", align="center")],
        [cell("Problem Families"), cell("202", align="center"), cell("411", align="center"), cell("+103.5%", align="center")],
        [cell("Student Solving Steps"), cell("788", align="center"), cell("1,536", align="center"), cell("+94.9%", align="center")],
        [cell("Multiclass Brier Score"), cell("0.942", align="center"), cell("<b>0.879</b>", align="center", color_hex="#047857"), cell("-6.7% (improved)", align="center", color_hex="#047857")],
        [cell("First-Error Accuracy"), cell("31.25%", align="center"), cell("<b>35.7%</b> (test)", align="center", color_hex="#047857"), cell("+14.2% (improved)", align="center", color_hex="#047857")],
        [cell("Unsupported Risk (R_commit)"), cell("0.0%", align="center"), cell("<b>0.0%</b>", align="center", color_hex="#047857"), cell("Guaranteed", align="center", color_hex="#047857")],
        [cell("Mean Latency"), cell("55.84 ms", align="center"), cell("76.31 ms", align="center"), cell("Within bound", align="center")],
        [cell("P95 Latency"), cell("—", align="center"), cell("352.11 ms", align="center"), cell("Sub-500 ms", align="center")],
    ]
    t1 = Table(scaling_data, colWidths=[130, 110, 120, 144])
    t1.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E3A8A")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CBD5E1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#FFFFFF"), colors.HexColor("#F8FAFC")]),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t1)
    story.append(Spacer(1, 4))

    # ── TABLE II: Topic Distribution ──
    story.append(Paragraph(
        "<b>Table II: Topic Distribution Across 411 BCS Problem Families (Frozen Splits)</b>",
        h2_style,
    ))
    topic_data = [
        [
            cell("<b>Topic Domain</b>", is_header=True),
            cell("<b>Total</b>", is_header=True, align="center"),
            cell("<b>Train</b>", is_header=True, align="center"),
            cell("<b>Dev</b>", is_header=True, align="center"),
            cell("<b>Test</b>", is_header=True, align="center"),
        ],
        [cell("Algebra & Number Systems"), cell("236 (57.4%)", align="center"), cell("118", align="center"), cell("59", align="center"), cell("59", align="center")],
        [cell("Percentages, Profit & Loss"), cell("56 (13.6%)", align="center"), cell("28", align="center"), cell("14", align="center"), cell("14", align="center")],
        [cell("Arithmetic & Mental Ability"), cell("40 (9.7%)", align="center"), cell("20", align="center"), cell("10", align="center"), cell("10", align="center")],
        [cell("Ratios & Proportions"), cell("29 (7.1%)", align="center"), cell("15", align="center"), cell("7", align="center"), cell("7", align="center")],
        [cell("Speed, Distance & Work/Time"), cell("26 (6.3%)", align="center"), cell("14", align="center"), cell("6", align="center"), cell("6", align="center")],
        [cell("Averages & Mixtures"), cell("17 (4.1%)", align="center"), cell("9", align="center"), cell("4", align="center"), cell("4", align="center")],
        [cell("Geometry & Mensuration"), cell("7 (1.7%)", align="center"), cell("3", align="center"), cell("2", align="center"), cell("2", align="center")],
        [cell("<b>Total</b>"), cell("<b>411</b>", align="center"), cell("<b>207</b> (50.4%)", align="center"), cell("<b>102</b> (24.8%)", align="center"), cell("<b>102</b> (24.8%)", align="center")],
    ]
    t2 = Table(topic_data, colWidths=[148, 92, 88, 88, 88])
    t2.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E3A8A")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CBD5E1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.HexColor("#FFFFFF"), colors.HexColor("#F8FAFC")]),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#EFF6FF")),
        ("BOX", (0, -1), (-1, -1), 0.8, colors.HexColor("#93C5FD")),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t2)

    story.append(PageBreak())

    # =====================================================================
    # PAGE 2: TOPIC CHART, TABLE III (COMPARATIVE TEST SPLIT)
    # =====================================================================
    # Figure 1: Topic Distribution
    story.append(Paragraph("<b>C. Benchmark Composition & Empirical Findings</b>", h1_style))
    story.append(Image(str(charts["topic_dist"]), width=6.6 * 72 * 0.93, height=2.1 * 72 * 0.93))
    story.append(Paragraph(
        "<b>Fig. 1.</b> Topic distribution across 411 BCS problem families. "
        "Algebra & Number Systems dominates (57.4%), reflecting the authentic composition "
        "of Bangladesh Civil Service examinations.",
        caption_style,
    ))
    story.append(Spacer(1, 3))

    # ── TABLE III: Comparative Evaluation on Test Split ──
    story.append(Paragraph(
        "<b>Table III: Comparative Evaluation on Frozen Test Split (N=8, 102 Families, 70 Histories)</b>",
        h2_style,
    ))
    comp_data = [
        [
            cell("<b>System</b>", is_header=True),
            cell("<b>Paradigm</b>", is_header=True),
            cell("<b>Risk (R_commit)</b>", is_header=True, align="center"),
            cell("<b>Coverage</b>", is_header=True, align="center"),
            cell("<b>Brier</b>", is_header=True, align="center"),
            cell("<b>First-Error</b>", is_header=True, align="center"),
            cell("<b>Latency</b>", is_header=True, align="center"),
        ],
        [cell("B0 (Rule/Template)"), cell("Handcrafted Rules"), cell("<b>0.0%</b>", align="center"), cell("0.0%", align="center"), cell("N/A", align="center"), cell("32.9%", align="center"), cell("<b>0.01 ms</b>", align="center")],
        [cell("B1 (Prompted LLM)"), cell("Standard LLM"), cell("56.5%", align="center", color_hex="#DC2626"), cell("65.7%", align="center"), cell("1.429", align="center"), cell("32.9%", align="center"), cell("0.07 ms", align="center")],
        [cell("B2 (Verify-then-Gen)"), cell("Stateless Verifier"), cell("<b>0.0%</b>", align="center"), cell("0.0%", align="center"), cell("1.429", align="center"), cell("31.4%", align="center"), cell("151.37 ms", align="center")],
        [cell("B3 (Bayesian)"), cell("Raw Likelihood Bayes"), cell("<b>0.0%</b>", align="center"), cell("0.0%", align="center"), cell("<b>0.810</b>", align="center"), cell("31.4%", align="center"), cell("166.82 ms", align="center")],
        [cell("B4 (IntelliCode)"), cell("Single-Writer BKT"), cell("71.4%", align="center", color_hex="#DC2626"), cell("100.0%", align="center"), cell("0.842", align="center"), cell("0.0%", align="center", color_hex="#DC2626"), cell("127.03 ms", align="center")],
        [cell("B5 (ScaffoldLM)"), cell("Plan Memory Loop"), cell("71.4%", align="center", color_hex="#DC2626"), cell("100.0%", align="center"), cell("0.998", align="center"), cell("0.0%", align="center", color_hex="#DC2626"), cell("127.18 ms", align="center")],
        [cell("B6 (SLOW)"), cell("Counterfactual Delta"), cell("71.4%", align="center", color_hex="#DC2626"), cell("100.0%", align="center"), cell("1.042", align="center"), cell("0.0%", align="center", color_hex="#DC2626"), cell("132.72 ms", align="center")],
        [cell("<b>GonitSathi (G)</b>"), cell("<b>Governed Controller</b>"), cell("<b>0.0%</b>", align="center", color_hex="#047857"), cell("<b>0.0%</b>", align="center"), cell("<b>1.009</b>", align="center"), cell("<b>35.7%</b>", align="center", color_hex="#047857"), cell("<b>162.00 ms</b>", align="center")],
    ]
    t3 = make_ieee_table(comp_data, [88, 82, 66, 60, 52, 64, 68])
    story.append(t3)
    story.append(Spacer(1, 4))

    # Figure 2: Benchmark chart
    story.append(Image(str(charts["eval_metrics"]), width=6.6 * 72 * 0.93, height=2.3 * 72 * 0.93))
    story.append(Paragraph(
        "<b>Fig. 2.</b> Benchmark results on 411-dataset test split: "
        "(a) False-attribution risk across 8 architectures — memory baselines B4–B6 exhibit 71.4% "
        "risk while GonitSathi maintains 0.0%; "
        "(b) Latency vs first-error accuracy frontier — GonitSathi establishes the Pareto optimum "
        "(35.7% accuracy, 162 ms latency, 0% risk).",
        caption_style,
    ))

    story.append(PageBreak())

    # =====================================================================
    # PAGE 3: TABLE IV (DEV vs TEST STABILITY), TABLE V (SCALING RISK),
    #         FIGURE 3, DISCUSSION
    # =====================================================================
    story.append(Paragraph("<b>D. Dev vs. Test Stability Analysis</b>", h1_style))

    # ── TABLE IV: Dev vs Test Stability ──
    story.append(Paragraph(
        "<b>Table IV: Dev vs. Test Stability for All 8 Architectures</b>",
        h2_style,
    ))
    stability_data = [
        [
            cell("<b>System</b>", is_header=True),
            cell("<b>Risk (Dev)</b>", is_header=True, align="center"),
            cell("<b>Risk (Test)</b>", is_header=True, align="center"),
            cell("<b>FE Acc (Dev)</b>", is_header=True, align="center"),
            cell("<b>FE Acc (Test)</b>", is_header=True, align="center"),
            cell("<b>Brier (Dev)</b>", is_header=True, align="center"),
            cell("<b>Brier (Test)</b>", is_header=True, align="center"),
        ],
        [cell("B0 (Rule)"), cell("0.0%", align="center"), cell("0.0%", align="center"), cell("32.7%", align="center"), cell("32.9%", align="center"), cell("N/A", align="center"), cell("N/A", align="center")],
        [cell("B1 (Prompted)"), cell("54.3%", align="center"), cell("56.5%", align="center"), cell("32.7%", align="center"), cell("32.9%", align="center"), cell("1.346", align="center"), cell("1.429", align="center")],
        [cell("B2 (Verify)"), cell("0.0%", align="center"), cell("0.0%", align="center"), cell("32.7%", align="center"), cell("31.4%", align="center"), cell("1.385", align="center"), cell("1.429", align="center")],
        [cell("B3 (Bayesian)"), cell("0.0%", align="center"), cell("0.0%", align="center"), cell("32.7%", align="center"), cell("31.4%", align="center"), cell("0.796", align="center"), cell("0.810", align="center")],
        [cell("B4 (IntelliCode)"), cell("69.2%", align="center"), cell("71.4%", align="center"), cell("0.0%", align="center"), cell("0.0%", align="center"), cell("0.832", align="center"), cell("0.842", align="center")],
        [cell("B5 (ScaffoldLM)"), cell("69.2%", align="center"), cell("71.4%", align="center"), cell("0.0%", align="center"), cell("0.0%", align="center"), cell("0.990", align="center"), cell("0.998", align="center")],
        [cell("B6 (SLOW)"), cell("69.2%", align="center"), cell("71.4%", align="center"), cell("0.0%", align="center"), cell("0.0%", align="center"), cell("1.015", align="center"), cell("1.042", align="center")],
        [cell("<b>GonitSathi (G)</b>"), cell("<b>0.0%</b>", align="center", color_hex="#047857"), cell("<b>0.0%</b>", align="center", color_hex="#047857"), cell("<b>36.5%</b>", align="center", color_hex="#047857"), cell("<b>35.7%</b>", align="center", color_hex="#047857"), cell("<b>1.003</b>", align="center"), cell("<b>1.009</b>", align="center")],
    ]
    t4 = make_ieee_table(stability_data, [80, 68, 68, 72, 72, 72, 72])
    story.append(t4)
    story.append(Spacer(1, 2))

    story.append(Paragraph(
        "The narrow variance between dev and test metrics "
        "(Delta A_FE = 0.8%, Delta Brier = 0.006) confirms that the results are robust "
        "and not overfitted to a particular subset. GonitSathi is the only system that "
        "simultaneously achieves 0.0% risk AND >35% first-error accuracy on <b>both</b> splits.",
        body_style,
    ))
    story.append(Spacer(1, 3))

    # ── TABLE V: Scaling Risk Effect ──
    story.append(Paragraph("<b>E. Scaling Effect on Baseline Risk</b>", h1_style))
    story.append(Paragraph(
        "<b>Table V: Scaling Effect on Unsupported-Commitment Risk: 202 vs. 411 Families</b>",
        h2_style,
    ))
    scaling_risk_data = [
        [
            cell("<b>System</b>", is_header=True),
            cell("<b>R_commit (202)</b>", is_header=True, align="center"),
            cell("<b>R_commit (411 Test)</b>", is_header=True, align="center"),
            cell("<b>Change</b>", is_header=True, align="center"),
        ],
        [cell("B0 (Rule/Template)"), cell("0.0%", align="center"), cell("0.0%", align="center"), cell("—", align="center")],
        [cell("B1 (Prompted LLM)"), cell("41.7%", align="center"), cell("56.5%", align="center", color_hex="#DC2626"), cell("+14.8 pp", align="center", color_hex="#DC2626")],
        [cell("B2 (Verify-then-Gen)"), cell("0.0%", align="center"), cell("0.0%", align="center"), cell("—", align="center")],
        [cell("B3 (Bayesian)"), cell("0.0%", align="center"), cell("0.0%", align="center"), cell("—", align="center")],
        [cell("B4 (IntelliCode)"), cell("56.3%", align="center"), cell("71.4%", align="center", color_hex="#DC2626"), cell("+15.2 pp", align="center", color_hex="#DC2626")],
        [cell("B5 (ScaffoldLM)"), cell("56.3%", align="center"), cell("71.4%", align="center", color_hex="#DC2626"), cell("+15.2 pp", align="center", color_hex="#DC2626")],
        [cell("B6 (SLOW)"), cell("56.3%", align="center"), cell("71.4%", align="center", color_hex="#DC2626"), cell("+15.2 pp", align="center", color_hex="#DC2626")],
        [cell("<b>GonitSathi (G)</b>"), cell("<b>0.0%</b>", align="center", color_hex="#047857"), cell("<b>0.0%</b>", align="center", color_hex="#047857"), cell("<b>Guaranteed</b>", align="center", color_hex="#047857")],
    ]
    t5 = make_ieee_table(scaling_risk_data, [126, 126, 126, 126])
    story.append(t5)
    story.append(Spacer(1, 3))

    # Figure 3: Scaling risk comparison
    story.append(Image(str(charts["scaling_risk"]), width=6.6 * 72 * 0.93, height=2.0 * 72 * 0.93))
    story.append(Paragraph(
        "<b>Fig. 3.</b> Scaling effect on false-attribution risk: memory-loop baselines (B4–B6) "
        "risk escalates from 56.3% to 71.4% (+15.2 pp) as the dataset grows from 202 to 411 families. "
        "GonitSathi maintains 0.0% risk at both scales — a structural guarantee of the governed controller.",
        caption_style,
    ))

    story.append(PageBreak())

    # =====================================================================
    # PAGE 4: DISCUSSION, TARGETS, RA CONTRIBUTION, SUPERVISOR REVIEW
    # =====================================================================
    story.append(Paragraph("<b>F. Discussion & Key Findings</b>", h1_style))
    story.append(Paragraph(
        "<b>1. Safety at Scale:</b> GonitSathi is the only system among the 8 evaluated architectures "
        "that maintains R_commit = 0.0% at both the 202-pilot and 411-full scales. "
        "The governed controller's safety guarantee is structural: the 2-observation corroboration rule "
        "prevents any unverified misconception from entering the persistent student model.<br/>"
        "<b>2. Improved Calibration:</b> The Multiclass Brier Score improves from 0.942 to 0.879, "
        "a 6.7% reduction. Broader topic coverage (BCS 32–50) introduces cleaner step structures "
        "that the symbolic verifier resolves with higher confidence.<br/>"
        "<b>3. Superior Error Localization:</b> GonitSathi achieves the highest first-error detection "
        "accuracy (35.7% test, 36.5% dev), 2.8–3.8 pp above the next-best systems, while "
        "memory-loop baselines B4–B6 score 0.0% (no fine-grained step provenance).<br/>"
        "<b>4. Memory-Loop Vulnerability:</b> B4, B5, B6 risk escalates from 56.3% to 71.4% "
        "as data diversity increases — confirmation bias amplifies with richer student interactions.<br/>"
        "<b>5. Interactive Latency:</b> Mean 76.31 ms (P95: 352.11 ms) remains below the 500 ms "
        "interactive threshold for real-time classroom deployment.",
        body_style,
    ))
    story.append(Spacer(1, 3))

    # Targets
    story.append(Paragraph("<b>G. Targets for Upcoming Updates</b>", h2_style))
    story.append(Paragraph(
        "1) <i>Threshold Tuning (Task 4.1)</i>: Calibrate decision threshold and entropy cap on frozen dev split.<br/>"
        "2) <i>Main Experiment E1 Finalization (Tasks 4.2 & 4.3)</i>: Produce final publication table with "
        "confidence intervals and effect sizes for ACML 2026 camera-ready.<br/>"
        "3) <i>Ablation Studies A1–A9 (Tasks 4.4 & 4.5)</i>: Systematically ablate evidence admission, "
        "contestation, probing, and symbolic verification.<br/>"
        "4) <i>Model Scaling (Task 5.2)</i>: Benchmark 1.7B, 4B, 8B open-weight LLMs on matched compute.",
        body_style,
    ))
    story.append(Spacer(1, 3))

    # RA Contribution table
    story.append(Paragraph("<b>H. Contribution by RA1, RA2, RA3, RA4</b>", h2_style))
    contrib_data = [
        [cell("<b>Work List</b>", is_header=True), cell("<b>RA Working</b>", is_header=True, align="center"), cell("<b>Comments / Deliverables</b>", is_header=True)],
        [cell("Literature Synthesis & Coordination"), cell("RA1, RA4", align="center"), cell("Hypothesis alignment RQ1–RQ5, claim ledger, Update 3 synthesis.")],
        [cell("BCS Benchmark Split Freezing"), cell("RA2, RA1", align="center"), cell("Topic-stratified, family-disjoint splits (207/102/102), 0% contamination.")],
        [cell("Full 411 Dataset Ingestion & Scaling"), cell("RA3, RA2", align="center"), cell("Scaled ingester across 41 exams; executed full 411-family evaluation.")],
        [cell("Comparative Baselines & Evaluation"), cell("RA4, RA3", align="center"), cell("Comparative evaluation of B0–B6 vs G; certified 112/112 tests.")],
    ]
    ct = Table(contrib_data, colWidths=[130, 70, 304])
    ct.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E3A8A")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CBD5E1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#FFFFFF"), colors.HexColor("#F8FAFC")]),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(ct)
    story.append(Spacer(1, 6))

    # Supervisor Review Box
    story.append(Paragraph("<b>I. Supervisor Review</b>", h2_style))
    review_rows = [
        [cell("<b>Evaluation Criteria</b>", is_header=True), cell("<b>Max Marks</b>", is_header=True, align="center"), cell("<b>Marks Given</b>", is_header=True, align="center")],
        [cell("Follow-up on previous update targets"), cell("2", align="center"), cell("")],
        [cell("Quality and depth of work done"), cell("3", align="center"), cell("")],
        [cell("Clarity and feasibility of next targets"), cell("2", align="center"), cell("")],
        [cell("Fair contribution breakdown (RA1–RA4)"), cell("2", align="center"), cell("")],
        [cell("Report presentation and formatting"), cell("1", align="center"), cell("")],
        [cell("<b>Total</b>"), cell("<b>10</b>", align="center"), cell("")],
    ]
    rt = Table(review_rows, colWidths=[334, 85, 85])
    rt.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#334155")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#94A3B8")),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]))

    sign_data = [
        [Paragraph("<b>Overall Rating:</b> &nbsp; [ ] Excellent &nbsp;&nbsp; [ ] Good &nbsp;&nbsp; [ ] Satisfactory &nbsp;&nbsp; [ ] Needs Improvement", callout_text)],
        [Paragraph("<b>Report Status:</b> &nbsp; [ ] Approved &nbsp;&nbsp; [ ] Approved with minor revisions &nbsp;&nbsp; [ ] Revise and resubmit", callout_text)],
        [Paragraph("<b>Supervisor Comments:</b><br/><br/>____________________________________________________________________________________<br/><br/>____________________________________________________________________________________", callout_text)],
        [Paragraph("<br/><b>Supervisor Signature:</b> ___________________________ &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; <b>Date:</b> ___________________", callout_text)],
    ]
    st = Table(sign_data, colWidths=[504])
    st.setStyle(TableStyle([
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))

    sup_box_data = [
        [Paragraph(
            "<b>Supervisor Review</b><br/><i>(To be filled by the supervisor only)</i>",
            ParagraphStyle("SupH", fontName=MAIN_FONT, fontSize=8.5, leading=11, alignment=1, textColor=colors.HexColor("#0F172A")),
        )],
        [Spacer(1, 2)],
        [rt],
        [Spacer(1, 2)],
        [st],
    ]
    sup_box = Table(sup_box_data, colWidths=[504])
    sup_box.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#64748B")),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(sup_box)

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"ACML 2026 Report compiled: {output_pdf_path}")


def main():
    repo_root = Path(__file__).resolve().parents[1]

    # Build the report
    report_pdf = repo_root / "docs" / "reports" / "update_3" / "update_3_report_acml.pdf"
    build_pdf_report(report_pdf)

    # Copy to Downloads
    downloads_dir = Path("C:/Users/Rayyan/Downloads")
    if downloads_dir.exists():
        dest = downloads_dir / "update_3_report_acml.pdf"
        with open(report_pdf, "rb") as f_in:
            data = f_in.read()
        with open(dest, "wb") as f_out:
            f_out.write(data)
        print(f"Copied to: {dest}")


if __name__ == "__main__":
    main()
