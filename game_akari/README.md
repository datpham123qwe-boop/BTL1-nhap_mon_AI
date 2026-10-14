# Bài toán Akari (Light Up) — Giải thuật Tìm kiếm AI

Tài liệu này mô tả chi tiết kiến trúc mã nguồn, danh sách các thuộc tính, phương thức và logic thuật toán cho bài toán **Akari (Light Up)** (thuộc hệ sinh thái Logic Puzzles trên `puzzle-pipes.com`) sử dụng ngôn ngữ **Python 3**[cite: 6]. Hệ thống bao gồm mô hình hóa không gian trạng thái bằng Bitmask, giải thuật Tìm kiếm mù (**DFS Backtracking**), giải thuật Tìm kiếm Heuristic (**A* kết hợp MRV & Constraint Propagation**) và bộ công cụ đo lường thời gian/bộ nhớ tự động[cite: 6].

---

## 1. Cấu trúc Thư mục

```text
game_akari/
├── logic.py             # Định nghĩa lớp AkariProblem, tiền xử lý Bitmask và kiểm tra Goal
├── blind_search.py      # Giải thuật Tìm kiếm mù theo chiều sâu (DFS Backtracking)
├── heuristic_search.py  # Giải thuật Tìm kiếm Heuristic (A* + MRV + Lan truyền ràng buộc)
├── test_akari.py        # Bộ sinh bản đồ có nghiệm và Benchmark đo Thời gian & Bộ nhớ (Mẫu)
└── README.md            # Tài liệu đặc tả kiến trúc, thuộc tính và phương thức
```

---

## 2. Module `logic.py` — Mô hình hóa Không gian Trạng thái

Module này chịu trách nhiệm chuyển đổi lưới bản đồ 2D sang hệ thống mặt nạ bit trên số nguyên lớn (`int` bitmask), giúp các thao tác bật đèn, phóng tia sáng và kiểm tra ràng buộc đạt độ phức tạp O(1).

### 2.1. Các hằng số quy ước
* `WHITE = -2`: Ô trắng (cho phép đặt bóng đèn và truyền tia sáng).
* `WALL = -1`: Tường đen không có số (chặn tia sáng, không có ràng buộc số đèn kề).
* `0 .. 4`: Tường đen có số gợi ý (chặn tia sáng, quy định chính xác số lượng bóng đèn ở 4 ô kề cạnh vuông góc).
* `DIRS = [(-1, 0), (1, 0), (0, -1), (0, 1)]`: 4 vector hướng vuông góc (Lên, Xuống, Trái, Phải).

### 2.2. Lớp `AkariProblem`

#### Bảng Thuộc tính (Attributes)

| Tên thuộc tính | Kiểu dữ liệu | Mô tả chi tiết |
| :--- | :--- | :--- |
| `grid` | `List[List[int]]` | Ma trận 2D kích thước `rows x cols` lưu bản đồ gốc. |
| `rows`, `cols` | `int` | Số hàng và số cột của bản đồ. |
| `white_coords` | `List[Tuple[int, int]]` | Danh sách tọa độ `(r, c)` của từng ô trắng theo thứ tự chỉ mục bit `u` từ `0` đến `W - 1`. |
| `coord_to_id` | `Dict[Tuple[int, int], int]` | Từ điển ánh xạ ngược từ tọa độ `(r, c)` của ô trắng sang chỉ mục bit `u`. |
| `num_white` | `int` | Tổng số ô trắng trên bản đồ (`W`). |
| `all_white_mask` | `int` | Mặt nạ bit chứa `W` bit `1` liên tiếp: `(1 << num_white) - 1`. Đại diện cho trạng thái 100% ô trắng đã sáng. |
| `ray_mask` | `List[int]` | `ray_mask[u]` lưu bitmask của toàn bộ các ô trắng được chiếu sáng (cùng hàng và cột trước khi chạm tường) khi đặt đèn tại ô `u`. |
| `ray_len` | `List[int]` | `ray_len[u]` lưu tổng số ô trắng được chiếu sáng bởi một đèn đặt tại `u` (`ray_mask[u].bit_count()`). |
| `max_ray_len` | `int` | Số lượng ô trắng tối đa mà một bóng đèn đơn lẻ có thể chiếu sáng trên bản đồ. Dùng để tính cận dưới Heuristic. |
| `clues` | `List[Tuple[int, int, int]]` | Danh sách các bức tường có số dưới dạng `(r, c, required_bulbs)`. |
| `num_clues` | `int` | Tổng số bức tường có số gợi ý trên bản đồ. |
| `clue_adj_mask` | `List[int]` | `clue_adj_mask[c_idx]` lưu bitmask các ô trắng nằm kề 4 hướng của bức tường có số thứ `c_idx`. |
| `clue_adj_cells` | `List[List[int]]` | `clue_adj_cells[c_idx]` lưu danh sách các chỉ mục ô trắng `u` nằm kề bức tường `c_idx`. |
| `white_to_clues` | `List[List[int]]` | `white_to_clues[u]` lưu danh sách chỉ mục `c_idx` của các bức tường có số nằm kề với ô trắng `u`. |

#### Các Phương thức (Methods) & Logic xử lý

* **`__init__(self, grid: List[List[int]])`**
  * **Bước 1 (Đánh chỉ mục):** Quét lưới từ trái sang phải, từ trên xuống dưới để gán mỗi ô `WHITE` một chỉ mục `u` và khởi tạo `all_white_mask`.
  * **Bước 2 (Tiền xử lý tia sáng):** Từ mỗi ô trắng `u`, bắn tia theo 4 hướng trong `DIRS` cho đến khi ra ngoài biên hoặc gặp tường (`!= WHITE`). Gom tất cả các ô trắng đi qua vào `ray_mask[u]` bằng phép toán `mask |= (1 << v)`.
  * **Bước 3 (Liên kết tường có số):** Với mỗi ô có giá trị `0..4`, kiểm tra 4 ô kề cạnh để lập mặt nạ `clue_adj_mask` và đồ thị hai phía giữa ô trắng `u` và tường `c_idx` (`white_to_clues`).
* **`is_goal(self, bulbs_mask: int) -> bool`**
  * Kiểm tra tính hợp lệ toàn cục của một cấu hình đặt đèn `bulbs_mask`:
    1. **Không chiếu nhau:** Với mọi bit `u` đang bật trong `bulbs_mask`, kiểm tra `(bulbs_mask & (self.ray_mask[u] ^ (1 << u))) == 0`.
    2. **Phủ sáng 100%:** Hợp (`|`) tất cả `ray_mask[u]` của các đèn đã đặt phải bằng `self.all_white_mask`.
    3. **Đủ số lượng quanh tường:** Với mọi tường `c_idx`, số bit `1` của phép giao `(bulbs_mask & self.clue_adj_mask[c_idx]).bit_count()` phải bằng đúng `required`.
* **`render(self, bulbs_mask: int = 0) -> str`**
  * Trực quan hóa trạng thái bàn cờ ra Console bằng ký tự Unicode (`██` cho tường đen, `0..4` cho tường có số, `💡` cho bóng đèn, và `·` cho tia sáng) phục vụ tính năng hiển thị trực quan[cite: 6].

---

## 3. Module `blind_search.py` — Giải thuật Tìm kiếm mù (DFS)

Module này hiện thực giải thuật **Tìm kiếm theo chiều sâu (Depth-First Search - DFS Backtracking)** sử dụng cấu trúc ngăn xếp LIFO (`stack`)[cite: 6].

### 3.1. Cấu trúc Trạng thái trong Stack
Mỗi phần tử trong `stack` là một tuple 4 thành phần:
```python
(u: int, bulbs_mask: int, lit_mask: int, rem_clues: Tuple[int, ...])
```
* `u`: Chỉ mục của ô trắng hiện tại đang được xét (`0 <= u <= W`).
* `bulbs_mask`: Bitmask các ô trắng đã được đặt bóng đèn (từ `0` đến `u - 1`).
* `lit_mask`: Bitmask các ô trắng hiện đã được chiếu sáng.
* `rem_clues`: Tuple lưu số lượng bóng đèn **còn thiếu** của từng bức tường có số.

### 3.2. Các Hàm & Logic Cắt tỉa (Pruning)

* **`solve_dfs(problem: lg.AkariProblem) -> Tuple[Optional[int], int]`**
  * **Tiền xử lý `suffix_mask`:** Khởi tạo mảng `suffix_mask[i]` chứa bitmask của các ô trắng từ chỉ mục `i` đến `num_white - 1`. Giúp đếm trong O(1) số lượng ô trắng **chưa xét tới** xung quanh bức tường `c_idx` bằng công thức:
    ```python
    rem_adj = (problem.clue_adj_mask[c_idx] & suffix_mask[u + 1]).bit_count()
    ```
  * **Điều kiện dừng (`u == num_white`):** Kiểm tra `lit_mask == problem.all_white_mask` và toàn bộ phần tử trong `rem_clues` bằng `0`. Nếu thỏa mãn, trả về `(bulbs_mask, nodes_explored)`.
  * **Logic rẽ nhánh 1 — Bỏ trống ô `u` (`can_leave_empty`):**
    * Kiểm tra các tường `c_idx` kề với `u`. Nếu `rem_clues[c_idx] > rem_adj` (số đèn còn cần lớn hơn số ô trống chưa xét còn lại quanh tường đó) -> **Cắt tỉa thiếu hụt (Clue Deficit Pruning)**.
  * **Logic rẽ nhánh 2 — Đặt đèn tại ô `u` (`can_place_bulb`):**
    * **Kiểm tra chiếu sáng trùng:** Ô `u` phải chưa bị đèn khác chiếu sáng (`not ((lit_mask >> u) & 1)`).
    * **Cắt tỉa vượt ngưỡng (Clue Overflow Pruning):** Với mọi tường `c_idx` kề với `u`, nếu `rem_clues[c_idx] == 0` (tường đã đủ đèn) thì không được phép đặt thêm. Nếu hợp lệ, giảm `rem_clues[c_idx]` đi `1` và đẩy trạng thái `(u + 1, bulbs_mask | (1 << u), lit_mask | ray_mask[u], new_clues)` vào `stack`.
* **`solve(problem: lg.AkariProblem) -> Optional[int]`**
  * Hàm wrapper gọi `solve_dfs(problem)` và trả về nghiệm `bulbs_mask`.

---

## 4. Module `heuristic_search.py` — Giải thuật Tìm kiếm Heuristic (A*)

Module này hiện thực giải thuật tìm kiếm có thông tin **A* (Best-First Search)** trên hàng đợi ưu tiên (`heapq`), kết hợp cơ chế **Lan truyền ràng buộc cục bộ (`fast_propagate`)** và chiến lược chọn biến động **MRV (`pick_next_decision`)**[cite: 6].

### 4.1. Lớp `AStarNode`

Sử dụng `__slots__` để tối ưu hóa cấp phát bộ nhớ cho từng node trong hàng đợi ưu tiên `open_set`.

#### Bảng Thuộc tính (Attributes)

| Tên thuộc tính | Kiểu dữ liệu | Mô tả chi tiết |
| :--- | :--- | :--- |
| `bulbs_mask` | `int` | Bitmask các ô trắng đã đặt bóng đèn. |
| `lit_mask` | `int` | Bitmask các ô trắng đã được chiếu sáng. |
| `forbidden_mask` | `int` | Bitmask các ô trắng **bị cấm đặt đèn** (do đã bị chiếu sáng, do nằm kề tường đã đủ đèn, hoặc do nhánh quyết định không đặt đèn). |
| `rem_clues` | `Tuple[int, ...]` | Số lượng bóng đèn còn thiếu quanh mỗi bức tường có số. |
| `f_score` | `float` | Điểm đánh giá Heuristic tổng hợp dùng để sắp xếp trong Min-Heap (`heapq`). |
| `unlit_cnt` | `int` | Số lượng ô trắng hiện chưa được chiếu sáng. |

#### Phương thức của `AStarNode`
* **`__lt__(self, other: "AStarNode") -> bool`:** Định nghĩa toán tử `<` cho `heapq`, ưu tiên mở rộng node có `f_score` nhỏ hơn (nếu bằng nhau thì ưu tiên `unlit_cnt` nhỏ hơn).

### 4.2. Các Hàm & Logic Giải thuật trong `heuristic_search.py`

* **`fast_propagate(problem, bulbs_mask, lit_mask, forbidden_mask, rem_clues)`**
  * Thực hiện vòng lặp suy diễn tất định trên các bức tường có số cho đến khi đạt trạng thái cân bằng:
    1. Tính mặt nạ các ô trắng kề tường `c_idx` còn có thể đặt đèn: `avail_mask = clue_adj_mask[c_idx] & ~forbidden_mask` và `avail_cnt = avail_mask.bit_count()`.
    2. **Phát hiện nhánh cụt:** Nếu `need < 0` hoặc `avail_cnt < need` (không còn đủ ô hợp lệ để đặt đủ đèn cho tường), trả về `None` để cắt bỏ nhánh ngay lập tức.
    3. **Quy tắc Tường bão hòa (`need == 0`):** Khóa toàn bộ các ô kề còn lại bằng lệnh `forbidden_mask |= avail_mask`.
    4. **Quy tắc Tường bắt buộc (`avail_cnt == need`):** Bắt buộc đặt bóng đèn vào tất cả các ô trong `avail_mask`, cập nhật `bulbs_mask`, phóng tia sáng vào `lit_mask` cùng `forbidden_mask`, và trừ `rem_clues` của các tường liên đới.
* **`pick_next_decision(problem, lit_mask, forbidden_mask, rem_clues) -> Tuple[int, int]`**
  * Thay vì chọn ô tuần tự như DFS, hàm áp dụng chiến lược **Minimum Remaining Values (MRV)** và trả về `(branch_u, status)`:
    1. **Ưu tiên 1 (Ràng buộc tường):** Nếu còn bức tường `c_idx` có `rem_clues[c_idx] > 0`, chọn ngay một ô trắng hợp lệ kề tường đó và trả về `(u, 2)` (cần phân nhánh).
    2. **Ưu tiên 2 (Ô tối bó hẹp nhất & Đơn trị):** Duyệt qua các ô trắng chưa sáng (`unlit_mask = all_white_mask ^ lit_mask`). Với mỗi ô tối `u`, tập các vị trí có thể đặt đèn để chiếu sáng `u` là `options = ray_mask[u] & ~forbidden_mask`:
       * Nếu `options == 0`: Ô `u` bị cô lập hoàn toàn, không thể được chiếu sáng -> Trả về `(-1, 0)` (**Nhánh cụt**).
       * Nếu `options.bit_count() == 1`: Chỉ còn duy nhất 1 vị trí `v` cứu sáng được `u` -> Trả về `(v, 1)` (**Ô bắt buộc / Unit Clause**).
       * Nếu `options.bit_count() > 1`: Tìm ô tối có ít vị trí cứu sáng nhất (`cnt` nhỏ nhất), sau đó chọn ứng viên `v` trong `options` chiếu sáng được nhiều ô tối khác nhất (`max_gain`) và trả về `(v, 2)`.
* **`compute_f_score(problem, lit_mask, rem_clues) -> Tuple[float, int]`**
  * Tính điểm đánh giá Heuristic dựa trên cận dưới số đèn cần để phủ sáng vùng tối và tổng số đèn còn thiếu ở các bức tường:
    ```python
    unlit_cnt = (problem.all_white_mask ^ lit_mask).bit_count()
    f_score = (unlit_cnt / problem.max_ray_len) + 2.0 * sum(rem_clues)
    ```
* **`solve_astar(problem: lg.AkariProblem) -> Tuple[Optional[int], int]`**
  * Khởi chạy `fast_propagate` tại trạng thái gốc và đưa vào hàng đợi ưu tiên `open_set`.
  * Khi rút một `node` khỏi `open_set`, chạy vòng lặp trượt (**Unit Propagation**): nếu `pick_next_decision` trả về `status == 1`, đặt đèn trực tiếp và gọi `fast_propagate` liên tục mà không cần tạo `AStarNode` mới.
  * Khi gặp `status == 2` tại ô `branch_u`, tách thành 2 nhánh con độc lập đẩy vào `open_set`:
    * **Nhánh 1:** Đặt bóng đèn tại `branch_u` (`bulbs_mask | (1 << branch_u)`).
    * **Nhánh 2:** Cấm đặt bóng đèn tại `branch_u` (`forbidden_mask | (1 << branch_u)`).

---

## 5. Module `test_akari.py` — Sinh Bản đồ & Đo lường Hiệu năng

Module này cung cấp bộ dữ liệu kiểm thử tự động và thu thập bảng số liệu về thời gian thực thi cùng mức tiêu tốn bộ nhớ phục vụ báo cáo[cite: 6].

* **`generate_solvable_akari(rows: int, cols: int, seed: int) -> List[List[int]]`**
  * Tạo các bức tường đen đối xứng tâm trên lưới `rows x cols`.
  * Tìm một **Tập độc lập cực đại (Maximal Independent Set)** trên đồ thị tầm nhìn của các ô trắng để làm cấu hình bóng đèn nghiệm ẩn (đảm bảo 100% ô trắng đều sáng và không có 2 đèn nào chiếu nhau).
  * Đếm số đèn trong nghiệm ẩn quanh các bức tường để gán con số gợi ý `0..4`, từ đó cam kết mọi bản đồ sinh ra đều **100% có nghiệm hợp lệ**.
* **`measure_solver(solver_func, problem: AkariProblem)`**
  * Sử dụng `time.perf_counter()` để đo thời gian thực thi chính xác tới phần nghìn mili-giây (`ms`).
  * Sử dụng thư viện chuẩn `tracemalloc` (`tracemalloc.get_traced_memory()`) để ghi nhận đỉnh bộ nhớ cấp phát (`Peak Memory` tính theo `KB`) của từng giải thuật[cite: 6].
* **`TestAkariBenchmark(unittest.TestCase)`**
  * Chạy kiểm thử tự động từ kích thước nhỏ (`6x6`) đến phức tạp (`14x14`), đối chiếu tính đúng đắn qua `problem.is_goal(sol)` và in bảng so sánh trực tiếp ra màn hình.

---

## 6. Hướng dẫn Chạy Chương trình

Yêu cầu môi trường: **Python 3.10+** (hỗ trợ sẵn phương thức `int.bit_count()` ở cấp độ C, không cần cài đặt thêm thư viện ngoài)[cite: 6].

Chạy trực tiếp bộ kiểm thử và đo lường Benchmark từ thư mục gốc của dự án:

```bash
py .\game_akari\test_akari.py
```

Hoặc sử dụng độc lập từng giải thuật trong mã nguồn Python:

```python
import logic as lg
import blind_search
import heuristic_search

# Khởi tạo bản đồ 3x3 (-2: Ô trắng, -1: Tường không số, 0..4: Tường có số)
grid = [
    [-2,  2, -2],
    [-2, -2, -1],
    [-2, -2, -2]
]

problem = lg.AkariProblem(grid)

# 1. Giải bằng DFS (Blind Search)
dfs_mask, dfs_nodes = blind_search.solve_dfs(problem)
print(f"DFS duyệt {dfs_nodes} nodes:")
print(problem.render(dfs_mask))

# 2. Giải bằng A* (Heuristic Search)
astar_mask, astar_nodes = heuristic_search.solve_astar(problem)
print(f"A* duyệt {astar_nodes} nodes:")
print(problem.render(astar_mask))
```