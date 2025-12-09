
#include <stdio.h>

double add_mul(double a, double b) {
    if (a > b) {
        return a * b + 1;
    } else {
        return a + b;
    }
}

int main(void) {
    // Example driver (not used by the Python round-trip)
    return 0;
}
