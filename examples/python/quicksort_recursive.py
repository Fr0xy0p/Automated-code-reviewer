"""
QuickSort without recursion depth guard or random pivot.
Fails on sorted arrays (worst case O(N^2)) and exceeds recursion limit on large N.
"""

def quicksort(nums):
    if len(nums) <= 1:
        return nums
    pivot = nums[0]
    less = [x for x in nums[1:] if x <= pivot]
    greater = [x for x in nums[1:] if x > pivot]
    return quicksort(less) + [pivot] + quicksort(greater)

