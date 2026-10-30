"""
Buggy Binary Search with Infinite Loop (TLE) on Edge Cases.
"""

def binary_search(nums, target):
    low = 0
    high = len(nums) - 1
    while low <= high:
        mid = (low + high) // 2
        if nums[mid] == target:
            return mid
        elif nums[mid] < target:
            low = mid  # Bug: should be mid + 1
        else:
            high = mid - 1
    return -1

