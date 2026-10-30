#include <stdio.h>
#include <stdlib.h>

/*
 * Clean, robust C program.
 * Validates array bounds, guards against zero division, and manages memory safely.
 */
int main(void) {
    int n;
    if (scanf("%d", &n) != 1 || n <= 0) {
        printf("0\n");
        return 0;
    }

    long long sum = 0;
    for (int i = 0; i < n; i++) {
        int val = 0;
        if (scanf("%d", &val) == 1) {
            sum += val;
        }
    }

    long long avg = sum / n;
    printf("%lld\n", avg);
    return 0;
}
