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

cases = [
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

for c in cases:
    state = TentsAndTreeState(c["grid"], c["row_limits"], c["col_limits"], c["trees"])
    result = dfs_search(state)
    print("=== ", c["name"], "===")
    print("Kết quả:", result)
    if result:
        for row in state.grid:
            print(row)
    print()