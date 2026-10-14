from typing import Tuple, Optional
import logic as lg


def solve_dfs(problem: lg.AkariProblem) -> Tuple[Optional[int], int]:
    """
    Giải thuật Tìm kiếm mù theo chiều sâu (DFS Backtracking).
    Duyệt tuần tự từ ô trắng u = 0 đến num_white - 1.
    Trả về: (bulbs_mask_solution, nodes_explored)
    """
    num_white = problem.num_white
    initial_clues = tuple(c[2] for c in problem.clues)

    # =====================================================================
    # TODO 1: Tạo mảng suffix_mask[i] chứa bitmask của các ô từ i đến num_white - 1
    # Mục đích: Giúp đếm nhanh xem quanh một bức tường còn bao nhiêu ô trắng CHƯA XÉT
    # bằng công thức: (problem.clue_adj_mask[c_idx] & suffix_mask[u + 1]).bit_count()
    # =====================================================================
    suffix_mask = [0] * (num_white + 1)

    stack = [(0, 0, 0, initial_clues)]
    nodes_explored = 0

    while stack:
        u, bulbs_mask, lit_mask, rem_clues = stack.pop()
        nodes_explored += 1

        # =================================================================
        # TODO 2: Kiểm tra điều kiện dừng khi đã duyệt hết ô trắng (u == num_white)
        # - Nếu toàn bộ ô trắng đã sáng (lit_mask == problem.all_white_mask)
        #   và mọi tường có số đã đủ đèn (all(c == 0 for c in rem_clues)):
        #   -> Trả về (bulbs_mask, nodes_explored)
        # =================================================================
        # [VIẾT CODE CỦA BẠN Ở ĐÂY]


        # =================================================================
        # TODO 3: Xét Nhánh 1 - KHÔNG đặt đèn tại ô u (can_leave_empty)
        # - Duyệt qua các bức tường c_idx kề với ô u (problem.white_to_clues[u]):
        #   + Tính số ô trắng chưa xét còn lại quanh tường c_idx (dùng suffix_mask[u + 1])
        #   + Nếu số đèn còn thiếu rem_clues[c_idx] > số ô còn lại -> Không thể bỏ trống!
        # =================================================================
        can_leave_empty = True
        # [VIẾT CODE CỦA BẠN Ở ĐÂY]


        # =================================================================
        # TODO 4: Xét Nhánh 2 - ĐẶT ĐÈN tại ô u (can_place_bulb)
        # - Điều kiện 1: Ô u chưa bị chiếu sáng bởi đèn khác: not ((lit_mask >> u) & 1)
        # - Điều kiện 2: Duyệt các tường c_idx trong problem.white_to_clues[u]:
        #   + Nếu tường đã đủ đèn (clues_list[c_idx] == 0) -> Bị lố đèn -> Cắt tỉa!
        #   + Giảm clues_list[c_idx] đi 1 và kiểm tra xem số đèn còn cần có vượt quá
        #     số ô chưa xét còn lại quanh tường đó không.
        # =================================================================
        can_place_bulb = False
        new_clues = None
        # [VIẾT CODE CỦA BẠN Ở ĐÂY]


        # =================================================================
        # TODO 5: Đẩy các trạng thái con hợp lệ vào stack (u + 1)
        # - Nếu can_place_bulb: cập nhật bulbs_mask | (1 << u) và lit_mask | problem.ray_mask[u]
        # - Nếu can_leave_empty: giữ nguyên bulbs_mask, lit_mask, rem_clues
        # =================================================================
        # [VIẾT CODE CỦA BẠN Ở ĐÂY]

    return None, nodes_explored


def solve(problem: lg.AkariProblem) -> Optional[int]:
    """Hàm wrapper trả về nghiệm bulbs_mask."""
    sol, _ = solve_dfs(problem)
    return sol