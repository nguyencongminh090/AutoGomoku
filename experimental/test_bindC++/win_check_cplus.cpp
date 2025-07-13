#include <vector>
#include <algorithm>
#include <set>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

class WinChecker {
public:
    /**
     * Check if there's a winning pattern in the given data.
     * 
     * @param data Vector of coordinate pairs
     * @return true if winning pattern found, false otherwise
     */
    static bool searchWin(const std::vector<std::vector<int>>& data) {
        if (data.empty()) {
            return false;
        }
        
        // Convert to set for O(1) lookup
        std::set<std::vector<int>> dataSet(data.begin(), data.end());
        
        // Direction vectors: right, down, diagonal-down-right, diagonal-up-right
        std::vector<std::pair<int, int>> directions = {
            {1, 0}, {0, 1}, {1, 1}, {1, -1}
        };
        
        for (const auto& point : data) {
            int x = point[0];
            int y = point[1];
            
            for (const auto& dir : directions) {
                int dx = dir.first;
                int dy = dir.second;
                
                // Check if we can form a line of 5 consecutive points
                std::vector<std::vector<int>> consecutivePoints;
                for (int i = 1; i <= 4; ++i) {
                    consecutivePoints.push_back({x + dx * i, y + dy * i});
                }
                
                // Check if all consecutive points exist in data
                bool allExist = true;
                for (const auto& pt : consecutivePoints) {
                    if (dataSet.find(pt) == dataSet.end()) {
                        allExist = false;
                        break;
                    }
                }
                
                if (allExist) {
                    // Check boundaries - make sure line doesn't extend beyond 5
                    std::vector<int> beforePoint = {x - dx, y - dy};
                    std::vector<int> afterPoint = {x + dx * 5, y + dy * 5};
                    
                    if (dataSet.find(beforePoint) == dataSet.end() && 
                        dataSet.find(afterPoint) == dataSet.end()) {
                        return true;
                    }
                }
            }
        }
        
        return false;
    }
    
    /**
     * Check if either player has won based on the move sequence.
     * 
     * @param moves Vector of moves (coordinate pairs)
     * @return true if either player has won, false otherwise
     */
    static bool isWin(const std::vector<std::vector<int>>& moves) {
        if (moves.empty()) {
            return false;
        }
        
        // Split moves into two players
        std::vector<std::vector<int>> player1Moves, player2Moves;
        
        for (size_t i = 0; i < moves.size(); ++i) {
            if (i % 2 == 0) {
                player1Moves.push_back(moves[i]);
            } else {
                player2Moves.push_back(moves[i]);
            }
        }
        
        // Check if either player has won
        return searchWin(player1Moves) || searchWin(player2Moves);
    }
    
    /**
     * Optimized version using bitset for better performance
     */
    static bool searchWinOptimized(const std::vector<std::vector<int>>& data) {
        if (data.empty()) {
            return false;
        }
        
        // For performance, we'll use a hash-based approach
        // This is a simplified version - in practice, you might want to use
        // a more sophisticated data structure for very large boards
        
        std::set<std::pair<int, int>> dataSet;
        for (const auto& point : data) {
            dataSet.insert({point[0], point[1]});
        }
        
        const std::vector<std::pair<int, int>> directions = {
            {1, 0}, {0, 1}, {1, 1}, {1, -1}
        };
        
        for (const auto& point : data) {
            int x = point[0];
            int y = point[1];
            
            for (const auto& [dx, dy] : directions) {
                // Check 5 consecutive points
                bool valid = true;
                for (int i = 1; i <= 4; ++i) {
                    if (dataSet.find({x + dx * i, y + dy * i}) == dataSet.end()) {
                        valid = false;
                        break;
                    }
                }
                
                if (valid) {
                    // Check boundaries
                    if (dataSet.find({x - dx, y - dy}) == dataSet.end() &&
                        dataSet.find({x + dx * 5, y + dy * 5}) == dataSet.end()) {
                        return true;
                    }
                }
            }
        }
        
        return false;
    }
    
    static bool isWinOptimized(const std::vector<std::vector<int>>& moves) {
        if (moves.empty()) {
            return false;
        }
        
        std::vector<std::vector<int>> player1Moves, player2Moves;
        
        for (size_t i = 0; i < moves.size(); ++i) {
            if (i % 2 == 0) {
                player1Moves.push_back(moves[i]);
            } else {
                player2Moves.push_back(moves[i]);
            }
        }
        
        return searchWinOptimized(player1Moves) || searchWinOptimized(player2Moves);
    }
};

// Python binding
namespace py = pybind11;

PYBIND11_MODULE(win_check_cpp, m) {
    m.doc() = "Win checking algorithm implemented in C++";
    
    py::class_<WinChecker>(m, "WinChecker")
        .def_static("search_win", &WinChecker::searchWin, 
                   "Check if there's a winning pattern in the given data")
        .def_static("is_win", &WinChecker::isWin, 
                   "Check if either player has won based on the move sequence")
        .def_static("search_win_optimized", &WinChecker::searchWinOptimized, 
                   "Optimized version of search_win")
        .def_static("is_win_optimized", &WinChecker::isWinOptimized, 
                   "Optimized version of is_win");
    
    // Also expose standalone functions for easier access
    m.def("search_win", &WinChecker::searchWin, "Check for winning pattern");
    m.def("is_win", &WinChecker::isWin, "Check if either player won");
    m.def("search_win_optimized", &WinChecker::searchWinOptimized, "Optimized win check");
    m.def("is_win_optimized", &WinChecker::isWinOptimized, "Optimized player win check");
}