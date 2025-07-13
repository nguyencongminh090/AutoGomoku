"""
Benchmark script to compare Python and C++ implementations of win checking.

To run this benchmark:
1. First compile the C++ extension:
   python setup.py build_ext --inplace

2. Then run the benchmark:
   python benchmark.py
"""

import time
import random
import statistics
from typing import List, Tuple, Callable

# Import Python implementation
from win_check import is_win, search_win, is_win_functional, search_win_functional

# Import C++ implementation
try:
    import win_check_cpp
    cpp_available = True
except ImportError:
    print("C++ module not available. Please compile it first with:")
    print("python setup.py build_ext --inplace")
    cpp_available = False


def generate_test_data(size: int, win_probability: float = 0.3) -> List[List[int]]:
    """
    Generate test data for benchmarking.
    
    Args:
        size: Number of moves to generate
        win_probability: Probability of generating a winning pattern
        
    Returns:
        List of coordinate pairs
    """
    moves = []
    
    if random.random() < win_probability and size >= 9:
        # Generate a winning pattern
        start_x, start_y = random.randint(0, 10), random.randint(0, 10)
        direction = random.choice([(1, 0), (0, 1), (1, 1), (1, -1)])
        
        # Add winning moves for player 1 (even indices)
        for i in range(5):
            moves.append([start_x + direction[0] * i, start_y + direction[1] * i])
            if len(moves) < size:
                # Add a random move for player 2
                moves.append([random.randint(0, 20), random.randint(0, 20)])
    
    # Fill remaining moves with random coordinates
    while len(moves) < size:
        moves.append([random.randint(0, 20), random.randint(0, 20)])
    
    return moves


def benchmark_function(func: Callable, test_cases: List[List[List[int]]], 
                      num_iterations: int = 100) -> Tuple[float, float]:
    """
    Benchmark a function with given test cases.
    
    Args:
        func: Function to benchmark
        test_cases: List of test cases
        num_iterations: Number of iterations to run
        
    Returns:
        Tuple of (mean_time, std_time) in seconds
    """
    times = []
    
    for _ in range(num_iterations):
        start_time = time.perf_counter()
        
        for test_case in test_cases:
            func(test_case)
        
        end_time = time.perf_counter()
        times.append(end_time - start_time)
    
    return statistics.mean(times), statistics.stdev(times)


def run_benchmark():
    """Run comprehensive benchmark comparing all implementations."""
    
    print("=== Win Check Algorithm Benchmark ===\n")
    
    # Generate test cases of different sizes
    test_sizes = [10, 50, 100, 500, 1000]
    test_cases_by_size = {}
    
    print("Generating test cases...")
    for size in test_sizes:
        cases = []
        for _ in range(20):  # 20 test cases per size
            cases.append(generate_test_data(size))
        test_cases_by_size[size] = cases
    
    # Define functions to benchmark
    functions = {
        "Python (original)": is_win,
        "Python (functional)": is_win_functional,
    }
    
    if cpp_available:
        functions.update({
            "C++ (standard)": win_check_cpp.is_win,
            "C++ (optimized)": win_check_cpp.is_win_optimized,
        })
    
    print("\nRunning benchmarks...\n")
    
    # Run benchmarks
    results = {}
    
    for size in test_sizes:
        print(f"Testing with {size} moves per test case:")
        results[size] = {}
        
        for name, func in functions.items():
            try:
                mean_time, std_time = benchmark_function(func, test_cases_by_size[size])
                results[size][name] = (mean_time, std_time)
                print(f"  {name:20}: {mean_time:.6f} ± {std_time:.6f} seconds")
            except Exception as e:
                print(f"  {name:20}: ERROR - {e}")
                results[size][name] = (float('inf'), float('inf'))
        
        print()
    
    # Print summary
    print("=== Performance Summary ===\n")
    
    for size in test_sizes:
        print(f"Size {size}:")
        size_results = results[size]
        
        # Find fastest implementation
        fastest_time = min(time for time, _ in size_results.values() if time != float('inf'))
        fastest_name = next(name for name, (time, _) in size_results.items() if time == fastest_time)
        
        print(f"  Fastest: {fastest_name} ({fastest_time:.6f}s)")
        
        # Show speedup ratios
        for name, (time, _) in size_results.items():
            if time != float('inf') and time != fastest_time:
                speedup = time / fastest_time
                print(f"  {name}: {speedup:.2f}x slower")
        
        print()
    
    # Memory usage test
    print("=== Memory Usage Test ===")
    test_large_data(10000)


def test_large_data(size: int):
    """Test with large datasets to evaluate memory usage."""
    print(f"\nTesting with {size} moves...")
    
    large_test_case = generate_test_data(size, win_probability=0.1)
    
    functions = {
        "Python (original)": is_win,
        "Python (functional)": is_win_functional,
    }
    
    if cpp_available:
        functions.update({
            "C++ (standard)": win_check_cpp.is_win,
            "C++ (optimized)": win_check_cpp.is_win_optimized,
        })
    
    for name, func in functions.items():
        try:
            start_time = time.perf_counter()
            result = func(large_test_case)
            end_time = time.perf_counter()
            
            print(f"  {name:20}: {end_time - start_time:.6f}s (result: {result})")
        except Exception as e:
            print(f"  {name:20}: ERROR - {e}")


def test_correctness():
    """Test that all implementations produce the same results."""
    print("=== Correctness Test ===\n")
    
    # Test cases with known results
    test_cases = [
        # No win
        ([[0, 0], [1, 0], [0, 1], [1, 1]], False),
        # Horizontal win for player 1
        ([[0, 0], [1, 0], [0, 1], [1, 1], [0, 2], [1, 2], [0, 3], [1, 3], [0, 4]], True),
        # Vertical win for player 2
        ([[0, 0], [1, 0], [0, 1], [1, 1], [2, 0], [1, 2], [2, 1], [1, 3], [2, 2], [1, 4]], True),
        # Diagonal win
        ([[0, 0], [1, 0], [1, 1], [2, 0], [2, 2], [3, 0], [3, 3], [4, 0], [4, 4]], True),
        # Empty case
        ([], False),
    ]
    
    functions = {
        "Python (original)": is_win,
        "Python (functional)": is_win_functional,
    }
    
    if cpp_available:
        functions.update({
            "C++ (standard)": win_check_cpp.is_win,
            "C++ (optimized)": win_check_cpp.is_win_optimized,
        })
    
    all_passed = True
    
    for i, (test_input, expected) in enumerate(test_cases):
        print(f"Test case {i + 1}: {test_input[:3]}{'...' if len(test_input) > 3 else ''}")
        
        for name, func in functions.items():
            try:
                result = func(test_input)
                status = "PASS" if result == expected else "FAIL"
                print(f"  {name:20}: {result} ({status})")
                
                if result != expected:
                    all_passed = False
            except Exception as e:
                print(f"  {name:20}: ERROR - {e}")
                all_passed = False
        
        print()
    
    print(f"Overall correctness: {'PASS' if all_passed else 'FAIL'}")
    return all_passed


if __name__ == "__main__":
    # Run correctness test first
    if test_correctness():
        print("\n" + "="*50)
        # Run performance benchmark
        run_benchmark()
    else:
        print("Correctness test failed. Please fix implementations before benchmarking.")