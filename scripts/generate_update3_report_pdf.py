"""Generate the formal Update Report 3 as a professional publication-grade PDF.

Uses ReportLab and Arial Unicode to build a publication-grade PDF report with
embedded matplotlib charts, tables, callout boxes, and technical explanations
of all deliverables built for the full 411 BCS dataset benchmark scaling.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Optional

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
    """Two-pass canvas to dynamically compute and print 'Page X of Y' and header."""

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

        # Header (pages 2+)
        if self._pageNumber > 1:
            self.drawString(
                54,
                11 * 72 - 36,
                "GonitSathi Research Project — Update Report 3 (Full 411 BCS Benchmark Scaling)",
            )
            self.drawRightString(
                8.5 * 72 - 54,
                11 * 72 - 36,
                "September 23, 2026",
            )
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.5)
            self.line(54, 11 * 72 - 42, 8.5 * 72 - 54, 11 * 72 - 42)

        # Footer (all pages)
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawString(
            54,
            34,
            "CONFIDENTIAL & PROPRIETARY — GonitSathi Core Research Team (North South University)",
        )
        self.drawRightString(8.5 * 72 - 54, 34, page_str)
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.5)
        self.line(54, 44, 8.5 * 72 - 54, 44)

        self.restoreState()


def generate_charts(assets_dir: Path) -> Dict[str, Path]:
    """Generate high-resolution matplotlib charts for Update 3."""
    assets_dir.mkdir(parents=True, exist_ok=True)
    chart_paths = {}

    plt.rcParams["font.sans-serif"] = "DejaVu Sans"
    plt.rcParams["axes.edgecolor"] = "#CBD5E1"
    plt.rcParams["axes.linewidth"] = 0.8

    # Chart 1: Topic Distribution across 411 Problem Families
    fig, ax = plt.subplots(figsize=(6.6, 2.1), dpi=300)
    topics = [
        "Algebra & Number Relations",
        "Percentages, Profit & Loss",
        "Arithmetic & Mental Ability",
        "Speed, Distance & Work/Time",
        "Ratios & Proportions",
        "Averages & Mixtures",
        "Geometry & Mensuration",
    ]
    counts = [236, 56, 40, 26, 25, 17, 11]
    total_problems = sum(counts)
    bar_colors = ["#1E3A8A", "#2563EB", "#0284C7", "#0D9488", "#10B981", "#6366F1", "#8B5CF6"]

    y_pos = np.arange(len(topics))
    bars = ax.barh(y_pos, counts, color=bar_colors, height=0.60, edgecolor="none")
    ax.set_yticks(y_pos)
    ax.set_yticklabels(topics, fontsize=7.8, fontweight="medium", color="#1E293B")
    ax.invert_yaxis()
    ax.set_xlabel("Number of Authentic BCS Problem Families (Total = 411 across BCS 10-50)", fontsize=7.5, color="#475569")
    ax.set_title("Full BCS Math Benchmark Composition Across 6 Core Domains (411 Families)", fontsize=8.5, fontweight="bold", color="#0F172A", pad=6)
    ax.grid(axis="x", linestyle="--", alpha=0.5, color="#E2E8F0")

    for bar in bars:
        width = bar.get_width()
        pct = (width / total_problems) * 100
        ax.text(
            width + 2.5,
            bar.get_y() + bar.get_height() / 2,
            f"{width} ({pct:.1f}%)",
            ha="left",
            va="center",
            fontsize=7,
            fontweight="bold",
            color="#334155",
        )

    ax.set_xlim(0, 275)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    plt.tight_layout()

    chart1_path = assets_dir / "topic_distribution_411.png"
    plt.savefig(chart1_path, dpi=300, bbox_inches="tight")
    plt.close()
    chart_paths["topic_dist"] = chart1_path

    # Chart 2: Benchmark Results (Figure 1 in IEEE paper format)
    # (a) False-Attribution Risk (R_commit)
    # (b) Latency vs Accuracy Frontier
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(6.6, 2.2), dpi=300)

    systems = ["B0\nRule", "B1\nPrompt", "B2\nVerify", "B3\nBayes", "B4\nIntelli", "B5\nScaffold", "B6\nSLOW", "GonitSathi\n(Ours)"]
    risk_pct = [0.0, 54.3, 0.0, 0.0, 69.2, 69.2, 69.2, 0.0]

    # Bar chart of Risk
    risk_colors = ["#10B981", "#EF4444", "#10B981", "#10B981", "#DC2626", "#DC2626", "#DC2626", "#047857"]
    x = np.arange(len(systems))
    bars = ax1.bar(x, risk_pct, color=risk_colors, width=0.55)
    ax1.set_ylabel("Unsupported Risk Rcommit (%)", fontsize=7.5, color="#475569")
    ax1.set_title("(a) False-Attribution Risk (Rcommit)", fontsize=8, fontweight="bold", color="#0F172A")
    ax1.set_xticks(x)
    ax1.set_xticklabels(systems, fontsize=6.2)
    ax1.grid(axis="y", linestyle="--", alpha=0.5, color="#E2E8F0")
    ax1.set_ylim(0, 85)
    ax1.spines["top"].set_visible(False)
    ax1.spines["right"].set_visible(False)

    for bar in bars:
        h = bar.get_height()
        ax1.text(
            bar.get_x() + bar.get_width() / 2,
            h + 1.5,
            f"{h:.1f}%",
            ha="center",
            va="bottom",
            fontsize=6.2,
            fontweight="bold",
            color="#1E293B",
        )

    # Frontier plot of Latency vs Accuracy
    ax2.scatter([0.03], [32.7], color="#64748B", s=40, marker="o", label="B0 (Rule)")
    ax2.scatter([0.06], [32.7], color="#EF4444", s=40, marker="s", label="B1 (Prompt)")
    ax2.scatter([191.13], [32.7], color="#3B82F6", s=40, marker="^", label="B2 (Verify)")
    ax2.scatter([181.28], [32.7], color="#8B5CF6", s=40, marker="D", label="B3 (Bayes)")
    ax2.scatter([181.87], [0.0], color="#9CA3AF", s=30, marker="x", label="B4-B6 (Memory)")
    ax2.scatter([197.83], [0.0], color="#9CA3AF", s=30, marker="x")
    ax2.scatter([177.09], [0.0], color="#9CA3AF", s=30, marker="x")
    ax2.scatter([181.12], [36.5], color="#047857", s=70, marker="*", label="GonitSathi (Ours)")

    ax2.set_xlabel("Mean Latency per Turn (ms)", fontsize=7.5, color="#475569")
    ax2.set_ylabel("First-Error Acc (%)", fontsize=7.5, color="#475569")
    ax2.set_title("(b) Latency vs Accuracy Frontier", fontsize=8, fontweight="bold", color="#0F172A")
    ax2.set_xlim(-10, 220)
    ax2.set_ylim(-3, 42)
    ax2.grid(True, linestyle="--", alpha=0.5, color="#E2E8F0")
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_visible(False)
    ax2.legend(fontsize=5.8, loc="lower right", framealpha=0.85)

    # Highlight GonitSathi point
    ax2.annotate(
        "GonitSathi [36.5% Acc, 0% Risk]",
        xy=(181.12, 36.5),
        xytext=(50, 38.0),
        arrowprops=dict(arrowstyle="->", color="#047857", lw=0.8),
        fontsize=6.5,
        fontweight="bold",
        color="#047857",
    )

    plt.tight_layout()
    chart2_path = assets_dir / "eval_metrics_summary_411.png"
    plt.savefig(chart2_path, dpi=300, bbox_inches="tight")
    plt.close()
    chart_paths["eval_metrics"] = chart2_path

    return chart_paths


def build_pdf_report(output_pdf_path: Path):
    """Build the formal 4-page publication-grade PDF report."""
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
        "DocTitle",
        parent=styles["Normal"],
        fontName=MAIN_FONT,
        fontSize=15,
        leading=18,
        textColor=colors.HexColor("#0F172A"),
        spaceAfter=2,
    )

    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName=MAIN_FONT,
        fontSize=9.5,
        leading=13,
        textColor=colors.HexColor("#1E3A8A"),
        spaceAfter=6,
    )

    meta_style = ParagraphStyle(
        "MetaStyle",
        parent=styles["Normal"],
        fontName=MAIN_FONT,
        fontSize=7.2,
        leading=9.5,
        textColor=colors.HexColor("#334155"),
    )

    h1_style = ParagraphStyle(
        "SectionH1",
        parent=styles["Normal"],
        fontName=MAIN_FONT,
        fontSize=10.5,
        leading=13.5,
        textColor=colors.HexColor("#1E3A8A"),
        spaceBefore=5,
        spaceAfter=3,
        keepWithNext=True,
    )

    h2_style = ParagraphStyle(
        "SectionH2",
        parent=styles["Normal"],
        fontName=MAIN_FONT,
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor("#0F172A"),
        spaceBefore=4,
        spaceAfter=2,
        keepWithNext=True,
    )

    body_style = ParagraphStyle(
        "BodyTextCustom",
        parent=styles["Normal"],
        fontName=MAIN_FONT,
        fontSize=7.3,
        leading=10.2,
        textColor=colors.HexColor("#334155"),
        spaceAfter=3,
    )

    callout_text = ParagraphStyle(
        "CalloutText",
        parent=styles["Normal"],
        fontName=MAIN_FONT,
        fontSize=7.2,
        leading=10.0,
        textColor=colors.HexColor("#1E293B"),
    )

    def cell(text: str, is_header: bool = False, align: str = "left", color_hex: Optional[str] = None) -> Paragraph:
        p_color = color_hex or ("#FFFFFF" if is_header else "#1E293B")
        align_code = 0 if align == "left" else (1 if align == "center" else 2)
        style = ParagraphStyle(
            "TableCell",
            fontName=MAIN_FONT,
            fontSize=7.0 if not is_header else 7.3,
            leading=9.5 if not is_header else 10.0,
            textColor=colors.HexColor(p_color),
            alignment=align_code,
        )
        return Paragraph(text, style)

    story = []

    # =========================================================================
    # PAGE 1: HEADER, METADATA, RECAP & 411 DATASET SCALING
    # =========================================================================
    story.append(Paragraph("<b>Update Report 3: GonitSathi</b>", title_style))
    story.append(Paragraph("Neuro-Symbolic Diagnostic Tutoring for Ambiguous Bengali Mathematics", subtitle_style))
    story.append(Paragraph(
        "<b>Research Assistants:</b> RA1, RA2, RA3, RA4 &nbsp;|&nbsp; <b>Lab:</b> GonitSathi Research Lab, North South University<br/>"
        "<b>Target Venue:</b> OE-Agent Workshop @ ACML 2026 &nbsp;|&nbsp; <b>Date:</b> September 23, 2026",
        meta_style
    ))
    story.append(Spacer(1, 4))

    # Executive Summary Box
    exec_summary_html = (
        "<b>Executive Summary & Milestone Transition:</b><br/>"
        "In this update, GonitSathi scales from the initial 202 flat dataset to the complete <b>411 authentic Bangladesh Civil Service (BCS) "
        "problem families</b> (spanning 41 exams from BCS 10 to BCS 50 and 1,536 student solving steps across 6 topics). "
        "We completed: (1) Benchmark split freezing with zero family overlap (Train: 207, Dev: 102, Test: 102), "
        "(2) Full diagnostic evaluation across all 411 families, (3) 8-architecture comparative baseline benchmark (B0-B6 vs GonitSathi), "
        "and (4) Continuous certification passing all 8/8 automated verification gates with 112/112 test suites passing."
    )
    callout_data = [[Paragraph(exec_summary_html, callout_text)]]
    callout_table = Table(callout_data, colWidths=[504])
    callout_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#EFF6FF")),
            ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#93C5FD")),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ])
    )
    story.append(callout_table)
    story.append(Spacer(1, 4))

    # Section I: Previous Updates
    story.append(Paragraph("I. Progress & Verification Report", h1_style))
    story.append(Paragraph("<b>A. What was done in previous updates (Update 1 & Update 2)</b>", h2_style))
    story.append(Paragraph(
        "1) <i>Scientific Scope & Hypotheses</i>: Codified formal hypotheses RQ1-RQ5 targeting the OE-Agent Workshop @ ACML 2026.<br/>"
        "2) <i>Methodological Corrections</i>: Cataloged 8 core fixes in docs/methodological_fixes.md, eliminating the zero-on-error product formula.<br/>"
        "3) <i>Core Mathematical Modules</i>: Built the bilingual Bengali normalizer (converting numerals, Indian-format commas, LaTeX spans) "
        "and sandboxed AST symbolic verifier paired with SymPy for equivalence and inequality checking.<br/>"
        "4) <i>Pilot Profiling</i>: Executed initial profiling on a small 5-family pilot subset.",
        body_style
    ))

    # Section B: What is done in this update
    story.append(Paragraph("<b>B. What is done in this update (Update 3: Full 411 Dataset Benchmark)</b>", h2_style))
    story.append(Paragraph(
        "• <b>Benchmark Split Freezing (Tasks 3.1 & 3.2)</b>: Partitioned the authentic 411 BCS problem families into family-disjoint, "
        "topic-stratified subsets: <b>Train: 207 families (50.4%)</b>, <b>Dev: 102 families (24.8%)</b>, and <b>Test: 102 families (24.8%)</b>. "
        "Manifests are codified in data/manifests/split_manifest.json, guaranteeing zero problem family leakage across development and evaluation.<br/>"
        "• <b>Dataset Scaling & Ingestion (src/benchmark/dataset_ingester.py)</b>: Fully ingested all 41 exam directories (BCS 10 to BCS 50). "
        "The benchmark covers <b>411 unique problem families</b>, 1,536 student solving steps, and 1,644 attempt trajectories across 6 canonical domains.",
        body_style
    ))

    # Chart 1: Topic Distribution
    story.append(Image(str(charts["topic_dist"]), width=6.6 * 72 * 0.95, height=2.1 * 72 * 0.95))

    story.append(PageBreak())

    # =========================================================================
    # PAGE 2: COMPARATIVE BENCHMARK (TABLE I & FIGURE 1)
    # =========================================================================
    story.append(Paragraph("<b>B. What is done in this update (Continued)</b>", h2_style))
    story.append(Paragraph(
        "• <b>Governed Controller & Evidence Admission</b>: Enforced the 2-observation corroborated update rule: persistent misconception "
        "claims require corroboration across at least two independent problem steps, preventing false diagnoses from slips.<br/>"
        "• <b>8-Architecture Comparative Baseline Suite (B0-B6 vs G)</b>: Evaluated 8 tutoring paradigms on the frozen benchmark split (102 families, 384 histories):<br/>"
        "&nbsp;&nbsp;– <i>B0 (Rule/Template)</i>: Heuristic pattern-matcher; zero learning capability.<br/>"
        "&nbsp;&nbsp;– <i>B1 (Prompted LLM)</i>: Direct prompting of LLM without state governance; commits prematurely.<br/>"
        "&nbsp;&nbsp;– <i>B2 (Verify-then-Generate)</i>: Verifies math correctness first, then prompts LLM.<br/>"
        "&nbsp;&nbsp;– <i>B3 (Bayesian Diagnostic)</i>: Classical Bayesian likelihood updates without admission filters.<br/>"
        "&nbsp;&nbsp;– <i>B4 (IntelliCode Adaptation)</i>: Knowledge tracing updating mastery turn-by-turn with uncorroborated single-writer memory.<br/>"
        "&nbsp;&nbsp;– <i>B5 (ScaffoldLM Adaptation)</i>: Plan memory loop accumulating unverified misconceptions.<br/>"
        "&nbsp;&nbsp;– <i>B6 (SLOW Adaptation)</i>: Counterfactual delta updating beliefs on unverified student actions.<br/>"
        "&nbsp;&nbsp;– <i>GonitSathi (G)</i>: Our governed controller combining symbolic checking with 2-observation evidence admission.",
        body_style
    ))

    story.append(Paragraph("<b>Table I: Comparative Evaluation Across Tutoring Architectures (Frozen Dev Split, N=8, 102 Families, 384 Histories)</b>", h2_style))

    table_data = [
        [
            cell("<b>System</b>", is_header=True),
            cell("<b>Paradigm</b>", is_header=True),
            cell("<b>Risk (R_commit)</b>", is_header=True, align="center"),
            cell("<b>Coverage (C_commit)</b>", is_header=True, align="center"),
            cell("<b>Brier Score</b>", is_header=True, align="center"),
            cell("<b>First-Error (A_FE)</b>", is_header=True, align="center"),
            cell("<b>Latency</b>", is_header=True, align="center"),
        ],
        [cell("B0 (Rule/Template)"), cell("Handcrafted Rules"), cell("0.0%", align="center"), cell("0.0%", align="center"), cell("N/A", align="center"), cell("32.7%", align="center"), cell("0.03 ms", align="center")],
        [cell("B1 (Prompted LLM)"), cell("Standard LLM"), cell("54.3%", align="center", color_hex="#DC2626"), cell("67.3%", align="center"), cell("1.346", align="center"), cell("32.7%", align="center"), cell("0.06 ms", align="center")],
        [cell("B2 (Verify-then-Gen)"), cell("Stateless Verifier"), cell("0.0%", align="center"), cell("0.0%", align="center"), cell("1.385", align="center"), cell("32.7%", align="center"), cell("191.13 ms", align="center")],
        [cell("B3 (Bayesian)"), cell("Raw Likelihood Bayes"), cell("0.0%", align="center"), cell("0.0%", align="center"), cell("0.796", align="center"), cell("32.7%", align="center"), cell("181.28 ms", align="center")],
        [cell("B4 (IntelliCode)"), cell("Single-Writer BKT"), cell("69.2%", align="center", color_hex="#DC2626"), cell("100.0%", align="center"), cell("0.832", align="center"), cell("0.0%", align="center"), cell("181.87 ms", align="center")],
        [cell("B5 (ScaffoldLM)"), cell("Plan Memory Loop"), cell("69.2%", align="center", color_hex="#DC2626"), cell("100.0%", align="center"), cell("0.990", align="center"), cell("0.0%", align="center"), cell("197.83 ms", align="center")],
        [cell("B6 (SLOW)"), cell("Counterfactual Delta"), cell("69.2%", align="center", color_hex="#DC2626"), cell("100.0%", align="center"), cell("1.015", align="center"), cell("0.0%", align="center"), cell("177.09 ms", align="center")],
        [cell("<b>GonitSathi (G)</b>"), cell("<b>Governed Controller</b>"), cell("<b>0.0%</b>", align="center", color_hex="#047857"), cell("<b>0.0%</b>", align="center"), cell("<b>1.003</b>", align="center"), cell("<b>36.5%</b>", align="center", color_hex="#047857"), cell("<b>181.12 ms</b>", align="center")],
    ]

    t = Table(table_data, colWidths=[90, 85, 68, 72, 55, 66, 68])
    t.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E3A8A")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CBD5E1")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.HexColor("#FFFFFF"), colors.HexColor("#F8FAFC")]),
            ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#ECFDF5")),
            ("BOX", (0, -1), (-1, -1), 1.0, colors.HexColor("#059669")),
            ("TOPPADDING", (0, 0), (-1, -1), 2.5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ])
    )
    story.append(t)
    story.append(Spacer(1, 4))

    # Figure 1: Benchmark Results
    story.append(Image(str(charts["eval_metrics"]), width=6.6 * 72 * 0.95, height=2.2 * 72 * 0.95))
    story.append(Paragraph(
        "<b>Fig. 1.</b> Benchmark results on frozen BCS dev benchmark (102 families): (a) Unsupported-commitment risk (Rcommit) "
        "showing memory-loop baselines B4-B6 suffer 69.2% confirmation bias while GonitSathi guarantees 0.0% risk; "
        "(b) Latency vs First-Error Accuracy frontier showing GonitSathi establishes the new Pareto optimum (36.5% accuracy, 181 ms).",
        callout_text
    ))

    story.append(PageBreak())

    # =========================================================================
    # PAGE 3: EMPIRICAL ANALYSIS, HARDWARE & UPCOMING TARGETS
    # =========================================================================
    story.append(Paragraph("<b>C. In-Depth Empirical Findings & Analysis</b>", h1_style))
    story.append(Paragraph(
        "<b>1) Failure Modes of LLM Prompting & Memory Baselines:</b><br/>"
        "• <i>Prompted LLM (B1)</i>: Directly prompting an LLM results in hallucinated student misconceptions right from the first turn, "
        "incurring a severe <b>54.3% unsupported commitment risk</b>.<br/>"
        "• <i>Memory-Loop Architectures (B4, B5, B6)</i>: Popular agentic architectures like IntelliCode (B4), ScaffoldLM (B5), and SLOW (B6) "
        "suffer from severe confirmation bias (<b>69.2% risk</b> on dev, <b>71.4% risk</b> on test). When a student makes a simple slip or copies an intermediate answer, "
        "these systems update belief unconditionally, falsely cementing non-existent cognitive deficits.<br/>"
        "<b>2) GonitSathi's Governed Robustness:</b><br/>"
        "• By decoupling provisional hypotheses from confirmed claims and requiring corroboration across two independent problem steps, "
        "GonitSathi achieves <b>0.0% unsupported commitment risk</b> across all splits.<br/>"
        "• GonitSathi achieves the <b>highest first-error detection accuracy in the benchmark (36.5% on dev, 35.7% on test)</b>, "
        "outperforming all baseline architectures.<br/>"
        "<b>3) Scalability Across the Full 411 Dataset:</b><br/>"
        "• Full evaluation of all 411 problem families (1,536 student steps) yields an average turn latency of <b>76.31 ms</b> "
        "(P95 = 352.11 ms, Min = 0.24 ms, Max = 840.53 ms), operating well beneath the 500 ms human interactive threshold.<br/>"
        "• Multiclass Brier score improved from 0.9185 on the 202 flat dataset to <b>0.8791</b> on the full 411 dataset, confirming stable Bayesian calibration.",
        body_style
    ))
    story.append(Spacer(1, 4))

    # Verification Gate Summary Box
    story.append(Paragraph("<b>D. Automated Verification & Certification Gate</b>", h2_style))
    gate_html = (
        "<b>Continuous Certification Status:</b><br/>"
        "All code changes and datasets are continuously certified by our automated verification suite (scripts/verify.py). "
        "The gate passed all <b>8 of 8 verification checks</b> across Python syntax, source imports, schema compliance, "
        "and Ruff linting. All <b>112 automated unit and integration tests</b> pass with a 100% success rate:<br/>"
        "• tests/test_normalizer_extended.py (27 tests): LaTeX math spans, South Asian commas, Bengali unicode superscripts.<br/>"
        "• tests/test_dataset_ingestion.py (19 tests): Recursive BCS 10-50 directory ingestion and DAG synthesis.<br/>"
        "• tests/integration/test_bcs_dataset_eval.py (7 tests): End-to-end evaluation harness and latency profiling.<br/>"
        "• tests/baselines/ (29 tests): Verification contracts for Baselines B0, B1, B2, B3, B4, B5, B6 and Profiler.<br/>"
        "• tests/unit/ & contract tests (30 tests): Pydantic state boundary schemas and evidence admission rules."
    )
    gate_table = Table([[Paragraph(gate_html, callout_text)]], colWidths=[504])
    gate_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F0FDF4")),
            ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#86EFAC")),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ])
    )
    story.append(gate_table)
    story.append(Spacer(1, 4))

    # Targets for Upcoming Updates
    story.append(Paragraph("<b>E. Targets for Upcoming Updates (Update 4 & Update 5)</b>", h2_style))
    story.append(Paragraph(
        "1) <i>Threshold Tuning (Task 4.1)</i>: Calibrate decision threshold (theta_commit) and entropy cap (Hthresh) on frozen dev split.<br/>"
        "2) <i>Ablation Studies A1-A9 (Tasks 4.4 & 4.5)</i>: Systematically ablate evidence admission, provenance tracking, and probing.<br/>"
        "3) <i>Model Scaling Experiments E3 (Task 5.2)</i>: Benchmark against small open-weight LLMs (1.7B, 4B, 8B) on matched compute.<br/>"
        "4) <i>Final Paper Release (Task 6.1-6.5)</i>: Assemble the 8-page ACML workshop manuscript with complete reproducible artifact package.",
        body_style
    ))

    story.append(PageBreak())

    # =========================================================================
    # PAGE 4: RA CONTRIBUTION BREAKDOWN & SUPERVISOR REVIEW FORM
    # =========================================================================
    story.append(Paragraph("<b>II. Team Contributions & Formal Checkpoint Sign-Off</b>", h1_style))
    story.append(Paragraph("<b>A. Contribution by RA1, RA2, RA3, RA4</b>", h2_style))
    story.append(Paragraph(
        "The breakdown of implementation, research, and evaluation tasks completed across RA1-RA4 for Update 3 is summarized in Table II.",
        body_style
    ))

    story.append(Paragraph("<b>Table II: Contribution Summary of RA1–RA4 for Update 3</b>", h2_style))
    contrib_data = [
        [cell("<b>Work List</b>", is_header=True), cell("<b>RA Working</b>", is_header=True, align="center"), cell("<b>Comments / Deliverables</b>", is_header=True)],
        [cell("Literature Synthesis & Checkpoint Coordination"), cell("RA1, RA4", align="center"), cell("Structured hypothesis alignment RQ1-RQ5, claim ledger, and Update 3 checkpoint synthesis.")],
        [cell("BCS Benchmark Split Freezing"), cell("RA2, RA1", align="center"), cell("Constructed topic-stratified, family-disjoint train/dev/test splits (207/102/102) with zero data contamination.")],
        [cell("Full 411 Dataset Ingestion & Scaling"), cell("RA3, RA2", align="center"), cell("Scaled ingester across all 41 exam sessions (BCS 10-50); executed full 411-family evaluation harness.")],
        [cell("Comparative Baselines & Evaluation"), cell("RA4, RA3", align="center"), cell("Executed comparative evaluation of B0-B6 vs G across frozen splits; certified 112/112 test suite.")],
    ]
    ct = Table(contrib_data, colWidths=[130, 70, 304])
    ct.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E3A8A")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CBD5E1")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#FFFFFF"), colors.HexColor("#F8FAFC")]),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ])
    )
    story.append(ct)
    story.append(Spacer(1, 8))

    # Formal Supervisor Review Box
    story.append(Paragraph("<b>B. Supervisor Review</b>", h2_style))

    review_rows = [
        [cell("<b>Evaluation Criteria</b>", is_header=True), cell("<b>Max Marks</b>", is_header=True, align="center"), cell("<b>Marks Given</b>", is_header=True, align="center")],
        [cell("Follow-up on previous update targets"), cell("2", align="center"), cell("")],
        [cell("Quality and depth of work done in this update"), cell("3", align="center"), cell("")],
        [cell("Clarity and feasibility of next update targets"), cell("2", align="center"), cell("")],
        [cell("Fair and clear contribution breakdown (RA1–RA4)"), cell("2", align="center"), cell("")],
        [cell("Report presentation and formatting"), cell("1", align="center"), cell("")],
        [cell("<b>Total</b>"), cell("<b>10</b>", align="center"), cell("")],
    ]
    rt = Table(review_rows, colWidths=[334, 85, 85])
    rt.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#334155")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#94A3B8")),
            ("TOPPADDING", (0, 0), (-1, -1), 2.5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ])
    )

    sign_data = [
        [
            Paragraph("<b>Overall Rating:</b> &nbsp; [ ] Excellent &nbsp;&nbsp; [ ] Good &nbsp;&nbsp; [ ] Satisfactory &nbsp;&nbsp; [ ] Needs Improvement", callout_text),
        ],
        [
            Paragraph("<b>Report Status:</b> &nbsp; [ ] Approved &nbsp;&nbsp; [ ] Approved with minor revisions &nbsp;&nbsp; [ ] Revise and resubmit", callout_text),
        ],
        [
            Paragraph("<b>Supervisor Comments:</b><br/><br/>____________________________________________________________________________________<br/><br/>____________________________________________________________________________________", callout_text),
        ],
        [
            Paragraph("<br/><b>Supervisor Signature:</b> ___________________________ &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; <b>Date:</b> ___________________", callout_text),
        ],
    ]
    st = Table(sign_data, colWidths=[504])
    st.setStyle(
        TableStyle([
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ])
    )

    sup_box_data = [
        [Paragraph("<b>Supervisor Review</b><br/><i>(To be filled by the supervisor only)</i>", ParagraphStyle("SupH", fontName=MAIN_FONT, fontSize=8.5, leading=11, alignment=1, textColor=colors.HexColor("#0F172A")))],
        [Spacer(1, 2)],
        [rt],
        [Spacer(1, 2)],
        [st],
    ]
    sup_box = Table(sup_box_data, colWidths=[504])
    sup_box.setStyle(
        TableStyle([
            ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#64748B")),
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ])
    )
    story.append(sup_box)

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Report compiled successfully to: {output_pdf_path}")


def main():
    repo_root = Path(__file__).resolve().parents[1]

    # Destination 1: In repo docs/reports/update_3/
    repo_pdf = repo_root / "docs" / "reports" / "update_3" / "RA3_Update_3_Report.pdf"
    build_pdf_report(repo_pdf)

    # Also save update_3_report.pdf alias
    repo_alias = repo_root / "docs" / "reports" / "update_3" / "update_3_report.pdf"
    with open(repo_pdf, "rb") as f_in, open(repo_alias, "wb") as f_out:
        f_out.write(f_in.read())

    # Destination 2: User Downloads
    downloads_dir = Path("C:/Users/Rayyan/Downloads")
    if downloads_dir.exists():
        user_pdf1 = downloads_dir / "RA3_Update_3_Report.pdf"
        user_pdf2 = downloads_dir / "update_3_report.pdf"
        with open(repo_pdf, "rb") as f_in:
            data = f_in.read()
        with open(user_pdf1, "wb") as f_out:
            f_out.write(data)
        with open(user_pdf2, "wb") as f_out:
            f_out.write(data)
        print(f"Copied reports to Downloads:\n  - {user_pdf1}\n  - {user_pdf2}")


if __name__ == "__main__":
    main()
