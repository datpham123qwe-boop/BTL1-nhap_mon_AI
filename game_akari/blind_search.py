from typing import Tuple, Optional
from game_akari import logic as lg


def solve_dfs(problem: lg.AkariProblem, on_step=None) -> Tuple[Optional[int], int]:
    """
    Giải thuật Tìm kiếm mù theo chiều sâu (DFS Backtracking) có tối ưu Lookahead.
    Duyệt tuần tự từ ô trắng u = 0 đến num_white - 1.
    Trả về: (bulbs_mask_solution, nodes_explored)
    """
    num_white = problem.num_white
    initial_clues = tuple(c[2] for c in problem.clues)

    # =====================================================================
    # TODO 1: Tạo mảng suffix_mask[i] chứa bitmask của các ô từ i đến num_white - 1
    # =====================================================================
    suffix_mask = [0] * (num_white + 1)
    for i in range(num_white - 1, -1, -1):
        suffix_mask[i] = suffix_mask[i + 1] | (1 << i)

    stack = [(0, 0, 0, initial_clues)]
    nodes_explored = 0

    while stack:
        u, bulbs_mask, lit_mask, rem_clues = stack.pop()
        nodes_explored += 1
        if on_step is not None:
            on_step(bulbs_mask, nodes_explored)

        # =================================================================
        # TODO 2: Kiểm tra điều kiện dừng khi đã duyệt hết ô trắng (u == num_white)
        # =================================================================
        if u == num_white:
            if lit_mask == problem.all_white_mask and all(c == 0 for c in rem_clues):
                return bulbs_mask, nodes_explored
            continue

        # =================================================================
        # TODO 3: Xét Nhánh 1 - KHÔNG đặt đèn tại ô u (can_leave_empty)
        # =================================================================
        can_leave_empty = True
        for c_idx in problem.white_to_clues[u]:
            rem_cells = (problem.clue_adj_mask[c_idx] & suffix_mask[u + 1]).bit_count()
            if rem_clues[c_idx] > rem_cells:
                can_leave_empty = False
                break

        # =================================================================
        # TODO 4: Xét Nhánh 2 - ĐẶT ĐÈN tại ô u (can_place_bulb)
        # =================================================================
        can_place_bulb = False
        new_clues = None
        
        # Điều kiện 1: Ô u chưa bị chiếu sáng bởi đèn khác
        if not ((lit_mask >> u) & 1):
            valid = True
            temp_clues = list(rem_clues)
            for c_idx in problem.white_to_clues[u]:
                if temp_clues[c_idx] <= 0:
                    valid = False
                    break
                temp_clues[c_idx] -= 1
                rem_cells = (problem.clue_adj_mask[c_idx] & suffix_mask[u + 1]).bit_count()
                if temp_clues[c_idx] > rem_cells:
                    valid = False
                    break
            if valid:
                can_place_bulb = True
                new_clues = tuple(temp_clues)

        # =================================================================
        # TODO 5: Đẩy các trạng thái con hợp lệ vào stack (u + 1)
        # =================================================================
        if can_place_bulb:
            stack.append((u + 1, bulbs_mask | (1 << u), lit_mask | problem.ray_mask[u], new_clues))
        if can_leave_empty:
            stack.append((u + 1, bulbs_mask, lit_mask, rem_clues))

    return None, nodes_explored


def solve(problem: lg.AkariProblem) -> Optional[int]:
    """Hàm wrapper trả về nghiệm bulbs_mask."""
    sol, _ = solve_dfs(problem)
    return sol