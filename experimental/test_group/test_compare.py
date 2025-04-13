import cv2
import numpy as np
from scipy.spatial import KDTree
import time
import random

# [Original UnionFindOriginal and groupOverlappingContoursOriginal unchanged]
class UnionFindOriginal:
    def __init__(self, size):
        self.parent = list(range(size))
    
    def find(self, u):
        while self.parent[u] != u:
            self.parent[u] = self.parent[self.parent[u]]
            u = self.parent[u]
        return u
    
    def union(self, u, v):
        root_u = self.find(u)
        root_v = self.find(v)
        if root_u != root_v:
            self.parent[root_v] = root_u

def groupOverlappingContoursOriginal(contours, distanceThreshold=10, areaSize=300):
    significant_contours = [cnt for cnt in contours if cv2.contourArea(cnt) >= areaSize]
    if not significant_contours:
        return []
    
    bounding_rects = [cv2.boundingRect(cnt) for cnt in significant_contours]
    masks = []
    for rect, cnt in zip(bounding_rects, significant_contours):
        mask = np.zeros((rect[3], rect[2]), dtype=np.uint8)
        shifted_cnt = cnt.copy()
        shifted_cnt[:, :, 0] -= rect[0]
        shifted_cnt[:, :, 1] -= rect[1]
        cv2.drawContours(mask, [shifted_cnt], -1, 255, thickness=cv2.FILLED)
        masks.append(mask)
    
    uf = UnionFindOriginal(len(significant_contours))
    
    for i in range(len(significant_contours)):
        for j in range(i + 1, len(significant_contours)):
            if uf.find(i) == uf.find(j):
                continue
            rect1 = bounding_rects[i]
            rect2 = bounding_rects[j]
            
            x_overlap = max(0, min(rect1[0] + rect1[2], rect2[0] + rect2[2]) - max(rect1[0], rect2[0]))
            y_overlap = max(0, min(rect1[1] + rect1[3], rect2[1] + rect2[3]) - max(rect1[1], rect2[1]))
            
            if x_overlap > 0 and y_overlap > 0:
                overlap_area = x_overlap * y_overlap
                if overlap_area > 0:
                    uf.union(i, j)
            else:
                center1 = np.array([rect1[0] + rect1[2] / 2, rect1[1] + rect1[3] / 2])
                center2 = np.array([rect2[0] + rect2[2] / 2, rect2[1] + rect2[3] / 2])
                distance = np.linalg.norm(center1 - center2)
                if distance <= distanceThreshold:
                    uf.union(i, j)
    
    groups = {}
    for idx in range(len(significant_contours)):
        root = uf.find(idx)
        if root not in groups:
            groups[root] = []
        groups[root].append(significant_contours[idx])
    
    grouped_contours = [np.vstack(group) for group in groups.values()]
    return grouped_contours

# [Improved UnionFindImproved and groupOverlappingContoursImproved unchanged]
class UnionFindImproved:
    def __init__(self, n):
        self.parent = list(range(n))
        self.rank = [0] * n
    
    def find(self, x):
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]
    
    def union(self, x, y):
        px, py = self.find(x), self.find(y)
        if px == py:
            return
        if self.rank[px] < self.rank[py]:
            px, py = py, px
        self.parent[py] = px
        if self.rank[px] == self.rank[py]:
            self.rank[px] += 1

def groupOverlappingContoursImproved(contours, distanceThreshold=10, areaSize=300, useConvexHull=True, useMasks=False, imageShape=None):
    significant_contours = [cnt for cnt in contours if cv2.contourArea(cnt) >= areaSize]
    if not significant_contours:
        return []
    
    n = len(significant_contours)
    bounding_rects = [cv2.boundingRect(cnt) for cnt in significant_contours]
    centers = np.array([(rect[0] + rect[2] / 2, rect[1] + rect[3] / 2) for rect in bounding_rects])
    
    uf = UnionFindImproved(n)
    
    if useMasks:
        if imageShape is None:
            raise ValueError("imageShape must be provided when useMasks=True")
        masks = [np.zeros(imageShape, dtype=np.uint8) for _ in range(n)]
        for i, cnt in enumerate(significant_contours):
            cv2.drawContours(masks[i], [cnt], -1, 255, thickness=cv2.FILLED)
    
    tree = KDTree(centers)
    
    for i in range(n):
        rect1 = bounding_rects[i]
        center1 = centers[i]
        
        indices = tree.query_ball_point(center1, distanceThreshold + max(rect1[2], rect1[3]))
        
        for j in indices:
            if i >= j:
                continue
            if uf.find(i) == uf.find(j):
                continue
            rect2 = bounding_rects[j]
            
            x_overlap = max(0, min(rect1[0] + rect1[2], rect2[0] + rect2[2]) - max(rect1[0], rect2[0]))
            y_overlap = max(0, min(rect1[1] + rect1[3], rect2[1] + rect2[3]) - max(rect1[1], rect2[1]))
            rects_overlap = x_overlap > 0 and y_overlap > 0
            
            distance = np.linalg.norm(center1 - centers[j]) if not rects_overlap else 0
            
            pixel_overlap = False
            if useMasks and (rects_overlap or distance <= distanceThreshold):
                overlap_mask = cv2.bitwise_and(masks[i], masks[j])
                pixel_overlap = np.any(overlap_mask)
            
            if rects_overlap or pixel_overlap or (distance > 0 and distance <= distanceThreshold):
                uf.union(i, j)
    
    groups = {}
    for idx in range(n):
        root = uf.find(idx)
        if root not in groups:
            groups[root] = []
        groups[root].append(significant_contours[idx])
    
    if useConvexHull:
        grouped_contours = [cv2.convexHull(np.vstack(group)) for group in groups.values()]
    else:
        grouped_contours = [np.vstack(group) for group in groups.values()]
    
    return grouped_contours

# Enhanced test contour generation
def generate_test_contours(num_contours, image_size=1000, max_size=50, min_size=10, overlap_prob=0.3, use_circles=True):
    contours = []
    for _ in range(num_contours):
        x = random.randint(0, image_size - max_size)
        y = random.randint(0, image_size - max_size)
        size = random.randint(min_size, max_size)
        
        if random.random() < overlap_prob and contours:
            prev_contour = random.choice(contours)
            prev_rect = cv2.boundingRect(prev_contour)
            x = random.randint(max(0, prev_rect[0] - size), min(image_size - size, prev_rect[0] + prev_rect[2]))
            y = random.randint(max(0, prev_rect[1] - size), min(image_size - size, prev_rect[1] + prev_rect[3]))
        
        if use_circles:
            # Generate circular contour
            theta = np.linspace(0, 2 * np.pi, 50)
            cx, cy = x + size // 2, y + size // 2
            points = np.vstack((
                cx + size // 2 * np.cos(theta),
                cy + size // 2 * np.sin(theta)
            )).T.astype(np.int32).reshape(-1, 1, 2)
        else:
            # Generate rectangular contour
            points = np.array([
                [x, y],
                [x + size, y],
                [x + size, y + size],
                [x, y + size]
            ], dtype=np.int32).reshape(-1, 1, 2)
        
        contours.append(points)
    
    return contours

# Enhanced comparison
def compare_results(original_groups, improved_groups):
    if len(original_groups) != len(improved_groups):
        return False, f"Different number of groups: {len(original_groups)} vs {len(improved_groups)}"
    
    original_counts = sorted([len(group) for group in original_groups])
    improved_counts = sorted([len(group) for group in improved_groups])
    
    if original_counts != improved_counts:
        return False, f"Different group sizes: {original_counts} vs {improved_counts}"
    
    return True, "Results are equivalent"

# Enhanced test runner
def run_tests():
    test_cases = [
        {"num_contours": 10, "distanceThreshold": 20, "areaSize": 100, "image_size": 1000},
        {"num_contours": 50, "distanceThreshold": 20, "areaSize": 100, "image_size": 1000},
        {"num_contours": 100, "distanceThreshold": 20, "areaSize": 100, "image_size": 1000},
    ]
    
    for idx, case in enumerate(test_cases, 1):
        print(f"\n=== Test Case {idx} ===")
        print(f"Parameters: {case}")
        
        # Generate circular contours
        contours = generate_test_contours(
            case["num_contours"],
            image_size=case["image_size"],
            max_size=50,
            min_size=10,
            overlap_prob=0.3,
            use_circles=True
        )
        
        # Run original algorithm
        start_time = time.time()
        original_result = groupOverlappingContoursOriginal(
            contours,
            distanceThreshold=case["distanceThreshold"],
            areaSize=case["areaSize"]
        )
        original_time = time.time() - start_time
        
        # Run improved algorithm
        start_time = time.time()
        improved_result = groupOverlappingContoursImproved(
            contours,
            distanceThreshold=case["distanceThreshold"],
            areaSize=case["areaSize"],
            useConvexHull=False,
            useMasks=False,
            imageShape=None
        )
        improved_time = time.time() - start_time
        
        # Compare results
        are_equal, message = compare_results(original_result, improved_result)
        
        # Print detailed stats
        print(f"Original Algorithm Time: {original_time:.4f} seconds")
        print(f"Improved Algorithm Time: {improved_time:.4f} seconds")
        print(f"Speed-Up Ratio: {(original_time / improved_time):.2f}x" if improved_time > 0 else "N/A")
        print(f"Number of Groups (Original): {len(original_result)}")
        print(f"Number of Groups (Improved): {len(improved_result)}")
        print(f"Group Sizes (Original): {[len(g) for g in original_result]}")
        print(f"Group Sizes (Improved): {[len(g) for g in improved_result]}")
        print(f"Results Match: {are_equal}")
        if not are_equal:
            print(f"Difference: {message}")

if __name__ == "__main__":
    run_tests()