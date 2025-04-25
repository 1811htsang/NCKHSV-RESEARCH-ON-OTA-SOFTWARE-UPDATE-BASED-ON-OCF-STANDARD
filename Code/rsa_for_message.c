#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include <math.h>
#include <time.h>
#include <string.h>

bool is_prime(int n) {
    if (n <= 1) return false;
    for (int i = 2; i * i <= n; i++) {
        if (n % i == 0) return false;
    }
    return true;
}

long long int generate_prime(int min, int max) {
    int prime;
    do {
        prime = rand() % (max - min + 1) + min;
    } while (!is_prime(prime));
    return prime;
}

long long int gcd(long long int a, long long int b) {
    while (b != 0) {
        long long int t = b;
        b = a % b;
        a = t;
    }
    return a;
}

long long int mod_inverse(long long int a, long long int m) {
    for (long long int x = 1; x < m; x++) {
        if ((a * x) % m == 1) {
            return x;
        }
    }
    return -1; // No modular inverse found
}

long long int power(long long int base, long long int exp, long long int mod) {
    long long int res = 1;
    base = base % mod;
    while (exp > 0) {
        if (exp % 2 == 1) res = (res * base) % mod;
        base = (base * base) % mod;
        exp = exp >> 1; // Equivalent to exp /= 2
    }
    return res;
}

int main() {
    long long int p, q, n, phi_n, e, d;
    srand(time(NULL));

    // Generate two distinct prime numbers p and q
    p = generate_prime(100, 20);
    q = generate_prime(100, 20);
    while (p == q) {
        q = generate_prime(10, 20);
    }

    // Calculate n and phi(n)
    n = p * q;
    phi_n = (p - 1) * (q - 1);

    // Choose e such that 1 < e < phi(n) and gcd(e, phi(n)) = 1
    e = generate_prime(3, phi_n - 1);
    while (gcd(e, phi_n) != 1) {
        e = generate_prime(3, phi_n - 1);
    }

    // Calculate d, the modular inverse of e mod phi(n)
    d = mod_inverse(e, phi_n);

    if (d == -1) {
        printf("No modular inverse found.\n");
        return 1;
    }

    // Display the keys
    printf("Public Key: (e: %lld, n: %lld)\n", e, n);
    printf("Private Key: (d: %lld, n: %lld)\n", d, n);
    printf("p: %lld, q: %lld\n", p, q);

    // Example encryption and decryption
    char *message = "#include <stdio.h> int main() { printf(\"Hello, World!\");    return 0;}";
    
    long long int encrypted_message[strlen(message)];
    for (int i = 0; i < strlen(message); i++) {
        encrypted_message[i] = power(message[i], e, n);
    }

    char decrypted_message[strlen(message)];
    for (int i = 0; i < strlen(message); i++) {
        decrypted_message[i] = (char)power(encrypted_message[i], d, n);
    }

    printf("Original Message: %s\n", message);
    printf("Encrypted Message: ");
    for (int i = 0; i < strlen(message); i++) {
        printf("%lld ", encrypted_message[i]);
    }
    printf("\nDecrypted Message: %s\n", decrypted_message);


    if (memcmp(message, decrypted_message, strlen(message)) == 0) {
        printf("Decryption successful!\n");
    } else {
        printf("Decryption failed.\n");
    }
    return 0;
}