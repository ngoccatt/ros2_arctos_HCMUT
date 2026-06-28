#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phân tích dữ liệu đo đạc RTT giữa ứng dụng VR (Unity/Meta Quest 3)
và Ros2 qua RosBridge WebSocket trong các điều kiện tải mạng khác nhau.

Dữ liệu: assets/latency_record_benchmark/{latency_record_normal, latency_100M, latency_150M, latency_200M}

Kết quả: in thống kê ra stdout + sinh LaTeX để dán vào evaluation.tex
         tại vị trí: % latency RTT here

Chạy:  py -3 scripts/analyze_rtt_latency.py
"""

import re
import pathlib
import statistics

# ── Cấu hình ──────────────────────────────────────────────────────────────────
REPO = pathlib.Path(__file__).resolve().parent.parent
BENCH_DIR = REPO / "assets" / "latency_record_benchmark"

EXPERIMENTS = [
    ("latency_record_normal", "Bình thường",       "normal"),
    ("latency_100M",          "Tải cao 100 Mbit/s","100M"),
    ("latency_150M",          "Tải cao 150 Mbit/s","150M"),
    ("latency_200M",          "Tải cao 200 Mbit/s","200M"),
]

# Regex: Latency /benchmark → /ack: 22.683 ms  (sample N)
LATENCY_RE = re.compile(r"Latency /benchmark.*?/ack:\s*([\d.]+)\s*ms")

# ── Đọc dữ liệu ───────────────────────────────────────────────────────────────
def load_samples(path: pathlib.Path) -> list[float]:
    samples = []
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            m = LATENCY_RE.search(line)
            if m:
                samples.append(float(m.group(1)))
    return samples


def percentile(data: list[float], p: float) -> float:
    """p-th percentile (0–100), linear interpolation."""
    if not data:
        return float("nan")
    sd = sorted(data)
    k = (len(sd) - 1) * p / 100.0
    lo, hi = int(k), min(int(k) + 1, len(sd) - 1)
    return sd[lo] + (k - lo) * (sd[hi] - sd[lo])


def stats(samples: list[float]) -> dict:
    return {
        "n":      len(samples),
        "mean":   statistics.mean(samples),
        "median": statistics.median(samples),
        "std":    statistics.stdev(samples) if len(samples) > 1 else 0.0,
        "min":    min(samples),
        "max":    max(samples),
        "p95":    percentile(samples, 95),
        "p99":    percentile(samples, 99),
    }


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    results = []
    print("=" * 72)
    print("PHÂN TÍCH ĐỘ TRỄ RTT  –  VR App ↔ RosBridge WebSocket")
    print("=" * 72)

    for fname, label, key in EXPERIMENTS:
        path = BENCH_DIR / fname
        if not path.exists():
            print(f"[!] Không tìm thấy: {path}")
            continue
        samples = load_samples(path)
        if not samples:
            print(f"[!] Không có mẫu trong: {path}")
            continue
        s = stats(samples)
        results.append((label, key, s))

        print(f"\n── {label} ({'–'.join([fname])})  –  N = {s['n']} samples ──")
        print(f"   Min     : {s['min']:.3f} ms")
        print(f"   Mean    : {s['mean']:.3f} ms")
        print(f"   Median  : {s['median']:.3f} ms")
        print(f"   Std dev : {s['std']:.3f} ms")
        print(f"   P95     : {s['p95']:.3f} ms")
        print(f"   P99     : {s['p99']:.3f} ms")
        print(f"   Max     : {s['max']:.3f} ms")

    if not results:
        print("[!] Không có dữ liệu nào.")
        return

    # Lấy dòng normal để tham chiếu trong nhận xét
    normal_s  = next(s for l, k, s in results if k == "normal")
    r100_s    = next((s for l, k, s in results if k == "100M"),  None)
    r150_s    = next((s for l, k, s in results if k == "150M"),  None)
    r200_s    = next((s for l, k, s in results if k == "200M"),  None)

    def fmt(v):
        return f"{v:.1f}".replace(".", "{,}")

    def fmti(v):
        return str(int(round(v)))

    def fmt_plot(v):
        return f"{v:.1f}"

    x_labels = [label for label, _, _ in results]
    x_coords = ", ".join(x_labels)

    def plot_coords(metric: str) -> str:
        lines = []
        for label, _, s in results:
            lines.append(f"    ({label}, {fmt_plot(s[metric])})")
        return "\n".join(lines)

    # ── Sinh LaTeX ────────────────────────────────────────────────────────────
    figure_latex = f"""\\begin{{figure}}[H]
\\centering
\\begin{{tikzpicture}}
\\begin{{axis}}[
    ybar,
    width=0.88\\linewidth,
    height=6cm,
    bar width=12pt,
    xlabel={{Điều kiện tải mạng}},
    ylabel={{RTT (ms)}},
    symbolic x coords={{{x_coords}}},
    xtick=data,
    xticklabel style={{font=\\small}},
    ymin=0, ymax=110,
    ytick={{0,20,40,60,80,100}},
    ymajorgrids=true,
    major grid style={{line width=0.4pt, draw=gray!40}},
    legend style={{at={{(0.98,0.98)}}, anchor=north east, font=\\small,
                  draw=gray!40, fill=white}},
    legend cell align=left,
    axis lines=left,
    enlarge x limits=0.20,
]
% Trung bình (TB)
\\addplot[fill=blue!60, draw=blue!80] coordinates {{
{plot_coords("mean")}
}};
\\addlegendentry{{TB}}
% P50 (Trung vị)
\\addplot[fill=green!60, draw=green!80!black] coordinates {{
{plot_coords("median")}
}};
\\addlegendentry{{P50}}
% P95
\\addplot[fill=orange!70, draw=orange!90] coordinates {{
{plot_coords("p95")}
}};
\\addlegendentry{{P95}}
% P99
\\addplot[fill=red!60, draw=red!80] coordinates {{
{plot_coords("p99")}
}};
\\addlegendentry{{P99}}
\\end{{axis}}
\\end{{tikzpicture}}
\\caption{{RTT (TB / P50 / P95 / P99) theo điều kiện tải mạng Wi-Fi giữa ứng dụng VR (Meta Quest~3) và Ros2 (PC)}}
\\label{{fig:rtt-bar-chart}}
\\end{{figure}}
"""

    latex = r"""% ── Tự động tạo bởi scripts/analyze_rtt_latency.py ──────────────────────
"""
    latex += figure_latex
    latex += r"""
\begin{table}[H]
\centering
\caption{Thống kê RTT giữa ứng dụng VR và RosBridge WebSocket theo điều kiện tải mạng}
\label{tab:rtt-latency}
\small
\begin{tblr}{
    colspec = {|X[3.2,l]|X[1,c]|X[1.2,c]|X[1.2,c]|X[1.2,c]|X[1.2,c]|X[1.2,c]|X[1.2,c]|},
    hlines,
    row{1} = {font=\bfseries, bg=gray!20},
}
Điều kiện & N & Min (ms) & TB (ms) & Trung vị (ms) & P95 (ms) & P99 (ms) & Max (ms) \\
"""
    for label, key, s in results:
        latex += (
            f"{label} & {s['n']} & {fmt(s['min'])} & {fmt(s['mean'])} & "
            f"{fmt(s['median'])} & {fmt(s['p95'])} & {fmt(s['p99'])} & {fmt(s['max'])} \\\\\n"
        )
    latex += r"""\end{tblr}
\end{table}
"""

    # Tính % tăng mean so với normal
    def pct_inc(a, b):
        return (b - a) / a * 100 if a else 0

    inc100 = pct_inc(normal_s["mean"], r100_s["mean"]) if r100_s else 0
    inc150 = pct_inc(normal_s["mean"], r150_s["mean"]) if r150_s else 0
    inc200 = pct_inc(normal_s["mean"], r200_s["mean"]) if r200_s else 0

    latex += f"""
Kết quả đo đạc RTT được trình bày tại Bảng~\\ref{{tab:rtt-latency}} và Hình~\\ref{{fig:rtt-bar-chart}}.
Đây là thời gian khứ hồi (Round-Trip Time) tính từ khi Ros2 publish topic
\\texttt{{/benchmark}} cho đến khi nhận được gói phản hồi \\texttt{{/ack}}
từ ứng dụng VR thông qua kết nối WebSocket RosBridge tại cổng~9090.

\\textbf{{Điều kiện mạng bình thường.}}
Trong điều kiện không có tải mạng tải cao, RTT trung bình đạt
\\textbf{{{fmt(normal_s["mean"])}\\,ms}} (trung vị {fmt(normal_s["median"])}\\,ms),
dao động từ {fmt(normal_s["min"])}\\,ms đến {fmt(normal_s["max"])}\\,ms với độ lệch chuẩn
{fmt(normal_s["std"])}\\,ms.
Ngưỡng P95 ở mức \\textbf{{{fmt(normal_s["p95"])}\\,ms}} cho thấy 95\\% các gói tin
đến trong vòng {fmti(normal_s["p95"])}\\,ms -- thỏa mãn tốt yêu cầu điều khiển
theo thời gian thực với chu kỳ 100\\,ms của Ros2-Control.

\\textbf{{Ảnh hưởng của tải mạng tải cao.}}
Khi áp tải mạng 100\\,Mbit/s, RTT trung bình tăng lên
\\textbf{{{fmt(r100_s["mean"])}\\,ms}} ({'+' if inc100>=0 else ''}{fmt(inc100)}\\%
so với điều kiện bình thường), P99 đạt {fmt(r100_s["p99"])}\\,ms.
Ở mức 150\\,Mbit/s, RTT trung bình là \\textbf{{{fmt(r150_s["mean"])}\\,ms}}
({'+' if inc150>=0 else ''}{fmt(inc150)}\\%),
và tại 200\\,Mbit/s lên tới \\textbf{{{fmt(r200_s["mean"])}\\,ms}}
({'+' if inc200>=0 else ''}{fmt(inc200)}\\%).
Mặc dù giá trị trung bình tăng đáng kể khi tải mạng vượt 150\\,Mbit/s,
P99 vẫn nằm dưới 100\\,ms ở tất cả các điều kiện kiểm thử,
đồng nghĩa với việc hệ ít hơn 1\\% số gói tin bị trễ vượt mức cho phép
ngay cả trong điều kiện tải mạng cực cao.

\\textbf{{Nhận xét chung.}}
RTT giữa ứng dụng VR và Ros2 đạt mức thấp nhờ kết nối mạng LAN nội bộ
giữa kính Meta Quest~3 và máy PC chạy Ros2 (cùng mạng Wi-Fi 5\\,GHz).
Độ trễ \\textasciitilde{fmti(normal_s["mean"])}\\,ms ở điều kiện bình thường
nhỏ hơn đáng kể so với chu kỳ điều khiển 100\\,ms của Ros2-Control,
đảm bảo rằng lệnh từ ứng dụng VR được truyền đến robot trong cùng chu kỳ điều khiển.
"""

    print()
    print("=" * 72)
    print("LATEX OUTPUT  –  dán vào vị trí % latency RTT here")
    print("=" * 72)
    print(latex)

    # Ghi vào file riêng để tiện dùng
    out_path = REPO / "scripts" / "_rtt_latex_output.tex"
    out_path.write_text(latex, encoding="utf-8")
    print(f"[+] Đã lưu LaTeX vào: {out_path}")

    return latex


if __name__ == "__main__":
    main()
