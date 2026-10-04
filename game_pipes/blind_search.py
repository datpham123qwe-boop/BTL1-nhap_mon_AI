from typing import Tuple, Optional, Set
import logic as lg

def solve_dfs(state: lg.PipeState, index: int, fixed_cells: Set[Tuple[int, int]]) -> Optional[lg.PipeState]:
    total_cells = state.rows * state.cols

    # Base case
    if index == total_cells:
        if state.is_goal():
            return state
        return None

    # Tọa độ (r, c)
    r = index // state.cols
    c = index % state.cols

    # Lấy các góc xoay duy nhất của ô
    rotations = lg.get_unique_rotations(state.grid[r][c])

    # Thử từng góc xoay
    for mask in rotations:
        state.grid[r][c] = mask
        fixed_cells.add((r, c))

        # Pruning
        if state.is_valid_cell_placement(r, c, fixed_cells):
            res = solve_dfs(state, index + 1, fixed_cells)
            if res is not None:
                return res # Đã tìm thấy kết quả -> Trả res

        # Backtrack: Thử góc xoay khác
        fixed_cells.remove((r, c))
    
    return None

def solve(initial_state: lg.PipeState) -> Optional[lg.PipeState]:
    """Hàm wrapper để khởi chạy thuật toán tìm kiếm DFS."""
    fixed_cells = set()
    return solve_dfs(initial_state, 0, fixed_cells)