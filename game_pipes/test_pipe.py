import unittest
import copy
import random
import time
from logic import PipeState
import logic
import blind_search
import heuristic_search  # Import thêm module A*
import sys

# Tăng giới hạn đệ quy của Python. 
sys.setrecursionlimit(2000)

def generate_random_tree(rows, cols):
    """Sinh một lưới ống nước liên thông ngẫu nhiên."""
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
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and (nr, nc) not in visited:
                grid[r][c] |= DIR_MAP[(dr, dc)]         
                grid[nr][nc] |= DIR_MAP[(-dr, -dc)]     
                dfs(nr, nc) 
                
    dfs(0, 0) 
    return grid

def scramble_grid(grid):
    """Xáo trộn bảng bằng cách xoay ngẫu nhiên các ô."""
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
    
    def test_2x2_tree(self):
        """Test cơ bản trên bảng tĩnh 2x2 cho cả DFS và A*."""
        scrambled_grid = [[3, 1], [2, 0]]
        
        # Test DFS
        state_dfs = PipeState(copy.deepcopy(scrambled_grid), wrap=True)
        res_dfs = blind_search.solve(state_dfs)
        self.assertIsNotNone(res_dfs, "DFS không giải được 2x2")
        self.assertTrue(res_dfs.is_goal(), "Nghiệm DFS không hợp lệ")

        # Test A*
        state_astar = PipeState(copy.deepcopy(scrambled_grid), wrap=True)
        res_astar = heuristic_search.solve(state_astar)
        self.assertIsNotNone(res_astar, "A* không giải được 2x2")
        self.assertTrue(res_astar.is_goal(), "Nghiệm A* không hợp lệ")

    def run_large_test(self, size):
        """Hàm so sánh trực tiếp tốc độ giữa DFS và A* trên cùng 1 bảng."""
        print(f"\n--- So sánh DFS và A* trên bảng {size}x{size} ---")
        solved_grid = generate_random_tree(size, size)
        scrambled_grid = scramble_grid(solved_grid)
        
        # Chạy DFS
        state_dfs = PipeState(copy.deepcopy(scrambled_grid), wrap=False)
        start_time_dfs = time.time()
        result_dfs = blind_search.solve(state_dfs)
        elapsed_dfs = time.time() - start_time_dfs
        
        # Chạy A*
        state_astar = PipeState(copy.deepcopy(scrambled_grid), wrap=False)
        start_time_astar = time.time()
        result_astar = heuristic_search.solve(state_astar)
        elapsed_astar = time.time() - start_time_astar
        
        # In kết quả Benchmark
        print(f"DFS (Duyệt mù): {elapsed_dfs:.4f} giây")
        print(f"A* (Heuristic): {elapsed_astar:.4f} giây")
        
        self.assertIsNotNone(result_dfs, "DFS thất bại!")
        self.assertIsNotNone(result_astar, "A* thất bại!")
        self.assertTrue(result_astar.is_goal(), "Nghiệm tìm được của A* bị sai luật!")

    def test_5x5_random(self):
        self.run_large_test(5)

    def test_7x7_random(self):
        self.run_large_test(7)

    def test_10x10_random(self):
        self.run_large_test(10)

    def test_30x30_random(self):
        self.run_large_test(30)

    def test_40x40_random(self):
        self.run_large_test(40)

if __name__ == '__main__':
    unittest.main()
