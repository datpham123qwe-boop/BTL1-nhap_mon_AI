from typing import List, Tuple, Dict

# Quy ước giá trị ô trên ma trận 2D:
#   -2 : Ô trắng 
#   -1 : Tường đen không có số 
# 0 -> 4 : Tường đen có số từ 0 đến 4 
WHITE = -2
WALL = -1

# 4 hướng di chuyển vuông góc: Lên, Xuống, Trái, Phải
DIRS = [(-1, 0), (1, 0), (0, -1), (0, 1)]

class AkariProblem:
    def __init__(self, grid: List[List[int]]):
        self.grid = [row[:] for row in grid] #deepcopy
        self.rows = len(grid)
        self.cols = len(grid[0]) if self.rows > 0 else 0

        self.white_coords: List[Tuple[int, int]] = []
        self.coord_to_id: Dict[Tuple[int, int], int] = {}
        
        self.num_white = 0
        self.all_white_mask = 0

        # Đếm ô trắng và tạo mask
        for r in range(self.rows):
            for c in range(self.cols):
                if grid[r][c] == WHITE:
                    u = len(self.white_coords) # ô trắng thứ u
                    self.white_coords.append((r,c))
                    self.coord_to_id[(r,c)] = u

        self.num_white = len(self.white_coords)
        self.all_white_mask = (1 << self.num_white) - 1 

        self.ray_mask: List[int] = [0] * self.num_white
        self.ray_len: List[int] = [0] * self.num_white
        self.max_ray_len = 1 # -> heuristic

        for u, (r, c) in enumerate(self.white_coords):
            mask = 1 << u
            for (dr, dc) in DIRS: # Quét 4 hướng xem chiếu tới đâu
                nr, nc = r + dr, c + dc
                while (0 <= nr < self.rows and 0 <= nc < self.cols) and self.grid[nr][nc] == WHITE:
                    v = self.coord_to_id[(nr, nc)]
                    mask |= (1 << v) # Các ô trắng có thể chiếu tới
                    nr, nc = nr + dr, nc + dc
            self.ray_mask[u] = mask
            count = mask.bit_count()
            self.ray_len[u] = count
            self.max_ray_len = max(self.max_ray_len,count)

        self.clues: List[Tuple[int, int, int]] = []          # Lưu (r, c, số_đèn_yêu_cầu)
        self.clue_adj_mask: List[int] = []                   # Bitmask các ô trắng kề tường c_idx
        self.clue_adj_cells: List[List[int]] = []            # Danh sách index ô trắng kề tường c_idx
        self.white_to_clues: List[List[int]] = [[] for _ in range(self.num_white)]

        for r in range(self.rows):
            for c in range(self.cols):
                if 0 <= grid[r][c] <= 4: # Quét tìm ô Đen
                    c_idx = len(self.clues) # index ô đen
                    self.clues.append((r,c,grid[r][c]))
                    adj_mask = 0 # mask các ô trắng kề
                    adj_list = [] # Danh sách idx ô trắng kề
                    for (dr, dc) in DIRS:
                        nr, nc = r + dr, c + dc
                        if (nr, nc) in self.coord_to_id: # Nếu là ô trắng
                            u = self.coord_to_id[(nr,nc)]
                            adj_mask |= 1 << u
                            adj_list.append(u)
                            self.white_to_clues[u].append(c_idx)   

                    self.clue_adj_mask.append(adj_mask)
                    self.clue_adj_cells.append(adj_list)

        self.num_clues = len(self.clues)

    def is_goal(self, bulbs_mask: int) -> bool:
        """
        @bulbs_mask: mask vị trí các bóng đèn trên ô trắng
        Kiểm tra trạng thái đích:
        1. Không có 2 bóng đèn nào chiếu vào nhau.
        2. Toàn bộ ô trắng đều được chiếu sáng.
        3. Mọi ô tường có số đều có đủ số bóng kề yêu cầu.
        """

        lit_mask = 0 # Đánh dấu ô đã được chiếu sáng
        # Không có 2 bóng đèn nào chiếu vào nhau
        for u in range(self.num_white): # Duyệt qua các ô trắng
            if ((bulbs_mask >> u) & 1) != 0: # Nếu ô đó chứa bóng đèn
                # Loại bỏ bit u khỏi ray_mask[u] bằng phép XOR, sau đó AND với bulbs_mask
                # Nếu != 0 -> trên đường chiếu của đèn u có ít nhất 1 bóng đèn khác
                other_bulbs_on_ray = self.ray_mask[u] ^ (1 << u)
                if (bulbs_mask & other_bulbs_on_ray) != 0:
                    return False

                lit_mask |= self.ray_mask[u] # Cập nhật các ô đã được chiếu sáng

        # Toàn bộ ô trắng phải được chiếu sáng.
        if lit_mask != self.all_white_mask:
            return False

        # Mọi ô đen có số đều có đủ số bóng yêu cầu
        for c_idx, (_, _, required) in enumerate(self.clues):
            bulbs_placed_around_clue = (bulbs_mask & self.clue_adj_mask[c_idx]).bit_count()
            if bulbs_placed_around_clue != required:
                return False

        return True
    def render(self, bulbs_mask: int = 0) -> str:
            """Hàm vẽ trực quan bàn cờ Akari ra Console."""
            lit_mask = 0
            for u in range(self.num_white):
                if (bulbs_mask >> u) & 1:
                    lit_mask |= self.ray_mask[u]

            lines = [f"┌{'───' * self.cols}┐"]
            for r in range(self.rows):
                row_str = "│"
                for c in range(self.cols):
                    val = self.grid[r][c]
                    if val == WALL:
                        row_str += " ██"
                    elif 0 <= val <= 4:
                        row_str += f" {val} "
                    else:
                        u = self.coord_to_id[(r, c)]
                        if (bulbs_mask >> u) & 1:
                            row_str += " 💡"
                        elif (lit_mask >> u) & 1:
                            row_str += " · "
                        else:
                            row_str += "   "
                row_str += "│"
                lines.append(row_str)
            lines.append(f"└{'───' * self.cols}┘")
            return "\n".join(lines)