import queue
import threading
import tkinter as tk
from tkinter import ttk

from benchmark.cases import make_cases
from benchmark.common import prepare, solve, valid


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

        self.cancel = threading.Event()
        self.messages = queue.Queue(maxsize=2)
        self.playing = False
        self.thread = None

        self.case_var = tk.StringVar(value=self.cases[0]["id"])
        self.algorithm = tk.StringVar(value="DFS")

        top = ttk.Frame(root, padding=12)
        top.pack(fill="x")
        ttk.Label(top, text="Test case").pack(side="left")

        ttk.Combobox(
            top,
            textvariable=self.case_var,
            state="readonly",
            width=14,
            values=[c["id"] for c in self.cases],
        ).pack(side="left", padx=8)

        ttk.Combobox(
            top,
            textvariable=self.algorithm,
            state="readonly",
            width=7,
            values=["DFS", "A*"],
        ).pack(side="left")

        for label, command in [
            ("Load / Reset", self.reset),
            ("Step", self.step),
            ("Play / Pause", self.toggle),
        ]:
            ttk.Button(
                top, text=label, command=command
            ).pack(side="left", padx=4)

        bar = ttk.Frame(root, padding=8)
        bar.pack(fill="x")
        ttk.Label(bar, text="Delay (ms)").pack(side="left")

        self.delay = tk.IntVar(value=200)
        tk.Scale(
            bar,
            from_=20,
            to=1000,
            orient="horizontal",
            variable=self.delay,
            length=300,
        ).pack(side="left")

        self.caption = tk.StringVar()
        ttk.Label(
            root, textvariable=self.caption, padding=8
        ).pack()

        self.canvas = tk.Canvas(
            root,
            width=760,
            height=620,
            bg="#eef2f6",
            highlightthickness=0,
        )
        self.canvas.pack(
            fill="both", expand=True, padx=15, pady=8
        )

        legend = (
            "Yellow: illuminated | Circle: bulb | Dark: wall"
            if game == "akari"
            else "Green: tree | Orange: tent | Edge labels: current / target"
        )
        ttk.Label(root, text=legend, padding=10).pack()

        root.protocol("WM_DELETE_WINDOW", self.close)
        self.reset()
        root.after(50, self.tick)

    def close(self):
        self.cancel.set()
        self.root.destroy()

    def reset(self):
        self.cancel.set()
        self.cancel = threading.Event()
        self.messages = queue.Queue(maxsize=2)
        self.thread = None
        self.playing = False
        self.done = False

        self.case = next(
            c for c in self.cases
            if c["id"] == self.case_var.get()
        )
        self.active_algorithm = self.algorithm.get()
        self.problem = prepare(self.case)

        self.caption.set(
            f'{self.case["id"]} | {self.active_algorithm} | Ready'
        )
        self.draw(
            0 if self.game == "akari" else self.case["grid"]
        )

    def start(self):
        if self.thread is not None or self.done:
            return

        case, algorithm = self.case, self.active_algorithm
        messages, cancel = self.messages, self.cancel

        def put(message):
            while not cancel.is_set():
                try:
                    messages.put(message, timeout=.1)
                    return
                except queue.Full:
                    pass
            raise Cancelled()

        def callback(board, nodes):
            snapshot = (
                board if isinstance(board, int)
                else [r[:] for r in board]
            )
            put(("step", snapshot, nodes))

        def work():
            try:
                result, nodes = solve(
                    case, prepare(case), algorithm, callback
                )
                status = (
                    "UNSAT" if result is None
                    else ("SOLVED" if valid(case, result) else "INVALID")
                )
                board = (
                    result if case["game"] == "akari"
                    else (result.grid if result else None)
                )
                put((status, board, nodes))

            except Cancelled:
                pass

            except Exception as exc:
                try:
                    put(("ERROR: " + str(exc), None, 0))
                except Cancelled:
                    pass

        self.thread = threading.Thread(
            target=work, daemon=True
        )
        self.thread.start()

    def consume(self):
        try:
            status, board, nodes = self.messages.get_nowait()
        except queue.Empty:
            return False

        if board is not None:
            self.draw(board)

        self.caption.set(
            f'{self.case["id"]} | {self.active_algorithm}'
            f" | {status} | Visited: {nodes}"
        )

        if status != "step":
            self.playing = False
            self.done = True

        return True

    def step(self):
        self.playing = False
        self.start()
        token = self.cancel

        def advance():
            if token.is_set() or self.done or self.playing:
                return
            if not self.consume():
                self.root.after(20, advance)

        advance()

    def toggle(self):
        self.start()
        if not self.done:
            self.playing = not self.playing

    def tick(self):
        if self.playing:
            self.consume()
        self.root.after(self.delay.get(), self.tick)

    def draw(self, board):
        cv = self.canvas
        cv.delete("all")

        grid = (
            self.case["grid"] if self.game == "akari" else board
        )
        rows, cols = len(grid), len(grid[0])
        size = min(56, 520 / max(rows, cols))
        left, top = 85, 65

        lit = 0
        if self.game == "akari":
            for u in range(self.problem.num_white):
                if board >> u & 1:
                    lit |= self.problem.ray_mask[u]

        for r in range(rows):
            for c in range(cols):
                x, y = left + c * size, top + r * size
                value = grid[r][c]
                color, symbol = "#ffffff", None

                if self.game == "akari":
                    if value != -2:
                        color = "#263448"
                        symbol = str(value) if value >= 0 else None
                    else:
                        u = self.problem.coord_to_id[r, c]
                        color = (
                            "#fff0b0" if lit >> u & 1 else "#ffffff"
                        )

                cv.create_rectangle(
                    x, y, x + size, y + size,
                    fill=color, outline="#a7b2c0",
                )

                if symbol is not None:
                    cv.create_text(
                        x + size / 2, y + size / 2,
                        text=symbol,
                        fill="white",
                        font=("Arial", 18, "bold"),
                    )

                if (
                    self.game == "akari"
                    and value == -2
                    and board >> u & 1
                ):
                    cv.create_oval(
                        x + size * .27, y + size * .27,
                        x + size * .73, y + size * .73,
                        fill="#f3ad18",
                        outline="#ad7310",
                        width=2,
                    )

                if self.game == "tents":
                    if value == 1:
                        cv.create_rectangle(
                            x + size * .45, y + size * .5,
                            x + size * .55, y + size * .85,
                            fill="#855b38", outline="",
                        )
                        cv.create_polygon(
                            x + size * .5, y + size * .12,
                            x + size * .18, y + size * .65,
                            x + size * .82, y + size * .65,
                            fill="#25875c",
                        )

                    elif value == 2:
                        cv.create_polygon(
                            x + size * .5, y + size * .18,
                            x + size * .12, y + size * .82,
                            x + size * .88, y + size * .82,
                            fill="#ed9445",
                            outline="#a45a25",
                        )
                        cv.create_line(
                            x + size * .5, y + size * .2,
                            x + size * .5, y + size * .82,
                            fill="#a45a25",
                            width=2,
                        )

        if self.game == "tents":
            for axis, limits in (
                ("row", self.case["row_limits"]),
                ("col", self.case["col_limits"]),
            ):
                for i, target in enumerate(limits):
                    count = (
                        sum(v == 2 for v in grid[i])
                        if axis == "row"
                        else sum(row[i] == 2 for row in grid)
                    )
                    x, y = (
                        (left - 35, top + (i + .5) * size)
                        if axis == "row"
                        else (left + (i + .5) * size, top - 25)
                    )
                    cv.create_text(
                        x, y,
                        text=f"{count}/{target}",
                        font=("Arial", 12, "bold"),
                        fill=(
                            "#238057" if count == target else "#46566b"
                        ),
                    )


def launch(game):
    root = tk.Tk()
    App(root, game)
    root.mainloop()