#include <iostream>
#include <vector>
#include <unordered_map>

/*
 * Clean, Optimal C++ Two Sum Implementation.
 * Time Complexity: O(N)
 * Space Complexity: O(N)
 * Handles empty arrays, duplicates, and large scale inputs defensively.
 */
int main() {
    int n, target;
    if (!(std::cin >> n >> target) || n < 2) {
        std::cout << "[]\n";
        return 0;
    }

    std::vector<int> nums(n);
    for (int i = 0; i < n; i++) {
        std::cin >> nums[i];
    }

    std::unordered_map<int, int> seen;
    for (int i = 0; i < n; i++) {
        int complement = target - nums[i];
        if (seen.find(complement) != seen.end()) {
            std::cout << "[" << seen[complement] << ", " << i << "]\n";
            return 0;
        }
        seen[nums[i]] = i;
    }

    std::cout << "[]\n";
    return 0;
}
