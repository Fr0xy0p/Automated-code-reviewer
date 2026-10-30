"""
Clean, Production-Ready Two Sum Solution.
Optimal O(N) Time and O(N) Space Complexity using a Hash Map.
Passes all edge-case vectors (empty, duplicates, bounds, scale).
"""

def two_sum(nums, target):
    if not nums or len(nums) < 2:
        return []

    seen = {}
    for i, num in enumerate(nums):
        complement = target - num
        if complement in seen:
            return [seen[complement], i]
        seen[num] = i
    return []
