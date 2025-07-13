"""
Functional version of win checking algorithm
"""

def search_win(data):
    """
    Check if there's a winning pattern in the given data.
    
    Args:
        data: List of [x, y] coordinates
        
    Returns:
        bool: True if winning pattern found, False otherwise
    """
    if not data:
        return False
        
    # Direction vectors: right, down, diagonal-down-right, diagonal-up-right
    directions = [(1, 0), (0, 1), (1, 1), (1, -1)]
    
    for point in data:
        x, y = point
        
        for dx, dy in directions:
            # Check if we can form a line of 5 consecutive points
            consecutive_points = [
                [x + dx * i, y + dy * i] for i in range(1, 5)
            ]
            
            # Check if all consecutive points exist in data
            if all(pt in data for pt in consecutive_points):
                # Check boundaries - make sure line doesn't extend beyond 5
                before_point = [x - dx, y - dy]
                after_point = [x + dx * 5, y + dy * 5]
                
                if before_point not in data and after_point not in data:
                    return True
    
    return False


def is_win(moves):
    """
    Check if either player has won based on the move sequence.
    
    Args:
        moves: List of moves (each move should have a to_num attribute or be a coordinate)
        
    Returns:
        bool: True if either player has won, False otherwise
    """
    if not moves:
        return False
        
    # Extract coordinates from moves
    if hasattr(moves[0], 'to_num'):
        data = [move.to_num for move in moves]
    else:
        data = moves
    
    # Split moves into two players (even indices = player 1, odd indices = player 2)
    player1_moves = data[::2]  # Even indices
    player2_moves = data[1::2]  # Odd indices
    
    # Check if either player has won
    return search_win(player1_moves) or search_win(player2_moves)


# Alternative functional approach with higher-order functions
def check_direction(data, point, direction):
    """
    Check if a winning line exists starting from point in given direction.
    
    Args:
        data: List of coordinates
        point: Starting point [x, y]
        direction: Direction vector (dx, dy)
        
    Returns:
        bool: True if winning line found
    """
    x, y = point
    dx, dy = direction
    
    # Generate consecutive points
    consecutive = [[x + dx * i, y + dy * i] for i in range(1, 5)]
    
    # Check if all consecutive points exist
    if not all(pt in data for pt in consecutive):
        return False
    
    # Check boundaries
    before = [x - dx, y - dy]
    after = [x + dx * 5, y + dy * 5]
    
    return before not in data and after not in data


def search_win_functional(data):
    """
    Functional version using higher-order functions.
    """
    if not data:
        return False
        
    directions = [(1, 0), (0, 1), (1, 1), (1, -1)]
    
    return any(
        check_direction(data, point, direction)
        for point in data
        for direction in directions
    )


def is_win_functional(moves):
    """
    Functional version of win checking.
    """
    if not moves:
        return False
        
    # Extract coordinates
    data = [move.to_num if hasattr(move, 'to_num') else move for move in moves]
    
    # Check both players
    return any(
        search_win_functional(data[start::2])
        for start in [0, 1]
    )


# Example usage and test
if __name__ == "__main__":
    # Test data - winning pattern
    test_moves = [
        [0, 0], [1, 0], [0, 1], [1, 1], [0, 2], [1, 2], [0, 3], [1, 3], [0, 4], [3, 5]
    ]
    
    print("Testing win check:")
    print(f"Result: {is_win(test_moves)}")
    print(f"Functional result: {is_win_functional(test_moves)}")