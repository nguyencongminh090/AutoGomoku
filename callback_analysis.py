#!/usr/bin/env python3
"""
Callback Analysis Script
Phân tích chi tiết vấn đề callback không được thực thi khi có nhiều hotkey presses
"""

import sys
import os
import time
import threading
import gc
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

class CallbackAnalyzer:
    """Analyze callback processing issues."""
    
    def __init__(self):
        self.results = {}
    
    def analyze_callback_processing_issue(self):
        """Analyze the callback processing issue found in stress test."""
        print("\n🔍 Analyzing Callback Processing Issue...")
        
        try:
            # Create a listener with the same configuration as stress test
            listener = self._create_listener(max_callback_workers=2, debounce_ms=50)
            
            # Add hotkeys
            hotkeys = ['alt+s', 'esc', 'ctrl+shift+x', 'alt+r', 'alt+d']
            
            def callback_factory(name):
                def callback():
                    time.sleep(0.001)  # Simulate some processing
                    return f"Callback {name} executed"
                return callback
            
            for i, hotkey in enumerate(hotkeys):
                listener.add_hotkey(hotkey, callback_factory(f"hotkey_{i}"))
            
            print(f"   Added {len(hotkeys)} hotkeys")
            
            # Simulate the same rapid presses as stress test
            start_time = time.perf_counter()
            press_count = 0
            
            # Monitor callback processing
            monitoring_thread = threading.Thread(target=self._monitor_callback_processing, args=(listener,), daemon=True)
            monitoring_thread.start()
            
            for _ in range(100):  # 100 rapid presses
                for hotkey in hotkeys:
                    listener.simulate_hotkey_press(hotkey)
                    press_count += 1
            
            end_time = time.perf_counter()
            duration = end_time - start_time
            
            # Wait a bit for callbacks to process
            time.sleep(2.0)
            
            final_stats = listener.get_stats()
            
            print(f"\n   📊 Callback Processing Analysis:")
            print(f"      Total presses: {press_count}")
            print(f"      Duration: {duration:.2f}s")
            print(f"      Callbacks executed: {final_stats['callback_count']}")
            print(f"      Failed callbacks: {final_stats['failed_callbacks']}")
            print(f"      Blocked callbacks: {final_stats['blocked_callbacks']}")
            print(f"      Queue size: {final_stats['queue_size']}")
            print(f"      Processing thread alive: {listener.processing_thread.is_alive()}")
            
            # Calculate processing rate
            if duration > 0:
                press_rate = press_count / duration
                callback_rate = final_stats['callback_count'] / duration
                print(f"      Press rate: {press_rate:.2f} presses/second")
                print(f"      Callback rate: {callback_rate:.2f} callbacks/second")
                
                if callback_rate < press_rate * 0.1:  # Less than 10% of presses processed
                    print("      ❌ CRITICAL: Callback processing is severely bottlenecked!")
                    issue_status = 'critical'
                elif callback_rate < press_rate * 0.5:  # Less than 50% of presses processed
                    print("      ⚠️  WARNING: Callback processing is slow")
                    issue_status = 'slow'
                else:
                    print("      ✅ Callback processing is normal")
                    issue_status = 'normal'
            else:
                issue_status = 'unknown'
            
            self.results['callback_processing_issue'] = {
                'press_count': press_count,
                'callback_count': final_stats['callback_count'],
                'queue_size': final_stats['queue_size'],
                'issue_status': issue_status,
                'status': 'good' if issue_status == 'normal' else 'poor'
            }
            
            # Cleanup
            del listener
            gc.collect()
            
        except Exception as e:
            print(f"   ❌ Callback analysis failed: {e}")
            self.results['callback_processing_issue'] = {'status': 'error', 'error': str(e)}
    
    def analyze_thread_pool_bottleneck(self):
        """Analyze thread pool bottleneck issues."""
        print("\n🧵 Analyzing Thread Pool Bottleneck...")
        
        try:
            # Test with different thread pool sizes
            thread_pool_sizes = [1, 2, 4, 8]
            
            for pool_size in thread_pool_sizes:
                print(f"\n   Testing with {pool_size} workers...")
                
                listener = self._create_listener(max_callback_workers=pool_size, debounce_ms=0)
                
                # Add hotkeys
                hotkeys = ['alt+s', 'esc', 'ctrl+shift+x', 'alt+r', 'alt+d']
                
                def callback_factory(name):
                    def callback():
                        time.sleep(0.01)  # Simulate processing time
                        return f"Callback {name} executed"
                    return callback
                
                for i, hotkey in enumerate(hotkeys):
                    listener.add_hotkey(hotkey, callback_factory(f"pool_{pool_size}_hotkey_{i}"))
                
                # Simulate rapid presses
                start_time = time.perf_counter()
                press_count = 0
                
                for _ in range(50):  # 50 rapid presses
                    for hotkey in hotkeys:
                        listener.simulate_hotkey_press(hotkey)
                        press_count += 1
                
                end_time = time.perf_counter()
                duration = end_time - start_time
                
                # Wait for processing
                time.sleep(1.0)
                
                final_stats = listener.get_stats()
                
                print(f"      Presses: {press_count}, Callbacks: {final_stats['callback_count']}, Queue: {final_stats['queue_size']}")
                
                # Calculate efficiency
                efficiency = final_stats['callback_count'] / press_count if press_count > 0 else 0
                print(f"      Efficiency: {efficiency:.2%}")
                
                if efficiency < 0.5:
                    print(f"      ⚠️  Low efficiency with {pool_size} workers")
                elif efficiency < 0.8:
                    print(f"      ⚠️  Moderate efficiency with {pool_size} workers")
                else:
                    print(f"      ✅ Good efficiency with {pool_size} workers")
                
                # Cleanup
                del listener
                gc.collect()
            
            self.results['thread_pool_bottleneck'] = {'status': 'completed'}
            
        except Exception as e:
            print(f"   ❌ Thread pool analysis failed: {e}")
            self.results['thread_pool_bottleneck'] = {'status': 'error', 'error': str(e)}
    
    def analyze_queue_processing_issue(self):
        """Analyze queue processing issues."""
        print("\n📦 Analyzing Queue Processing Issue...")
        
        try:
            # Create listener with queue monitoring
            listener = self._create_listener(max_callback_workers=1, debounce_ms=0)
            
            # Add hotkeys
            hotkeys = ['alt+s', 'esc', 'ctrl+shift+x']
            
            def slow_callback(name):
                def callback():
                    time.sleep(0.1)  # Slow callback
                    return f"Slow callback {name}"
                return callback
            
            for i, hotkey in enumerate(hotkeys):
                listener.add_hotkey(hotkey, slow_callback(f"slow_{i}"))
            
            print("   Added slow callbacks")
            
            # Monitor queue processing
            queue_sizes = []
            callback_counts = []
            
            def monitor_queue():
                for i in range(20):
                    stats = listener.get_stats()
                    queue_sizes.append(stats['queue_size'])
                    callback_counts.append(stats['callback_count'])
                    time.sleep(0.1)
            
            monitor_thread = threading.Thread(target=monitor_queue, daemon=True)
            monitor_thread.start()
            
            # Simulate rapid presses
            start_time = time.perf_counter()
            
            for _ in range(30):  # 30 rapid presses
                for hotkey in hotkeys:
                    listener.simulate_hotkey_press(hotkey)
            
            end_time = time.perf_counter()
            duration = end_time - start_time
            
            # Wait for monitoring to complete
            monitor_thread.join()
            
            print(f"\n   📊 Queue Processing Analysis:")
            print(f"      Duration: {duration:.2f}s")
            print(f"      Initial queue size: {queue_sizes[0] if queue_sizes else 0}")
            print(f"      Final queue size: {queue_sizes[-1] if queue_sizes else 0}")
            print(f"      Initial callbacks: {callback_counts[0] if callback_counts else 0}")
            print(f"      Final callbacks: {callback_counts[-1] if callback_counts else 0}")
            
            # Analyze queue growth
            if len(queue_sizes) > 1:
                queue_growth_rate = (queue_sizes[-1] - queue_sizes[0]) / len(queue_sizes)
                print(f"      Queue growth rate: {queue_growth_rate:.2f} items/check")
                
                if queue_growth_rate > 1:
                    print("      ❌ Queue is growing faster than processing")
                    queue_status = 'overflowing'
                elif queue_growth_rate > 0:
                    print("      ⚠️  Queue is growing slowly")
                    queue_status = 'growing'
                else:
                    print("      ✅ Queue is being processed efficiently")
                    queue_status = 'stable'
            else:
                queue_status = 'unknown'
            
            self.results['queue_processing_issue'] = {
                'queue_growth_rate': queue_growth_rate if len(queue_sizes) > 1 else 0,
                'queue_status': queue_status,
                'status': 'good' if queue_status == 'stable' else 'poor'
            }
            
            # Cleanup
            del listener
            gc.collect()
            
        except Exception as e:
            print(f"   ❌ Queue analysis failed: {e}")
            self.results['queue_processing_issue'] = {'status': 'error', 'error': str(e)}
    
    def analyze_debounce_impact(self):
        """Analyze the impact of debouncing on callback processing."""
        print("\n⏱️  Analyzing Debounce Impact...")
        
        try:
            # Test different debounce values
            debounce_values = [0, 50, 100, 200]
            
            for debounce_ms in debounce_values:
                print(f"\n   Testing with {debounce_ms}ms debounce...")
                
                listener = self._create_listener(max_callback_workers=2, debounce_ms=debounce_ms)
                
                # Add hotkeys
                hotkeys = ['alt+s', 'esc', 'ctrl+shift+x']
                
                def callback_factory(name):
                    def callback():
                        time.sleep(0.001)
                        return f"Callback {name}"
                    return callback
                
                for i, hotkey in enumerate(hotkeys):
                    listener.add_hotkey(hotkey, callback_factory(f"debounce_{debounce_ms}_hotkey_{i}"))
                
                # Simulate rapid presses
                start_time = time.perf_counter()
                press_count = 0
                
                for _ in range(100):  # 100 rapid presses
                    for hotkey in hotkeys:
                        listener.simulate_hotkey_press(hotkey)
                        press_count += 1
                
                end_time = time.perf_counter()
                duration = end_time - start_time
                
                # Wait for processing
                time.sleep(debounce_ms / 1000.0 + 0.1)
                
                final_stats = listener.get_stats()
                
                print(f"      Presses: {press_count}, Callbacks: {final_stats['callback_count']}, Queue: {final_stats['queue_size']}")
                
                # Calculate debounce effectiveness
                effectiveness = final_stats['callback_count'] / press_count if press_count > 0 else 0
                print(f"      Effectiveness: {effectiveness:.2%}")
                
                if debounce_ms == 0:
                    if effectiveness < 0.5:
                        print("      ⚠️  Low effectiveness without debounce")
                    else:
                        print("      ✅ Good effectiveness without debounce")
                else:
                    if effectiveness < 0.1:
                        print("      ⚠️  Debounce too aggressive")
                    elif effectiveness < 0.3:
                        print("      ⚠️  Debounce moderately aggressive")
                    else:
                        print("      ✅ Debounce working well")
                
                # Cleanup
                del listener
                gc.collect()
            
            self.results['debounce_impact'] = {'status': 'completed'}
            
        except Exception as e:
            print(f"   ❌ Debounce analysis failed: {e}")
            self.results['debounce_impact'] = {'status': 'error', 'error': str(e)}
    
    def _create_listener(self, max_callback_workers: int = 1, debounce_ms: int = 500):
        """Create a listener with the specified configuration."""
        return StressTestListener(max_callback_workers=max_callback_workers, debounce_ms=debounce_ms)
    
    def _monitor_callback_processing(self, listener):
        """Monitor callback processing in real-time."""
        for i in range(10):
            time.sleep(0.2)
            stats = listener.get_stats()
            print(f"      Monitor {i+1}: Callbacks={stats['callback_count']}, Queue={stats['queue_size']}")
    
    def run_comprehensive_analysis(self):
        """Run comprehensive callback analysis."""
        print("🚀 Starting Callback Processing Analysis")
        print("=" * 60)
        
        analyses = [
            self.analyze_callback_processing_issue,
            self.analyze_thread_pool_bottleneck,
            self.analyze_queue_processing_issue,
            self.analyze_debounce_impact
        ]
        
        for analysis in analyses:
            try:
                analysis()
            except Exception as e:
                print(f"   ❌ Analysis failed with exception: {e}")
        
        # Print comprehensive summary
        print("\n" + "=" * 60)
        print("📋 CALLBACK ANALYSIS SUMMARY")
        print("=" * 60)
        
        for test_name, result in self.results.items():
            if result.get('status') == 'good':
                print(f"✅ {test_name}: PASSED")
            elif result.get('status') == 'poor':
                print(f"⚠️  {test_name}: ISSUES DETECTED")
            else:
                print(f"❌ {test_name}: FAILED - {result.get('error', 'Unknown error')}")
        
        # Overall assessment
        passed = sum(1 for result in self.results.values() if result.get('status') == 'good')
        total = len(self.results)
        
        print(f"\nOverall Analysis: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 No callback processing issues detected!")
        elif passed >= total * 0.5:
            print("⚠️  Minor callback processing issues detected.")
        else:
            print("❌ Significant callback processing issues detected!")

# StressTestListener class (same as in hotkey_stress_test.py)
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

if __name__ == "__main__":
    analyzer = CallbackAnalyzer()
    analyzer.run_comprehensive_analysis()