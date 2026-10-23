
import heapq
from itertools import count

try:
    from game_minesweeper.logic import TentsAndTreeState, TENT, EMPTY
except ImportError:
    from logic import TentsAndTreeState, TENT, EMPTY

#số vô cực, dùng để đánh dấu trạng thái không có lời giải
INF = float("inf")

#kiểm tra trạng thái đích
def is_goal(state, tree_index):
    return (
        tree_index == len(state.trees)
        and state.row_tents == state.row_limits
        and state.col_tents == state.col_limits
    )


#kiểm tra khả năng hoàn thành
#thực hiện forward checking: loại sớm một trạng thái nếu các điều kiện cần lời giải đã không còn đúng
"""def is_feasible(state, tree_index):
    remaining = len(state.trees) - tree_index

    row_need = [l - c for l, c in zip(state.row_limits, state.row_tents)]
    col_need = [l - c for l, c in zip(state.col_limits, state.col_tents)]

    # Số lều còn thiếu phải khớp số cây còn lại
    if sum(row_need) != remaining or sum(col_need) != remaining:
        return False

    # Mỗi cây còn lại phải còn ít nhất một ô đặt được
    for i in range(tree_index, len(state.trees)):
        if not state.get_successors(i):
            return False

    # Hàng/cột cần k lều thì phải có ít nhất k cây còn lại nằm sát nó
    rest = state.trees[tree_index:]
    for r, need in enumerate(row_need):
        if need > sum(1 for tr, _ in rest if abs(tr - r) <= 1):
            return False
    for c, need in enumerate(col_need):
        if need > sum(1 for _, tc in rest if abs(tc - c) <= 1):
            return False

    return True
"""
def is_feasible(state, tree_index):
    """Forward checking mạnh: đếm số ô ứng viên THỰC SỰ còn đặt được."""
    n = len(state.trees)
    remaining = n - tree_index
    rows, cols = len(state.grid), len(state.grid[0])

    row_need = [l - c for l, c in zip(state.row_limits, state.row_tents)]
    col_need = [l - c for l, c in zip(state.col_limits, state.col_tents)]

    # Số lều còn thiếu phải khớp số cây còn lại, và không hàng/cột nào đặt dư
    if sum(row_need) != remaining or sum(col_need) != remaining:
        return False
    if min(row_need, default=0) < 0 or min(col_need, default=0) < 0:
        return False

    # Mỗi cây còn lại phải còn ô đặt được; gom các ô ứng viên (đã loại ô bị lều khác chặn)
    cand = set()
    for i in range(tree_index, n):
        succ = state.get_successors(i)
        if not succ:
            return False
        cand.update(succ)

    cand_r = [0] * rows
    cand_c = [0] * cols
    for r, c in cand:
        cand_r[r] += 1
        cand_c[c] += 1

    # Hàng/cột cần k lều thì phải còn ít nhất k ô ứng viên
    for r in range(rows):
        if row_need[r] > cand_r[r]:
            return False
    for c in range(cols):
        if col_need[c] > cand_c[c]:
            return False
    return True



def heuristic(state, tree_index):
    if not is_feasible(state, tree_index):
        return INF
    return len(state.trees) - tree_index

"""
def A_star_search(state, tree_index=0):
    h0 = heuristic(state, tree_index)
    if h0 == INF:
        return None, 0

    serial = count()  # phá hòa cuối cùng, tránh so sánh state
    # (f, h, serial, g, tree_index, state): f nhỏ trước, hòa f thì h nhỏ trước
    frontier = [(0 + h0, h0, next(serial), 0, tree_index, state)]
    expanded = 0

    while frontier:
        f, h, _, g, idx, current = heapq.heappop(frontier)

        if is_goal(current, idx):
            return current, expanded

        expanded += 1

        for r, c in current.get_successors(idx):
            grid = [row[:] for row in current.grid]
            grid[r][c] = TENT
            nxt = TentsAndTreeState(
                grid, current.row_limits, current.col_limits, current.trees
            )

            nh = heuristic(nxt, idx + 1)
            if nh == INF:
                continue  # trạng thái chết, không đưa vào frontier

            ng = g + 1
            heapq.heappush(frontier, (ng + nh, nh, next(serial), ng, idx + 1, nxt))

    return None, expanded
"""

def A_star_search(state, tree_index=0, on_step=None):
    """Trả về (goal_state, số nút đã mở rộng), hoặc (None, số nút) nếu vô nghiệm."""
    h0 = heuristic(state, tree_index)
    if h0 == INF:
        return None, 0

    rows, cols = len(state.grid), len(state.grid[0])
    initial_mask = 0
    for r in range(rows):
        for c in range(cols):
            if state.grid[r][c] == TENT:
                initial_mask |= 1 << (r * cols + c)

    cur = initial_mask  # mask của bàn cờ đang nằm trong state

    def load_mask(mask):
        """Chỉ lật những ô khác nhau giữa mask hiện tại và mask cần nạp."""
        nonlocal cur
        diff = cur ^ mask
        while diff:
            low = diff & -diff
            i = low.bit_length() - 1
            r, c = divmod(i, cols)
            if mask & low:
                state.grid[r][c] = TENT
                state.row_tents[r] += 1
                state.col_tents[c] += 1
            else:
                state.grid[r][c] = EMPTY
                state.row_tents[r] -= 1
                state.col_tents[c] -= 1
            diff ^= low
        cur = mask

    serial = count()
    # Khóa: (f, h, MRV, -serial, idx, mask)
    #  - f, h : tiêu chuẩn A* (h nhỏ = sâu hơn, nên ưu tiên đi sâu)
    #  - MRV  : cây kế tiếp ít lựa chọn nhất thì đi trước
    #  - -serial: LIFO, nút sinh sau được lấy trước
    frontier = [(tree_index + h0, h0, 0, 0, tree_index, initial_mask)]
    expanded = 0

    while frontier:
        f, h, _, _, idx, mask = heapq.heappop(frontier)
        load_mask(mask)

        expanded += 1
        if on_step is not None:
            on_step(state.grid, expanded)

        if is_goal(state, idx):
            return state, expanded

        for r, c in state.get_successors(idx):
            state.grid[r][c] = TENT
            state.row_tents[r] += 1
            state.col_tents[c] += 1

            nh = heuristic(state, idx + 1)
            nxt = len(state.get_successors(idx + 1)) if nh != INF else 0

            state.grid[r][c] = EMPTY
            state.row_tents[r] -= 1
            state.col_tents[c] -= 1

            if nh == INF:
                continue  # nhánh chết, không đưa vào frontier

            next_mask = mask | (1 << (r * cols + c))
            heapq.heappush(
                frontier,
                (idx + 1 + nh, nh, nxt, -next(serial), idx + 1, next_mask),
            )

    load_mask(initial_mask)
    return None, expanded