# BÀI TẬP LỚN 1: TÌM KIẾM - TRÍ TUỆ NHÂN TẠO (HK1 26-27)

Dự án này hiện thực các giải thuật tìm kiếm cơ bản và nâng cao trong Trí tuệ nhân tạo để tự động giải quyết 2 bài toán Logic Puzzles: **Pipes** (Nối ống nước) và **Minesweeper** (Dò mìn). Toàn bộ hệ thống được phát triển bằng ngôn ngữ Python 3, tích hợp giao diện trực quan step-by-step và công cụ đo lường hiệu năng tự động để phục vụ viết báo cáo môn học.

## 👥 Phân công nhiệm vụ (Nhóm 5 thành viên)

| Phân nhóm | Thành viên | Trách nhiệm chuyên môn |
| :--- | :--- | :--- |
| **Team Pipes**<br>*(Game 1)* | **Thành viên 1** | Lập trình cấu trúc ma trận Pipes, quy tắc xoay ống và hiện thực giải thuật tìm kiếm mù (DFS hoặc BrFS). |
| | **Thành viên 2** | Thiết kế hàm Heuristic (VD: đếm số đầu ống hở), hiện thực giải thuật A* và viết báo cáo thuật toán cho Pipes. |
| **Team Minesweeper**<br>*(Game 2)* | **Thành viên 3** | Lập trình cấu trúc bảng Dò mìn, logic tính toán các ô kề và hiện thực giải thuật tìm kiếm mù (DFS hoặc BrFS). |
| | **Thành viên 4** | Thiết kế hàm Heuristic (VD: suy luận xác suất mìn dựa trên các số đã mở), hiện thực giải thuật A* và viết báo cáo thuật toán cho Minesweeper. |
| **UI & Benchmark** | **Thành viên 5** | Xây dựng bộ dựng hình UI dùng chung (hiển thị step-by-step cho cả 2 game). Viết script đo lường tự động thời gian và dung lượng RAM tiêu tốn cho các test cases. |

## 📁 Cấu trúc thư mục mã nguồn

```text
BTL1_NhomX/
│
├── game_pipes/              # Mã nguồn độc lập cho trò chơi Pipes
│   ├── logic.py             # Định nghĩa không gian trạng thái, action xoay ống, goal test
│   ├── blind_search.py      # Cài đặt thuật toán DFS/BrFS
│   └── heuristic_search.py  # Cài đặt thuật toán A* và hàm Heuristic đếm đầu hở
│
├── game_minesweeper/        # Mã nguồn độc lập cho trò chơi Minesweeper
│   ├── logic.py             # Định nghĩa trạng thái bảng mìn, action mở ô/cắm cờ, goal test
│   ├── blind_search.py      # Cài đặt thuật toán DFS/BrFS
│   └── heuristic_search.py  # Cài đặt thuật toán A* và hàm Heuristic đánh giá rủi ro
│
├── core_ui/                 # Module đồ họa dùng chung
│   ├── assets/              # Chứa file ảnh tĩnh (ống nước chữ L/T/I, icon quả mìn, lá cờ...)
│   └── grid_renderer.py     # Nhận ma trận trạng thái từ thuật toán và render ra màn hình
│
├── benchmark/               # Module tự động hóa và dữ liệu test
│   ├── test_cases/          # Chứa các file input (.txt/.json) định nghĩa map từ dễ đến khó
│   └── performance.py       # Script chạy ngầm thuật toán, đo lường thời gian/RAM và xuất CSV
│
├── main.py                  # Entry point: Menu dòng lệnh điều hướng chạy UI hoặc Benchmark
└── requirements.txt         # Khai báo các thư viện phụ thuộc (pygame, tkinter, tracemalloc...)


🚀 Hướng dẫn Cài đặt & Khởi chạy
1. Yêu cầu hệ thống

Python 3.x (Bắt buộc).

Cài đặt các thư viện cần thiết:

Bash
pip install -r requirements.txt
2. Chạy chế độ Trực quan (Step-by-step UI)
Chế độ này mở cửa sổ đồ họa, cho phép quan sát chi tiết từng bước thuật toán duyệt qua các trạng thái không gian.

Bash
# Chạy game Pipes với thuật toán A*
python main.py --game pipes --algo astar --mode ui

# Chạy game Minesweeper với thuật toán BFS
python main.py --game minesweeper --algo bfs --mode ui
3. Chạy chế độ Đo lường (Benchmark Mode)
Chế độ này sẽ tắt giao diện, nạp toàn bộ các ma trận trong benchmark/test_cases/ và chạy ngầm tất cả thuật toán để đánh giá hiệu suất.

Bash
python main.py --mode benchmark
Kết quả đầu ra: Hệ thống sẽ tự động sinh ra file report_metrics.csv ghi nhận chi tiết thời gian (giây) và sự tiêu tốn bộ nhớ (MB) của từng giải thuật đối với từng input.