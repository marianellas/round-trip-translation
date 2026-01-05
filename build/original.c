
#include <stdio.h>

double is_sum_even(double a, double b) {
    if ((int(a) + int(b)) % 2 == 0) {
        return 1;
    } else {
        return 0;
    }
}

int main(void) {
    // Example driver (not used by the Python round-trip)
    return 0;
}
