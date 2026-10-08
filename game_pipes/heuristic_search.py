import heapq
import copy
from typing import Optional, Set, Tuple
import logic as lg

class SearchNode:
    """
    Cấu trúc lưu trữ trạng thái tìm kiếm
    """
    def __init__(self, state: lg.PipeState, g: int, h: int):
        self.state = state
        self.g = g # Chi phí đường đi từ trạng thái đầu tiên (bằng index của ô đó)
        self.h = h # Chi phí ước lượng đến đích (Lấy từ hàm Heuristic: Tổng số Leaks trong số ống đã chốt)
        self.f = g + h

    def __lt__(self, other):
        # Hàm so sánh < cho Priority Queue
        if self.f == other.f:
            return self.h < other.h
        return self.f < other.f


def get_heuristic_diff(state: lg.PipeState, current_index: int) -> int:
    """
    Tính sự thay đổi (Delta) của Heuristic với độ phức tạp O(1).
    current_index: Là chỉ mục của ô VỪA ĐƯỢC ĐẶT XUỐNG.
    """
    delta_h = 0
    cols = state.cols
    
    r = current_index // cols
    c = current_index % cols
    mask = state.grid[current_index] # Truy cập mảng 1D trực tiếp bằng current_index
    
    for d in lg.DIRECTIONS:
        if (mask & d) != 0:
            neighbor_cell = state.get_neighbor(r, c, d)
            
            if neighbor_cell:
                nr, nc = neighbor_cell
                neighbor_index = nr * cols + nc
                
                if neighbor_index > current_index: # Nếu hướng ống quay ra vùng chưa chốt -> +1 Leak
                    delta_h += 1
                elif neighbor_index < current_index: # Ngược lại -> bịt 1 hướng ống đã chốt -> -1 Leak
                    delta_h -= 1
            
    return delta_h


def solve_astar(initial_state: lg.PipeState) -> Optional[lg.PipeState]:
    """
    A* Search
    """
    rows, cols = initial_state.rows, initial_state.cols
    total_cells = rows * cols

    root = SearchNode(initial_state, 0, 0)
    
    open_set = [] # Priority Queue chứa các node trạng thái sắp xếp theo f() min
    heapq.heappush(open_set, root)
    
    while open_set:
        current_node = heapq.heappop(open_set)
        
        if current_node.g == total_cells: # Nếu đã đến ô cuối -> Ktra goal
            if current_node.state.is_goal():
                return current_node.state
            else:
                continue
        
        r = current_node.g // cols
        c = current_node.g % cols
        index = current_node.g
        
        # Lấy các góc xoay duy nhất
        rotations = lg.get_unique_rotations(current_node.state.grid[index])

        # Sinh ra các trạng thái con valid và tính f() + push queue
        for mask in rotations:
            child_state = current_node.state.clone() 
            child_state.grid[index] = mask
            
            if child_state.is_valid_cell_placement(r, c, current_node.g):
                gn = current_node.g + 1
                delta_h = get_heuristic_diff(child_state, current_node.g)
                hn = current_node.h + delta_h
                child_node = SearchNode(child_state, gn, hn)    
                heapq.heappush(open_set, child_node)     
            
    return None

def solve(initial_state: lg.PipeState) -> Optional[lg.PipeState]:
    """Hàm wrapper để khởi chạy thuật toán tìm kiếm A*."""
    return solve_astar(initial_state)
