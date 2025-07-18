# Phân Tích Hiệu Suất - Listener.py

## Tổng Quan
Tài liệu này phân tích hiệu suất của file `source/utils/listener.py` với trọng tâm vào hai yêu cầu chính:
1. **Kiểm tra hiệu suất khi nhấn và giữ phím** (Press and Hold Performance)
2. **Kiểm tra hiệu suất khi thực hiện tác vụ nặng** (Heavy Task Performance)

## Kiến Trúc Hiện Tại

### Thiết Kế Thread-Safe
```python
class Listener:
    def __init__(self, max_callback_workers: int = 1, debounce_ms: int = 500):
        self._pressed_scan_codes  = set()           # Theo dõi phím đang nhấn
        self._hotkey_map          = {}              # Mapping hotkey -> callback
        self._lock                = Lock()          # Thread synchronization
        self._stop_event          = Event()         # Shutdown signal
        self._debounce_ms         = debounce_ms     # Debounce thời gian
        self._last_callback_times = {}              # Per-hotkey debounce tracking
        self._callback_executor   = ThreadPoolExecutor(max_workers=max_callback_workers)
```

## 1. Phân Tích Hiệu Suất Press and Hold

### Vấn Đề Hiện Tại

#### 1.1 Debounce Mechanism
- **Thời gian debounce mặc định**: 500ms (quá cao cho press & hold)
- **Vấn đề**: Khi nhấn giữ phím, callback chỉ được trigger một lần do debounce
- **Tác động**: Không hỗ trợ repeat action khi giữ phím

```python
# Dòng 115-122 trong listener.py
if (current_time_ms - last_time_ms) >= self._debounce_ms:
    logging.info("Hotkey triggered: %s", current_hotkey)
    try:
        self._callback_executor.submit(callback_to_run)
        self._last_callback_times[current_hotkey] = current_time_ms
```

#### 1.2 Event Processing
- **Vấn đề**: Chỉ xử lý sự kiện 'down', bỏ qua 'up'
- **Hạn chế**: Không thể phân biệt single press vs press & hold
- **Thiếu tính năng**: Không có callback cho key release

### Đề Xuất Cải Thiện Press & Hold

#### 1.1 Thêm Hỗ Trợ Repeat Action
```python
class Listener:
    def __init__(self, max_callback_workers: int = 1, debounce_ms: int = 500, 
                 repeat_enabled: bool = False, repeat_delay_ms: int = 100):
        # ... existing code ...
        self._repeat_enabled = repeat_enabled
        self._repeat_delay_ms = repeat_delay_ms
        self._key_press_timers = {}  # Timer cho mỗi hotkey đang nhấn
```

#### 1.2 Enhanced Event Handling
```python
def _listen_loop(self):
    while not self._stop_event.is_set():
        try:
            event = keyboard.read_event(suppress=False)
            
            if event.event_type == 'down':
                self._handle_key_down(event)
            elif event.event_type == 'up':
                self._handle_key_up(event)
                
    def _handle_key_down(self, event):
        # Xử lý initial press và start repeat timer nếu cần
        
    def _handle_key_up(self, event):
        # Cancel repeat timer và trigger release callback
```

## 2. Phân Tích Hiệu Suất Heavy Task

### Vấn Đề Hiện Tại

#### 2.1 ThreadPoolExecutor Configuration
```python
# Dòng 58-61
self._callback_executor = ThreadPoolExecutor(
    max_workers=max_callback_workers,  # Mặc định = 1
    thread_name_prefix='HotkeyCallback'
)
```

**Vấn đề:**
- **Max workers = 1**: Callback chạy tuần tự, blocking nhau
- **Không có queue management**: Có thể bị memory leak khi submit quá nhiều task
- **Không có timeout**: Heavy task có thể chạy vô hạn

#### 2.2 Resource Management
```python
# Dòng 134-140
try:
    self._callback_executor.submit(callback_to_run)
    self._last_callback_times[current_hotkey] = current_time_ms
except RuntimeError:
    if not self._stop_event.is_set():
        logging.warning("Callback queue is full, skipping hotkey: %s", current_hotkey)
```

**Hạn chế:**
- Không có monitoring resource usage
- Không có cơ chế cancel running tasks
- Memory cleanup không đầy đủ

### Tác Động Trong Ứng Dụng Gomoku

Từ phân tích `model.py`, listener được sử dụng với:
```python
self.__listener = Listener(max_callback_workers=1, debounce_ms=50)

# Các hotkey được đăng ký:
self.__listener.add_hotkey('ctrl+shift+x', self.start_game_thread)  # Heavy task!
self.__listener.add_hotkey('alt+d', self.__display_search_info)     # Medium task
self.__listener.add_hotkey('alt+q', self.__stop_engine_search)      # Light task
```

**Vấn đề cụ thể:**
- `start_game_thread()` là heavy task (khởi động game engine)
- Với `max_workers=1`, các hotkey khác bị block khi game đang start
- `debounce_ms=50` quá thấp, có thể gây double-trigger

## 3. Đề Xuất Cải Thiện

### 3.1 Enhanced Configuration
```python
class Listener:
    def __init__(self, 
                 max_callback_workers: int = 2,
                 debounce_ms: int = 100,
                 max_queue_size: int = 10,
                 task_timeout_seconds: int = 30,
                 enable_monitoring: bool = False):
```

### 3.2 Priority-Based Task Execution
```python
from enum import Enum
from queue import PriorityQueue

class TaskPriority(Enum):
    CRITICAL = 1    # System controls (stop, exit)
    HIGH = 2        # User interactions  
    NORMAL = 3      # Regular operations
    LOW = 4         # Heavy computations

def add_hotkey(self, hotkey_str: str, callback: CallbackFunc, 
               priority: TaskPriority = TaskPriority.NORMAL):
```

### 3.3 Resource Monitoring
```python
class PerformanceMonitor:
    def __init__(self):
        self.task_times = {}
        self.memory_usage = {}
        self.queue_sizes = {}
        
    def log_task_start(self, task_id):
        self.task_times[task_id] = time.time()
        
    def log_task_end(self, task_id):
        duration = time.time() - self.task_times[task_id]
        logging.info(f"Task {task_id} completed in {duration:.3f}s")
```

## 4. Benchmark Test Cases

### 4.1 Press & Hold Test
```python
def test_press_hold_performance():
    """Test press and hold performance with various configurations"""
    listener = Listener(debounce_ms=50, repeat_enabled=True, repeat_delay_ms=100)
    
    press_count = 0
    def callback():
        nonlocal press_count
        press_count += 1
        
    listener.add_hotkey("ctrl+t", callback)
    
    # Simulate holding Ctrl+T for 5 seconds
    # Expected: ~50 callbacks (100ms interval)
    assert 45 <= press_count <= 55
```

### 4.2 Heavy Task Test
```python
def test_heavy_task_performance():
    """Test performance with heavy computational tasks"""
    import psutil
    
    listener = Listener(max_callback_workers=3, task_timeout_seconds=10)
    
    def heavy_task():
        # Simulate heavy computation
        time.sleep(2)
        return sum(range(1000000))
        
    def light_task():
        return "quick response"
        
    # Test concurrent execution
    start_time = time.time()
    listener.add_hotkey("ctrl+h", heavy_task, priority=TaskPriority.LOW)
    listener.add_hotkey("ctrl+l", light_task, priority=TaskPriority.HIGH)
    
    # Trigger both - light task should complete quickly despite heavy task running
```

## 5. Khuyến Nghị Triển Khai

### 5.1 Immediate Fixes
1. **Tăng max_callback_workers** trong model.py từ 1 lên 2-3
2. **Điều chỉnh debounce_ms** phù hợp với từng hotkey
3. **Thêm timeout** cho callback execution

### 5.2 Long-term Improvements
1. **Implement priority queue** cho task scheduling
2. **Add performance monitoring** để track resource usage
3. **Support press & hold patterns** cho repetitive actions
4. **Add circuit breaker** để prevent system overload

### 5.3 Configuration cho Gomoku App
```python
# Trong model.py
self.__listener = Listener(
    max_callback_workers=3,     # Cho phép 3 task concurrent
    debounce_ms=100,           # Cân bằng responsive vs double-trigger
    task_timeout_seconds=15,   # Timeout cho heavy tasks
    enable_monitoring=True     # Performance tracking
)

# Priority-based hotkey registration
self.__listener.add_hotkey('ctrl+shift+x', self.start_game_thread, 
                          priority=TaskPriority.LOW)      # Heavy task
self.__listener.add_hotkey('esc', self.turn_off, 
                          priority=TaskPriority.CRITICAL) # Emergency stop
```

## 6. Kết Luận

### Điểm Mạnh Hiện Tại
- ✅ Thread-safe design với proper locking
- ✅ Per-hotkey debounce mechanism  
- ✅ Graceful shutdown handling
- ✅ Exception handling trong listener loop

### Điểm Cần Cải Thiện
- ❌ Không hỗ trợ press & hold patterns
- ❌ Limited concurrency (max_workers=1)
- ❌ Thiếu monitoring và resource management
- ❌ Không có task prioritization
- ❌ Không có timeout cho heavy tasks

### Tác Động Hiệu Suất
- **Press & Hold**: Hiện tại không hỗ trợ, cần implement repeat mechanism
- **Heavy Tasks**: Bị bottleneck do single worker thread, cần tăng concurrency và thêm priority handling

Việc triển khai các cải thiện đề xuất sẽ nâng cao đáng kể hiệu suất của hệ thống, đặc biệt trong môi trường ứng dụng Gomoku với nhiều tác vụ phức tạp chạy đồng thời.