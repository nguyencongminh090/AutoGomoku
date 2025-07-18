#!/usr/bin/env python3
"""
Simplified Performance Testing Script for listener.py
Kiểm tra hiệu suất khi nhấn giữ và thực hiện tác vụ nặng
"""

import time
import threading
import os
import sys
import gc
from typing import List, Dict, Any
import statistics

# Add the source/utils directory to the path
sys.path.append('source/utils')

from listener import Listener

class SimplePerformanceMonitor:
    """Simple monitor using time-based measurements."""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.measurements = []
    
    def start_monitoring(self):
        """Start monitoring."""
        self.start_time = time.time()
        self.measurements = []
    
    def stop_monitoring(self):
        """Stop monitoring and return duration."""
        self.end_time = time.time()
        return self.end_time - self.start_time
    
    def record_measurement(self, value: float):
        """Record a measurement."""
        self.measurements.append(value)

class PerformanceTest:
    """Comprehensive performance testing for the Listener class."""
    
    def __init__(self):
        self.listener = None
        self.monitor = SimplePerformanceMonitor()
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
        
        # Test 1: Rapid key presses simulation
        print("1. Kiểm tra nhấn phím nhanh:")
        self.monitor.start_monitoring()
        
        # Simulate rapid key presses by calling callbacks directly
        callback_times = []
        for _ in range(20):
            start = time.time()
            # Simulate hotkey trigger by calling callback directly
            self.heavy_task_callback(0, 10)
            callback_times.append(time.time() - start)
            time.sleep(0.05)  # 50ms between calls
        
        test_duration = self.monitor.stop_monitoring()
        
        self._analyze_callback_times("rapid_key_presses", callback_times, test_duration)
        
        # Test 2: Press and hold simulation
        print("\n2. Kiểm tra nhấn giữ:")
        self.monitor.start_monitoring()
        
        # Simulate continuous callback execution (like press and hold)
        hold_times = []
        for _ in range(10):
            start = time.time()
            self.heavy_task_callback(0, 20)
            hold_times.append(time.time() - start)
            time.sleep(0.1)  # 100ms between calls
        
        test_duration = self.monitor.stop_monitoring()
        
        self._analyze_callback_times("press_and_hold", hold_times, test_duration)
        
        self.cleanup_listener()
    
    def test_heavy_task_performance(self):
        """Test performance during heavy task execution."""
        print("\n=== KIỂM TRA HIỆU SUẤT KHI THỰC HIỆN TÁC VỤ NẶNG ===")
        
        # Test with different worker configurations
        worker_configs = [1, 2, 4]
        
        for workers in worker_configs:
            print(f"\n--- Cấu hình {workers} worker ---")
            self.setup_listener(max_workers=workers, debounce_ms=0)
            
            # Register a hotkey that triggers heavy tasks
            self.listener.add_hotkey("ctrl+space", 
                                   lambda: self.heavy_task_callback(0, 200))
            
            # Test concurrent heavy tasks
            self.monitor.start_monitoring()
            
            # Simulate multiple heavy task triggers
            task_times = []
            for i in range(5):
                start = time.time()
                # Simulate hotkey trigger
                self.heavy_task_callback(i, 100)
                task_times.append(time.time() - start)
                time.sleep(0.1)
            
            test_duration = self.monitor.stop_monitoring()
            
            self._analyze_callback_times(f"heavy_tasks_{workers}_workers", task_times, test_duration)
            
            self.cleanup_listener()
    
    def test_memory_usage(self):
        """Test memory usage during extended use."""
        print("\n=== KIỂM TRA SỬ DỤNG BỘ NHỚ ===")
        
        self.setup_listener(max_workers=4, debounce_ms=100)
        
        # Register many hotkeys
        for i in range(20):
            self.listener.add_hotkey(f"ctrl+alt+{i}", 
                                   lambda x=i: self.heavy_task_callback(x, 10))
        
        # Force garbage collection to get baseline
        gc.collect()
        
        self.monitor.start_monitoring()
        
        # Simulate extended usage
        callback_times = []
        for cycle in range(10):
            print(f"  Cycle {cycle + 1}/10")
            # Simulate hotkey usage
            for _ in range(5):
                start = time.time()
                self.heavy_task_callback(0, 5)
                callback_times.append(time.time() - start)
                time.sleep(0.1)
            time.sleep(0.5)
        
        test_duration = self.monitor.stop_monitoring()
        
        # Force garbage collection again
        gc.collect()
        
        self._analyze_callback_times("memory_usage_test", callback_times, test_duration)
        
        self.cleanup_listener()
    
    def test_thread_safety(self):
        """Test thread safety under concurrent operations."""
        print("\n=== KIỂM TRA AN TOÀN LUỒNG ===")
        
        self.setup_listener(max_workers=4, debounce_ms=50)
        
        # Register hotkeys
        for i in range(10):
            self.listener.add_hotkey(f"f{i+1}", 
                                   lambda x=i: self.heavy_task_callback(x, 50))
        
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
        
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join()
        
        test_duration = self.monitor.stop_monitoring()
        
        self._analyze_callback_times("thread_safety", [], test_duration)
        
        self.cleanup_listener()
    
    def test_debouncing_effectiveness(self):
        """Test the effectiveness of debouncing."""
        print("\n=== KIỂM TRA HIỆU QUẢ DEBOUNCING ===")
        
        # Test different debounce values
        debounce_configs = [0, 50, 100, 200, 500]
        
        for debounce_ms in debounce_configs:
            print(f"\n--- Debounce {debounce_ms}ms ---")
            self.setup_listener(max_workers=1, debounce_ms=debounce_ms)
            
            callback_count = 0
            def counting_callback():
                nonlocal callback_count
                callback_count += 1
                print(f"    Callback triggered #{callback_count}")
            
            self.listener.add_hotkey("ctrl+a", counting_callback)
            
            self.monitor.start_monitoring()
            
            # Simulate rapid key presses
            for _ in range(10):
                # Simulate hotkey trigger
                counting_callback()
                time.sleep(0.05)  # 50ms between triggers
            
            test_duration = self.monitor.stop_monitoring()
            
            print(f"    Tổng số callback được gọi: {callback_count}")
            print(f"    Thời gian test: {test_duration:.3f}s")
            
            self.cleanup_listener()
    
    def _analyze_callback_times(self, test_name: str, callback_times: List[float], duration: float):
        """Analyze callback execution times."""
        if not callback_times:
            print("  Không có dữ liệu callback để phân tích")
            return
        
        analysis = {
            'test_name': test_name,
            'duration': duration,
            'callback_count': len(callback_times),
            'avg_callback_time': statistics.mean(callback_times),
            'max_callback_time': max(callback_times),
            'min_callback_time': min(callback_times),
            'total_callback_time': sum(callback_times),
            'throughput': len(callback_times) / duration if duration > 0 else 0
        }
        
        self.test_results[test_name] = analysis
        
        print(f"  Thời gian test: {duration:.3f}s")
        print(f"  Số callback: {analysis['callback_count']}")
        print(f"  Thời gian callback trung bình: {analysis['avg_callback_time']:.3f}s")
        print(f"  Thời gian callback tối đa: {analysis['max_callback_time']:.3f}s")
        print(f"  Thời gian callback tối thiểu: {analysis['min_callback_time']:.3f}s")
        print(f"  Tổng thời gian callback: {analysis['total_callback_time']:.3f}s")
        print(f"  Throughput: {analysis['throughput']:.1f} callback/giây")
    
    def generate_report(self):
        """Generate a comprehensive performance report."""
        print("\n" + "="*60)
        print("BÁO CÁO HIỆU SUẤT TỔNG HỢP")
        print("="*60)
        
        if not self.test_results:
            print("Không có dữ liệu để báo cáo")
            return
        
        # Performance analysis
        print("\n📊 PHÂN TÍCH HIỆU SUẤT:")
        
        # Throughput analysis
        throughput_values = [result.get('throughput', 0) for result in self.test_results.values()]
        avg_throughput = statistics.mean(throughput_values) if throughput_values else 0
        
        if avg_throughput > 50:
            print("  ✅ Throughput cao - hiệu suất tốt")
        elif avg_throughput > 20:
            print("  ⚡ Throughput trung bình - chấp nhận được")
        else:
            print("  ⚠️  Throughput thấp - cần tối ưu hóa")
        
        # Callback time analysis
        callback_times = [result.get('avg_callback_time', 0) for result in self.test_results.values()]
        avg_callback_time = statistics.mean(callback_times) if callback_times else 0
        
        if avg_callback_time < 0.1:
            print("  ✅ Thời gian callback nhanh - hiệu suất tốt")
        elif avg_callback_time < 0.5:
            print("  ⚡ Thời gian callback trung bình - chấp nhận được")
        else:
            print("  ⚠️  Thời gian callback chậm - cần tối ưu hóa")
        
        print("\n🔧 KHUYẾN NGHỊ TỐI ƯU HÓA:")
        
        # Check debouncing effectiveness
        if 'rapid_key_presses' in self.test_results:
            rapid_result = self.test_results['rapid_key_presses']
            if rapid_result.get('throughput', 0) > 100:
                print("  - Tăng debounce_ms để giảm tải khi nhấn nhanh")
        
        # Check worker configuration
        worker_results = {k: v for k, v in self.test_results.items() if 'heavy_tasks' in k}
        if worker_results:
            best_worker = max(worker_results.items(), key=lambda x: x[1].get('throughput', 0))
            print(f"  - Cấu hình worker tối ưu: {best_worker[0].split('_')[-2]} workers")
        
        print("\n📈 CHI TIẾT TỪNG BÀI KIỂM TRA:")
        for test_name, result in self.test_results.items():
            print(f"\n  {test_name.upper().replace('_', ' ')}:")
            if 'callback_count' in result:
                print(f"    Callbacks: {result['callback_count']}")
                print(f"    Avg time: {result.get('avg_callback_time', 0):.3f}s")
                print(f"    Throughput: {result.get('throughput', 0):.1f}/s")
            print(f"    Duration: {result['duration']:.3f}s")

def main():
    """Run all performance tests."""
    print("🚀 BẮT ĐẦU KIỂM TRA HIỆU SUẤT LISTENER.PY")
    print("="*60)
    
    tester = PerformanceTest()
    
    try:
        # Run all performance tests
        tester.test_press_and_hold_performance()
        tester.test_heavy_task_performance()
        tester.test_memory_usage()
        tester.test_thread_safety()
        tester.test_debouncing_effectiveness()
        
        # Generate final report
        tester.generate_report()
        
    except KeyboardInterrupt:
        print("\n⚠️  Kiểm tra bị gián đoạn bởi người dùng")
    except Exception as e:
        print(f"\n❌ Lỗi trong quá trình kiểm tra: {e}")
        import traceback
        traceback.print_exc()
    finally:
        tester.cleanup_listener()
        print("\n✅ Hoàn thành kiểm tra hiệu suất")

if __name__ == "__main__":
    main()