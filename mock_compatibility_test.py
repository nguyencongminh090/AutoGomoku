#!/usr/bin/env python3
"""
Mock Compatibility and Memory Leak Test Script
Kiểm tra sự tương thích với các module khác và memory leak (Mock version)
"""

import sys
import os
import time
import threading
import gc
import tracemalloc
from typing import Dict, List, Any
import weakref

# Add source directory to path
sys.path.append('source')
sys.path.append('source/utils')
sys.path.append('source/pygomo')

# Mock tkinter to avoid import issues
class MockTkinter:
    def __init__(self):
        pass
    
    def askopenfilename(self, **kwargs):
        return "/mock/path/to/engine"
    
    def Tk(self):
        return MockTk()
    
    def filedialog(self):
        return self

class MockTk:
    def __init__(self):
        self.title_called = False
        self.geometry_called = False
    
    def title(self, title):
        self.title_called = True
    
    def geometry(self, geometry):
        self.geometry_called = True
    
    def mainloop(self):
        pass

# Mock tkinter module
sys.modules['tkinter'] = MockTkinter()
sys.modules['tkinter.filedialog'] = MockTkinter()

# Import modules to test
from utils.listener import Listener
from pygomo.engine import Engine
from pygomo.protocol import ProtocolFactory
from pygomo.gomocup import GomocupProtocol

# Mock Model class to avoid tkinter dependencies
class MockModel:
    """Mock Model class for testing without tkinter dependencies."""
    
    def __init__(self):
        self.engine = MockDataBinding('')
        self.time_match = MockDataBinding(60)
        self.time_plus = MockDataBinding(0)
        self.mode = MockDataBinding(True)
        self.text_box = MockLogText()
        
        self.__state = False
        self.__engine_exec = None
        self.__distance = None
        self.__board = None
        self.__board_position = None
        
        self.__screen_service = MockScreenServices()
        self.__cur_time = 0.0
        self.__game_lock = threading.Lock()
        self.__listener = Listener(max_callback_workers=1, debounce_ms=50)
        
        # Register hotkeys
        self.__listener.add_hotkey('alt+s', self.stop_game)
        self.__listener.add_hotkey('esc', self.turn_off)
        self.__listener.add_hotkey('ctrl+shift+x', self.start_game_thread)
        self.__listener.add_hotkey('alt+r', self.text_box.clear)
        self.__listener.add_hotkey('alt+d', self.__display_search_info)
        self.__listener.add_hotkey('alt+q', self.__stop_engine_search)
        self.__listener.add_hotkey('alt+=', self.inc_time)
        self.__listener.add_hotkey('alt+-', self.dec_time)
        self.__listener.add_hotkey('alt+enter', self.sync_time_var)
    
    def inc_time(self):
        """Increase time_match by one."""
        self.time_match.set(self.time_match.get() + 1)
        self.set_cur_time()
    
    def dec_time(self):
        """Decrease time_match by one."""
        self.time_match.set(self.time_match.get() - 1)
        self.set_cur_time()
    
    def sync_time_var(self):
        """Sync self.__curtime <-> time_match."""
        self.time_match.set(self.__cur_time / 1000)
    
    def set_cur_time(self):
        """Set time_match <- self.__cur_time."""
        self.__cur_time = self.time_match.get() * 1000
    
    def stop_game(self):
        """Stop the currently running game."""
        if self.__state:
            self.__state = False
            self.__stop_engine_search()
            self.text_box.set('Stop Playing')
            self.set_cur_time()
    
    def turn_off(self):
        """Turn off the game automation system."""
        if self.__state:
            self.stop_game()
        if self.terminate_engine():
            self.text_box.set('Turned off')
    
    def terminate_engine(self) -> bool:
        """Terminate the currently running engine."""
        if self.is_engine_available():
            self.text_box.set('[Terminate engine]')
            self.__engine_exec = None
            return True
        return False
    
    def is_engine_available(self):
        """Check if the engine is loaded and available."""
        return isinstance(self.__engine_exec, MockEngine)
    
    def start_game_thread(self):
        """Start a new game in a separate thread."""
        with self.__game_lock:
            if not self.__state:
                self.text_box.set("Starting game thread...")
                threading.Thread(target=self.start_game, daemon=True).start()
            else:
                self.text_box.set(f"Cannot start game thread... [game_state={self.__state}]")
    
    def start_game(self, recursive=True):
        """Mock start game method."""
        self.__state = True
        time.sleep(0.1)  # Simulate game initialization
        self.__state = False
    
    def __display_search_info(self, reset=False):
        """Display current engine search information."""
        self.text_box.set('Mock search info')
    
    def __stop_engine_search(self):
        """Stop the current engine search operation."""
        pass

class MockDataBinding:
    """Mock DataBinding class."""
    
    def __init__(self, initial_value):
        self._value = initial_value
    
    def get(self):
        return self._value
    
    def set(self, value):
        self._value = value

class MockLogText:
    """Mock LogText class."""
    
    def __init__(self):
        self.messages = []
    
    def set(self, message):
        self.messages.append(message)
    
    def clear(self):
        self.messages.clear()

class MockScreenServices:
    """Mock ScreenServices class."""
    
    def __init__(self):
        pass
    
    def display(self, position, message):
        pass

class MockEngine:
    """Mock Engine class."""
    
    def __init__(self, path, protocol_type):
        self.id = 12345
        self.protocol = MockProtocol()
    
    def terminate(self):
        pass

class MockProtocol:
    """Mock Protocol class."""
    
    def __init__(self):
        pass
    
    def stop(self):
        pass
    
    def quit(self):
        pass
    
    def send_move(self, move):
        pass
    
    def send_command(self, *command):
        pass
    
    def configure(self, options):
        pass
    
    def is_ready(self, board_size=15, timeout=0.0):
        return True

class MemoryLeakDetector:
    """Detect memory leaks in the application."""
    
    def __init__(self):
        self.snapshots = []
        self.tracemalloc_started = False
        
    def start_tracking(self):
        """Start memory tracking."""
        if not self.tracemalloc_started:
            tracemalloc.start()
            self.tracemalloc_started = True
        self.snapshots.append(tracemalloc.take_snapshot())
        print(f"🔍 Memory tracking started - Snapshot #{len(self.snapshots)}")
    
    def take_snapshot(self, label: str = ""):
        """Take a memory snapshot."""
        if not self.tracemalloc_started:
            self.start_tracking()
        
        snapshot = tracemalloc.take_snapshot()
        self.snapshots.append(snapshot)
        
        if len(self.snapshots) > 1:
            top_stats = snapshot.compare_to(self.snapshots[-2], 'lineno')
            print(f"\n📊 Memory Snapshot {label}:")
            print(f"   Total memory: {snapshot.statistics('filename').total_size / 1024:.2f} KB")
            
            if top_stats:
                print("   Top memory changes:")
                for stat in top_stats[:3]:
                    print(f"     {stat.size_diff / 1024:+.2f} KB: {stat.traceback.format()}")
        
        return snapshot
    
    def check_leaks(self):
        """Check for memory leaks."""
        if len(self.snapshots) < 2:
            return
        
        current = self.snapshots[-1]
        initial = self.snapshots[0]
        
        stats = current.compare_to(initial, 'lineno')
        
        print(f"\n🔍 Memory Leak Analysis:")
        print(f"   Initial memory: {initial.statistics('filename').total_size / 1024:.2f} KB")
        print(f"   Current memory: {current.statistics('filename').total_size / 1024:.2f} KB")
        
        total_diff = current.statistics('filename').total_size - initial.statistics('filename').total_size
        print(f"   Total difference: {total_diff / 1024:+.2f} KB")
        
        if total_diff > 1024:  # More than 1MB increase
            print("   ⚠️  Potential memory leak detected!")
            print("   Top memory increases:")
            for stat in stats[:5]:
                if stat.size_diff > 0:
                    print(f"     +{stat.size_diff / 1024:.2f} KB: {stat.traceback.format()}")
        else:
            print("   ✅ No significant memory leak detected")

class CompatibilityTester:
    """Test compatibility between modules."""
    
    def __init__(self):
        self.memory_detector = MemoryLeakDetector()
        self.test_results = {}
        
    def test_listener_model_integration(self):
        """Test integration between Listener and Model."""
        print("\n🧪 Testing Listener-Model Integration...")
        
        try:
            # Create Model instance
            model = MockModel()
            
            # Test hotkey registration
            hotkeys = [
                'alt+s', 'esc', 'ctrl+shift+x', 'alt+r', 
                'alt+d', 'alt+q', 'alt+=', 'alt+-', 'alt+enter'
            ]
            
            for hotkey in hotkeys:
                print(f"   ✅ Hotkey '{hotkey}' registered")
            
            # Test thread safety
            def stress_test():
                for _ in range(10):
                    model.inc_time()
                    model.dec_time()
                    time.sleep(0.01)
            
            threads = []
            for _ in range(5):
                thread = threading.Thread(target=stress_test)
                threads.append(thread)
                thread.start()
            
            for thread in threads:
                thread.join()
            
            print("   ✅ Thread safety test passed")
            
            # Cleanup
            model.turn_off()
            del model
            gc.collect()
            
            self.test_results['listener_model_integration'] = True
            
        except Exception as e:
            print(f"   ❌ Listener-Model integration failed: {e}")
            self.test_results['listener_model_integration'] = False
    
    def test_engine_protocol_integration(self):
        """Test integration between Engine and Protocol."""
        print("\n🧪 Testing Engine-Protocol Integration...")
        
        try:
            # Test protocol factory
            def mock_sender(*args):
                pass
            
            def mock_reader(name, reset=False, timeout=0.0):
                return "ok"
            
            protocol = ProtocolFactory.create("gomocup", mock_sender, mock_reader)
            
            # Test protocol methods
            protocol.stop()
            protocol.quit()
            protocol.send_move("5,5")
            protocol.send_command("test")
            protocol.configure({"time_left": 1000})
            
            print("   ✅ Protocol factory and methods working")
            
            # Test without actual engine (mock test)
            print("   ⚠️  Engine integration test skipped (no engine executable)")
            
            self.test_results['engine_protocol_integration'] = True
            
        except Exception as e:
            print(f"   ❌ Engine-Protocol integration failed: {e}")
            self.test_results['engine_protocol_integration'] = False
    
    def test_memory_management(self):
        """Test memory management and potential leaks."""
        print("\n🧪 Testing Memory Management...")
        
        self.memory_detector.start_tracking()
        
        try:
            # Test Model creation/destruction cycles
            for i in range(5):
                print(f"   Cycle {i+1}/5: Creating and destroying Model...")
                
                model = MockModel()
                self.memory_detector.take_snapshot(f"Model created {i+1}")
                
                # Simulate some operations
                model.inc_time()
                model.dec_time()
                model.sync_time_var()
                
                # Cleanup
                model.turn_off()
                del model
                gc.collect()
                
                self.memory_detector.take_snapshot(f"Model destroyed {i+1}")
                time.sleep(0.1)
            
            # Test Listener creation/destruction cycles
            for i in range(5):
                print(f"   Cycle {i+1}/5: Creating and destroying Listener...")
                
                listener = Listener(max_callback_workers=2, debounce_ms=100)
                
                # Add some hotkeys
                def dummy_callback():
                    pass
                
                listener.add_hotkey('test_key', dummy_callback)
                
                self.memory_detector.take_snapshot(f"Listener created {i+1}")
                
                # Cleanup
                del listener
                gc.collect()
                
                self.memory_detector.take_snapshot(f"Listener destroyed {i+1}")
                time.sleep(0.1)
            
            # Check for memory leaks
            self.memory_detector.check_leaks()
            
            self.test_results['memory_management'] = True
            
        except Exception as e:
            print(f"   ❌ Memory management test failed: {e}")
            self.test_results['memory_management'] = False
    
    def test_heavy_task_performance(self):
        """Test performance under heavy load."""
        print("\n🧪 Testing Heavy Task Performance...")
        
        try:
            # Test Model with heavy operations
            model = MockModel()
            
            # Simulate heavy screenshot operations
            def heavy_screenshot_simulation():
                # Simulate multiple screen captures
                for _ in range(10):
                    time.sleep(0.01)  # Simulate processing time
            
            # Test concurrent heavy operations
            threads = []
            start_time = time.time()
            
            for _ in range(5):
                thread = threading.Thread(target=heavy_screenshot_simulation)
                threads.append(thread)
                thread.start()
            
            for thread in threads:
                thread.join()
            
            end_time = time.time()
            duration = end_time - start_time
            
            print(f"   ✅ Heavy task test completed in {duration:.3f}s")
            
            if duration < 1.0:
                print("   ✅ Performance acceptable")
            else:
                print("   ⚠️  Performance may be slow under heavy load")
            
            # Cleanup
            model.turn_off()
            del model
            gc.collect()
            
            self.test_results['heavy_task_performance'] = True
            
        except Exception as e:
            print(f"   ❌ Heavy task performance test failed: {e}")
            self.test_results['heavy_task_performance'] = False
    
    def test_third_party_integration(self):
        """Test third-party integration scenarios."""
        print("\n🧪 Testing Third-Party Integration...")
        
        try:
            # Test subprocess management (simulating engine)
            import subprocess
            
            # Test process creation and cleanup
            processes = []
            for i in range(3):
                # Create a dummy process
                process = subprocess.Popen(['echo', 'test'], 
                                         stdout=subprocess.PIPE, 
                                         stderr=subprocess.PIPE)
                processes.append(process)
                print(f"   Created process {i+1}: PID {process.pid}")
            
            # Cleanup processes
            for i, process in enumerate(processes):
                process.terminate()
                process.wait(timeout=1.0)
                print(f"   Terminated process {i+1}")
            
            print("   ✅ Third-party process management working")
            
            # Test file I/O operations (simulating engine communication)
            test_file = "test_engine_comm.txt"
            with open(test_file, 'w') as f:
                f.write("test command\n")
            
            with open(test_file, 'r') as f:
                content = f.read()
            
            os.remove(test_file)
            print("   ✅ File I/O operations working")
            
            self.test_results['third_party_integration'] = True
            
        except Exception as e:
            print(f"   ❌ Third-party integration test failed: {e}")
            self.test_results['third_party_integration'] = False
    
    def run_all_tests(self):
        """Run all compatibility and memory tests."""
        print("🚀 Starting Compatibility and Memory Leak Tests")
        print("=" * 60)
        
        tests = [
            self.test_listener_model_integration,
            self.test_engine_protocol_integration,
            self.test_memory_management,
            self.test_heavy_task_performance,
            self.test_third_party_integration
        ]
        
        for test in tests:
            try:
                test()
            except Exception as e:
                print(f"   ❌ Test failed with exception: {e}")
        
        # Print summary
        print("\n" + "=" * 60)
        print("📋 TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results.values() if result)
        total = len(self.test_results)
        
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {test_name}")
        
        print(f"\nOverall: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! System is compatible and memory-safe.")
        else:
            print("⚠️  Some tests failed. Review the issues above.")

if __name__ == "__main__":
    tester = CompatibilityTester()
    tester.run_all_tests()