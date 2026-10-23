import argparse
import csv
import json
import multiprocessing as mp
import platform
import statistics
import time
import tracemalloc
from pathlib import Path

from benchmark.cases import make_cases
from benchmark.common import prepare, solve, valid


def worker(conn, case, algorithm, mode):
    try:
        if mode == "memory":
            tracemalloc.start()

        state = prepare(case)

        start = time.perf_counter_ns()
        solution, nodes = solve(case, state, algorithm)
        elapsed = (time.perf_counter_ns() - start) / 1e6

        peak = (
            tracemalloc.get_traced_memory()[1] / 1024
            if mode == "memory" else 0
        )

        if mode == "memory":
            tracemalloc.stop()

        ok = (
            valid(case, solution)
            if solution is not None
            else not case["expected"]
        )
        status = (
            ("SOLVED" if solution is not None else "UNSAT")
            if ok else "INVALID"
        )

        conn.send(dict(
            status=status,
            ms=elapsed,
            kib=peak,
            nodes=nodes,
        ))

    except Exception as exc:
        conn.send(dict(status="ERROR", error=repr(exc)))

    finally:
        conn.close()


def run_one(case, algorithm, mode, timeout):
    ctx = mp.get_context("spawn")
    parent, child = ctx.Pipe(duplex=False)
    process = ctx.Process(
        target=worker,
        args=(child, case, algorithm, mode),
    )
    process.start()
    child.close()

    try:
        if parent.poll(timeout):
            try:
                return parent.recv()
            except EOFError:
                return dict(
                    status="ERROR",
                    error="Worker exited without result",
                )
        return dict(status="TIMEOUT")

    finally:
        if process.is_alive():
            process.terminate()
        process.join()
        parent.close()


def tex_escape(text):
    table = {
        "\\": r"\textbackslash{}",
        "_": r"\_",
        "%": r"\%",
        "&": r"\&",
        "#": r"\#",
        "{": r"\{",
        "}": r"\}",
        "$": r"\$",
        "^": r"\textasciicircum{}",
        "~": r"\textasciitilde{}",
    }
    return "".join(table.get(c, c) for c in str(text))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--timeout", type=float, default=10)
    args = parser.parse_args()

    if args.repeats < 1 or args.timeout <= 0:
        parser.error("repeats and timeout must be positive")

    out = Path("results")
    out.mkdir(exist_ok=True)
    cases = make_cases()

    (out / "cases.json").write_text(
        json.dumps(cases, indent=2),
        encoding="utf-8",
    )

    config = (
        f"Python {platform.python_version()}; "
        f"{platform.platform()}; "
        f"CPU: {platform.processor() or platform.machine()}; "
        f"repeats={args.repeats}; "
        f"timeout={args.timeout}s per worker"
    )
    (out / "environment.txt").write_text(
        config, encoding="utf-8"
    )

    rows, raw = [], []

    for case in cases:
        for algorithm in ("DFS", "A*"):
            times, memories, nodes = [], [], []
            status = "ERROR"

            for repetition in range(args.repeats):
                for mode in ("time", "memory"):
                    result = run_one(
                        case, algorithm, mode, args.timeout
                    )
                    raw.append(dict(
                        case=case["id"],
                        algorithm=algorithm,
                        repetition=repetition + 1,
                        mode=mode,
                        **result,
                    ))

                    status = result["status"]
                    if status not in ("SOLVED", "UNSAT"):
                        break

                    if mode == "time":
                        times.append(result["ms"])
                        nodes.append(result["nodes"])
                    else:
                        memories.append(result["kib"])

                if status not in ("SOLVED", "UNSAT"):
                    break

            complete = (
                len(times) == len(memories) == args.repeats
            )

            row = dict(
                game=case["game"],
                case=case["id"],
                algorithm=algorithm,
                status=status,
                time_ms="",
                peak_python_kib="",
                nodes="",
            )

            if complete:
                row.update(
                    time_ms=round(statistics.median(times), 4),
                    peak_python_kib=round(max(memories), 2),
                    nodes=nodes[0],
                )

            rows.append(row)
            print(row, flush=True)

            (out / "raw.json").write_text(
                json.dumps(raw, indent=2),
                encoding="utf-8",
            )

    with (out / "summary.csv").open(
        "w", newline="", encoding="utf-8-sig"
    ) as f:
        writer = csv.DictWriter(
            f, fieldnames=list(rows[0])
        )
        writer.writeheader()
        writer.writerows(rows)

    (out / "environment.tex").write_text(
        tex_escape(config), encoding="utf-8"
    )

    for game in ("akari", "tents"):
        lines = [
            r"\begin{center}\small",
            r"\begin{tabular}{llrrrr}",
            r"\toprule",
            r"Case & Solver & Status & ms & KiB & Nodes \\",
            r"\midrule",
        ]

        for row in rows:
            if row["game"] == game:
                values = [
                    row[k]
                    for k in (
                        "case", "algorithm", "status",
                        "time_ms", "peak_python_kib", "nodes",
                    )
                ]
                lines.append(
                    " & ".join(
                        tex_escape(v if v != "" else "--")
                        for v in values
                    ) + r" \\"
                )

        lines += [
            r"\bottomrule",
            r"\end{tabular}\end{center}",
        ]
        (out / f"{game}_table.tex").write_text(
            "\n".join(lines), encoding="utf-8"
        )

        pairs = []
        for case in cases:
            pair = [
                r for r in rows
                if r["case"] == case["id"] and r["game"] == game
            ]
            if len(pair) == 2 and all(
                r["status"] == "SOLVED" and r["time_ms"] != ""
                for r in pair
            ):
                pairs.append(pair)

        faster = sum(
            b["time_ms"] < a["time_ms"] for a, b in pairs
        )

        text = (
            f"Trong {len(pairs)} bộ dữ liệu có nghiệm mà cả hai "
            f"giải thuật hoàn tất đầy đủ phép đo, A* có thời gian "
            f"trung vị thấp hơn DFS ở {faster} bộ. "
            "So sánh này chỉ áp dụng cho các bộ dữ liệu đã chạy. "
            "Số nút giúp quan sát lượng tìm kiếm, nhưng thời gian "
            "còn phụ thuộc chi phí kiểm tra ràng buộc, sao chép "
            "trạng thái và quản lý hàng đợi. "
            "Các dòng TIMEOUT không được xem là vô nghiệm và "
            "không được đưa vào so sánh thời gian."
        )
        (out / f"{game}_analysis.tex").write_text(
            text, encoding="utf-8"
        )


if __name__ == "__main__":
    mp.freeze_support()
    main()