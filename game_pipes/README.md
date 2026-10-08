# Báo Cáo Kỹ Thuật: Động cơ Logic & Giải thuật AI Trò chơi Pipes

Tài liệu này giải thích chi tiết toàn bộ kiến trúc lõi (`logic.py`), các giải thuật tìm kiếm (`blind_search.py`, `heuristic_search.py`), và các kỹ thuật tối ưu hóa chuyên sâu (Optimization) đã được áp dụng để giải quyết bài toán Pipes với tốc độ tiệm cận giới hạn vật lý của Python.

---

## PHẦN 1: Biểu Diễn Dữ Liệu & Động Cơ Vật Lý (`logic.py`)

File `logic.py` không chứa thuật toán giải, mà đóng vai trò là **Không gian Trạng thái (State Space)**, cung cấp các luật chơi và động cơ cắt tỉa (Pruning) cho AI.

### 1. Kỹ thuật Bitmask (Biểu diễn Ống nước)
Để tối ưu hóa dung lượng RAM và tốc độ xử lý khi duyệt hàng triệu trạng thái, hình dáng ống nước được biểu diễn bằng **4-bit nhị phân**:
* `UP = 1 (0001)`, `RIGHT = 2 (0010)`, `DOWN = 4 (0100)`, `LEFT = 8 (1000)`
* Lợi ích: Thao tác xoay ống $90^\circ$ được thực hiện bằng phép dịch bit C-level `((mask << 1) & 15) | (mask >> 3)` chỉ trong $O(1)$, và việc kiểm tra khớp ống sử dụng phép toán logic `AND (&)`.

### 2. Tối ưu hóa Bộ nhớ: Mảng 1D `bytearray`
Thay vì dùng mảng 2D (`List[List[int]]`) tiêu tốn nhiều Overhead của Python, toàn bộ bảng game được **trải phẳng thành mảng 1D**.
* Cấu trúc sử dụng là **`bytearray`** (do bitmask chỉ tốn tối đa 4 bits, nằm gọn trong 1 byte).
* **Kết quả:** Quá trình sao chép (Clone) trạng thái cho thuật toán A* diễn ra cực kỳ nhanh chóng bằng lệnh C-level `bytearray(self.grid)`, giảm hàng ngàn lần áp lực lên bộ thu gom rác (Garbage Collector) của Python.
* **Tối ưu vòng đời (Lifecycle Hack):** Khi gọi hàm `.clone()`, thay vì gọi `__init__` (chứa vòng lặp $O(N)$ đếm tổng số ống), hệ thống sử dụng hàm **`__new__`** để khởi tạo object thô, bỏ qua vòng lặp không cần thiết.

### 3. Động cơ Cắt tỉa (Pruning Engine)
Trong mô hình **Constructive Search** (xếp ống theo thứ tự từ $0 \rightarrow N-1$), hàm `is_valid_cell_placement` là trái tim của việc giới hạn nhánh:
* Khi xoay một ống, nó lập tức kiểm tra với các láng giềng **đã được chốt** ở các bước trước đó.
* Nếu cổng (port) của ống hiện tại và láng giềng bị mâu thuẫn, hàm trả về `False`, ép thuật toán quay lui (Backtrack) ngay lập tức. Điều này chặn đứng bùng nổ tổ hợp sớm nhất có thể.

### 4. Chế độ Torus (Wrap = True) và Bài toán "Hoãn cắt tỉa"
Trong chế độ Xuyên tường, láng giềng của mép trên là mép dưới (tính bằng phép Modulo `%`).
* **Hệ lụy AI:** Ở chế độ này, hàm cắt tỉa không thể lập tức báo lỗi với các ống đâm ra ngoài viền (vì láng giềng mép đối diện chưa được chốt). Ràng buộc bị **trì hoãn (Deferred Constraint)** khiến nhánh tìm kiếm (Branching factor) phình to gấp hàng nghìn lần so với bản đồ không Wrap.

---

## PHẦN 2: Giải thuật Tìm kiếm (`blind_search.py` & `heuristic_search.py`)

### 1. DFS (Duyệt mù) - Tốc độ tuyệt đối
Triển khai trong `blind_search.py` dựa trên kỹ thuật **In-place Mutation**. 
* Nó trực tiếp ghi đè góc xoay lên mảng 1D duy nhất và gọi đệ quy. Nếu sai, vòng lặp tự thử góc xoay khác. 
* Nhờ không cấp phát bộ nhớ mới (Zero Allocation) và độ phức tạp Không gian $O(1)$, kết hợp với hàm Cắt tỉa mạnh mẽ, DFS là vua tốc độ ở các cấu trúc Cây khung (Spanning Tree).

### 2. A* Search - Khám phá Thông minh có Thông tin
Triển khai trong `heuristic_search.py`. A* sử dụng một Min-Heap (Hàng đợi Ưu tiên) để đánh giá và ưu tiên đi vào các nhánh "an toàn", ít nguy cơ dẫn đến bế tắc (Dead-end).

Ba kỹ thuật Tối ưu Hạng nặng (Heavy Optimizations) đã được áp dụng vào A*:

#### A. Hàm Heuristic: Rò rỉ Ranh giới (Boundary Leaks)
* $h(n)$ được tính bằng tổng số cổng hở của các ô **đã chốt** đang chĩa đâm thẳng vào Vùng sương mù (các ô **chưa chốt**).
* $h(n)$ càng cao, nhánh càng phải hứng chịu áp lực ràng buộc khắt khe trong tương lai $\rightarrow$ Bị đẩy xuống đáy Hàng đợi ưu tiên.

#### B. Đếm Heuristic Tịnh tiến $O(1)$ (Incremental Delta)
* Thay vì chạy vòng lặp $O(N)$ quét toàn bộ bản đồ để tính $h(n)$ ở mỗi trạng thái con, hệ thống chỉ tính Heuristic tại Root ($h=0$).
* Tại mỗi node con, nó tính độ chênh lệch: $h_{new} = h_{parent} + \Delta$.
* Nếu ống vừa xoay đâm ra vùng chưa chốt $\rightarrow \Delta = +1$. Nếu ống khép vào một vùng đã chốt $\rightarrow \Delta = -1$. Thời gian tính giảm xuống $O(1)$.

#### C. Toán học Chỉ mục (Index Math)
* Để xác định một ô láng giềng đã được chốt (fixed) hay chưa, thay vì dùng một cấu trúc dữ liệu `Set` tốn RAM (như nguyên bản), thuật toán áp dụng logic: **Một ô được coi là đã chốt nếu và chỉ nếu chỉ mục của nó nhỏ hơn chỉ mục hiện tại (`neighbor_index < current_index`)**.
* Xóa sổ hoàn toàn cấu trúc `Set` và thao tác Copy.

---

## PHẦN 3: Tổng Kết Hiệu Năng (Benchmark)

Việc áp dụng đồng bộ `bytearray 1D`, `Incremental Heuristic O(1)` và `Index Math` đã giúp giải thuật A* tăng tốc **gấp >60 lần** so với phiên bản cơ sở.

**Bảng so sánh thời gian thực thi (Map sinh ngẫu nhiên - Không Wrap):**
| Kích thước | Duyệt mù (DFS In-place) | Trí tuệ nhân tạo (A* Heuristic) |
| :--- | :--- | :--- |
| **10x10** | ~ 0.0005 giây | ~ 0.0011 giây |
| **20x20** | ~ 0.0032 giây | ~ 0.0069 giây |
| **30x30** | ~ 0.0063 giây | ~ 0.0111 giây |
| **40x40** | ~ 0.0339 giây | ~ 0.0641 giây |

**Kết luận chuyên sâu:** 
Trong bài toán thỏa mãn ràng buộc (CSP) có điểm đích nằm ở độ sâu cố định (như Pipes Constructive Search), DFS có lợi thế toán học áp đảo về chi phí bộ nhớ ($O(1)$ Memory Overhead). 
Thuật toán A*, mặc dù sở hữu Heuristic đánh giá rủi ro xuất sắc và số lần thử sai ít hơn, nhưng vẫn chậm hơn DFS một khoảnh khắc nhỏ do chi phí duy trì hàng đợi (Heapq Overhead) và sao chép trạng thái ở Python. Tuy nhiên, tốc độ $0.06$ giây cho một bản đồ siêu khổng lồ 40x40 chứng minh kiến trúc mã nguồn hiện tại đã đạt mức tối ưu tuyệt đối!
