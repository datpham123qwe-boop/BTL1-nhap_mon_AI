from typing import Tuple, Optional, Set
import logic as lg

def solve_dfs(state: lg.PipeState, index: int) -> Optional[lg.PipeState]:
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
    rotations = lg.get_unique_rotations(state.grid[index])

    # Thử từng góc xoay
    for mask in rotations:
        state.grid[index] = mask

        # Nếu hướng xoay này hợp lí -> đi tiếp theo hướng này
        if state.is_valid_cell_placement(r, c, index):
            res = solve_dfs(state, index + 1)
            if res is not None:
                return res # Đã tìm thấy kết quả -> Trả res
    
    return None

def solve(initial_state: lg.PipeState) -> Optional[lg.PipeState]:
    """Hàm wrapper để khởi chạy thuật toán tìm kiếm DFS."""
    return solve_dfs(initial_state, 0)