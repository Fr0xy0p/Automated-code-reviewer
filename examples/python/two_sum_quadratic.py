"""
Two Sum - Naive Quadratic O(N^2) Solution.
Fails asymptotic scale tests on large inputs.
"""

def two_sum(nums, target):
    n = len(nums)
    for i in range(n):
        for j in range(i + 1, n):
            if nums[i] + nums[j] == target:
                return [i, j]
    return []

