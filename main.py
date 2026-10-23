import random
from time import perf_counter_ns

from game_minesweeper.logic import TentsAndTreeState, TENT
from game_minesweeper.blind_search import dfs_search
from game_minesweeper.heuristic_search import A_star_search

DFS_NODE_LIMIT = 2_000_000


class NodeLimit(Exception):
    pass


# ---------- Test case thủ công (đã sửa cho đúng) ----------
cases = [
    {   # có nghiệm: lều (0,1)
        "name": "case0_don_gian",
        "grid": [[0] * 3 for _ in range(3)],
        "row_limits": [1, 0, 0],
        "col_limits": [0, 1, 0],
        "trees": [(0, 0)],
    },
    {   # có nghiệm: lều (0,1)
        "name": "case1_1_cay",
        "grid": [[0] * 3 for _ in range(3)],
        "row_limits": [1, 0, 0],
        "col_limits": [0, 1, 0],
        "trees": [(1, 1)],
    },
    {   # có nghiệm: lều (0,1) và (2,3)
        "name": "case2_2_cay",
        "grid": [[0] * 4 for _ in range(4)],
        "row_limits": [1, 0, 1, 0],
        "col_limits": [0, 1, 0, 1],
        "trees": [(0, 0), (1, 3)],
    },
    {   # vô nghiệm: tổng giới hạn (1) khác số cây (2)
        "name": "case3_vo_nghiem",
        "grid": [[0] * 3 for _ in range(3)],
        "row_limits": [0, 1, 0],
        "col_limits": [1, 0, 0],
        "trees": [(0, 0), (1, 2)],
        "expect_solution": False,
    },
]


# ---------- Sinh bản đồ có nghiệm đảm bảo ----------
def generate_case(size, n_trees, seed):
    """Đặt lều hợp lệ trước, gắn mỗi lều một cây kề, rồi đếm giới hạn từ LỀU."""
    rng = random.Random(seed)
    tents, trees, used = [], [], set()
    attempts = 0
    while len(tents) < n_trees and attempts < 20000:
        attempts += 1
        r, c = rng.randrange(size), rng.randrange(size)
        if (r, c) in used:
            continue
        if any(abs(r - a) <= 1 and abs(c - b) <= 1 for a, b in tents):
            continue
        nbrs = [
            (r + dr, c + dc)
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))
            if 0 <= r + dr < size and 0 <= c + dc < size and (r + dr, c + dc) not in used
        ]
        if not nbrs:
            continue
        tree = rng.choice(nbrs)
        tents.append((r, c))
        trees.append(tree)
        used.add((r, c))
        used.add(tree)

    row_limits = [0] * size
    col_limits = [0] * size
    for r, c in tents:          # đếm theo LỀU, không phải theo cây
        row_limits[r] += 1
        col_limits[c] += 1
    rng.shuffle(trees)
    return {
        "name": f"gen_{size}x{size}_{len(trees)}cay",
        "grid": [[0] * size for _ in range(size)],
        "row_limits": row_limits,
        "col_limits": col_limits,
        "trees": trees,
    }


def build_generated_cases():
    plan = [(8, 8), (9, 10), (10, 12), (11, 14), (12, 16)]
    return [generate_case(size, n, seed=size) for size, n in plan]


cases.extend(build_generated_cases())


# ---------- Kiểm tra lời giải độc lập ----------
def is_valid_solution(grid, row_limits, col_limits, trees):
    R, C = len(grid), len(grid[0])
    tents = [(r, c) for r in range(R) for c in range(C) if grid[r][c] == TENT]
    if len(tents) != len(trees):
        return False
    for r in range(R):
        if sum(1 for t in tents if t[0] == r) != row_limits[r]:
            return False
    for c in range(C):
        if sum(1 for t in tents if t[1] == c) != col_limits[c]:
            return False
    for i, (a, b) in enumerate(tents):
        for x, y in tents[i + 1:]:
            if abs(a - x) <= 1 and abs(b - y) <= 1:
                return False
    # mỗi cây ghép với một lều kề riêng
    adj = [
        [j for j, (a, b) in enumerate(tents) if abs(a - tr) + abs(b - tc) == 1]
        for tr, tc in trees
    ]
    match = {}

    def try_assign(i, seen):
        for j in adj[i]:
            if j in seen:
                continue
            seen.add(j)
            if j not in match or try_assign(match[j], seen):
                match[j] = i
                return True
        return False

    return all(try_assign(i, set()) for i in range(len(trees)))


# ---------- Chạy thuật toán ----------
def make_state(case):
    grid = [row[:] for row in case["grid"]]
    return TentsAndTreeState(
        grid, list(case["row_limits"]), list(case["col_limits"]), list(case["trees"])
    )


def run_dfs(state):
    counter = {"n": 0}

    def on_step(_grid, _nodes):
        counter["n"] += 1
        if counter["n"] > DFS_NODE_LIMIT:
            raise NodeLimit

    start = perf_counter_ns()
    try:
        ok = dfs_search(state, 0, on_step)
    except NodeLimit:
        ok = None
    ms = (perf_counter_ns() - start) / 1_000_000
    return ok, ms, counter["n"]

def run_astar(state):
    start = perf_counter_ns()
    sol, expanded = A_star_search(state)
    ms = (perf_counter_ns() - start) / 1_000_000
    return sol, ms, expanded


def check(label, case, state, claimed):
    """In kết quả đã xác minh, không tin giá trị trả về của thuật toán."""
    if claimed is None:
        return "vượt giới hạn"
    if not claimed:
        return "không tìm thấy"
    ok = is_valid_solution(state.grid, case["row_limits"], case["col_limits"], case["trees"])
    return "ĐÚNG" if ok else "SAI (lời giải không hợp lệ!)"


def main():
    print(f"{'case':<22}{'DFS ms':>12}{'DFS nút':>12}{'A* ms':>12}{'A* nút':>10}  DFS / A*")
    for case in cases:
        dfs_state = make_state(case)
        dfs_ok, dfs_ms, dfs_nodes = run_dfs(dfs_state)

        a_state = make_state(case)
        a_sol, a_ms, a_nodes = run_astar(a_state)

        dfs_txt = check("DFS", case, dfs_state, dfs_ok)
        a_txt = check("A*", case, a_state, a_sol is not None)

        dfs_nodes_txt = f">{DFS_NODE_LIMIT}" if dfs_ok is None else dfs_nodes
        print(
            f"{case['name']:<22}{dfs_ms:>12.3f}{str(dfs_nodes_txt):>12}"
            f"{a_ms:>12.3f}{a_nodes:>10}  {dfs_txt} / {a_txt}"
        )


if __name__ == "__main__":
    main()