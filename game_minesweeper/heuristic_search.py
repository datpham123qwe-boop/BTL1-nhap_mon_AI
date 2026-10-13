
import heapq
from itertools import count

try:
    from game_minesweeper.logic import TentsAndTreeState, TENT
except ImportError:
    from logic import TentsAndTreeState, TENT

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
def is_feasible(state, tree_index):
    """Forward checking: False nếu chắc chắn không thể hoàn thành lời giải."""
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


def heuristic(state, tree_index):
    if not is_feasible(state, tree_index):
        return INF
    return len(state.trees) - tree_index


def A_star_search(state, tree_index=0):
    """Trả về (goal_state, số nút đã mở rộng), hoặc (None, số nút) nếu vô nghiệm."""
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
Hàm hiện trả về một tuple, không phải giá trị Boolean:

solution, expanded = A_star_search(state)

if solution is not None:
    print(solution.grid)
    print("Số nút đã mở rộng:", expanded)
else:
    print("Không tìm thấy lời giải")
"""