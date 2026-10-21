# main.py
"""from game_minesweeper.logic import TentsAndTreeState
from game_minesweeper.blind_search import dfs_search



def main():
    grid = [
        [0, 0, 0],
        [0, 0, 0]
    ]
    row_limits = [1, 1]
    col_limits = [1, 1, 1]
    trees = [(0, 0)]
    game_state = TentsAndTreeState(grid, row_limits, col_limits, trees)
    is_solved = dfs_search(game_state)

    if is_solved:
        print("Tìm thấy lời giải! Cấu hình lều như sau:")
        for row in game_state.grid:
            print(row)
    else:
        print("Bài toán không có lời giải.")

if __name__ == "__main__":
    main()"""

from game_minesweeper.logic import TentsAndTreeState
from game_minesweeper.blind_search import dfs_search
from game_minesweeper.heuristic_search import A_star_search
from time import perf_counter_ns

cases = [
    {
        "name": "case0_test_don_gian",
        "grid": [
            [0, 0, 0],
            [0, 0, 0],
            [0, 0, 0],
        ],
        "row_limits": [1, 0, 0],
        "col_limits": [0, 1, 0],
        "trees": [(0, 0)],
    },
    {
        "name": "case1_co_loi_giai_1_tree",
        "grid": [
            [0, 0, 0],
            [0, 0, 0],
            [0, 0, 0],
        ],
        "row_limits": [0, 1, 0],
        "col_limits": [0, 1, 0],
        "trees": [(1, 1)],
    },
    {
        "name": "case2_co_loi_giai_2_tree",
        "grid": [
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
        ],
        "row_limits": [1, 1, 0, 0],
        "col_limits": [0, 1, 1, 0],
        "trees": [(0, 0), (1, 3)],
    },
    {
        "name": "case3_khong_co_loi_giai",
        "grid": [
            [0, 0, 0],
            [0, 0, 0],
            [0, 0, 0],
        ],
        "row_limits": [0, 1, 0],
        "col_limits": [1, 0, 0],
        "trees": [(0, 0), (1, 2)],
    },
]

def make_state(case):
    grid = [row[:] for row in case["grid"]]
    return TentsAndTreeState(grid, case["row_limits"], case["col_limits"], case["trees"])


def main():
    for case in cases:
        print(f"=== {case['name']} ===")

        dfs_state = make_state(case)
        start = perf_counter_ns()
        dfs_result = dfs_search(dfs_state)
        dfs_time = (perf_counter_ns() - start) / 1_000_000
        print(f"DFS: {dfs_result}, thời gian: {dfs_time:.6f} ms")

        astar_state = make_state(case)
        start = perf_counter_ns()
        astar_solution, expanded = A_star_search(astar_state)
        astar_time = (perf_counter_ns() - start) / 1_000_000
        print(f"A*: {astar_solution is not None}, thời gian: {astar_time:.6f} ms, nút mở rộng: {expanded}")

        if dfs_result:
            print("Lời giải DFS:")
            for row in dfs_state.grid:
                print(row)
        if astar_solution is not None:
            print("Lời giải A*:")
            for row in astar_solution.grid:
                print(row)
        print()


if __name__ == "__main__":
    main()