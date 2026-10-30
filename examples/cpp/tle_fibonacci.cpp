#include <iostream>

/*
 * Exponential O(2^N) Branching Recursion.
 * Triggers Time Limit Exceeded (TLE) on scale tests (e.g. N = 40).
 */
long long fib(int n) {
    if (n <= 1) return n;
    return fib(n - 1) + fib(n - 2);
}

int main() {
    int n;
    if (std::cin >> n) {
        std::cout << fib(n) << std::endl;
    }
    return 0;
}

