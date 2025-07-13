"""
Simple example showing how to use the C++ module.

This is the most straightforward way to use the compiled C++ code.
"""

def main():
    print("Loading C++ Win Check Module")
    print("=" * 40)
    
    # Step 1: Import the compiled C++ module
    try:
        import win_check_cpp
        print("✓ C++ module loaded successfully!")
    except ImportError as e:
        print("✗ Failed to load C++ module:")
        print(f"  Error: {e}")
        print("\nTo fix this:")
        print("1. Make sure you compiled the module:")
        print("   python setup.py build_ext --inplace")
        print("2. Check that the .so/.pyd file exists in the current directory")
        return
    
    # Step 2: Create test data
    print("\nCreating test data...")
    
    # Test case 1: No winner
    no_win_moves = [
        [0, 0], [1, 0],  # Player 1: (0,0), Player 2: (1,0)
        [0, 1], [1, 1],  # Player 1: (0,1), Player 2: (1,1)
        [2, 0], [2, 1],  # Player 1: (2,0), Player 2: (2,1)
    ]
    
    # Test case 2: Player 1 wins (vertical line)
    player1_wins = [
        [0, 0], [1, 0],  # Player 1: (0,0), Player 2: (1,0)
        [0, 1], [1, 1],  # Player 1: (0,1), Player 2: (1,1)
        [0, 2], [1, 2],  # Player 1: (0,2), Player 2: (1,2)
        [0, 3], [1, 3],  # Player 1: (0,3), Player 2: (1,3)
        [0, 4]           # Player 1: (0,4) - WINS!
    ]
    
    # Test case 3: Player 2 wins (horizontal line)
    player2_wins = [
        [0, 0], [1, 0],  # Player 1: (0,0), Player 2: (1,0)
        [0, 1], [1, 1],  # Player 1: (0,1), Player 2: (1,1)
        [0, 2], [1, 2],  # Player 1: (0,2), Player 2: (1,2)
        [0, 3], [1, 3],  # Player 1: (0,3), Player 2: (1,3)
        [2, 0], [1, 4],  # Player 1: (2,0), Player 2: (1,4) - WINS!
    ]
    
    # Step 3: Test the C++ functions
    print("\nTesting C++ functions:")
    
    # Method 1: Using standalone functions
    print("\n1. Using standalone functions:")
    test_cases = [
        ("No winner", no_win_moves),
        ("Player 1 wins", player1_wins),
        ("Player 2 wins", player2_wins),
    ]
    
    for description, moves in test_cases:
        result = win_check_cpp.is_win(moves)
        print(f"   {description:15}: {result}")
    
    # Method 2: Using class methods
    print("\n2. Using class methods:")
    for description, moves in test_cases:
        result = win_check_cpp.WinChecker.is_win(moves)
        print(f"   {description:15}: {result}")
    
    # Method 3: Using optimized version
    print("\n3. Using optimized version:")
    for description, moves in test_cases:
        result = win_check_cpp.is_win_optimized(moves)
        print(f"   {description:15}: {result}")
    
    # Step 4: Test individual player data
    print("\nTesting individual player data:")
    
    # Extract player 1 moves (even indices)
    player1_moves = player1_wins[::2]  # [0, 2, 4, 6, 8] -> [(0,0), (0,1), (0,2), (0,3), (0,4)]
    print(f"Player 1 moves: {player1_moves}")
    
    # Test if player 1 has winning pattern
    player1_result = win_check_cpp.search_win(player1_moves)
    print(f"Player 1 has winning pattern: {player1_result}")
    
    # Extract player 2 moves (odd indices)
    player2_moves = player2_wins[1::2]  # [1, 3, 5, 7, 9] -> [(1,0), (1,1), (1,2), (1,3), (1,4)]
    print(f"Player 2 moves: {player2_moves}")
    
    # Test if player 2 has winning pattern
    player2_result = win_check_cpp.search_win(player2_moves)
    print(f"Player 2 has winning pattern: {player2_result}")
    
    # Step 5: Performance demonstration
    print("\nPerformance demonstration:")
    
    import time
    
    # Generate larger test case
    large_moves = []
    for i in range(1000):
        large_moves.append([i % 50, (i * 3) % 50])
    
    # Time the C++ function
    start_time = time.perf_counter()
    result = win_check_cpp.is_win(large_moves)
    end_time = time.perf_counter()
    
    print(f"Processed {len(large_moves)} moves in {end_time - start_time:.6f} seconds")
    print(f"Result: {result}")
    
    # Step 6: Error handling example
    print("\nError handling:")
    
    try:
        # Test with invalid data
        invalid_moves = [[1, 2, 3]]  # Invalid format
        result = win_check_cpp.is_win(invalid_moves)
        print(f"Invalid data result: {result}")
    except Exception as e:
        print(f"Error with invalid data: {e}")
    
    try:
        # Test with empty data
        empty_moves = []
        result = win_check_cpp.is_win(empty_moves)
        print(f"Empty data result: {result}")
    except Exception as e:
        print(f"Error with empty data: {e}")
    
    print("\n" + "=" * 40)
    print("All tests completed successfully!")


if __name__ == "__main__":
    main()