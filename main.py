# main.py
"""
Script chạy thử nghiệm và so sánh thuật toán cho bài toán Tents and Trees
"""

from time import perf_counter_ns
from game_tent.logic import TentsAndTreeState
from game_tent.blind_search import dfs_search
from game_tent.heuristic_search import A_star_search

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
    print("=" * 70)
    print("   BÀI TẬP LỚN 1 - SO SÁNH GIẢI THUẬT CHO TENTS AND TREES")
    print("=" * 70)
    for case in cases:
        print(f"\n=== {case['name']} ===")

        dfs_state = make_state(case)
        start = perf_counter_ns()
        dfs_result = dfs_search(dfs_state)
        dfs_time = (perf_counter_ns() - start) / 1_000_000
        print(f"DFS: {'Thành công' if dfs_result else 'Vô nghiệm'}, Thời gian: {dfs_time:.4f} ms")

        astar_state = make_state(case)
        start = perf_counter_ns()
        astar_solution, expanded = A_star_search(astar_state)
        astar_time = (perf_counter_ns() - start) / 1_000_000
        print(f"A* : {'Thành công' if astar_solution is not None else 'Vô nghiệm'}, Thời gian: {astar_time:.4f} ms, Nodes mở rộng: {expanded}")

        if dfs_result:
            print("Lời giải DFS:")
            for row in dfs_state.grid:
                print(row)
        if astar_solution is not None:
            print("Lời giải A*:")
            for row in astar_solution.grid:
                print(row)


if __name__ == "__main__":
    main()
