import heapq
import copy
from typing import Optional, Set, Tuple
import logic as lg

class SearchNode:
    """
    PHẦN 1: Cấu trúc lưu trữ trạng thái tìm kiếm
    """
    def __init__(self, state: lg.PipeState, fixed_cells: Set[Tuple[int, int]], g: int, h: int):
        # TODO 1.1: Khởi tạo các thuộc tính cơ bản
        self.state = state
        self.fixed_cells = fixed_cells
        self.g = g #Số thực tế / Số lượng ô đã cố định
        self.h = h # heuristic func
        
        # TODO 1.2: Tính giá trị f(n) = g(n) + h(n)
        self.f = g + h

    def __lt__(self, other):
        # TODO 1.3: Định nghĩa hàm so sánh < (less than) cho Priority Queue
        # Gợi ý: Hàng đợi ưu tiên sẽ lấy Node có f nhỏ nhất. 
        # Nếu self.f == other.f, hãy so sánh self.h và other.h (ưu tiên h nhỏ hơn).
        if self.f == other.f:
            return self.h < other.h
        return self.f < other.f


def calculate_heuristic(state: lg.PipeState, fixed_cells: Set[Tuple[int, int]]) -> int: # Check: Uprade to O(1)
    """
    PHẦN 2: Logic hàm tính Heuristic h(n) (Đếm cổng hở ranh giới (Leaks))
    """
    # TODO 2.1: Khởi tạo biến đếm open_ports = 0
    open_ports = 0
    # TODO 2.2: Duyệt vòng lặp qua từng tọa độ (r, c) CHỈ NẰM TRONG tập fixed_cells
    for (r, c) in fixed_cells:
        # TODO 2.3: Lấy bitmask của ô (r, c) từ state.grid
        mask = state.grid[r][c]
        # TODO 2.4: Dùng vòng lặp duyệt qua các hướng trong lg.DIRECTIONS (UP, RIGHT, DOWN, LEFT)
        for d in lg.DIRECTIONS:
            # Kiểm tra xem ô (r, c) có chĩa ống ra hướng này không (dùng phép &)
            # Nếu có chĩa ống:
            if (mask & d) != 0:
                # TODO 2.5: Gọi hàm state.get_neighbor(r, c, direction) để lấy tọa độ láng giềng
                neighbor_cell = state.get_neighbor(r, c, d)
                # TODO 2.6: Kiểm tra 2 điều kiện:
                # 1. Láng giềng KHÁC None (không bị đâm ra ngoài tường ở chế độ non-wrap)
                # 2. Láng giềng KHÔNG NẰM TRONG tập fixed_cells
                # Nếu cả 2 điều kiện đúng -> Tăng open_ports lên 1
                if neighbor_cell and neighbor_cell not in fixed_cells:
                    open_ports += 1
                
    # TODO 2.7: Trả về giá trị open_ports
    return open_ports


def solve_astar(initial_state: lg.PipeState) -> Optional[lg.PipeState]:
    """
    PHẦN 3: Luồng thực thi chính của A* Search
    """
    rows, cols = initial_state.rows, initial_state.cols
    total_cells = rows * cols

    # TODO 3.1: KHỞI TẠO ROOT NODE
    # - fixed_cells ban đầu = set() rỗng
    fixed_cells = set()
    # - g = 0
    g = 0
    # - h = gọi hàm calculate_heuristic() cho initial_state
    h = calculate_heuristic(initial_state, fixed_cells)
    # - Tạo root node bằng class SearchNode
    root = SearchNode(initial_state, fixed_cells, g, h)
    
    # TODO 3.2: KHỞI TẠO HÀNG ĐỢI ƯU TIÊN
    open_set = []
    heapq.heappush(open_set, root)
    
    # TODO 3.3: BẮT ĐẦU VÒNG LẶP KHÁM PHÁ
    while open_set:
    
        # TODO 3.4: Pop Node có f nhỏ nhất ra khỏi open_set
        current_node = heapq.heappop(open_set)
        
        # TODO 3.5: KIỂM TRA ĐÍCH (GOAL TEST)
        if current_node.g == total_cells:
            if current_node.state.is_goal():
        #     Nếu trả về True -> return current_node.state (Đã giải xong!)
                return current_node.state
        #     Nếu False -> continue (Bỏ qua nhánh này, lấy node tiếp theo)
            else:
                continue
        
        # TODO 3.6: CHUẨN BỊ SINH TRẠNG THÁI CON
        # - Tính r, c từ current_node.index (gợi ý: r = index // cols, c = index % cols)
        r = current_node.g // cols
        c = current_node.g % cols
        # - Lấy danh sách góc xoay bằng hàm lg.get_unique_rotations() cho ô (r, c)
        rotations = lg.get_unique_rotations(current_node.state.grid[r][c])
        
        # TODO 3.7: DUYỆT QUA TỪNG GÓC XOAY (EXPAND)
        for mask in rotations:
            # a. Tạo bản sao sâu (clone) của trạng thái: child_state = current_node.state.clone() 
            child_state = current_node.state.clone() 
            # b. Tạo bản sao của fixed_cells: child_fixed_cells = current_node.fixed_cells.copy()
            child_fixed_cells = current_node.fixed_cells.copy()
            # c. Áp dụng góc xoay: child_state.grid[r][c] = mask
            child_state.grid[r][c] = mask
            
            # d. CẮT TỈA (Pruning):
            # Gọi child_state.is_valid_cell_placement(r, c, child_fixed_cells)
            # Nếu HỢP LỆ:
            #     - Thêm (r, c) vào child_fixed_cells
            #     - Tính g_new = current_node.g + 1
            #     - Tính h_new = calculate_heuristic(child_state, child_fixed_cells)
            #     - Tạo ChildNode mới bằng class SearchNode
            #     - Push ChildNode vào open_set bằng heapq.heappush
            if child_state.is_valid_cell_placement(r, c, child_fixed_cells):
                child_fixed_cells.add((r,c))
                gn = current_node.g + 1
                hn = calculate_heuristic(child_state, child_fixed_cells)
                child_node = SearchNode(child_state, child_fixed_cells, gn, hn)    
                heapq.heappush(open_set, child_node)     
            # (Nếu không hợp lệ thì không làm gì cả, vòng lặp tự chuyển sang góc xoay tiếp theo)
            
    # Nếu hàng đợi trống rỗng mà chưa return, nghĩa là vô nghiệm
    return None

def solve(initial_state: lg.PipeState) -> Optional[lg.PipeState]:
    """Hàm wrapper để khởi chạy thuật toán tìm kiếm A*."""
    return solve_astar(initial_state)
