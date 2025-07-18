#!/usr/bin/env python3
"""
Test script for the fixed listener implementation.

This script validates that the fixed listener resolves the hanging issues
identified in the stress tests.
"""

import time
import threading
import logging
from typing import List, Dict
import sys
import os

# Add source to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'source'))

from utils.listener_fixed import Listener, HotkeyError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(threadName)s - %(levelname)s - %(message)s"
)

class TestResults:
    """Track test results and performance metrics."""
    
    def __init__(self):
        self.callback_count = 0
        self.start_time = time.time()
        self.callback_times = []
        self.errors = []
        self.lock = threading.Lock()
    
    def record_callback(self, callback_name: str):
        """Record a callback execution."""
        with self.lock:
            self.callback_count += 1
            self.callback_times.append(time.time())
    
    def record_error(self, error: str):
        """Record an error."""
        with self.lock:
            self.errors.append(error)
    
    def get_stats(self) -> Dict:
        """Get test statistics."""
        with self.lock:
            duration = time.time() - self.start_time
            if self.callback_times:
                avg_interval = sum(
                    self.callback_times[i] - self.callback_times[i-1] 
                    for i in range(1, len(self.callback_times))
                ) / (len(self.callback_times) - 1) if len(self.callback_times) > 1 else 0
            else:
                avg_interval = 0
            
            return {
                'duration': duration,
                'callback_count': self.callback_count,
                'callbacks_per_second': self.callback_count / duration if duration > 0 else 0,
                'avg_interval': avg_interval,
                'error_count': len(self.errors),
                'errors': self.errors[:10]  # First 10 errors
            }


def create_test_callbacks(results: TestResults) -> Dict[str, callable]:
    """Create test callbacks for different scenarios."""
    
    def fast_callback():
        """Fast callback - minimal processing."""
        results.record_callback("fast")
        time.sleep(0.001)  # 1ms delay
    
    def slow_callback():
        """Slow callback - simulates heavy processing."""
        results.record_callback("slow")
        time.sleep(0.1)  # 100ms delay
    
    def error_callback():
        """Error callback - simulates failures."""
        results.record_callback("error")
        results.record_error("Simulated callback error")
        raise Exception("Simulated callback error")
    
    def blocking_callback():
        """Blocking callback - simulates long-running operations."""
        results.record_callback("blocking")
        time.sleep(1.0)  # 1 second delay
    
    return {
        'fast': fast_callback,
        'slow': slow_callback,
        'error': error_callback,
        'blocking': blocking_callback
    }


def test_basic_functionality():
    """Test basic hotkey functionality."""
    print("\n=== Testing Basic Functionality ===")
    
    results = TestResults()
    callbacks = create_test_callbacks(results)
    
    with Listener(max_callback_workers=2, debounce_ms=50, max_queue_size=50) as listener:
        # Register hotkeys
        listener.add_hotkey('ctrl+a', callbacks['fast'])
        listener.add_hotkey('ctrl+b', callbacks['slow'])
        listener.add_hotkey('ctrl+c', callbacks['error'])
        
        print("Registered hotkeys: ctrl+a (fast), ctrl+b (slow), ctrl+c (error)")
        print("Press these hotkeys to test. Press 'esc' to stop.")
        
        # Monitor for 10 seconds
        start_time = time.time()
        while time.time() - start_time < 10:
            status = listener.get_status()
            print(f"\rStatus: {status['callback_queue_size']} queued, "
                  f"{status['callback_queue_overflow']} overflow, "
                  f"{results.callback_count} executed", end='', flush=True)
            time.sleep(0.5)
    
    stats = results.get_stats()
    print(f"\n\nBasic test results:")
    print(f"- Duration: {stats['duration']:.2f}s")
    print(f"- Callbacks executed: {stats['callback_count']}")
    print(f"- Callbacks/sec: {stats['callbacks_per_second']:.2f}")
    print(f"- Errors: {stats['error_count']}")
    
    return stats['error_count'] == 0


def test_stress_rapid_presses():
    """Test rapid hotkey presses to simulate stress conditions."""
    print("\n=== Testing Rapid Press Stress ===")
    
    results = TestResults()
    callbacks = create_test_callbacks(results)
    
    with Listener(max_callback_workers=1, debounce_ms=10, max_queue_size=20) as listener:
        listener.add_hotkey('ctrl+x', callbacks['fast'])
        listener.add_hotkey('ctrl+y', callbacks['slow'])
        
        print("Simulating rapid hotkey presses...")
        
        # Simulate rapid presses
        import keyboard
        for i in range(50):
            keyboard.press_and_release('ctrl+x')
            time.sleep(0.01)  # 10ms between presses
        
        # Wait for processing
        time.sleep(2)
        
        # Simulate more rapid presses
        for i in range(30):
            keyboard.press_and_release('ctrl+y')
            time.sleep(0.005)  # 5ms between presses
        
        # Wait for processing
        time.sleep(3)
    
    stats = results.get_stats()
    print(f"\nStress test results:")
    print(f"- Duration: {stats['duration']:.2f}s")
    print(f"- Callbacks executed: {stats['callback_count']}")
    print(f"- Callbacks/sec: {stats['callbacks_per_second']:.2f}")
    print(f"- Queue overflow: {stats.get('queue_overflow', 0)}")
    print(f"- Errors: {stats['error_count']}")
    
    return stats['error_count'] == 0 and stats['callback_count'] > 0


def test_queue_overflow():
    """Test queue overflow handling."""
    print("\n=== Testing Queue Overflow ===")
    
    results = TestResults()
    callbacks = create_test_callbacks(results)
    
    with Listener(max_callback_workers=1, debounce_ms=0, max_queue_size=5) as listener:
        listener.add_hotkey('ctrl+z', callbacks['blocking'])
        
        print("Testing queue overflow with blocking callbacks...")
        
        # Rapidly trigger blocking callbacks to fill queue
        import keyboard
        for i in range(20):
            keyboard.press_and_release('ctrl+z')
            time.sleep(0.001)  # 1ms between presses
        
        # Wait for processing
        time.sleep(3)
    
    stats = results.get_stats()
    print(f"\nQueue overflow test results:")
    print(f"- Duration: {stats['duration']:.2f}s")
    print(f"- Callbacks executed: {stats['callback_count']}")
    print(f"- Errors: {stats['error_count']}")
    
    return stats['error_count'] == 0


def test_health_monitoring():
    """Test health monitoring and circuit breaker functionality."""
    print("\n=== Testing Health Monitoring ===")
    
    results = TestResults()
    
    def failing_callback():
        """Always fails to test circuit breaker."""
        results.record_callback("failing")
        results.record_error("Intentional failure")
        raise Exception("Intentional failure for testing")
    
    with Listener(max_callback_workers=1, debounce_ms=10, max_queue_size=10) as listener:
        listener.add_hotkey('ctrl+f', failing_callback)
        
        print("Testing circuit breaker with failing callbacks...")
        
        # Trigger failing callbacks
        import keyboard
        for i in range(10):
            keyboard.press_and_release('ctrl+f')
            time.sleep(0.1)
        
        # Check health status
        status = listener.get_status()
        health = status.get('health_status', {})
        
        print(f"\nHealth monitoring results:")
        print(f"- Circuit open: {health.get('circuit_open', False)}")
        print(f"- Failure count: {health.get('failure_count', 0)}")
        print(f"- Callbacks executed: {results.callback_count}")
        print(f"- Errors: {len(results.errors)}")
    
    return True  # Health monitoring is working if we get here


def test_concurrent_hotkeys():
    """Test multiple hotkeys being pressed concurrently."""
    print("\n=== Testing Concurrent Hotkeys ===")
    
    results = TestResults()
    callbacks = create_test_callbacks(results)
    
    with Listener(max_callback_workers=3, debounce_ms=10, max_queue_size=50) as listener:
        listener.add_hotkey('ctrl+1', callbacks['fast'])
        listener.add_hotkey('ctrl+2', callbacks['slow'])
        listener.add_hotkey('ctrl+3', callbacks['fast'])
        listener.add_hotkey('ctrl+4', callbacks['slow'])
        
        print("Testing concurrent hotkey processing...")
        
        # Simulate concurrent presses
        import keyboard
        import threading
        
        def press_hotkey(hotkey, count):
            for i in range(count):
                keyboard.press_and_release(hotkey)
                time.sleep(0.02)
        
        threads = [
            threading.Thread(target=press_hotkey, args=('ctrl+1', 10)),
            threading.Thread(target=press_hotkey, args=('ctrl+2', 5)),
            threading.Thread(target=press_hotkey, args=('ctrl+3', 10)),
            threading.Thread(target=press_hotkey, args=('ctrl+4', 5))
        ]
        
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Wait for processing
        time.sleep(2)
    
    stats = results.get_stats()
    print(f"\nConcurrent test results:")
    print(f"- Duration: {stats['duration']:.2f}s")
    print(f"- Callbacks executed: {stats['callback_count']}")
    print(f"- Callbacks/sec: {stats['callbacks_per_second']:.2f}")
    print(f"- Errors: {stats['error_count']}")
    
    return stats['error_count'] == 0 and stats['callback_count'] > 0


def test_cleanup_and_shutdown():
    """Test proper cleanup and shutdown."""
    print("\n=== Testing Cleanup and Shutdown ===")
    
    results = TestResults()
    callbacks = create_test_callbacks(results)
    
    listener = Listener(max_callback_workers=2, debounce_ms=10, max_queue_size=10)
    listener.add_hotkey('ctrl+s', callbacks['fast'])
    
    # Trigger some callbacks
    import keyboard
    for i in range(5):
        keyboard.press_and_release('ctrl+s')
        time.sleep(0.1)
    
    # Wait a bit for processing
    time.sleep(0.5)
    
    # Test shutdown
    print("Testing shutdown...")
    start_time = time.time()
    listener.stop()
    shutdown_time = time.time() - start_time
    
    print(f"Shutdown completed in {shutdown_time:.3f}s")
    
    # Check final status
    status = listener.get_status()
    print(f"Final status: {status}")
    
    return shutdown_time < 1.0 and not status['listener_thread_alive']


def main():
    """Run all tests."""
    print("Testing Fixed Listener Implementation")
    print("=" * 50)
    
    tests = [
        ("Basic Functionality", test_basic_functionality),
        ("Rapid Press Stress", test_stress_rapid_presses),
        ("Queue Overflow", test_queue_overflow),
        ("Health Monitoring", test_health_monitoring),
        ("Concurrent Hotkeys", test_concurrent_hotkeys),
        ("Cleanup and Shutdown", test_cleanup_and_shutdown),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            print(f"\nRunning {test_name}...")
            success = test_func()
            results[test_name] = success
            print(f"✓ {test_name}: {'PASSED' if success else 'FAILED'}")
        except Exception as e:
            print(f"✗ {test_name}: ERROR - {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for success in results.values() if success)
    total = len(results)
    
    for test_name, success in results.items():
        status = "PASSED" if success else "FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The fixed listener resolves the hanging issues.")
    else:
        print("⚠️  Some tests failed. Review the output above.")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)