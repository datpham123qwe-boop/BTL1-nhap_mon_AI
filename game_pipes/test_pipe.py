import unittest
import copy
import random
import time
from logic import PipeState
import logic
import blind_search
import sys

# Tăng giới hạn đệ quy của Python. 
# Mặc định Python giới hạn đệ quy khoảng 1000. Đối với bảng 10x10, thuật toán DFS có thể cần đi sâu 100 bước đệ quy liên tục.
# Nếu bảng lớn hơn nữa (VD: 35x35) thì sẽ vượt quá 1000 bước. Việc tăng giới hạn giúp tránh lỗi RecursionError.
sys.setrecursionlimit(3000)

def generate_random_tree(rows, cols):
    """
    Hàm sinh một mạng lưới ống nước hoàn chỉnh (đã giải xong) có kích thước rows x cols.
    Sử dụng thuật toán Randomized Depth-First Search (DFS ngẫu nhiên) để tạo ra một 
    Cây Khung (Spanning Tree) phủ kín toàn bộ bảng lưới mà không có vòng lặp (no loops).
    Đây là kỹ thuật kinh điển để tạo Mê cung (Maze generation).
    """
    grid = [[0 for _ in range(cols)] for _ in range(rows)] # Khởi tạo bảng rỗng
    visited = set()
    
    # Ánh xạ từ vector di chuyển (dr, dc) sang bitmask của ống nước
    DIR_MAP = {
        (-1, 0): logic.UP,    # Đi lên -> Mở cổng Bắc
        (0, 1): logic.RIGHT,  # Đi sang phải -> Mở cổng Đông
        (1, 0): logic.DOWN,   # Đi xuống -> Mở cổng Nam
        (0, -1): logic.LEFT   # Đi sang trái -> Mở cổng Tây
    }
    
    def dfs(r, c):
        visited.add((r, c))
        directions = [(-1, 0), (0, 1), (1, 0), (0, -1)]
        random.shuffle(directions) # Trộn ngẫu nhiên 4 hướng để tạo cây đi ngẫu nhiên
        
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            # Nếu láng giềng nằm trong bảng và chưa được thăm
            if 0 <= nr < rows and 0 <= nc < cols and (nr, nc) not in visited:
                # Nối ống giữa ô hiện tại (r,c) và ô láng giềng (nr, nc)
                grid[r][c] |= DIR_MAP[(dr, dc)]         # Mở cổng ở ô hiện tại chĩa ra
                grid[nr][nc] |= DIR_MAP[(-dr, -dc)]     # Mở cổng ở ô láng giềng để đón vào (ngược lại)
                
                dfs(nr, nc) # Tiếp tục đệ quy đi đào đường ống tiếp
                
    dfs(0, 0) # Bắt đầu sinh từ góc trên cùng bên trái
    return grid

def scramble_grid(grid):
    """
    Hàm xáo trộn bảng (Tạo đề bài).
    Nhận vào một bảng đã giải hoàn chỉnh (từ hàm generate_random_tree), 
    sau đó xoay mỗi ô ngẫu nhiên từ 0 đến 3 lần.
    """
    rows, cols = len(grid), len(grid[0])
    scrambled = [[0]*cols for _ in range(rows)]
    for r in range(rows):
        for c in range(cols):
            mask = grid[r][c]
            # Chọn số lần xoay ngẫu nhiên
            rotations = random.randint(0, 3)
            for _ in range(rotations):
                mask = logic.rotate_90(mask) # Xoay 90 độ
            scrambled[r][c] = mask
    return scrambled


class TestPipeDFS(unittest.TestCase):
    def test_2x2_tree(self):
        """Test cơ bản trên bảng 2x2 tĩnh (hard-coded) để kiểm tra tính đúng đắn cơ bản của DFS."""
        scrambled_grid = [[3, 1], [2, 0]]
        state = PipeState(scrambled_grid, wrap=False)
        result = blind_search.solve(state)
        self.assertIsNotNone(result, "Lỗi: Không tìm thấy lời giải cho map 2x2")
        self.assertTrue(result.is_goal(), "Lỗi: Nghiệm trả về không hợp lệ")

    def test_3x3_tree(self):
        """Test nâng cao trên bảng 3x3 tĩnh để kiểm tra khả năng cắt tỉa (Pruning) ở cấu trúc phức tạp hơn."""
        scrambled_grid = [[3, 2, 1], [10, 0, 10], [12, 5, 3]]
        state = PipeState(scrambled_grid, wrap=False)
        result = blind_search.solve(state)
        self.assertIsNotNone(result)
        self.assertTrue(result.is_goal())

    def run_large_test(self, size):
        """
        Hàm helper (hỗ trợ) để chạy test tự động sinh trên các kích thước lớn.
        Đồng thời đo đạc thời gian chạy (Benchmark).
        """
        print(f"\n--- Chạy DFS trên bảng {size}x{size} ---")
        
        # 1. Sinh map hợp lệ ngẫu nhiên (Mê cung ống nước)
        solved_grid = generate_random_tree(size, size)
        
        # 2. Xáo trộn map để làm đề bài cho AI
        scrambled_grid = scramble_grid(solved_grid)
        
        # 3. Khởi tạo State và Bắt đầu tính giờ
        state = PipeState(scrambled_grid, wrap=False)
        start_time = time.time()
        
        # 4. Gọi thuật toán tìm kiếm (DFS)
        result = blind_search.solve(state)
        
        # 5. Chốt thời gian và in kết quả ra Terminal
        elapsed = time.time() - start_time
        print(f"Thời gian giải {size}x{size}: {elapsed:.4f} giây")
        
        # 6. Kiểm tra (Assert) kết quả có tồn tại và phải thỏa mãn đúng luật của Game (.is_goal)
        self.assertIsNotNone(result, f"Không thể giải được {size}x{size}")
        self.assertTrue(result.is_goal(), f"Nghiệm tìm được cho {size}x{size} không hợp lệ")


    def test_5x5_random(self):
        """Đánh giá hiệu năng DFS trên bảng ngẫu nhiên 5x5."""
        self.run_large_test(5)

    def test_7x7_random(self):
        """Đánh giá hiệu năng DFS trên bảng ngẫu nhiên 7x7."""
        self.run_large_test(7)

    def test_10x10_random(self):
        """Đánh giá hiệu năng DFS trên bảng ngẫu nhiên 10x10."""
        self.run_large_test(10)

    def test_15x15_random(self):
        self.run_large_test(15)
    def test_20x20_random(self):
        self.run_large_test(20)
    def test_30x30_random(self):
        self.run_large_test(30)
    def test_40x40_random(self):
        self.run_large_test(40)
    def test_45x45_random(self):
        self.run_large_test(45)

if __name__ == '__main__':
    unittest.main()
