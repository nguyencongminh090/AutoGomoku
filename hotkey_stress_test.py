#!/usr/bin/env python3
"""
Hotkey Stress Test Script
Mô phỏng tình huống treo phần mềm khi có nhiều hotkey được nhấn liên tục
"""

import sys
import os
import time
import threading
import gc
import tracemalloc
from typing import Dict, List, Any, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
import queue
import weakref

# Mock external dependencies
class MockKeyboard:
    """Mock keyboard module."""
    
    def __init__(self):
        self.hotkeys = {}
        self.callback_count = 0
        self.blocked = False
    
    def add_hotkey(self, hotkey, callback):
        self.hotkeys[hotkey] = callback
        return True
    
    def remove_hotkey(self, hotkey):
        if hotkey in self.hotkeys:
            del self.hotkeys[hotkey]
        return True
    
    def wait(self, key):
        time.sleep(0.01)
    
    def simulate_hotkey_press(self, hotkey):
        """Simulate hotkey press."""
        if hotkey in self.hotkeys and not self.blocked:
            try:
                self.callback_count += 1
                self.hotkeys[hotkey]()
            except Exception as e:
                print(f"   ❌ Callback error for {hotkey}: {e}")

# Mock external modules
sys.modules['keyboard'] = MockKeyboard()

# Mock Listener class with potential issues
class StressTestListener:
    """Listener class designed to test stress conditions."""
    
    def __init__(self, max_callback_workers: int = 1, debounce_ms: int = 500):
        self.max_callback_workers = max_callback_workers
        self.debounce_ms = debounce_ms
        self.hotkeys = {}
        self.callback_workers = ThreadPoolExecutor(max_workers=max_callback_workers)
        self.debounce_timers = {}
        self.lock = threading.Lock()
        self.callback_queue = queue.Queue()
        self.callback_count = 0
        self.failed_callbacks = 0
        self.blocked_callbacks = 0
        self.memory_usage = []
        
        # Start callback processing thread
        self.processing_thread = threading.Thread(target=self._process_callbacks, daemon=True)
        self.processing_thread.start()
    
    def add_hotkey(self, hotkey: str, callback: Callable):
        """Add a hotkey binding."""
        with self.lock:
            self.hotkeys[hotkey] = callback
        return True
    
    def remove_hotkey(self, hotkey: str):
        """Remove a hotkey binding."""
        with self.lock:
            if hotkey in self.hotkeys:
                del self.hotkeys[hotkey]
        return True
    
    def _process_callbacks(self):
        """Process callbacks from queue."""
        while True:
            try:
                callback_data = self.callback_queue.get(timeout=1.0)
                if callback_data is None:  # Shutdown signal
                    break
                
                hotkey, callback = callback_data
                self.callback_count += 1
                
                # Simulate potential blocking
                if self.callback_count % 100 == 0:
                    time.sleep(0.1)  # Simulate heavy processing
                
                try:
                    callback()
                except Exception as e:
                    self.failed_callbacks += 1
                    print(f"   ❌ Callback failed: {e}")
                
                self.callback_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"   ❌ Callback processing error: {e}")
    
    def simulate_hotkey_press(self, hotkey: str):
        """Simulate hotkey press with potential blocking."""
        if hotkey in self.hotkeys:
            try:
                # Add to queue (potential blocking point)
                self.callback_queue.put((hotkey, self.hotkeys[hotkey]), timeout=0.1)
            except queue.Full:
                self.blocked_callbacks += 1
                print(f"   ⚠️  Callback queue full for {hotkey}")
    
    def get_stats(self):
        """Get listener statistics."""
        return {
            'callback_count': self.callback_count,
            'failed_callbacks': self.failed_callbacks,
            'blocked_callbacks': self.blocked_callbacks,
            'queue_size': self.callback_queue.qsize(),
            'hotkey_count': len(self.hotkeys)
        }
    
    def __del__(self):
        """Cleanup on destruction."""
        if hasattr(self, 'callback_workers'):
            self.callback_workers.shutdown(wait=False)
        if hasattr(self, 'callback_queue'):
            self.callback_queue.put(None)  # Shutdown signal

class HotkeyStressTester:
    """Test hotkey stress conditions and potential hanging."""
    
    def __init__(self):
        self.results = {}
        self.memory_detector = None
        
    def test_rapid_hotkey_presses(self):
        """Test rapid hotkey presses to simulate hanging."""
        print("\n🔥 Testing Rapid Hotkey Presses...")
        
        try:
            # Create listener with limited workers
            listener = StressTestListener(max_callback_workers=2, debounce_ms=50)
            
            # Add multiple hotkeys
            hotkeys = ['alt+s', 'esc', 'ctrl+shift+x', 'alt+r', 'alt+d', 'alt+q', 'alt+=', 'alt+-', 'alt+enter']
            
            def callback_factory(name):
                def callback():
                    time.sleep(0.001)  # Simulate some processing
                    return f"Callback {name} executed"
                return callback
            
            for i, hotkey in enumerate(hotkeys):
                listener.add_hotkey(hotkey, callback_factory(f"hotkey_{i}"))
            
            print(f"   Added {len(hotkeys)} hotkeys")
            
            # Simulate rapid presses
            start_time = time.perf_counter()
            press_count = 0
            
            for _ in range(1000):  # 1000 rapid presses
                for hotkey in hotkeys:
                    listener.simulate_hotkey_press(hotkey)
                    press_count += 1
                    
                    # Check for hanging every 100 presses
                    if press_count % 100 == 0:
                        stats = listener.get_stats()
                        print(f"   Press {press_count}: Callbacks={stats['callback_count']}, Failed={stats['failed_callbacks']}, Blocked={stats['blocked_callbacks']}")
                        
                        # Check if system is hanging
                        if stats['blocked_callbacks'] > 10:
                            print("   ⚠️  Potential hanging detected - too many blocked callbacks")
                            break
            
            end_time = time.perf_counter()
            duration = end_time - start_time
            
            final_stats = listener.get_stats()
            
            print(f"\n   📊 Rapid Press Test Results:")
            print(f"      Total presses: {press_count}")
            print(f"      Duration: {duration:.2f}s")
            print(f"      Callbacks executed: {final_stats['callback_count']}")
            print(f"      Failed callbacks: {final_stats['failed_callbacks']}")
            print(f"      Blocked callbacks: {final_stats['blocked_callbacks']}")
            print(f"      Queue size: {final_stats['queue_size']}")
            
            # Assessment
            if final_stats['blocked_callbacks'] == 0:
                print("      ✅ No hanging detected")
                hanging_status = 'none'
            elif final_stats['blocked_callbacks'] < 10:
                print("      ⚠️  Minor hanging detected")
                hanging_status = 'minor'
            else:
                print("      ❌ Significant hanging detected")
                hanging_status = 'significant'
            
            self.results['rapid_hotkey_presses'] = {
                'press_count': press_count,
                'duration': duration,
                'blocked_callbacks': final_stats['blocked_callbacks'],
                'hanging_status': hanging_status,
                'status': 'good' if hanging_status == 'none' else 'poor'
            }
            
            # Cleanup
            del listener
            gc.collect()
            
        except Exception as e:
            print(f"   ❌ Rapid hotkey test failed: {e}")
            self.results['rapid_hotkey_presses'] = {'status': 'error', 'error': str(e)}
    
    def test_memory_leak_with_hotkeys(self):
        """Test memory leaks during hotkey operations."""
        print("\n🧠 Testing Memory Leaks with Hotkeys...")
        
        try:
            tracemalloc.start()
            initial_snapshot = tracemalloc.take_snapshot()
            
            # Create and destroy listeners multiple times
            for cycle in range(10):
                print(f"   Cycle {cycle+1}/10: Creating and destroying listener...")
                
                listener = StressTestListener(max_callback_workers=3, debounce_ms=100)
                
                # Add hotkeys and simulate presses
                hotkeys = ['alt+s', 'esc', 'ctrl+shift+x', 'alt+r', 'alt+d']
                
                def callback_factory(name):
                    def callback():
                        time.sleep(0.001)
                        return f"Callback {name}"
                    return callback
                
                for i, hotkey in enumerate(hotkeys):
                    listener.add_hotkey(hotkey, callback_factory(f"cycle_{cycle}_hotkey_{i}"))
                
                # Simulate some presses
                for _ in range(50):
                    for hotkey in hotkeys:
                        listener.simulate_hotkey_press(hotkey)
                
                # Take memory snapshot
                current_snapshot = tracemalloc.take_snapshot()
                top_stats = current_snapshot.compare_to(initial_snapshot, 'lineno')
                
                total_memory = current_snapshot.statistics('filename').total_size
                print(f"      Memory usage: {total_memory / 1024:.2f}KB")
                
                # Check for memory increases
                if top_stats:
                    largest_increase = max(top_stats, key=lambda x: x.size_diff)
                    if largest_increase.size_diff > 1024:  # More than 1KB
                        print(f"      ⚠️  Memory increase: +{largest_increase.size_diff / 1024:.2f}KB")
                
                # Cleanup
                del listener
                gc.collect()
                
                time.sleep(0.1)
            
            final_snapshot = tracemalloc.take_snapshot()
            final_stats = final_snapshot.compare_to(initial_snapshot, 'lineno')
            
            total_memory_diff = final_snapshot.statistics('filename').total_size - initial_snapshot.statistics('filename').total_size
            
            print(f"\n   📊 Memory Leak Analysis:")
            print(f"      Total memory difference: {total_memory_diff / 1024:+.2f}KB")
            
            if total_memory_diff < 1024:  # Less than 1MB
                print("      ✅ No significant memory leak detected")
                leak_status = 'none'
            elif total_memory_diff < 5120:  # Less than 5MB
                print("      ⚠️  Minor memory leak detected")
                leak_status = 'minor'
            else:
                print("      ❌ Significant memory leak detected")
                leak_status = 'significant'
            
            # Show top memory increases
            if final_stats:
                print("      Top memory increases:")
                for stat in final_stats[:3]:
                    if stat.size_diff > 0:
                        print(f"        +{stat.size_diff / 1024:.2f}KB: {stat.traceback.format()}")
            
            self.results['memory_leak_with_hotkeys'] = {
                'total_memory_diff': total_memory_diff,
                'leak_status': leak_status,
                'status': 'good' if leak_status == 'none' else 'poor'
            }
            
            tracemalloc.stop()
            
        except Exception as e:
            print(f"   ❌ Memory leak test failed: {e}")
            self.results['memory_leak_with_hotkeys'] = {'status': 'error', 'error': str(e)}
    
    def test_thread_blocking_scenarios(self):
        """Test scenarios where threads might block."""
        print("\n🔒 Testing Thread Blocking Scenarios...")
        
        try:
            # Test with limited thread pool
            listener = StressTestListener(max_callback_workers=1, debounce_ms=0)
            
            # Add hotkeys with potentially blocking callbacks
            hotkeys = ['alt+s', 'esc', 'ctrl+shift+x', 'alt+r', 'alt+d']
            
            def blocking_callback(name):
                def callback():
                    time.sleep(0.1)  # Simulate blocking operation
                    return f"Blocking callback {name}"
                return callback
            
            for i, hotkey in enumerate(hotkeys):
                listener.add_hotkey(hotkey, blocking_callback(f"blocking_{i}"))
            
            print("   Added blocking callbacks")
            
            # Simulate rapid presses to cause blocking
            start_time = time.perf_counter()
            
            for _ in range(50):  # 50 rapid presses
                for hotkey in hotkeys:
                    listener.simulate_hotkey_press(hotkey)
            
            end_time = time.perf_counter()
            duration = end_time - start_time
            
            final_stats = listener.get_stats()
            
            print(f"\n   📊 Thread Blocking Test Results:")
            print(f"      Duration: {duration:.2f}s")
            print(f"      Callbacks executed: {final_stats['callback_count']}")
            print(f"      Blocked callbacks: {final_stats['blocked_callbacks']}")
            print(f"      Queue size: {final_stats['queue_size']}")
            
            # Assessment
            if final_stats['blocked_callbacks'] == 0:
                print("      ✅ No thread blocking detected")
                blocking_status = 'none'
            elif final_stats['blocked_callbacks'] < 20:
                print("      ⚠️  Minor thread blocking detected")
                blocking_status = 'minor'
            else:
                print("      ❌ Significant thread blocking detected")
                blocking_status = 'significant'
            
            self.results['thread_blocking_scenarios'] = {
                'duration': duration,
                'blocked_callbacks': final_stats['blocked_callbacks'],
                'blocking_status': blocking_status,
                'status': 'good' if blocking_status == 'none' else 'poor'
            }
            
            # Cleanup
            del listener
            gc.collect()
            
        except Exception as e:
            print(f"   ❌ Thread blocking test failed: {e}")
            self.results['thread_blocking_scenarios'] = {'status': 'error', 'error': str(e)}
    
    def test_callback_queue_overflow(self):
        """Test callback queue overflow scenarios."""
        print("\n📦 Testing Callback Queue Overflow...")
        
        try:
            # Create listener with small queue
            listener = StressTestListener(max_callback_workers=1, debounce_ms=0)
            
            # Add hotkeys
            hotkeys = ['alt+s', 'esc', 'ctrl+shift+x', 'alt+r', 'alt+d', 'alt+q', 'alt+=', 'alt+-']
            
            def slow_callback(name):
                def callback():
                    time.sleep(0.05)  # Slow callback
                    return f"Slow callback {name}"
                return callback
            
            for i, hotkey in enumerate(hotkeys):
                listener.add_hotkey(hotkey, slow_callback(f"slow_{i}"))
            
            print("   Added slow callbacks")
            
            # Rapidly press hotkeys to overflow queue
            start_time = time.perf_counter()
            press_count = 0
            
            for _ in range(200):  # 200 rapid presses
                for hotkey in hotkeys:
                    listener.simulate_hotkey_press(hotkey)
                    press_count += 1
                    
                    # Check queue status
                    if press_count % 50 == 0:
                        stats = listener.get_stats()
                        print(f"   Press {press_count}: Queue={stats['queue_size']}, Blocked={stats['blocked_callbacks']}")
            
            end_time = time.perf_counter()
            duration = end_time - start_time
            
            final_stats = listener.get_stats()
            
            print(f"\n   📊 Queue Overflow Test Results:")
            print(f"      Total presses: {press_count}")
            print(f"      Duration: {duration:.2f}s")
            print(f"      Final queue size: {final_stats['queue_size']}")
            print(f"      Blocked callbacks: {final_stats['blocked_callbacks']}")
            print(f"      Failed callbacks: {final_stats['failed_callbacks']}")
            
            # Assessment
            if final_stats['blocked_callbacks'] == 0:
                print("      ✅ No queue overflow detected")
                overflow_status = 'none'
            elif final_stats['blocked_callbacks'] < 50:
                print("      ⚠️  Minor queue overflow detected")
                overflow_status = 'minor'
            else:
                print("      ❌ Significant queue overflow detected")
                overflow_status = 'significant'
            
            self.results['callback_queue_overflow'] = {
                'press_count': press_count,
                'duration': duration,
                'blocked_callbacks': final_stats['blocked_callbacks'],
                'overflow_status': overflow_status,
                'status': 'good' if overflow_status == 'none' else 'poor'
            }
            
            # Cleanup
            del listener
            gc.collect()
            
        except Exception as e:
            print(f"   ❌ Queue overflow test failed: {e}")
            self.results['callback_queue_overflow'] = {'status': 'error', 'error': str(e)}
    
    def test_deadlock_scenarios(self):
        """Test potential deadlock scenarios."""
        print("\n🔐 Testing Deadlock Scenarios...")
        
        try:
            # Create listener with potential deadlock conditions
            listener = StressTestListener(max_callback_workers=2, debounce_ms=0)
            
            # Add hotkeys that might cause deadlocks
            hotkeys = ['alt+s', 'esc', 'ctrl+shift+x', 'alt+r']
            
            # Create callbacks that might deadlock
            def deadlock_prone_callback(name):
                def callback():
                    # Simulate potential deadlock condition
                    with threading.Lock():
                        time.sleep(0.01)
                        # Try to acquire another lock (potential deadlock)
                        with threading.Lock():
                            time.sleep(0.01)
                    return f"Deadlock prone callback {name}"
                return callback
            
            for i, hotkey in enumerate(hotkeys):
                listener.add_hotkey(hotkey, deadlock_prone_callback(f"deadlock_{i}"))
            
            print("   Added deadlock-prone callbacks")
            
            # Simulate rapid presses
            start_time = time.perf_counter()
            
            for _ in range(100):  # 100 rapid presses
                for hotkey in hotkeys:
                    listener.simulate_hotkey_press(hotkey)
            
            end_time = time.perf_counter()
            duration = end_time - start_time
            
            final_stats = listener.get_stats()
            
            print(f"\n   📊 Deadlock Test Results:")
            print(f"      Duration: {duration:.2f}s")
            print(f"      Callbacks executed: {final_stats['callback_count']}")
            print(f"      Failed callbacks: {final_stats['failed_callbacks']}")
            print(f"      Blocked callbacks: {final_stats['blocked_callbacks']}")
            
            # Assessment
            if final_stats['failed_callbacks'] == 0 and final_stats['blocked_callbacks'] == 0:
                print("      ✅ No deadlock detected")
                deadlock_status = 'none'
            elif final_stats['failed_callbacks'] < 5:
                print("      ⚠️  Minor deadlock symptoms detected")
                deadlock_status = 'minor'
            else:
                print("      ❌ Potential deadlock detected")
                deadlock_status = 'significant'
            
            self.results['deadlock_scenarios'] = {
                'duration': duration,
                'failed_callbacks': final_stats['failed_callbacks'],
                'blocked_callbacks': final_stats['blocked_callbacks'],
                'deadlock_status': deadlock_status,
                'status': 'good' if deadlock_status == 'none' else 'poor'
            }
            
            # Cleanup
            del listener
            gc.collect()
            
        except Exception as e:
            print(f"   ❌ Deadlock test failed: {e}")
            self.results['deadlock_scenarios'] = {'status': 'error', 'error': str(e)}
    
    def run_comprehensive_stress_test(self):
        """Run comprehensive stress tests."""
        print("🚀 Starting Hotkey Stress Tests")
        print("=" * 60)
        
        tests = [
            self.test_rapid_hotkey_presses,
            self.test_memory_leak_with_hotkeys,
            self.test_thread_blocking_scenarios,
            self.test_callback_queue_overflow,
            self.test_deadlock_scenarios
        ]
        
        for test in tests:
            try:
                test()
            except Exception as e:
                print(f"   ❌ Test failed with exception: {e}")
        
        # Print comprehensive summary
        print("\n" + "=" * 60)
        print("📋 STRESS TEST SUMMARY")
        print("=" * 60)
        
        for test_name, result in self.results.items():
            if result.get('status') == 'good':
                print(f"✅ {test_name}: PASSED")
            elif result.get('status') == 'poor':
                print(f"⚠️  {test_name}: HANGING DETECTED")
            else:
                print(f"❌ {test_name}: FAILED - {result.get('error', 'Unknown error')}")
        
        # Overall assessment
        passed = sum(1 for result in self.results.values() if result.get('status') == 'good')
        total = len(self.results)
        
        print(f"\nOverall Stress Test: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 No hanging issues detected!")
        elif passed >= total * 0.6:
            print("⚠️  Minor hanging issues detected. Consider optimizations.")
        else:
            print("❌ Significant hanging issues detected. Immediate attention required.")

if __name__ == "__main__":
    tester = HotkeyStressTester()
    tester.run_comprehensive_stress_test()