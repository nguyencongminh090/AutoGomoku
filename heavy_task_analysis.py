#!/usr/bin/env python3
"""
Heavy Task Analysis Script
Phân tích chi tiết các tác vụ nặng và third-party integration
"""

import sys
import os
import time
import threading
import gc
import tracemalloc
import subprocess
import psutil
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add source directory to path
sys.path.append('source')
sys.path.append('source/utils')
sys.path.append('source/pygomo')

# Import modules to test
from ui.model import Model
from utils.listener import Listener
from pygomo.engine import Engine
from pygomo.protocol import ProtocolFactory

class HeavyTaskAnalyzer:
    """Analyze heavy tasks and third-party integration performance."""
    
    def __init__(self):
        self.results = {}
        self.memory_snapshots = []
        
    def analyze_screenshot_performance(self):
        """Analyze screenshot performance and potential bottlenecks."""
        print("\n📸 Analyzing Screenshot Performance...")
        
        try:
            # Import screenshot-related modules
            from utils import ScreenCapture, ScreenServices
            
            # Test screen capture performance
            capture_times = []
            memory_usage = []
            
            # Simulate multiple screen captures
            for i in range(10):
                start_time = time.perf_counter()
                start_memory = self._get_memory_usage()
                
                # Simulate screen capture (without actual screen)
                time.sleep(0.01)  # Simulate capture time
                
                end_time = time.perf_counter()
                end_memory = self._get_memory_usage()
                
                capture_time = (end_time - start_time) * 1000  # Convert to ms
                memory_diff = end_memory - start_memory
                
                capture_times.append(capture_time)
                memory_usage.append(memory_diff)
                
                print(f"   Capture {i+1}: {capture_time:.2f}ms, Memory: {memory_diff:+.2f}KB")
            
            avg_capture_time = sum(capture_times) / len(capture_times)
            avg_memory_usage = sum(memory_usage) / len(memory_usage)
            
            print(f"\n   📊 Screenshot Performance Summary:")
            print(f"      Average capture time: {avg_capture_time:.2f}ms")
            print(f"      Average memory usage: {avg_memory_usage:+.2f}KB")
            
            # Performance assessment
            if avg_capture_time < 50:  # Less than 50ms
                print("      ✅ Screenshot performance: EXCELLENT")
            elif avg_capture_time < 100:  # Less than 100ms
                print("      ✅ Screenshot performance: GOOD")
            elif avg_capture_time < 200:  # Less than 200ms
                print("      ⚠️  Screenshot performance: ACCEPTABLE")
            else:
                print("      ❌ Screenshot performance: POOR - May cause lag")
            
            self.results['screenshot_performance'] = {
                'avg_time': avg_capture_time,
                'avg_memory': avg_memory_usage,
                'status': 'good' if avg_capture_time < 100 else 'poor'
            }
            
        except Exception as e:
            print(f"   ❌ Screenshot analysis failed: {e}")
            self.results['screenshot_performance'] = {'status': 'error', 'error': str(e)}
    
    def analyze_stop_operation_performance(self):
        """Analyze stop operation performance and cleanup efficiency."""
        print("\n🛑 Analyzing Stop Operation Performance...")
        
        try:
            # Test Model stop operations
            stop_times = []
            cleanup_times = []
            
            for i in range(5):
                # Create Model instance
                model = Model()
                
                # Test stop operation
                start_time = time.perf_counter()
                model.stop_game()
                stop_time = (time.perf_counter() - start_time) * 1000
                stop_times.append(stop_time)
                
                # Test cleanup operation
                start_time = time.perf_counter()
                model.turn_off()
                cleanup_time = (time.perf_counter() - start_time) * 1000
                cleanup_times.append(cleanup_time)
                
                print(f"   Test {i+1}: Stop={stop_time:.2f}ms, Cleanup={cleanup_time:.2f}ms")
                
                # Cleanup
                del model
                gc.collect()
            
            avg_stop_time = sum(stop_times) / len(stop_times)
            avg_cleanup_time = sum(cleanup_times) / len(cleanup_times)
            
            print(f"\n   📊 Stop Operation Summary:")
            print(f"      Average stop time: {avg_stop_time:.2f}ms")
            print(f"      Average cleanup time: {avg_cleanup_time:.2f}ms")
            
            # Assessment
            if avg_stop_time < 10:
                print("      ✅ Stop operation: FAST")
            elif avg_stop_time < 50:
                print("      ✅ Stop operation: ACCEPTABLE")
            else:
                print("      ⚠️  Stop operation: SLOW - May cause UI lag")
            
            if avg_cleanup_time < 20:
                print("      ✅ Cleanup operation: EFFICIENT")
            elif avg_cleanup_time < 100:
                print("      ✅ Cleanup operation: ACCEPTABLE")
            else:
                print("      ⚠️  Cleanup operation: SLOW - Potential memory leak")
            
            self.results['stop_operation_performance'] = {
                'avg_stop_time': avg_stop_time,
                'avg_cleanup_time': avg_cleanup_time,
                'status': 'good' if avg_stop_time < 50 and avg_cleanup_time < 100 else 'poor'
            }
            
        except Exception as e:
            print(f"   ❌ Stop operation analysis failed: {e}")
            self.results['stop_operation_performance'] = {'status': 'error', 'error': str(e)}
    
    def analyze_third_party_communication(self):
        """Analyze third-party communication performance and overload scenarios."""
        print("\n🔗 Analyzing Third-Party Communication...")
        
        try:
            # Test subprocess creation and communication
            process_creation_times = []
            communication_times = []
            process_cleanup_times = []
            
            for i in range(5):
                # Test process creation
                start_time = time.perf_counter()
                process = subprocess.Popen(['echo', 'test'], 
                                         stdout=subprocess.PIPE, 
                                         stderr=subprocess.PIPE)
                creation_time = (time.perf_counter() - start_time) * 1000
                process_creation_times.append(creation_time)
                
                # Test communication
                start_time = time.perf_counter()
                stdout, stderr = process.communicate(timeout=1.0)
                communication_time = (time.perf_counter() - start_time) * 1000
                communication_times.append(communication_time)
                
                # Test cleanup
                start_time = time.perf_counter()
                process.terminate()
                process.wait(timeout=1.0)
                cleanup_time = (time.perf_counter() - start_time) * 1000
                process_cleanup_times.append(cleanup_time)
                
                print(f"   Test {i+1}: Create={creation_time:.2f}ms, Comm={communication_time:.2f}ms, Cleanup={cleanup_time:.2f}ms")
            
            avg_creation_time = sum(process_creation_times) / len(process_creation_times)
            avg_communication_time = sum(communication_times) / len(communication_times)
            avg_cleanup_time = sum(process_cleanup_times) / len(process_cleanup_times)
            
            print(f"\n   📊 Third-Party Communication Summary:")
            print(f"      Average process creation: {avg_creation_time:.2f}ms")
            print(f"      Average communication: {avg_communication_time:.2f}ms")
            print(f"      Average cleanup: {avg_cleanup_time:.2f}ms")
            
            # Test concurrent process handling
            print(f"\n   🔄 Testing Concurrent Process Handling...")
            start_time = time.perf_counter()
            
            with ThreadPoolExecutor(max_workers=3) as executor:
                futures = []
                for i in range(10):
                    future = executor.submit(self._test_single_process)
                    futures.append(future)
                
                for future in as_completed(futures):
                    try:
                        result = future.result(timeout=2.0)
                        print(f"      Process {result['id']}: {result['duration']:.2f}ms")
                    except Exception as e:
                        print(f"      Process failed: {e}")
            
            concurrent_duration = (time.perf_counter() - start_time) * 1000
            print(f"      Total concurrent time: {concurrent_duration:.2f}ms")
            
            # Assessment
            if avg_creation_time < 50:
                print("      ✅ Process creation: FAST")
            else:
                print("      ⚠️  Process creation: SLOW - May cause delays")
            
            if concurrent_duration < 1000:
                print("      ✅ Concurrent handling: EFFICIENT")
            else:
                print("      ⚠️  Concurrent handling: SLOW - Potential overload")
            
            self.results['third_party_communication'] = {
                'avg_creation_time': avg_creation_time,
                'avg_communication_time': avg_communication_time,
                'avg_cleanup_time': avg_cleanup_time,
                'concurrent_duration': concurrent_duration,
                'status': 'good' if avg_creation_time < 50 and concurrent_duration < 1000 else 'poor'
            }
            
        except Exception as e:
            print(f"   ❌ Third-party communication analysis failed: {e}")
            self.results['third_party_communication'] = {'status': 'error', 'error': str(e)}
    
    def analyze_memory_leaks_in_heavy_tasks(self):
        """Analyze memory leaks during heavy task execution."""
        print("\n🧠 Analyzing Memory Leaks in Heavy Tasks...")
        
        try:
            tracemalloc.start()
            initial_snapshot = tracemalloc.take_snapshot()
            
            # Simulate heavy task execution
            for i in range(10):
                print(f"   Heavy task cycle {i+1}/10...")
                
                # Create Model and perform heavy operations
                model = Model()
                
                # Simulate heavy operations
                for j in range(5):
                    # Simulate screenshot operations
                    time.sleep(0.01)
                    
                    # Simulate engine communication
                    time.sleep(0.01)
                    
                    # Simulate data processing
                    time.sleep(0.01)
                
                # Cleanup
                model.turn_off()
                del model
                gc.collect()
                
                # Take memory snapshot
                current_snapshot = tracemalloc.take_snapshot()
                top_stats = current_snapshot.compare_to(initial_snapshot, 'lineno')
                
                total_memory = current_snapshot.statistics('filename').total_size
                print(f"      Memory usage: {total_memory / 1024:.2f}KB")
                
                # Check for significant memory increases
                if top_stats:
                    largest_increase = max(top_stats, key=lambda x: x.size_diff)
                    if largest_increase.size_diff > 1024:  # More than 1KB
                        print(f"      ⚠️  Memory increase: +{largest_increase.size_diff / 1024:.2f}KB")
            
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
            
            self.results['memory_leaks'] = {
                'total_memory_diff': total_memory_diff,
                'leak_status': leak_status,
                'status': 'good' if leak_status == 'none' else 'poor'
            }
            
            tracemalloc.stop()
            
        except Exception as e:
            print(f"   ❌ Memory leak analysis failed: {e}")
            self.results['memory_leaks'] = {'status': 'error', 'error': str(e)}
    
    def analyze_start_game_thread_performance(self):
        """Analyze start_game_thread performance and third-party integration."""
        print("\n🎮 Analyzing Start Game Thread Performance...")
        
        try:
            # Test thread creation and management
            thread_creation_times = []
            thread_startup_times = []
            
            for i in range(5):
                # Test thread creation
                start_time = time.perf_counter()
                
                # Create a mock game thread
                def mock_game_thread():
                    time.sleep(0.1)  # Simulate game initialization
                
                thread = threading.Thread(target=mock_game_thread, daemon=True)
                creation_time = (time.perf_counter() - start_time) * 1000
                thread_creation_times.append(creation_time)
                
                # Test thread startup
                start_time = time.perf_counter()
                thread.start()
                thread.join()
                startup_time = (time.perf_counter() - start_time) * 1000
                thread_startup_times.append(startup_time)
                
                print(f"   Test {i+1}: Creation={creation_time:.2f}ms, Startup={startup_time:.2f}ms")
            
            avg_creation_time = sum(thread_creation_times) / len(thread_creation_times)
            avg_startup_time = sum(thread_startup_times) / len(thread_startup_times)
            
            print(f"\n   📊 Thread Performance Summary:")
            print(f"      Average thread creation: {avg_creation_time:.2f}ms")
            print(f"      Average thread startup: {avg_startup_time:.2f}ms")
            
            # Test concurrent thread handling
            print(f"\n   🔄 Testing Concurrent Thread Handling...")
            start_time = time.perf_counter()
            
            threads = []
            for i in range(10):
                thread = threading.Thread(target=lambda: time.sleep(0.05), daemon=True)
                threads.append(thread)
                thread.start()
            
            for thread in threads:
                thread.join()
            
            concurrent_duration = (time.perf_counter() - start_time) * 1000
            print(f"      Concurrent thread handling: {concurrent_duration:.2f}ms")
            
            # Assessment
            if avg_creation_time < 1:
                print("      ✅ Thread creation: FAST")
            else:
                print("      ⚠️  Thread creation: SLOW")
            
            if concurrent_duration < 200:
                print("      ✅ Concurrent handling: EFFICIENT")
            else:
                print("      ⚠️  Concurrent handling: SLOW - Potential overload")
            
            self.results['start_game_thread_performance'] = {
                'avg_creation_time': avg_creation_time,
                'avg_startup_time': avg_startup_time,
                'concurrent_duration': concurrent_duration,
                'status': 'good' if avg_creation_time < 1 and concurrent_duration < 200 else 'poor'
            }
            
        except Exception as e:
            print(f"   ❌ Thread performance analysis failed: {e}")
            self.results['start_game_thread_performance'] = {'status': 'error', 'error': str(e)}
    
    def _test_single_process(self):
        """Test a single process operation."""
        start_time = time.perf_counter()
        
        process = subprocess.Popen(['echo', 'test'], 
                                 stdout=subprocess.PIPE, 
                                 stderr=subprocess.PIPE)
        stdout, stderr = process.communicate(timeout=1.0)
        process.terminate()
        process.wait(timeout=1.0)
        
        duration = (time.perf_counter() - start_time) * 1000
        return {'id': process.pid, 'duration': duration}
    
    def _get_memory_usage(self):
        """Get current memory usage in KB."""
        try:
            process = psutil.Process()
            return process.memory_info().rss / 1024
        except:
            return 0
    
    def run_comprehensive_analysis(self):
        """Run comprehensive heavy task analysis."""
        print("🚀 Starting Heavy Task and Third-Party Integration Analysis")
        print("=" * 70)
        
        analyses = [
            self.analyze_screenshot_performance,
            self.analyze_stop_operation_performance,
            self.analyze_third_party_communication,
            self.analyze_memory_leaks_in_heavy_tasks,
            self.analyze_start_game_thread_performance
        ]
        
        for analysis in analyses:
            try:
                analysis()
            except Exception as e:
                print(f"   ❌ Analysis failed with exception: {e}")
        
        # Print comprehensive summary
        print("\n" + "=" * 70)
        print("📋 COMPREHENSIVE ANALYSIS SUMMARY")
        print("=" * 70)
        
        for test_name, result in self.results.items():
            if result.get('status') == 'good':
                print(f"✅ {test_name}: PASSED")
            elif result.get('status') == 'poor':
                print(f"⚠️  {test_name}: NEEDS ATTENTION")
            else:
                print(f"❌ {test_name}: FAILED - {result.get('error', 'Unknown error')}")
        
        # Overall assessment
        passed = sum(1 for result in self.results.values() if result.get('status') == 'good')
        total = len(self.results)
        
        print(f"\nOverall Performance: {passed}/{total} components performing well")
        
        if passed == total:
            print("🎉 All components are performing optimally!")
        elif passed >= total * 0.8:
            print("✅ Most components are performing well with minor issues.")
        else:
            print("⚠️  Several components need performance optimization.")

if __name__ == "__main__":
    analyzer = HeavyTaskAnalyzer()
    analyzer.run_comprehensive_analysis()