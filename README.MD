BTL1_NhomX/
│
├── algorithms/              # Chứa logic thuật toán tìm kiếm (độc lập với game)
│   ├── search_strategy.py   # Interface/Class cơ sở định nghĩa cấu trúc hàm tìm kiếm chung
│   ├── blind_search.py      # Chứa class kế thừa cài đặt thuật toán DFS, BrFS
│   └── heuristic_search.py  # Chứa class kế thừa cài đặt thuật toán A*, Hill Climbing
│
├── games/                   # Logic và luật chơi của 2 bài toán Logic Puzzles
│   ├── game_1/               # Bài toán 1 (ví dụ: Pipes)
│   │   ├── state.py         # Cấu trúc dữ liệu lưới, hàm sinh trạng thái kề, hàm kiểm tra đích
│   │   └── heuristic.py     # Hàm tính toán giá trị heuristic riêng cho Pipes
│   └── game_2/               # Bài toán 2 (ví dụ: Tents)
│       ├── state.py
│       └── heuristic.py
│
├── ui/                      # Chịu trách nhiệm hiển thị trực quan (như game)
│   └── visualizer.py        # Nhận luồng trạng thái từ thuật toán để render step-by-step bằng pygame/tkinter
│
├── utils/                   # Các công cụ hỗ trợ chạy hàng loạt và đo lường
│   ├── input_reader.py      # Đọc dữ liệu đầu vào (text/json) để khởi tạo lưới ban đầu
│   └── performance.py       # Decorator hoặc class đo lường thời gian chạy, dung lượng RAM tiêu tốn
│
├── tests/                   # Bộ unit test độc lập
│   ├── test_rules.py        # Test các thao tác chuyển đổi trạng thái của game có hợp lệ không
│   └── test_heuristics.py   # Đảm bảo hàm heuristic trả về giá trị tính toán đúng mong đợi
│
├── inputs/                  # Thư mục chứa các file map/mức độ khó tự thiết kế
├── main.py                  # Điểm neo chương trình: ghép nối giao diện, game và thuật toán
├── requirements.txt         # Khai báo các thư viện phụ thuộc (ví dụ: pygame, openpyxl, pytest)