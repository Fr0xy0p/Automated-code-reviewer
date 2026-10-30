#include <stdio.h>
#include <stdlib.h>

/*
 * Buggy C program: Calculates average without checking if n == 0.
 * On empty input (n = 0), triggers SIGFPE (divide by zero exception).
 */
int main(void) {
    int n;
    if (scanf("%d", &n) != 1) {
        return 0;
    }

    long long sum = 0;
    for (int i = 0; i < n; i++) {
        int val;
        if (scanf("%d", &val) == 1) {
            sum += val;
        }
    }

    // Bug: If n == 0, division by zero occurs here -> SIGFPE
    long long avg = sum / n;
    printf("%lld\n", avg);
    return 0;
}

