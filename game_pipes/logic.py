from typing import List, Tuple, Optional, Set
from collections import deque
import copy

# Định nghĩa 4 hướng của ống bằng bitmask:
# UP (bit 0), RIGHT (bit 1), DOWN (bit 2), LEFT (bit 3)
UP = 1      # 0001
RIGHT = 2   # 0010
DOWN = 4    # 0100
LEFT = 8    # 1000

'''
Vd: Ống chữ I có dạng: 1010, 0101
    Ống chữ L: 1100, 0110, 0011, 1001
    Bình chứa (chỉ 1 cổng vào): 1000, 0100, 0010, 0001
    Ô trống: 0000
    ...
'''

DIRECTIONS = [UP, RIGHT, DOWN, LEFT]

# Offset cho grid
DIR_OFFSETS = {
    UP: (-1, 0),
    RIGHT: (0, 1),
    DOWN: (1, 0),
    LEFT: (0, -1),
}

OPPOSITE = {
    UP: DOWN,
    RIGHT: LEFT,
    DOWN: UP,
    LEFT: RIGHT,
}

def rotate_90(mask: int) -> int:
    '''
    Xoay ống 90 độ theo chiều kim đồng hồ
    Dịch 1 bit sang trái và đưa bit đó về cuối
    '''
    return ((mask << 1) & 15) | (mask >> 3)

def get_unique_rotations(mask: int) -> List[int]:
    """Trả về danh sách các góc xoay duy nhất của một loại ống"""
    rotations = []
    curr = mask
    for _ in range(4):
        if curr not in rotations:
            rotations.append(curr)
        curr = rotate_90(curr)
    return rotations
class PipeState:
    def __init__(self, grid, wrap: bool = False, rows: int = None, cols: int = None):
        # Tối ưu giải thuật: trải mảng 2D thành bytearray 1D
        if isinstance(grid, list) and isinstance(grid[0], list):
            self.rows = len(grid)
            self.cols = len(grid[0])
            self.grid = bytearray(val for row in grid for val in row)
        else:
            self.grid = grid # grid ở đây đã là bytearray 1D
            self.rows = rows
            self.cols = cols
            
        self.wrap = wrap    # Mode Wrap
        self.total_pipes = 0
        self.start_pipe = None 
        
        # Đếm tổng số ống & tìm tọa độ ống đầu tiên
        for idx in range(self.rows * self.cols):
            if self.grid[idx] != 0:
                self.total_pipes += 1
                if self.start_pipe is None:
                    self.start_pipe = (idx // self.cols, idx % self.cols)

    def get_neighbor(self, r, c, direction):
        """
        Lấy tọa độ các ô lân cận của ô (r,c) theo hướng direction.
        """
        dr, dc = DIR_OFFSETS[direction]
        neighbor_r, neighbor_c = r + dr, c + dc
        if self.wrap: # Nếu bật wrap -> cuốn biên theo %
            return (neighbor_r % self.rows, neighbor_c % self.cols)
        else:
            if 0 <= neighbor_r < self.rows and 0 <= neighbor_c < self.cols:
                return (neighbor_r, neighbor_c)
            return None
        
    def is_valid_cell_placement(self, r: int, c: int, current_index: int) -> bool:
        """
        Kiểm tra tính hợp lệ của ô (r, c) đối với các ô lân cận ĐÃ CỐ ĐỊNH trong quá trình tìm kiếm.
        Phải nối với vùng đã chốt + Ko chĩa ra ngoài biên nếu non wrap
        Dùng cho cắt tỉa nhánh (Pruning).
        """
        cur_cell = self.grid[r * self.cols + c]

        for d in DIRECTIONS:
            has_port = ((cur_cell & d) != 0)
            neighbor_cell = self.get_neighbor(r, c, d)

            if neighbor_cell is None: # Chế độ wrap -> Neighbor ko bao h None
                # Nếu chế độ non-wrap và chĩa ra ngoài biên chứ ko phải neighbor
                if has_port:
                    return False 
            else:
                nr, nc = neighbor_cell
                neighbor_index = nr * self.cols + nc
                if neighbor_index < current_index: # Nếu neighbor nằm trong vùng đã chốt
                    neighbor_mask = self.grid[neighbor_index]
                    neighbor_has_port = ((neighbor_mask & OPPOSITE[d]) != 0)
                    if has_port != neighbor_has_port: # phải nối với nhau
                        return False  

        return True

    # def count_open_ports(self) -> int:
    #     """
    #     Đếm số lượng cổng nối bị hở hoặc không khớp trên toàn map.
    #     Dùng cho Heuristic.
    #     """
    #     open_count = 0
    #     for r in range(self.rows):
    #         for c in range(self.cols):
    #             mask = self.grid[r * self.cols + c]
    #             for d in DIRECTIONS:
    #                 if (mask & d) != 0:
    #                     nb = self.get_neighbor(r, c, d)
    #                     if nb is None:
    #                         open_count += 1
    #                     else:
    #                         nr, nc = nb
    #                         if (self.grid[nr * self.cols + nc] & OPPOSITE[d]) == 0:
    #                             open_count += 1
    #     return open_count

    def is_goal(self) -> bool:
        """
        Kiểm tra trạng thái đích -> Toàn bộ ống phải tạo thành 1 Tree
        1. BFS duyệt toàn bộ các ống để kiểm tra tất cả các ống đều khớp với ống bên cạnh và tạo thành 1 thành phần liên thông duy nhất.
        2. Đường ống ko tạo chu trình (Check: E = V - 1).
        """
        if self.total_pipes == 0:
            return True
        if self.start_pipe is None:
            return False

        # 1. BFS
        visited = set()
        queue = deque([self.start_pipe]) 
        visited.add(self.start_pipe) 
        total_connections = 0

        while queue:
            curr_r, curr_c = queue.popleft()
            cur_pipe_mask = self.grid[curr_r * self.cols + curr_c]

            for dir in DIRECTIONS:
                if (cur_pipe_mask & dir) != 0:
                    total_connections += 1
                    nb = self.get_neighbor(curr_r, curr_c, dir)
                    if nb is None: 
                        return False

                    nr, nc = nb
                    if (self.grid[nr * self.cols + nc] & OPPOSITE[dir]) == 0: 
                        return False
                    
                    if (nr, nc) not in visited:
                        visited.add((nr,nc))
                        queue.append((nr,nc))

        if len(visited) != self.total_pipes:
            return False

        # 2
        if (total_connections // 2) != (self.total_pipes - 1):
            return False

        return True

    def clone(self):
        """Deepcopy bằng bytearray bỏ qua __init__"""
        new_state = PipeState.__new__(PipeState) # Bỏ qua constructor
        new_state.grid = bytearray(self.grid)    # Copy memory C-level
        new_state.rows = self.rows
        new_state.cols = self.cols
        new_state.wrap = self.wrap
        new_state.total_pipes = self.total_pipes
        new_state.start_pipe = self.start_pipe
        return new_state

