#include <iostream>
#include <vector>

/*
 * C++ Segmentation Fault on Empty Array Corner Case.
 * Accesses nums[0] without checking if vector is empty.
 */
int main() {
    int n;
    if (!(std::cin >> n)) {
        return 0;
    }

    std::vector<int> nums(n);
    for (int i = 0; i < n; i++) {
        std::cin >> nums[i];
    }

    // Bug: If n == 0, nums is empty. Dereferencing nums[0] triggers SIGSEGV / ASan error!
    int first_element = nums[0];
    std::cout << "First element is: " << first_element << std::endl;

    return 0;
}

