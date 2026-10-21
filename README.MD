# BÀI TẬP LỚN 1: TÌM KIẾM TRONG KHÔNG GIAN TRẠNG THÁI
### MÔN HỌC: TRÍ TUỆ NHÂN TẠO (ARTIFICIAL INTELLIGENCE)
**Trường Đại học Bách Khoa — ĐHQG-HCM**  
**Khoa Khoa học và Kỹ thuật Máy tính**

---

## 📌 1. Giới thiệu Tổng quan

Dự án này hiện thực các giải thuật tìm kiếm cơ bản (**Blind Search**) và nâng cao (**Heuristic Search**) trong môn Trí tuệ Nhân tạo để tự động giải quyết **2 bài toán Logic Puzzles** thuộc hệ sinh thái `puzzle-pipes.com`:

1. **Bài toán 1: Akari (Light Up)** — từ [puzzle-light-up.com](https://www.puzzle-light-up.com/)
2. **Bài toán 2: Tents and Trees (Cắm lều)** — từ [puzzle-tents.com](https://www.puzzle-tents.com/)

Hệ thống được phát triển 100% bằng ngôn ngữ **Python 3**, sử dụng mô hình hóa cấu trúc dữ liệu tối ưu (**Bitmask Acceleration** và **Constraint Satisfaction Problem - CSP**), đảm bảo khả năng mở rộng không gian tìm kiếm, cắt tỉa nhánh cụt sớm và đo lường chi tiết hiệu năng phục vụ báo cáo khoa học.

---

## 📁 2. Cấu trúc Thư mục Dự án

```text
/
├── game_akari/              # Module hoàn chỉnh cho bài toán Akari (Light Up)
│   ├── logic.py             # Mô hình hóa Bitmask O(1), tiền xử lý tia sáng, kiểm tra Goal
│   ├── blind_search.py      # Giải thuật DFS Backtracking trên cây nhị phân quyết định
│   ├── heuristic_search.py  # Constructive A* kết hợp Lan truyền ràng buộc & MRV
│   └── README.md            # Đặc tả kỹ thuật chi tiết cấu trúc thuộc tính & phương thức của Akari
│
├── game_tent/               # Module hoàn chỉnh cho bài toán Tents and Trees (Cắm lều)
│   ├── logic.py             # Định nghĩa TentsAndTreeState, ràng buộc 8 hướng & dung lượng hàng/cột
│   ├── blind_search.py      # DFS Backtracking đệ quy In-place
│   └── heuristic_search.py  # A* Search với bộ lọc Lookahead Forward Checking (is_feasible)
│
├── main.py                  # Entry point chạy thử nghiệm và so sánh tự động cho Tents and Trees
└── README.md                # Tài liệu tổng thể kiến trúc, giải thuật và hướng dẫn sử dụng
```

---

## 💡 3. Chi tiết Bài toán 1: Akari (Light Up)

### 3.1. Luật chơi
* Cho bảng $R \times C$ gồm các ô trắng và ô đen (tường).
* Đặt các bóng đèn vào ô trắng sao cho:
  1. **Toàn bộ ô trắng đều được chiếu sáng:** Tia sáng lan truyền 4 hướng vuông góc cho đến khi gặp tường đen hoặc mép bảng.
  2. **Không có 2 bóng đèn nào chiếu thẳng vào nhau.**
  3. **Thỏa mãn tường số:** Bức tường có ghi số $k \in \{0, 1, 2, 3, 4\}$ phải có chính xác đúng $k$ bóng đèn ở các ô kề cạnh vuông góc.

### 3.2. Mô hình hóa Bitmask ([`game_akari/logic.py`](game_akari/logic.py))
* Đánh chỉ mục $N$ ô trắng thành các số nguyên $u \in [0, N - 1]$.
* Toàn bộ trạng thái bàn cờ được quy về các phép toán bitwise trên số nguyên lớn (`int`):
  * `bulbs_mask`: Bitmask đại diện cho vị trí đặt đèn (bit thứ $u = 1$ nghĩa là có đèn tại $u$).
  * `ray_mask[u]`: Mảng tiền tính toán mặt nạ các ô trắng được chiếu sáng bởi đèn tại $u$.
  * Kiểm tra 2 đèn chiếu nhau đạt độ phức tạp $O(1)$: `bulbs_mask & (ray_mask[u] ^ (1 << u)) != 0`.
  * Vùng chiếu sáng tích lũy: `lit_mask |= ray_mask[u]`.
  * Kiểm tra hoàn thành bàn cờ: `lit_mask == all_white_mask`.

### 3.3. Giải thuật Tìm kiếm Mù ([`game_akari/blind_search.py`](game_akari/blind_search.py))
* **Chiến lược:** DFS Backtracking lặp trên Ngăn xếp LIFO (`stack`) duyệt tuần tự các ô từ $0 \to N - 1$.
* **Cây nhị phân:** Tại mỗi ô $u$, sinh tối đa 2 nhánh:
  1. *Nhánh bỏ trống:* Giữ nguyên trạng thái và bước tiếp sang $u + 1$.
  2. *Nhánh đặt đèn:* Bật bit thứ $u$, cập nhật `lit_mask | ray_mask[u]`, giảm số đèn cần của các tường kề.
* **Cắt tỉa nhìn trước (Lookahead Pruning):**
  * Tận dụng `suffix_mask` để đếm số ô trống phía sau trong $O(1)$:
    * Nếu bỏ qua ô $u$ mà số ô trống còn lại quanh tường $< \text{rem\_clues}$ $\implies$ **Cắt tỉa thiếu đèn (Deficit Pruning)**.
    * Nếu đặt đèn mà ô $u$ đã bị đèn khác chiếu hoặc làm tường kề vượt số lượng ($\le 0$) $\implies$ **Cắt tỉa thừa đèn (Overflow Pruning)**.

### 3.4. Giải thuật Tìm kiếm Heuristic ([`game_akari/heuristic_search.py`](game_akari/heuristic_search.py))
A* trong Akari là sự kết hợp giữa **Heuristic Search + Lan truyền ràng buộc (Constraint Propagation) + MRV**:
1. **Lan truyền ràng buộc (`fast_propagate`):**
   * Tự động khóa các ô kề tường đã đủ đèn (`need == 0`).
   * Tự động cắm đèn vào các ô kề tường khi số ô khả dụng bằng số đèn cần (`need == avail`).
   * Cắt tỉa ngay nhánh cụt khi `need < 0` hoặc `avail < need`.
2. **Chọn biến rẽ nhánh MRV (`pick_next_decision`):**
   * Ưu tiên giải quyết các bức tường còn thiếu đèn trước (vùng ràng buộc chặt nhất).
   * Tìm ô tối có ít phương án chiếu sáng nhất (MRV), trong các phương án đó chọn ô có độ phủ sáng rộng nhất (`max gain`).
3. **Cơ chế trượt tự động (Unit Propagation Slide):**
   * Tự động điền chuỗi các ô bắt buộc duy nhất mà không cần tạo nhánh đẩy vào Priority Queue, giảm thiểu tối đa overhead của Min-Heap.
4. **Hàm đánh giá Heuristic $f(n)$ (`compute_f_score`):**
   $$f(n) = \frac{\text{unlit\_cnt}}{\text{max\_ray\_len}} + 2 \times \sum \text{rem\_clues}$$
   * $\frac{\text{unlit\_cnt}}{\text{max\_ray\_len}}$ là cận dưới toán học của bài toán Che phủ tập hợp (Set Cover).

---

## ⛺ 4. Chi tiết Bài toán 2: Tents and Trees (Cắm lều)

### 4.1. Luật chơi
* Cho bàn cờ kích thước $R \times C$ chứa các ô cỏ và các ô có cây ($T$).
* Cắm các chiếc lều ($A$) sao cho:
  1. **Ghép cặp 1 - 1:** Mỗi cây gắn liền với đúng 1 chiếc lều ở 4 hướng trực giao (Lên, Xuống, Trái, Phải).
  2. **Quy tắc không chạm nhau:** Hai chiếc lều không được chạm nhau ở bất kỳ ô nào trong 8 hướng lân cận (kể cả 4 đường chéo).
  3. **Chỉ tiêu biên:** Số lượng lều trên mỗi hàng $r$ và cột $c$ phải bằng chính xác con số ghi ở ngoài rìa (`row_limits[r]` và `col_limits[c]`).

### 4.2. Mô hình hóa Trạng thái ([`game_tent/logic.py`](game_tent/logic.py))
* `TentsAndTreeState` quản lý ma trận lưới `grid` với các hằng số: `EMPTY = 0`, `TREE = 1`, `TENT = 2`.
* Mảng `row_tents` và `col_tents` theo dõi số lượng lều thực tế hiện có trên từng hàng và cột.
* Hàm `is_valid_tent_placement(r, c)` kiểm tra 4 điều kiện: trong biên, ô trống, chưa vượt giới hạn hàng/cột, và không có lều nào trong 8 hướng xung quanh.
* Hàm `get_successors(tree_index)` quét 4 hướng vuông góc quanh cây `tree_index` để trả về các vị trí cắm lều hợp lệ.

### 4.3. Giải thuật Tìm kiếm Mù ([`game_tent/blind_search.py`](game_tent/blind_search.py))
* **Chiến lược:** DFS Backtracking đệ quy **In-place Mutation**.
* Tại cây thứ `tree_index`, lấy danh sách các vị trí cắm lều hợp lệ:
  * Thử cắm lều: `grid[r][c] = TENT`, tăng đếm `row_tents[r]` và `col_tents[c]`.
  * Đâm sâu giải quyết cây tiếp theo: `dfs_search(state, tree_index + 1)`.
  * Nếu nhánh dưới bế tắc: Quay lui hoàn tác `grid[r][c] = EMPTY`, giảm bộ đếm lều.
* **Ưu điểm:** Bộ nhớ tiêu thụ gần như $0$ byte cấp phát mới, tốc độ duyệt cục bộ cực nhanh.

### 4.4. Giải thuật Tìm kiếm Heuristic ([`game_tent/heuristic_search.py`](game_tent/heuristic_search.py))
A* sử dụng cấu trúc Min-Heap `heapq` với hàm đánh giá $f(n) = g(n) + h(n)$:
1. **Chi phí tích lũy $g(n)$:** Bằng số cây đã được ghép lều thành công (`tree_index`).
2. **Hàm Heuristic Admissible $h(n)$:**
   $$h(n) = \text{len(trees)} - \text{tree\_index}$$
   Vì mỗi cây còn lại bắt buộc cần đúng 1 lều, số bước cắm lều tối thiểu luôn bằng số cây còn lại $\implies h(n) \le h^*(n)$ (Admissible 100%).
3. **Động cơ Lookahead Forward Checking (`is_feasible`):**
   Gán $h(n) = \infty$ để tiêu diệt nhánh chết ngay từ gốc nếu vi phạm 1 trong 3 điều kiện:
   * **Cân bằng số lượng:** Tổng số lều còn thiếu trên các hàng/cột phải bằng chính xác số cây còn lại.
   * **Triệt tiêu miền giá trị (Domain wipe-out):** Mọi cây còn lại bắt buộc phải còn ít nhất một ô kề hợp lệ để cắm lều.
   * **Khả năng với tới (Reachability):** Hàng/cột cần thêm $k$ lều thì phải có ít nhất $k$ cây nằm sát hàng/cột đó (khoảng cách $\le 1$).

---

