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
    """Trả về danh sách các góc xoay duy nhất của một loại ống."""
    rotations = []
    curr = mask
    for _ in range(4):
        if curr not in rotations:
            rotations.append(curr)
        curr = rotate_90(curr)
    return rotations

class PipeState:
    def __init__(self, grid: List[List[int]], wrap: bool = False):
        self.rows = len(grid)
        self.cols = len(grid[0])
        self.grid = grid    # Ma trận int x int đại diện cho trạng thái hiện tại của trò chơi
        self.wrap = wrap    # Bật tắt chế độ chơi Pipe Wrap (Torus - cuốn biên)
        self.total_pipes = 0
        self.start_pipe = None # Tọa độ ô bắt đầu
        
        # Lấy tọa độ pipe đầu và đếm tổng số ô pipe
        for r in range(self.rows):
            for c in range(self.cols):
                cur_pipe_mask = self.grid[r][c]
                if cur_pipe_mask == 0: # Ko có ống
                    continue
                self.total_pipes += 1
                if self.start_pipe is None:
                    self.start_pipe = (r,c)

    def get_neighbor(self, r, c, direction):
        """
        Lấy tọa độ các ô lân cận của ô (r,c) theo hướng direction.
        Nếu wrap=True: cuốn biên theo modulo.
        Nếu wrap=False: trả về None nếu ra khỏi biên.
        """
        dr, dc = DIR_OFFSETS[direction]
        neighbor_r, neighbor_c = r + dr, c + dc
        if self.wrap: #Nếu chế độ wrap
            return (neighbor_r % self.rows, neighbor_c % self.cols)
        else:
            if 0 <= neighbor_r < self.rows and 0 <= neighbor_c < self.cols:
                return (neighbor_r, neighbor_c)
            return None
        
    def is_valid_cell_placement(self, r: int, c: int, fixed_cells: Set[Tuple[int, int]]) -> bool:
        """
        Kiểm tra tính hợp lệ của ô (r, c) đối với các ô lân cận ĐÃ CỐ ĐỊNH trong quá trình tìm kiếm.
        Dùng cho cắt tỉa nhánh (Pruning).
        """
        cur_cell = self.grid[r][c]

        for d in DIRECTIONS:
            has_port = ((cur_cell & d) != 0)
            neighbor_cell = self.get_neighbor(r, c, d)

            if neighbor_cell is None: # Chế độ wrap -> Neighbor ko bao h None
                # Chế độ non-wrap và chĩa ra ngoài biên chứ ko phải neighbor
                if has_port:
                    return False 
            else:
                nr, nc = neighbor_cell
                if (nr, nc) in fixed_cells:
                    # Ô neighbor này đã được cố định trước đó -> Kiểm tra tính khớp nối đối xứng
                    neighbor_mask = self.grid[nr][nc]
                    neighbor_has_port = ((neighbor_mask & OPPOSITE[d]) != 0)
                    if has_port != neighbor_has_port:
                        return False  # Cổng không khớp nhau

        return True

    def count_open_ports(self) -> int:
        """
        Đếm số lượng cổng nối bị hở hoặc không khớp trên toàn map.
        Dùng cho Heuristic.
        """
        open_count = 0
        for r in range(self.rows):
            for c in range(self.cols):
                mask = self.grid[r][c]
                for d in DIRECTIONS:
                    if (mask & d) != 0:
                        nb = self.get_neighbor(r, c, d)
                        if nb is None:
                            open_count += 1
                        else:
                            nr, nc = nb
                            if (self.grid[nr][nc] & OPPOSITE[d]) == 0:
                                open_count += 1
        return open_count

    def is_goal(self) -> bool:
        """
        Kiểm tra trạng thái đích -> Toàn bộ ống phải tạo thành 1 Tree
        1. BFS duyệt toàn bộ các ống để kiểm tra tất cả các ống đều khớp với ống bên cạnh
         và tạo thành 1 thành phần liên thông duy nhất.
        2. Đường ống ko tạo chu trình (Check: E = V - 1).
        """

        if self.total_pipes == 0:
            return True
        if self.start_pipe is None:
            return False

        visited = set()
        queue = deque([self.start_pipe]) # Chứa tọa độ (r,c)
        visited.add(self.start_pipe) # Chứa tọa độ (r,c) các pipe đã đi qua
        total_connections = 0

        # Kiểm tra liên thông + Không hở
        while queue:
            curr_r, curr_c = queue.popleft()
            cur_pipe_mask = self.grid[curr_r][curr_c]

            for dir in DIRECTIONS:
                if (cur_pipe_mask & dir) != 0:
                    total_connections += 1
                    nb = self.get_neighbor(curr_r, curr_c, dir)
                    if nb is None: # Ống chĩa vào hướng ko có neighbor
                        return False

                    nr, nc = nb
                    if (self.grid[nr][nc] & OPPOSITE[dir]) == 0: # neighbor ko có ống đón
                        return False
                    
                    if (nr, nc) not in visited:
                        visited.add((nr,nc))
                        queue.append((nr,nc))

        # Phải thăm được tất cả các pipe
        if len(visited) != self.total_pipes:
            return False

        # E != V - 1 -> đồ thị có chu trình -> Loại
        if (total_connections // 2) != (self.total_pipes - 1):
            return False

        return True

    # Utils
    def clone(self):
        """DeepCopy PipeState hiện tại"""
        new_grid = [row[:] for row in self.grid]
        new_state = PipeState(new_grid, self.wrap)
        new_state.total_pipes = self.total_pipes
        new_state.start_pipe = self.start_pipe
        return new_state

    def to_tuple(self) -> Tuple[Tuple[int, ...], ...]:
        """Chuyển thành tuple để dùng làm key trong tập set (đã duyệt)."""
        return tuple(tuple(row) for row in self.grid)
