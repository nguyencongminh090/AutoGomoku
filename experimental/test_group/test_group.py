import cv2
import numpy as np
from scipy.spatial import KDTree

class UnionFind:
    def __init__(self, n):
        self.parent = list(range(n))
        self.rank = [0] * n
    
    def find(self, x):
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])  # Path compression
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

def groupOverlappingContours(contours, distanceThreshold=10, areaSize=300, useConvexHull=False, useMasks=False, imageShape=None):
    """
    Group overlapping or nearby contours efficiently.
    
    Parameters:
    - contours: List of contours from cv2.findContours.
    - distanceThreshold: Max distance between contour centers to consider them related.
    - areaSize: Minimum contour area to filter noise.
    - useConvexHull: If True, merge grouped contours into a convex hull; else, concatenate points.
    - useMasks: If True, use pixel-level overlap detection (requires imageShape).
    - imageShape: Tuple (height, width) of the image, required if useMasks=True.
    
    Returns:
    - List of grouped contours.
    """
    significant_contours = [cnt for cnt in contours if cv2.contourArea(cnt) >= areaSize]
    if not significant_contours:
        return []
    
    n = len(significant_contours)
    bounding_rects = [cv2.boundingRect(cnt) for cnt in significant_contours]
    centers = np.array([(rect[0] + rect[2] / 2, rect[1] + rect[3] / 2) for rect in bounding_rects])
    
    uf = UnionFind(n)
    
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
    
    grouped_contours = [cv2.convexHull(np.vstack(group)) if useConvexHull else np.vstack(group) for group in groups.values()]
    return grouped_contours

# Example usage
if __name__ == "__main__":
    # Simulated contours (replace with real cv2.findContours output)
    contours = [
        np.array([[10, 10], [10, 20], [20, 20], [20, 10]], dtype=np.int32),  # Square 1
        np.array([[15, 15], [15, 25], [25, 25], [25, 15]], dtype=np.int32),  # Square 2 (overlaps Square 1)
        np.array([[50, 50], [50, 60], [60, 60], [60, 50]], dtype=np.int32)   # Square 3 (separate)
    ]
    image_shape = (100, 100)  # Example image size
    
    # Test with convex hull and masks
    result = groupOverlappingContours(
        contours, 
        distanceThreshold=10, 
        areaSize=50, 
        useConvexHull=False, 
        useMasks=False, 
        imageShape=image_shape
    )
    
    print(f"Number of groups: {len(result)}")
    for i, group in enumerate(result):
        print(f"Group {i + 1} points: {len(group)}")
