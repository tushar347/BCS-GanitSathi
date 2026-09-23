"""Generate publication-quality charts for ACML 2026 Update 3 Report with zero overlaps.
"""
from pathlib import Path
import shutil
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

def generate_all_charts():
    repo_root = Path(__file__).resolve().parent.parent
    assets_dir = repo_root / 'docs' / 'reports' / 'update_3' / 'report_assets'
    assets_dir.mkdir(parents=True, exist_ok=True)
    downloads_assets = Path(r'C:\Users\Rayyan\Downloads\report_assets')
    downloads_assets.mkdir(parents=True, exist_ok=True)

    plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
    plt.rcParams['axes.edgecolor'] = '#555555'
    plt.rcParams['axes.linewidth'] = 0.8

    # ══════════════════════════════════════════════════════
    # 1. DATASET GROWTH BAR CHART (bar_dataset_growth.png)
    # ══════════════════════════════════════════════════════
    fig, ax = plt.subplots(figsize=(5.6, 2.6), dpi=300)
    metrics = ['Exam Sessions', 'Problem Families', 'Solving Steps']
    u2 = [22, 202, 788]
    u3 = [41, 411, 1536]
    x = np.arange(len(metrics))
    w = 0.32

    ax.bar(x - w/2, u2, w, color='#93C5FD', label='Update 2 (202 Dataset)', edgecolor='white', linewidth=0.8)
    ax.bar(x + w/2, u3, w, color='#1E3A8A', label='Update 3 (411 Dataset)', edgecolor='white', linewidth=0.8)

    for i, (v2, v3) in enumerate(zip(u2, u3)):
        pct = ((v3 - v2) / v2) * 100
        # Left bar value (Update 2)
        ax.annotate(f"{v2:,}", xy=(x[i] - w/2, v2), xytext=(0, 4), textcoords='offset points',
                    ha='center', va='bottom', fontsize=7.5, color='#475569', fontweight='medium')
        # Right bar value (Update 3)
        ax.annotate(f"{v3:,}", xy=(x[i] + w/2, v3), xytext=(0, 4), textcoords='offset points',
                    ha='center', va='bottom', fontsize=7.5, color='#1E293B', fontweight='bold')
        # Right bar percentage increase
        ax.annotate(f"+{pct:.0f}%", xy=(x[i] + w/2, v3), xytext=(0, 16), textcoords='offset points',
                    ha='center', va='bottom', fontsize=7, color='#047857', fontweight='bold')

    ax.set_xticks(x)
    ax.set_xticklabels(metrics, fontsize=8.5, fontweight='medium', color='#0F172A')
    ax.set_title('Dataset Scaling: Update 2 vs. Update 3', fontsize=9.5, fontweight='bold', pad=8, color='#0F172A')
    ax.set_ylim(0, 2000)
    ax.set_ylabel('Count', fontsize=8, color='#475569')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(axis='y', linestyle='--', alpha=0.35)
    ax.legend(fontsize=7.8, loc='upper left', framealpha=0.92)
    plt.tight_layout()
    chart1_file = assets_dir / 'bar_dataset_growth.png'
    plt.savefig(chart1_file, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved: {chart1_file}")

    # ══════════════════════════════════════════════════════
    # 2. TOPIC DISTRIBUTION PIE CHART (pie_topic_distribution.png)
    # ══════════════════════════════════════════════════════
    fig, ax = plt.subplots(figsize=(6.2, 2.7), dpi=300)
    topic_names = [
        'Algebra & Number Systems',
        'Percentages, Profit & Loss',
        'Arithmetic & Mental Ability',
        'Ratios & Proportions',
        'Speed, Distance & Work/Time',
        'Averages & Mixtures',
        'Geometry & Mensuration'
    ]
    counts = [236, 56, 40, 29, 26, 17, 7]
    total = sum(counts)
    pcts = [(c / total) * 100 for c in counts]
    legend_labels = [f'{name} ({c}, {p:.1f}%)' for name, c, p in zip(topic_names, counts, pcts)]
    colors_pie = ['#1E3A8A', '#2563EB', '#0284C7', '#0D9488', '#10B981', '#6366F1', '#8B5CF6']
    explode = (0.03, 0.02, 0.02, 0.02, 0.02, 0.04, 0.06)

    def autopct_filter(pct):
        return f'{pct:.1f}%' if pct >= 5.0 else ''

    wedges, texts, autotexts = ax.pie(
        counts,
        autopct=autopct_filter,
        startangle=135,
        pctdistance=0.72,
        colors=colors_pie,
        explode=explode,
        wedgeprops={'edgecolor': 'white', 'linewidth': 1.2}
    )
    for at in autotexts:
        at.set_fontsize(7)
        at.set_fontweight('bold')
        at.set_color('white')

    ax.legend(
        wedges,
        legend_labels,
        title='Mathematical Domains (411 Total)',
        title_fontsize=7.5,
        loc='center left',
        bbox_to_anchor=(0.92, 0.5),
        fontsize=6.8,
        frameon=True,
        framealpha=0.95
    )
    ax.set_title('Topic Distribution: 411 BCS Problem Families (BCS 10–50)', fontsize=9.5, fontweight='bold', pad=10, color='#0F172A')
    plt.tight_layout()
    chart2_file = assets_dir / 'pie_topic_distribution.png'
    plt.savefig(chart2_file, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved: {chart2_file}")

    # ══════════════════════════════════════════════════════
    # 3. SCALING RISK BAR CHART (bar_risk_scaling.png)
    # ══════════════════════════════════════════════════════
    fig, ax = plt.subplots(figsize=(6.4, 2.5), dpi=300)
    systems = ['B0\n(Rule)', 'B1\n(Prompt)', 'B2\n(Verify)', 'B3\n(Bayes)', 'B4\n(Intelli)', 'B5\n(Scaffold)', 'B6\n(SLOW)', 'GonitSathi\n(Ours)']
    risk_202 = [0.0, 41.7, 0.0, 0.0, 56.3, 56.3, 56.3, 0.0]
    risk_411 = [0.0, 56.5, 0.0, 0.0, 71.4, 71.4, 71.4, 0.0]
    x = np.arange(len(systems))
    w = 0.32

    ax.bar(x - w/2, risk_202, w, color='#93C5FD', label='202 Families (Update 2)', edgecolor='white', linewidth=0.5)
    ax.bar(x + w/2, risk_411, w, color='#1E3A8A', label='411 Families (Update 3)', edgecolor='white', linewidth=0.5)

    for i, (r2, r4) in enumerate(zip(risk_202, risk_411)):
        if r4 > 0 and r4 > r2:
            diff = r4 - r2
            ax.annotate(f'+{diff:.1f}pp', xy=(x[i] + w/2, r4), xytext=(0, 4), textcoords='offset points',
                        ha='center', va='bottom', fontsize=6.5, fontweight='bold', color='#DC2626')

    ax.set_ylabel('Unsupported-Commitment Risk (%)', fontsize=8, color='#475569')
    ax.set_title('Scaling Effect on False-Attribution Risk: 202 vs. 411 Families', fontsize=9.2, fontweight='bold', pad=8, color='#0F172A')
    ax.set_xticks(x)
    ax.set_xticklabels(systems, fontsize=7.2, color='#1E293B')
    ax.set_ylim(0, 95)
    ax.grid(axis='y', linestyle='--', alpha=0.35)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.legend(fontsize=7.2, loc='upper left', ncol=2, framealpha=0.92, columnspacing=1.0)
    plt.tight_layout()
    chart3_file = assets_dir / 'bar_risk_scaling.png'
    plt.savefig(chart3_file, dpi=300, bbox_inches='tight')
    # Also save as scaling_risk_comparison.png for consistency
    plt.savefig(assets_dir / 'scaling_risk_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved: {chart3_file}")

    # ══════════════════════════════════════════════════════
    # 4. SCATTER LATENCY VS ACCURACY (scatter_latency_accuracy.png)
    # ══════════════════════════════════════════════════════
    fig, ax = plt.subplots(figsize=(5.2, 3.2), dpi=300)
    data = {
        'B0 (Rule)': (0.01, 32.9, '#64748B', 'o', 50),
        'B1 (Prompt)': (0.07, 32.9, '#EF4444', 's', 50),
        'B2 (Verify)': (151.37, 31.4, '#3B82F6', '^', 50),
        'B3 (Bayes)': (166.82, 31.4, '#8B5CF6', 'D', 50),
        'B4 (Intelli)': (127.03, 0.0, '#9CA3AF', 'x', 40),
        'B5 (Scaffold)': (127.18, 0.0, '#9CA3AF', 'x', 40),
        'B6 (SLOW)': (132.72, 0.0, '#9CA3AF', 'x', 40),
        'GonitSathi': (162.0, 35.7, '#047857', '*', 120),
    }
    for name, (lat, acc, col, mk, sz) in data.items():
        lbl = name if name not in ('B5 (Scaffold)', 'B6 (SLOW)') else None
        ax.scatter([lat], [acc], color=col, s=sz, marker=mk, label=lbl, zorder=5)
    ax.annotate('GonitSathi\n[35.7% Acc, 0% Risk]', xy=(162.0, 35.7), xytext=(40, 40),
                arrowprops=dict(arrowstyle='->', color='#047857', lw=1), fontsize=7.5, fontweight='bold', color='#047857')
    ax.annotate('B4-B6: 0% Accuracy\n71.4% Risk', xy=(129, 0), xytext=(30, 8),
                arrowprops=dict(arrowstyle='->', color='#DC2626', lw=0.8), fontsize=7, color='#DC2626')
    ax.set_xlabel('Mean Latency per Turn (ms)', fontsize=8)
    ax.set_ylabel('First-Error Detection Accuracy (%)', fontsize=8)
    ax.set_title('Latency vs Accuracy Frontier (Test Split, 411 Families)', fontsize=9, fontweight='bold', pad=6)
    ax.set_xlim(-10, 200)
    ax.set_ylim(-4, 48)
    ax.grid(True, linestyle='--', alpha=0.4)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.legend(fontsize=6.5, loc='upper left', framealpha=0.9)
    plt.tight_layout()
    chart4_file = assets_dir / 'scatter_latency_accuracy.png'
    plt.savefig(chart4_file, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved: {chart4_file}")

    # Copy all generated assets to Downloads\report_assets
    for f in assets_dir.glob('*.png'):
        dest = downloads_assets / f.name
        shutil.copy2(f, dest)
        print(f"Copied to Downloads: {dest}")

if __name__ == '__main__':
    generate_all_charts()
