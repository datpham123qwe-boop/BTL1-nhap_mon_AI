import unittest
import copy
import random
import time
from logic import PipeState
import logic
import blind_search
import heuristic_search
import sys

sys.setrecursionlimit(2000)

def generate_random_tree(rows, cols, wrap=False):
    """
    Sinh lưới ống nước.
    Nếu wrap=True, ống sẽ tự động quấn sang mép đối diện tạo thành bản đồ Torus hoàn hảo.
    """
    grid = [[0 for _ in range(cols)] for _ in range(rows)] 
    visited = set()
    
    DIR_MAP = {
        (-1, 0): logic.UP,    
        (0, 1): logic.RIGHT,  
        (1, 0): logic.DOWN,   
        (0, -1): logic.LEFT   
    }
    
    def dfs(r, c):
        visited.add((r, c))
        directions = [(-1, 0), (0, 1), (1, 0), (0, -1)]
        random.shuffle(directions) 
        
        for dr, dc in directions:
            if wrap:
                # Chế độ Xuyên biên (Modulo)
                nr, nc = (r + dr) % rows, (c + dc) % cols
                if (nr, nc) not in visited:
                    grid[r][c] |= DIR_MAP[(dr, dc)]         
                    grid[nr][nc] |= DIR_MAP[(-dr, -dc)]     
                    dfs(nr, nc)
            else:
                # Chế độ bình thường (Chặn tường)
                nr, nc = r + dr, c + dc
                if 0 <= nr < rows and 0 <= nc < cols and (nr, nc) not in visited:
                    grid[r][c] |= DIR_MAP[(dr, dc)]         
                    grid[nr][nc] |= DIR_MAP[(-dr, -dc)]     
                    dfs(nr, nc) 
                
    dfs(0, 0) 
    return grid

def scramble_grid(grid):
    rows, cols = len(grid), len(grid[0])
    scrambled = [[0]*cols for _ in range(rows)]
    for r in range(rows):
        for c in range(cols):
            mask = grid[r][c]
            rotations = random.randint(0, 3)
            for _ in range(rotations):
                mask = logic.rotate_90(mask) 
            scrambled[r][c] = mask
    return scrambled

class TestPipeAlgorithms(unittest.TestCase):
    
    def run_large_test(self, size, wrap=False):
        mode_str = "CÓ WRAP" if wrap else "KHÔNG WRAP"
        print(f"\n--- So sánh DFS và A* trên bảng {size}x{size} ({mode_str}) ---")
        
        # Sinh map phù hợp chính xác với chế độ Wrap tương ứng
        solved_grid = generate_random_tree(size, size, wrap=wrap)
        scrambled_grid = scramble_grid(solved_grid)
        
        # Chạy DFS
        state_dfs = PipeState(copy.deepcopy(scrambled_grid), wrap=wrap)
        start_time_dfs = time.time()
        result_dfs = blind_search.solve(state_dfs)
        elapsed_dfs = time.time() - start_time_dfs
        
        # Chạy A*
        state_astar = PipeState(copy.deepcopy(scrambled_grid), wrap=wrap)
        start_time_astar = time.time()
        result_astar = heuristic_search.solve(state_astar)
        elapsed_astar = time.time() - start_time_astar
        
        print(f"DFS (Duyệt mù): {elapsed_dfs:.4f} giây")
        print(f"A* (Heuristic): {elapsed_astar:.4f} giây")
        
        self.assertIsNotNone(result_dfs, "DFS thất bại!")
        self.assertIsNotNone(result_astar, "A* thất bại!")
        self.assertTrue(result_astar.is_goal(), "Nghiệm của A* bị sai!")

    # ==========================================
    # CÁC BÀI TEST CHUẨN (KHÔNG WRAP) - Tốc độ cực cao
    # ==========================================
    def test_10x10_no_wrap(self):
        self.run_large_test(10, wrap=False)

    def test_20x20_no_wrap(self):
        self.run_large_test(20, wrap=False)
        
    def test_30x30_no_wrap(self):
        self.run_large_test(30, wrap=False)

    def test_40x40_no_wrap(self):
        self.run_large_test(40, wrap=False)
    # ==========================================
    # CÁC BÀI TEST TORUS (CÓ WRAP) - Phức tạp cao
    # ==========================================
    # Lưu ý: Do đặc thù hoãn cắt tỉa (Deferred Pruning) của Wrap Mode
    # Hệ số phân nhánh rất lớn, chỉ nên test tối đa 15x15 để tránh tràn RAM
    def test_07x07_wrap(self):
        self.run_large_test(7, wrap=True)

    def test_10x10_wrap(self):
        self.run_large_test(10, wrap=True)
        
    def test_12x12_wrap(self):
        self.run_large_test(12, wrap=True)

    def test_15x15_wrap(self):
        self.run_large_test(15, wrap=True)
if __name__ == '__main__':
    unittest.main()
