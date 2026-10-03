# Lõi Logic Trò chơi (game_pipes/logic.py)

File `logic.py` là **"Trái tim Vật lý"** (Physics Engine) và **Biểu diễn Không gian Trạng thái** (State Space Representation) của trò chơi Pipes. Nó không chứa thuật toán tìm kiếm (DFS, BFS), mà cung cấp toàn bộ các luật chơi, cách biểu diễn dữ liệu và các hàm phục vụ cho việc sinh/cắt tỉa nhánh của AI.

---

## 1. Biểu diễn dữ liệu (Kỹ thuật Bitmask)

Để đạt tốc độ tối đa khi AI duyệt hàng triệu trạng thái, hình dáng ống nước không được biểu diễn bằng mảng hay chuỗi, mà dùng **4 bit nhị phân** đại diện cho 4 cổng:
- `UP = 1` (0001)
- `RIGHT = 2` (0010)
- `DOWN = 4` (0100)
- `LEFT = 8` (1000)

*Ví dụ:* Một ống vuông góc chĩa lên và sang phải có giá trị là `1 + 2 = 3` (0011).
* **Hàm `rotate_90(mask)`:** Dùng phép dịch bit (`(mask << 1) & 15 | (mask >> 3)`) để xoay ống nước $90^\circ$ theo chiều kim đồng hồ với tốc độ phần cứng.
* **Hàm `get_unique_rotations(mask)`:** Loại bỏ các góc xoay bị trùng lặp (vd: ống thẳng ngang xoay $180^\circ$ vẫn là ống ngang), giúp AI giảm số lượng nhánh thừa phải duyệt.

---

## 2. Giải phẫu Lớp `PipeState`

`PipeState` lưu trữ ma trận bảng game và các thao tác kiểm tra trạng thái.

### A. Tối ưu hóa Khởi tạo (`__init__`)
Thay vì tính toán lại ở mọi State, hàm `__init__` quét ma trận 1 lần duy nhất để tìm:
- `total_pipes`: Tổng số lượng ô chứa ống nước.
- `start_pipe`: Tọa độ của ống nước đầu tiên tìm thấy.
*(Mẹo tối ưu: Vì thao tác xoay ống không làm tăng giảm số lượng ống, 2 biến này là bất biến. Việc tính trước giúp hàm `is_goal` chạy siêu tốc ở cuối).*

### B. Lấy Láng giềng (`get_neighbor`)
Xử lý đồng thời 2 chế độ chơi:
- **Non-wrap (Bình thường):** Trả về `None` nếu láng giềng nằm ngoài bản đồ.
- **Wrap (Xuyên tường - Torus):** Dùng phép chia lấy dư (`% rows`, `% cols`) để tự động quấn láng giềng ở mép bản đồ sang mép đối diện.

### C. Động cơ Cắt tỉa Nhánh (`is_valid_cell_placement`)
Đây là **chìa khóa giúp thuật toán Constructive Search không bị tràn RAM**. Khi AI chốt góc xoay cho 1 ô `(r,c)`:
1. Nó kiểm tra ô đó với các láng giềng **đã được chốt** nằm trong `fixed_cells` (thường là ô bên trên và bên trái).
2. Nếu cổng nối của ô `(r,c)` và láng giềng bị lệch nhau (dùng phép XOR bitmask: `has_port != neighbor_has_port`), hàm lập tức trả về `False`.
3. AI sẽ dựa vào `False` để hủy nhánh đệ quy hiện tại ngay lập tức, tiết kiệm hàng tỷ phép toán thừa.
*(Lưu ý: Nhờ cơ chế Delay Constraint, ở chế độ Wrap, các ống đâm ra ngoài viền sẽ được tự do cho đến khi mép đối diện của bản đồ được chốt).*

### D. Kiểm tra Trạng thái Đích (`is_goal`)
Hàm Goal Test đã được **gộp chung (Merged)** cực kỳ tối ưu:
Nó sử dụng duy nhất một thuật toán **BFS Flood-Fill**, thực hiện 3 nhiệm vụ cùng một lúc:
1. **Kiểm tra liên thông & vỡ ống:** Quá trình BFS sẽ quét theo các đường ống. Nếu phát hiện ống đâm ra ngoài viền (`None`) hoặc ống chĩa vào hàng xóm mà hàng xóm không bịt kín $\rightarrow$ Trả về `False` ngay (Phát hiện rò rỉ).
2. **Đếm liên thông:** Nếu BFS kết thúc suôn sẻ, nó so sánh số ô duyệt được (`len(visited)`) với `total_pipes`. Nếu bằng nhau, toàn bộ mạng lưới là một khối duy nhất.
3. **Kiểm tra Chu trình:** Mạng lưới phải là một đồ thị Cây phi chu trình (Acyclic Tree), được xác thực bằng công thức số cạnh $E = V - 1$.

### E. Hàm đánh giá Heuristic (`count_open_ports`)
Đếm tổng số "đầu cắm hở" (chĩa vào tường hoặc chĩa vào khoảng không) trên toàn bộ bản đồ. Giá trị này được thuật toán **A*** sử dụng để ước lượng số bước tối thiểu còn lại cần để giải quyết (Heuristic).
