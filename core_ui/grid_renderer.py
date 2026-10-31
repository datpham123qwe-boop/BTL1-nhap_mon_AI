import queue
import threading
import time
import tkinter as tk
from tkinter import ttk
import tracemalloc

from benchmark.cases import make_cases
from benchmark.common import prepare, solve, valid
from game_tent.logic import TentsAndTreeState


class Cancelled(Exception):
    pass


class App:
    def __init__(self, root, game):
        self.root, self.game = root, game
        self.cases = [c for c in make_cases() if c["game"] == game]

        root.title(
            "Akari - Light Up" if game == "akari" else "Tents and Trees"
        )
        root.geometry("850x820")
        root.minsize(750, 720)

        # Style
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Ribbon.TFrame", background="#e9ecef", relief="flat")
        style.configure("StatKey.TLabel", font=("Segoe UI", 9, "bold"), foreground="#495057")
        style.configure("StatVal.TLabel", font=("Segoe UI", 9, "bold"), foreground="#1c3d5a")

        self.cancel = threading.Event()
        self.messages = queue.Queue(maxsize=2)
        self.playing = False
        self.thread = None
        self.done = False

        self.case_var = tk.StringVar(value=self.cases[0]["id"])
        self.algorithm = tk.StringVar(value="A*" if game == "akari" else "DFS")
        self.delay = tk.IntVar(value=150)

        self.marks = set()
        self.history = []
        self.history_index = 0
        self.current_board = None

        self._build_ui()

        root.protocol("WM_DELETE_WINDOW", self.close)
        self.reset()
        root.after(50, self.tick)

    def _build_ui(self):
        root = self.root

        # =========================================================
        # 1. TOP CONTROL PANEL (Toolbar & Timeline)
        # =========================================================
        top_panel = ttk.Frame(root, padding=(12, 10, 12, 4))
        top_panel.pack(fill="x")

        # Row 1: Case selector, Algorithm selector, Actions
        row1 = ttk.Frame(top_panel)
        row1.pack(fill="x", pady=(0, 6))

        ttk.Label(row1, text="Test case:", font=("Segoe UI", 9, "bold")).pack(side="left")
        cb_case = ttk.Combobox(
            row1,
            textvariable=self.case_var,
            state="readonly",
            width=9,
            values=[c["id"] for c in self.cases],
        )
        cb_case.pack(side="left", padx=(4, 12))
        cb_case.bind("<<ComboboxSelected>>", lambda _: self.reset())

        ttk.Label(row1, text="Thuật toán:", font=("Segoe UI", 9, "bold")).pack(side="left")
        cb_algo = ttk.Combobox(
            row1,
            textvariable=self.algorithm,
            state="readonly",
            width=6,
            values=["A*", "DFS"],
        )
        cb_algo.pack(side="left", padx=(4, 16))
        cb_algo.bind("<<ComboboxSelected>>", lambda _: self.reset())

        # Buttons on right
        btn_box = ttk.Frame(row1)
        btn_box.pack(side="right")
        for label, cmd in [
            ("⟲ Reset", self.reset),
            ("◀ Step Back", self.step_back),
            ("Step ▶", self.step),
            ("▶ / ⏸ Play", self.toggle),
        ]:
            ttk.Button(btn_box, text=label, command=cmd).pack(side="left", padx=2)

        # Row 2: Timeline scrubber & Speed delay slider
        row2 = ttk.Frame(top_panel)
        row2.pack(fill="x")

        ttk.Label(row2, text="Timeline:", font=("Segoe UI", 9, "bold")).pack(side="left", padx=(0, 4))
        self.timeline_var = tk.IntVar(value=0)
        self.timeline = ttk.Scale(
            row2,
            from_=0,
            to=1,
            orient="horizontal",
            variable=self.timeline_var,
            command=self.on_timeline_slide,
        )
        self.timeline.pack(side="left", fill="x", expand=True, padx=4)

        self.step_label = ttk.Label(row2, text="0 / 0", font=("Segoe UI", 9, "bold"), width=8)
        self.step_label.pack(side="left", padx=(2, 16))

        ttk.Label(row2, text="Tốc độ:", font=("Segoe UI", 9)).pack(side="left", padx=(0, 4))
        self.delay_slider = tk.Scale(
            row2,
            from_=20,
            to=800,
            orient="horizontal",
            variable=self.delay,
            length=130,
            showvalue=False,
        )
        self.delay_slider.pack(side="left")
        self.delay_label = ttk.Label(row2, text="150ms", width=6)
        self.delay_label.pack(side="left", padx=2)
        self.delay.trace_add("write", lambda *_: self.delay_label.config(text=f"{self.delay.get()}ms"))

        # =========================================================
        # 2. STATS RIBBON (Real-time Metrics Dashboard HUD)
        # =========================================================
        dash_frame = ttk.Frame(root, style="Ribbon.TFrame", padding=(10, 6, 10, 6))
        dash_frame.pack(fill="x", padx=12, pady=(4, 6))

        # Status badge
        self.lbl_status = ttk.Label(
            dash_frame, text="● Sẵn sàng", font=("Segoe UI", 9, "bold"), foreground="#2c3e50"
        )
        self.lbl_status.pack(side="left", padx=(4, 10))

        ttk.Separator(dash_frame, orient="vertical").pack(side="left", fill="y", padx=4)

        # Nodes
        self.lbl_nodes = ttk.Label(dash_frame, text="Nodes: 0", style="StatVal.TLabel")
        self.lbl_nodes.pack(side="left", padx=8)

        ttk.Separator(dash_frame, orient="vertical").pack(side="left", fill="y", padx=4)

        # Time
        self.lbl_time = ttk.Label(
            dash_frame, text="⏱ 0.00 ms", font=("Segoe UI", 9, "bold"), foreground="#0d6efd"
        )
        self.lbl_time.pack(side="left", padx=8)

        ttk.Separator(dash_frame, orient="vertical").pack(side="left", fill="y", padx=4)

        # Peak Memory
        self.lbl_mem = ttk.Label(
            dash_frame, text="💾 0.00 KiB", font=("Segoe UI", 9, "bold"), foreground="#6f42c1"
        )
        self.lbl_mem.pack(side="left", padx=8)

        ttk.Separator(dash_frame, orient="vertical").pack(side="left", fill="y", padx=4)

        # g, h, f
        self.lbl_ghf = ttk.Label(
            dash_frame, text="g=0 | h=0 | f=0", font=("Segoe UI", 9), foreground="#198754"
        )
        self.lbl_ghf.pack(side="left", padx=8)

        ttk.Separator(dash_frame, orient="vertical").pack(side="left", fill="y", padx=4)

        # Conflicts / Valid status
        self.lbl_conflicts = ttk.Label(
            dash_frame, text="✅ Trạng thái hợp lệ", font=("Segoe UI", 9, "bold"), foreground="#27ae60"
        )
        self.lbl_conflicts.pack(side="left", padx=8)

        # =========================================================
        # 3. GAME BOARD CANVAS (Centered & Responsive)
        # =========================================================
        canvas_container = ttk.Frame(root, padding=2)
        canvas_container.pack(fill="both", expand=True, padx=12, pady=(0, 4))

        self.canvas = tk.Canvas(
            canvas_container,
            bg="#f4f6f9",
            highlightthickness=1,
            highlightbackground="#cfd8dc",
            cursor="hand2",
        )
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<Button-3>", self.on_canvas_right_click)
        self.canvas.bind(
            "<Configure>",
            lambda e: self.draw(self.current_board) if self.current_board is not None else None,
        )


    def close(self):
        self.cancel.set()
        try:
            tracemalloc.stop()
        except Exception:
            pass
        self.root.destroy()

    def reset(self):
        self.cancel.set()
        self.cancel = threading.Event()
        self.messages = queue.Queue(maxsize=2)
        self.thread = None
        self.playing = False
        self.done = False
        self.marks = set()

        try:
            tracemalloc.stop()
        except Exception:
            pass

        self.case = next(c for c in self.cases if c["id"] == self.case_var.get())
        self.active_algorithm = self.algorithm.get()
        self.problem = prepare(self.case)

        initial_board = 0 if self.game == "akari" else [r[:] for r in self.case["grid"]]
        self.history = [("Ready", initial_board, 0, 0.0, 0.0)]
        self.history_index = 0
        self.current_board = initial_board

        self._update_timeline()
        self._show_state("Ready", initial_board, 0, 0.0, 0.0)

    # -------------------------------------------------------------
    # State Display: Metrics HUD, Timer, Memory & Canvas Redraw
    # -------------------------------------------------------------
    def _show_state(self, status, board, nodes, elapsed_ms=0.0, peak_kib=0.0):
        self.current_board = board
        if board is not None:
            self.draw(board)

        # 1. Update Status Badge
        status_clean = status.replace("✅", "").strip()
        if status_clean == "Ready":
            self.lbl_status.config(text="● Sẵn sàng", foreground="#2c3e50")
        elif status_clean == "Solving...":
            self.lbl_status.config(text="● Đang giải...", foreground="#d35400")
        elif "SOLVED" in status_clean:
            self.lbl_status.config(text="● SOLVED", foreground="#27ae60")
        elif "UNSAT" in status_clean:
            self.lbl_status.config(text="● UNSAT", foreground="#c0392b")
        elif "Player" in status_clean:
            self.lbl_status.config(text="● Tự giải", foreground="#2980b9")
        else:
            self.lbl_status.config(text=f"● {status_clean}", foreground="#6c757d")

        # 2. Nodes Visited
        self.lbl_nodes.config(text=f"Nodes: {nodes}")

        # 3. Elapsed Time (ms / s)
        if elapsed_ms < 0.0001:
            time_str = "0.00 ms"
        elif elapsed_ms < 1.0:
            time_str = f"{elapsed_ms:.4f} ms"
        elif elapsed_ms < 1000.0:
            time_str = f"{elapsed_ms:.2f} ms"
        else:
            time_str = f"{elapsed_ms / 1000.0:.2f} s"
        self.lbl_time.config(text=f"⏱ {time_str}")

        # 4. Peak Memory (KiB)
        self.lbl_mem.config(text=f"💾 {peak_kib:.2f} KiB")

        # 5. Explainable AI (g, h, f) & Constraints Check
        if self.game == "akari":
            bulbs_mask = board if isinstance(board, int) else 0
            g = bulbs_mask.bit_count()
            lit = 0
            for u in range(self.problem.num_white):
                if (bulbs_mask >> u) & 1:
                    lit |= self.problem.ray_mask[u]
            unlit = (self.problem.all_white_mask ^ lit).bit_count()
            h = round(unlit / max(1, self.problem.max_ray_len), 1)
            f = round(g + h, 1)

            clashes, clue_errors = self.check_akari_constraints(bulbs_mask)
            conflicts = []
            if clashes:
                conflicts.append(f"{len(clashes)} đèn chiếu nhau")
            if clue_errors:
                conflicts.append(f"{len(clue_errors)} ô tường sai")
        else:
            grid = board if board is not None else self.case["grid"]
            rows, cols = len(grid), len(grid[0])
            tents = sum(grid[r][c] == 2 for r in range(rows) for c in range(cols))
            total_trees = len(self.case["trees"])
            g = tents
            h = max(0, total_trees - tents)
            f = g + h

            clash_tents, row_errs, col_errs = self.check_tents_constraints(grid)
            conflicts = []
            if clash_tents:
                conflicts.append(f"{len(clash_tents)} lều kề nhau")
            if row_errs or col_errs:
                conflicts.append(f"Vượt chỉ tiêu ({len(row_errs) + len(col_errs)})")

        self.lbl_ghf.config(text=f"g={g} | h={h} | f={f}")

        # 6. Conflicts indicator
        if conflicts:
            self.lbl_conflicts.config(text=f"⚠️ {', '.join(conflicts)}", foreground="#c0392b")
        else:
            self.lbl_conflicts.config(text="✅ Trạng thái hợp lệ", foreground="#27ae60")

    def check_akari_constraints(self, bulbs_mask):
        clashes = set()
        for u in range(self.problem.num_white):
            if (bulbs_mask >> u) & 1:
                others = (self.problem.ray_mask[u] & bulbs_mask) & ~(1 << u)
                if others:
                    clashes.add(u)

        clue_errors = []
        for c_idx, (r, c, target) in enumerate(self.problem.clues):
            placed = (self.problem.clue_adj_mask[c_idx] & bulbs_mask).bit_count()
            if placed > target:
                clue_errors.append((r, c, placed, target))
        return clashes, clue_errors

    def check_tents_constraints(self, grid):
        rows, cols = len(grid), len(grid[0])
        tents = [(r, c) for r in range(rows) for c in range(cols) if grid[r][c] == 2]

        clash_tents = set()
        for i in range(len(tents)):
            r1, c1 = tents[i]
            for j in range(i + 1, len(tents)):
                r2, c2 = tents[j]
                if max(abs(r1 - r2), abs(c1 - c2)) <= 1:
                    clash_tents.add((r1, c1))
                    clash_tents.add((r2, c2))

        row_errs = [r for r in range(rows) if sum(grid[r][c] == 2 for c in range(cols)) > self.case["row_limits"][r]]
        col_errs = [c for c in range(cols) if sum(grid[r][c] == 2 for r in range(rows)) > self.case["col_limits"][c]]
        return clash_tents, row_errs, col_errs

    # -------------------------------------------------------------
    # Timeline Scrubber (2.1)
    # -------------------------------------------------------------
    def _update_timeline(self):
        total = max(1, len(self.history) - 1)
        self.timeline.configure(to=total)
        self.timeline_var.set(self.history_index)
        self.step_label.config(text=f"{self.history_index} / {total}")

    def on_timeline_slide(self, val):
        idx = int(float(val))
        if 0 <= idx < len(self.history) and idx != self.history_index:
            self.playing = False
            self.history_index = idx
            item = self.history[idx]
            self._show_state(*item)
            self._update_timeline()

    # -------------------------------------------------------------
    # Player Mode Click Interaction (Left: Place, Right: Mark X)
    # -------------------------------------------------------------
    def on_canvas_click(self, event):
        if not hasattr(self, "grid_left") or self.cell_size <= 0:
            return

        c = int((event.x - self.grid_left) // self.cell_size)
        r = int((event.y - self.grid_top) // self.cell_size)

        grid = self.case["grid"]
        rows, cols = len(grid), len(grid[0])
        if not (0 <= r < rows and 0 <= c < cols):
            return

        self.playing = False
        if (r, c) in self.marks:
            self.marks.remove((r, c))

        prev_time = self.history[self.history_index][3] if len(self.history[self.history_index]) > 3 else 0.0
        prev_mem = self.history[self.history_index][4] if len(self.history[self.history_index]) > 4 else 0.0

        if self.game == "akari":
            if grid[r][c] != -2:
                return  # Wall cell
            u = self.problem.coord_to_id[r, c]
            current_bulbs = self.current_board if isinstance(self.current_board, int) else 0
            new_bulbs = current_bulbs ^ (1 << u)
            nodes = self.history[self.history_index][2] if self.history else 0

            self.history = self.history[: self.history_index + 1]
            status = "SOLVED" if self.problem.is_goal(new_bulbs) else "Player"
            self.history.append((status, new_bulbs, nodes, prev_time, prev_mem))
            self.history_index = len(self.history) - 1
            self._update_timeline()
            self._show_state(status, new_bulbs, nodes, prev_time, prev_mem)

        elif self.game == "tents":
            if grid[r][c] == 1:
                return  # Tree cell

            current_grid = [row[:] for row in self.current_board]
            current_grid[r][c] = 0 if current_grid[r][c] == 2 else 2
            nodes = self.history[self.history_index][2] if self.history else 0

            test_state = TentsAndTreeState(
                current_grid,
                self.case["row_limits"][:],
                self.case["col_limits"][:],
                [tuple(t) for t in self.case["trees"]],
            )
            self.history = self.history[: self.history_index + 1]
            status = "SOLVED" if valid(self.case, test_state) else "Player"
            self.history.append((status, current_grid, nodes, prev_time, prev_mem))
            self.history_index = len(self.history) - 1
            self._update_timeline()
            self._show_state(status, current_grid, nodes, prev_time, prev_mem)

    def on_canvas_right_click(self, event):
        if not hasattr(self, "grid_left") or self.cell_size <= 0:
            return

        c = int((event.x - self.grid_left) // self.cell_size)
        r = int((event.y - self.grid_top) // self.cell_size)

        grid = self.case["grid"]
        rows, cols = len(grid), len(grid[0])
        if not (0 <= r < rows and 0 <= c < cols):
            return

        self.playing = False
        prev_time = self.history[self.history_index][3] if len(self.history[self.history_index]) > 3 else 0.0
        prev_mem = self.history[self.history_index][4] if len(self.history[self.history_index]) > 4 else 0.0

        if self.game == "akari":
            if grid[r][c] != -2:
                return  # Wall cell
            u = self.problem.coord_to_id[r, c]
            current_bulbs = self.current_board if isinstance(self.current_board, int) else 0

            if (current_bulbs >> u) & 1:
                new_bulbs = current_bulbs ^ (1 << u)
                self.marks.add((r, c))
                nodes = self.history[self.history_index][2] if self.history else 0
                self.history = self.history[: self.history_index + 1]
                status = "SOLVED" if self.problem.is_goal(new_bulbs) else "Player"
                self.history.append((status, new_bulbs, nodes, prev_time, prev_mem))
                self.history_index = len(self.history) - 1
                self._update_timeline()
                self._show_state(status, new_bulbs, nodes, prev_time, prev_mem)
            else:
                if (r, c) in self.marks:
                    self.marks.remove((r, c))
                else:
                    self.marks.add((r, c))
                self.draw(self.current_board)

        elif self.game == "tents":
            if grid[r][c] == 1:
                return  # Tree cell

            current_grid = [row[:] for row in self.current_board]
            if current_grid[r][c] == 2:
                current_grid[r][c] = 0
                self.marks.add((r, c))
                nodes = self.history[self.history_index][2] if self.history else 0
                test_state = TentsAndTreeState(
                    current_grid,
                    self.case["row_limits"][:],
                    self.case["col_limits"][:],
                    [tuple(t) for t in self.case["trees"]],
                )
                self.history = self.history[: self.history_index + 1]
                status = "SOLVED" if valid(self.case, test_state) else "Player"
                self.history.append((status, current_grid, nodes, prev_time, prev_mem))
                self.history_index = len(self.history) - 1
                self._update_timeline()
                self._show_state(status, current_grid, nodes, prev_time, prev_mem)
            else:
                if (r, c) in self.marks:
                    self.marks.remove((r, c))
                else:
                    self.marks.add((r, c))
                self.draw(self.current_board)

    # -------------------------------------------------------------
    # Search Engine Controls (Thread + Queue + Performance Metrics)
    # -------------------------------------------------------------
    def start(self):
        if self.thread is not None or self.done:
            return

        case, algorithm = self.case, self.active_algorithm
        messages, cancel = self.messages, self.cancel

        def put(message):
            while not cancel.is_set():
                try:
                    messages.put(message, timeout=0.1)
                    return
                except queue.Full:
                    pass
            raise Cancelled()

        def work():
            try:
                tracemalloc.start()
                start_ns = time.perf_counter_ns()

                def callback(board, nodes):
                    elapsed = (time.perf_counter_ns() - start_ns) / 1e6
                    peak = tracemalloc.get_traced_memory()[1] / 1024
                    snapshot = board if isinstance(board, int) else [r[:] for r in board]
                    put(("Solving...", snapshot, nodes, elapsed, peak))

                result, nodes = solve(case, prepare(case), algorithm, callback)
                elapsed = (time.perf_counter_ns() - start_ns) / 1e6
                peak = tracemalloc.get_traced_memory()[1] / 1024
                tracemalloc.stop()

                status = "UNSAT" if result is None else ("SOLVED" if valid(case, result) else "INVALID")
                board = result if case["game"] == "akari" else ([r[:] for r in result.grid] if result else None)
                put((status, board, nodes, elapsed, peak))

            except Cancelled:
                try:
                    tracemalloc.stop()
                except Exception:
                    pass

            except Exception as exc:
                try:
                    tracemalloc.stop()
                except Exception:
                    pass
                try:
                    put(("ERROR: " + str(exc), None, 0, 0.0, 0.0))
                except Cancelled:
                    pass

        self.thread = threading.Thread(target=work, daemon=True)
        self.thread.start()

    def consume(self):
        try:
            status, board, nodes, elapsed, peak = self.messages.get_nowait()
        except queue.Empty:
            return False

        self.history.append((status, board, nodes, elapsed, peak))
        self.history_index = len(self.history) - 1
        self._update_timeline()
        self._show_state(status, board, nodes, elapsed, peak)

        if status != "Solving...":
            self.playing = False
            self.done = True

        return True

    def step(self):
        self.playing = False
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            item = self.history[self.history_index]
            self._update_timeline()
            self._show_state(*item)
            return

        if self.done:
            return

        self.start()
        token = self.cancel

        def advance():
            if token.is_set() or self.done or self.playing:
                return
            if not self.consume():
                self.root.after(20, advance)

        advance()

    def step_back(self):
        self.playing = False
        if self.history_index > 0:
            self.history_index -= 1
            item = self.history[self.history_index]
            self._update_timeline()
            self._show_state(*item)

    def toggle(self):
        self.start()
        if not self.done or self.history_index < len(self.history) - 1:
            self.playing = not self.playing

    def tick(self):
        if self.playing:
            if self.history_index < len(self.history) - 1:
                self.history_index += 1
                item = self.history[self.history_index]
                self._update_timeline()
                self._show_state(*item)
                if item[0] != "Solving..." and self.history_index == len(self.history) - 1:
                    self.playing = False
            else:
                self.consume()
        self.root.after(self.delay.get(), self.tick)

    # -------------------------------------------------------------
    # Rendering on Canvas (Centering & Dynamic Scaling)
    # -------------------------------------------------------------
    def draw(self, board):
        cv = self.canvas
        cv.delete("all")

        grid = self.case["grid"] if self.game == "akari" else board
        rows, cols = len(grid), len(grid[0])

        w = cv.winfo_width()
        h = cv.winfo_height()
        if w < 100 or h < 100:
            w, h = 780, 640

        margin_x = 90 if self.game == "tents" else 50
        margin_y = 70 if self.game == "tents" else 50
        avail_w = max(100, w - margin_x)
        avail_h = max(100, h - margin_y)

        size = max(20, min(90, int(min(avail_w / cols, avail_h / rows))))
        grid_w = cols * size
        grid_h = rows * size

        if self.game == "tents":
            offset_x = 24
            offset_y = 16
            left = max(55, int((w - grid_w) / 2) + offset_x)
            top = max(40, int((h - grid_h) / 2) + offset_y)
        else:
            left = max(20, int((w - grid_w) / 2))
            top = max(20, int((h - grid_h) / 2))

        self.grid_left, self.grid_top, self.cell_size = left, top, size

        # Akari: compute lit and conflicts
        lit = 0
        clashes = set()
        clue_violations = set()

        if self.game == "akari":
            bulbs_mask = board if isinstance(board, int) else 0
            for u in range(self.problem.num_white):
                if (bulbs_mask >> u) & 1:
                    lit |= self.problem.ray_mask[u]

            clashes, clue_errs = self.check_akari_constraints(bulbs_mask)
            clue_violations = {(r, c) for r, c, _, _ in clue_errs}

        # Tents: compute conflicts
        clash_tents = set()
        if self.game == "tents":
            clash_tents, _, _ = self.check_tents_constraints(grid)

        # Draw Cells
        for r in range(rows):
            for c in range(cols):
                x, y = left + c * size, top + r * size
                value = grid[r][c]
                color, symbol = "#ffffff", None

                if self.game == "akari":
                    if value != -2:
                        color = "#922b21" if (r, c) in clue_violations else "#1c2833"
                        symbol = str(value) if value >= 0 else None
                    else:
                        u = self.problem.coord_to_id[r, c]
                        color = "#ffec6e" if (lit >> u & 1) else "#ffffff"

                elif self.game == "tents":
                    if (r, c) in clash_tents:
                        color = "#fadbd8"  # Red warning

                # Base Cell
                cv.create_rectangle(
                    x,
                    y,
                    x + size,
                    y + size,
                    fill=color,
                    outline="#a7b2c0" if (r, c) not in clue_violations else "#e74c3c",
                    width=2 if (r, c) in clue_violations else 1,
                )

                # Clue in Wall
                if symbol is not None:
                    cv.create_text(
                        x + size / 2,
                        y + size / 2,
                        text=symbol,
                        fill="white",
                        font=("Arial", max(10, int(size * 0.45)), "bold"),
                    )

                # Bulb or X Mark (Akari)
                if self.game == "akari" and value == -2:
                    if (board >> u & 1):
                        if u in clashes:
                            cv.create_oval(
                                x + size * 0.1,
                                y + size * 0.1,
                                x + size * 0.9,
                                y + size * 0.9,
                                fill="#f9d5d5",
                                outline="#e74c3c",
                                width=2,
                            )
                        cv.create_text(
                            x + size / 2,
                            y + size / 2,
                            text="💡",
                            font=("Segoe UI Emoji", int(size * 0.48)),
                        )
                    elif (r, c) in self.marks:
                        cv.create_text(
                            x + size / 2,
                            y + size / 2,
                            text="✕",
                            fill="#7f8c8d",
                            font=("Arial", max(10, int(size * 0.42)), "bold"),
                        )

                # Tree, Tent or X Mark (Tents)
                if self.game == "tents":
                    if value == 1:
                        cv.create_text(
                            x + size / 2,
                            y + size / 2,
                            text="🌲",
                            font=("Segoe UI Emoji", int(size * 0.58)),
                        )
                    elif value == 2:
                        cv.create_text(
                            x + size / 2,
                            y + size / 2,
                            text="⛺",
                            font=("Segoe UI Emoji", int(size * 0.55)),
                        )
                    elif (r, c) in self.marks and value == 0:
                        cv.create_text(
                            x + size / 2,
                            y + size / 2,
                            text="✕",
                            fill="#7f8c8d",
                            font=("Arial", max(10, int(size * 0.42)), "bold"),
                        )

        # Draw Row & Col limits (Tents)
        if self.game == "tents":
            label_offset_x = max(24, int(size * 0.42))
            label_offset_y = max(18, int(size * 0.32))
            label_font_size = max(9, min(14, int(size * 0.23)))

            for axis, limits in (("row", self.case["row_limits"]), ("col", self.case["col_limits"])):
                for i, target in enumerate(limits):
                    count = sum(v == 2 for v in grid[i]) if axis == "row" else sum(row[i] == 2 for row in grid)
                    x, y = (
                        (left - label_offset_x, top + (i + 0.5) * size)
                        if axis == "row"
                        else (left + (i + 0.5) * size, top - label_offset_y)
                    )

                    if count > target:
                        fill_color = "#e74c3c"
                    elif count == target:
                        fill_color = "#18AE4D"
                    else:
                        fill_color = "#46566b"

                    cv.create_text(
                        x,
                        y,
                        text=f"{count}/{target}",
                        font=("Arial", label_font_size, "bold"),
                        fill=fill_color,
                    )


def launch(game):
    root = tk.Tk()
    App(root, game)
    root.mainloop()
