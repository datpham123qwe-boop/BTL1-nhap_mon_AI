import heapq
from typing import Optional, Tuple, List, Set
from game_akari import logic as lg


def get_next_candidates(problem: lg.AkariProblem, lit_mask: int, rem_clues: Tuple[int, ...]) -> List[int]:
    """
    Tìm tập hợp các vị trí đặt bóng đèn tiếp theo (Tại cạnh tường hoặc ô trắng cần chiếu sáng):
    - Trả về [] (rỗng) nếu phát hiện nhánh cụt (tường thiếu ô hoặc ô tối bị cô lập).
    - Trả về danh sách gồm 1 phần tử [v] nếu phát hiện nước đi bắt buộc.
    - Trả về danh sách các ô ứng viên [v1, v2, ...] của ràng buộc chặt nhất.
    """
    blocked_mask = lit_mask # Lấy blocked_mask: vị trí cấm đặt đèn
    for c_idx in range(problem.num_clues): 
        if rem_clues[c_idx] == 0:
           blocked_mask |= problem.clue_adj_mask[c_idx] 

    best_candidates: List[int] = [] #ds ứng viên tốt nhất
    min_choices = float("inf")  # Dựa trên số lựa chọn đặt ít nhất

    for c_idx in range(problem.num_clues):  #Quét từng ô tường
        need = rem_clues[c_idx]
        avail_cells = []
        if need > 0:    # Nếu ô tường cần đặt đèn -> khảo sát ứng viên
            for u in problem.clue_adj_cells[c_idx]:
                if not ((blocked_mask >> u) & 1):
                    avail_cells.append(u)
            count = len(avail_cells)
            if count < need:    # ko còn ô để đặt theo clue -> nhánh cụt
                return []
            elif count == need: # Vừa đúng -> chọn ứng viên này luôn
                if min_choices > 1:
                    min_choices = 1
                best_candidates = [avail_cells[0]]
            elif count < min_choices:   # Tạm chọn ứng viên tốt nhất
                min_choices = count
                best_candidates = avail_cells

    for u in range(problem.num_white):  # Duyệt qua các ô trắng
        if not ((lit_mask >> u) & 1):
            options_mask = problem.ray_mask[u] & ~blocked_mask  # Lấy danh sách các vị trí có thể thắp sáng ô trắng này
            if options_mask == 0:   # ô trắng bị cô lập -> nhánh cụt
                return []
            count = options_mask.bit_count()
            if count < min_choices:
                min_choices = count
                best_candidates = [v for v in range(problem.num_white) if (options_mask >> v) & 1]

    return best_candidates


def compute_f_score(problem: lg.AkariProblem, bulbs_mask: int, lit_mask: int, rem_clues: Tuple[int, ...]) -> Tuple[float, int]:
    """
    Hàm A*: f(n) = g(n) + h(n)
    - g(n): Số lượng bóng đèn đã đặt.
    - h(n): Ước lượng số bóng đèn tối thiểu cần đặt thêm để phủ sáng vùng tối và thỏa mãn tường.
    Trả về: (f_score, unlit_cnt)
    """
    unlit_cnt = (problem.all_white_mask ^ lit_mask).bit_count() # Số ô trắng chưa thắp
    g_cost = bulbs_mask.bit_count() # Số đèn đã đặt
    h_cost = (unlit_cnt / problem.max_ray_len) + sum(rem_clues) # ước lượng số đèn tối thiểu cần đặt

    return (g_cost + h_cost, unlit_cnt)

def solve_astar(problem: lg.AkariProblem, on_step=None) -> Tuple[Optional[int], int]:
    """
    Mỗi bước chọn 1 node có f min nhất và đặt 1 bóng đèn hợp lệ.
    Trả về: (bulbs_mask_solution, nodes_explored)
    """
    initial_clues = tuple(c[2] for c in problem.clues)
    (f0, unlit0) = compute_f_score(problem, 0, 0, initial_clues)
    open_set = [(f0, unlit0, 0, 0, initial_clues)]  # minHeap chứa các Node cần duyệt
    visited: Set[int] = {0} # Tập chứa trạng thái đã thăm
    nodes_explored = 0

    while open_set: # Duyệt đến khi hết Heap
        f_score, unlit_cnt, bulbs_mask, lit_mask, rem_clues = heapq.heappop(open_set)   # pop node có f min
        nodes_explored += 1
        if on_step is not None:
            on_step(bulbs_mask, nodes_explored)

        if unlit_cnt == 0 and all(c == 0 for c in rem_clues):   # Ktra trạng thái đích
            return bulbs_mask, nodes_explored

        candidates = get_next_candidates(problem, lit_mask, rem_clues)  # Lấy nước đi ứng viên từ node này
        for v in candidates:    # Tạo ra các node con hợp lệ kế tiếp và push vào heap
            next_bulbs = bulbs_mask | (1 << v)
            if next_bulbs in visited:
                continue
            visited.add(next_bulbs)
            next_lit = lit_mask | problem.ray_mask[v]
            clues_list = list(rem_clues)
            for clue in problem.white_to_clues[v]:
                clues_list[clue] -= 1
            next_clues = tuple(clues_list)
            next_f, next_unlit = compute_f_score(problem, next_bulbs, next_lit, next_clues)
            heapq.heappush(open_set, (next_f, next_unlit, next_bulbs, next_lit, next_clues))

    return None, nodes_explored

def solve(problem: lg.AkariProblem) -> Optional[int]:
    sol, _ = solve_astar(problem)
    return sol