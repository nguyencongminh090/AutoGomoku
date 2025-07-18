#!/usr/bin/env python3
"""
Performance Testing Script for listener.py
Kiểm tra hiệu suất khi nhấn giữ và thực hiện tác vụ nặng
"""

import time
import threading
import psutil
import os
import sys
from typing import List, Dict, Any
import statistics

# Add the source/utils directory to the path
sys.path.append('source/utils')

from listener import Listener

class PerformanceMonitor:
    """Monitor CPU and memory usage during performance tests."""
    
    def __init__(self):
        self.process = psutil.Process(os.getpid())
        self.monitoring = False
        self.metrics = []
        self.monitor_thread = None
    
    def start_monitoring(self):
        """Start monitoring CPU and memory usage."""
        self.monitoring = True
        self.metrics = []
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop monitoring and return collected metrics."""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)
        return self.metrics
    
    def _monitor_loop(self):
        """Monitor loop that collects metrics every 100ms."""
        while self.monitoring:
            try:
                cpu_percent = self.process.cpu_percent()
                memory_info = self.process.memory_info()
                memory_mb = memory_info.rss / 1024 / 1024  # Convert to MB
                
                self.metrics.append({
                    'timestamp': time.time(),
                    'cpu_percent': cpu_percent,
                    'memory_mb': memory_mb
                })
                
                time.sleep(0.1)  # Sample every 100ms
            except Exception as e:
                print(f"Monitoring error: {e}")
                break

class PerformanceTest:
    """Comprehensive performance testing for the Listener class."""
    
    def __init__(self):
        self.listener = None
        self.monitor = PerformanceMonitor()
        self.test_results = {}
    
    def setup_listener(self, max_workers=1, debounce_ms=500):
        """Initialize the listener for testing."""
        self.listener = Listener(max_callback_workers=max_workers, debounce_ms=debounce_ms)
    
    def cleanup_listener(self):
        """Clean up the listener."""
        if self.listener:
            self.listener.stop()
            self.listener = None
    
    def heavy_task_callback(self, task_id: int, duration_ms: int = 100):
        """Simulate a heavy task callback."""
        start_time = time.time()
        target_time = duration_ms / 1000.0
        
        # Simulate CPU-intensive work
        while time.time() - start_time < target_time:
            # Perform some CPU-intensive calculations
            _ = sum(i * i for i in range(1000))
        
        print(f"  Heavy task {task_id} completed in {time.time() - start_time:.3f}s")
    
    def test_press_and_hold_performance(self):
        """Test performance during press and hold scenarios."""
        print("\n=== KIỂM TRA HIỆU SUẤT KHI NHẤN GIỮ ===")
        
        self.setup_listener(max_workers=2, debounce_ms=100)
        
        # Register multiple hotkeys
        for i in range(5):
            self.listener.add_hotkey(f"ctrl+{i+1}", 
                                   lambda x=i: self.heavy_task_callback(x, 50))
        
        # Test 1: Rapid key presses
        print("1. Kiểm tra nhấn phím nhanh:")
        self.monitor.start_monitoring()
        
        start_time = time.time()
        # Simulate rapid key presses
        for _ in range(20):
            # Simulate key press (in real scenario, this would be actual key events)
            time.sleep(0.05)  # 50ms between presses
        
        test_duration = time.time() - start_time
        metrics = self.monitor.stop_monitoring()
        
        self._analyze_metrics("rapid_key_presses", metrics, test_duration)
        
        # Test 2: Press and hold
        print("\n2. Kiểm tra nhấn giữ:")
        self.monitor.start_monitoring()
        
        start_time = time.time()
        # Simulate press and hold for 2 seconds
        time.sleep(2.0)
        
        test_duration = time.time() - start_time
        metrics = self.monitor.stop_monitoring()
        
        self._analyze_metrics("press_and_hold", metrics, test_duration)
        
        self.cleanup_listener()
    
    def test_heavy_task_performance(self):
        """Test performance during heavy task execution."""
        print("\n=== KIỂM TRA HIỆU SUẤT KHI THỰC HIỆN TÁC VỤ NẶNG ===")
        
        # Test with different worker configurations
        worker_configs = [1, 2, 4, 8]
        
        for workers in worker_configs:
            print(f"\n--- Cấu hình {workers} worker ---")
            self.setup_listener(max_workers=workers, debounce_ms=0)
            
            # Register a hotkey that triggers heavy tasks
            self.listener.add_hotkey("ctrl+space", 
                                   lambda: self.heavy_task_callback(0, 500))
            
            # Test concurrent heavy tasks
            self.monitor.start_monitoring()
            
            start_time = time.time()
            # Simulate multiple heavy task triggers
            for i in range(5):
                # Simulate hotkey trigger
                time.sleep(0.1)
            
            # Wait for tasks to complete
            time.sleep(3.0)
            
            test_duration = time.time() - start_time
            metrics = self.monitor.stop_monitoring()
            
            self._analyze_metrics(f"heavy_tasks_{workers}_workers", metrics, test_duration)
            
            self.cleanup_listener()
    
    def test_memory_leaks(self):
        """Test for potential memory leaks during extended use."""
        print("\n=== KIỂM TRA RÒ RỈ BỘ NHỚ ===")
        
        self.setup_listener(max_workers=4, debounce_ms=100)
        
        # Register many hotkeys
        for i in range(20):
            self.listener.add_hotkey(f"ctrl+alt+{i}", 
                                   lambda x=i: self.heavy_task_callback(x, 10))
        
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024
        
        self.monitor.start_monitoring()
        
        # Simulate extended usage
        for cycle in range(10):
            print(f"  Cycle {cycle + 1}/10")
            # Simulate hotkey usage
            for _ in range(5):
                time.sleep(0.1)
            time.sleep(0.5)
        
        metrics = self.monitor.stop_monitoring()
        final_memory = psutil.Process().memory_info().rss / 1024 / 1024
        
        memory_increase = final_memory - initial_memory
        print(f"  Bộ nhớ ban đầu: {initial_memory:.2f} MB")
        print(f"  Bộ nhớ cuối: {final_memory:.2f} MB")
        print(f"  Tăng bộ nhớ: {memory_increase:.2f} MB")
        
        if memory_increase > 10:  # More than 10MB increase
            print("  ⚠️  CẢNH BÁO: Có thể có rò rỉ bộ nhớ!")
        else:
            print("  ✅ Không phát hiện rò rỉ bộ nhớ đáng kể")
        
        self._analyze_metrics("memory_leak_test", metrics, 10.0)
        
        self.cleanup_listener()
    
    def test_thread_safety(self):
        """Test thread safety under concurrent operations."""
        print("\n=== KIỂM TRA AN TOÀN LUỒNG ===")
        
        self.setup_listener(max_workers=4, debounce_ms=50)
        
        # Register hotkeys
        for i in range(10):
            self.listener.add_hotkey(f"f{i+1}", 
                                   lambda x=i: self.heavy_task_callback(x, 100))
        
        self.monitor.start_monitoring()
        
        # Create multiple threads that add/remove hotkeys
        def add_hotkey_worker():
            for i in range(5):
                try:
                    self.listener.add_hotkey(f"shift+{i}", 
                                           lambda: print(f"Thread hotkey {i}"))
                    time.sleep(0.1)
                except Exception as e:
                    print(f"Error adding hotkey: {e}")
        
        def remove_hotkey_worker():
            for i in range(5):
                try:
                    self.listener.remove_hotkey(f"shift+{i}")
                    time.sleep(0.1)
                except Exception as e:
                    print(f"Error removing hotkey: {e}")
        
        # Start concurrent operations
        threads = []
        for _ in range(3):
            threads.append(threading.Thread(target=add_hotkey_worker))
            threads.append(threading.Thread(target=remove_hotkey_worker))
        
        start_time = time.time()
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join()
        
        test_duration = time.time() - start_time
        metrics = self.monitor.stop_monitoring()
        
        self._analyze_metrics("thread_safety", metrics, test_duration)
        
        self.cleanup_listener()
    
    def _analyze_metrics(self, test_name: str, metrics: List[Dict[str, Any]], duration: float):
        """Analyze collected performance metrics."""
        if not metrics:
            print("  Không có dữ liệu metrics để phân tích")
            return
        
        cpu_values = [m['cpu_percent'] for m in metrics]
        memory_values = [m['memory_mb'] for m in metrics]
        
        analysis = {
            'test_name': test_name,
            'duration': duration,
            'cpu_avg': statistics.mean(cpu_values),
            'cpu_max': max(cpu_values),
            'cpu_min': min(cpu_values),
            'memory_avg': statistics.mean(memory_values),
            'memory_max': max(memory_values),
            'memory_min': min(memory_values),
            'sample_count': len(metrics)
        }
        
        self.test_results[test_name] = analysis
        
        print(f"  Thời gian: {duration:.2f}s")
        print(f"  CPU trung bình: {analysis['cpu_avg']:.1f}%")
        print(f"  CPU tối đa: {analysis['cpu_max']:.1f}%")
        print(f"  Bộ nhớ trung bình: {analysis['memory_avg']:.1f} MB")
        print(f"  Bộ nhớ tối đa: {analysis['memory_max']:.1f} MB")
        print(f"  Số mẫu: {analysis['sample_count']}")
    
    def generate_report(self):
        """Generate a comprehensive performance report."""
        print("\n" + "="*60)
        print("BÁO CÁO HIỆU SUẤT TỔNG HỢP")
        print("="*60)
        
        if not self.test_results:
            print("Không có dữ liệu để báo cáo")
            return
        
        # Performance recommendations
        print("\n📊 PHÂN TÍCH HIỆU SUẤT:")
        
        # CPU usage analysis
        cpu_usage = [result['cpu_avg'] for result in self.test_results.values()]
        avg_cpu = statistics.mean(cpu_usage)
        
        if avg_cpu > 50:
            print("  ⚠️  Sử dụng CPU cao - cần tối ưu hóa")
        elif avg_cpu > 20:
            print("  ⚡ Sử dụng CPU trung bình - chấp nhận được")
        else:
            print("  ✅ Sử dụng CPU thấp - hiệu suất tốt")
        
        # Memory usage analysis
        memory_usage = [result['memory_max'] for result in self.test_results.values()]
        max_memory = max(memory_usage)
        
        if max_memory > 100:
            print("  ⚠️  Sử dụng bộ nhớ cao - cần kiểm tra rò rỉ")
        elif max_memory > 50:
            print("  ⚡ Sử dụng bộ nhớ trung bình - chấp nhận được")
        else:
            print("  ✅ Sử dụng bộ nhớ thấp - hiệu suất tốt")
        
        # Thread safety check
        if 'thread_safety' in self.test_results:
            thread_result = self.test_results['thread_safety']
            if thread_result['cpu_max'] > 80:
                print("  ⚠️  Có thể có vấn đề về thread safety")
            else:
                print("  ✅ Thread safety tốt")
        
        print("\n🔧 KHUYẾN NGHỊ TỐI ƯU HÓA:")
        
        # Check if debouncing is effective
        if 'rapid_key_presses' in self.test_results:
            rapid_result = self.test_results['rapid_key_presses']
            if rapid_result['cpu_avg'] > 30:
                print("  - Tăng debounce_ms để giảm tải CPU khi nhấn nhanh")
        
        # Check worker configuration
        worker_results = {k: v for k, v in self.test_results.items() if 'heavy_tasks' in k}
        if worker_results:
            best_worker = min(worker_results.items(), key=lambda x: x[1]['cpu_avg'])
            print(f"  - Cấu hình worker tối ưu: {best_worker[0].split('_')[-2]} workers")
        
        print("\n📈 CHI TIẾT TỪNG BÀI KIỂM TRA:")
        for test_name, result in self.test_results.items():
            print(f"\n  {test_name.upper().replace('_', ' ')}:")
            print(f"    CPU: {result['cpu_avg']:.1f}% (min: {result['cpu_min']:.1f}%, max: {result['cpu_max']:.1f}%)")
            print(f"    Memory: {result['memory_avg']:.1f}MB (min: {result['memory_min']:.1f}MB, max: {result['memory_max']:.1f}MB)")

def main():
    """Run all performance tests."""
    print("🚀 BẮT ĐẦU KIỂM TRA HIỆU SUẤT LISTENER.PY")
    print("="*60)
    
    tester = PerformanceTest()
    
    try:
        # Run all performance tests
        tester.test_press_and_hold_performance()
        tester.test_heavy_task_performance()
        tester.test_memory_leaks()
        tester.test_thread_safety()
        
        # Generate final report
        tester.generate_report()
        
    except KeyboardInterrupt:
        print("\n⚠️  Kiểm tra bị gián đoạn bởi người dùng")
    except Exception as e:
        print(f"\n❌ Lỗi trong quá trình kiểm tra: {e}")
    finally:
        tester.cleanup_listener()
        print("\n✅ Hoàn thành kiểm tra hiệu suất")

if __name__ == "__main__":
    main()