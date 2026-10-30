#include <stdio.h>
#include <stdlib.h>

/*
 * Buffer overflow edge case.
 * Fixed array of 10 ints, reads n elements into it.
 * When n > 10, triggers AddressSanitizer stack-buffer-overflow.
 */
int main(void) {
    int n;
    if (scanf("%d", &n) != 1) {
        return 0;
    }

    int buffer[10];
    for (int i = 0; i < n; i++) {
        // Bug: No boundary check against buffer capacity (10)
        scanf("%d", &buffer[i]);
    }

    int sum = 0;
    for (int i = 0; i < n; i++) {
        sum += buffer[i];
    }
    printf("%d\n", sum);
    return 0;
}
