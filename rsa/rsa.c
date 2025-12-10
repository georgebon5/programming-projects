#include <stdio.h>
#include <stdlib.h>
#include <string.h>


// Συνάρτηση για υπολογισμό του Euler's Totient Function (φ(N)) για δύο πρώτους αριθμούς p και q
long long totient(long long p, long long q) {
    // Η φόρμουλα για το φ(N) είναι (p - 1) * (q - 1) όταν p και q είναι πρώτοι
    return (p - 1) * (q - 1); // Διορθώθηκε ο πολλαπλασιασμός
}

// Συνάρτηση για υπολογισμό του Μέγιστου Κοινού Διαιρέτη (GCD) δύο αριθμών
long long gcd(long long p, long long q) {
    // Βασική συνάρτηση του Ευκλειδη για υπολογισμό του GCD
    if (q == 0) {
        return p;  // Αν το q είναι 0, τότε το p είναι το GCD
    } else if (p == 0) {
        return q;  // Αν το p είναι 0, τότε το q είναι το GCD
    } else {
        return gcd(q, p % q);  // Αντίστροφος υπολογισμός του GCD
    }
}

// Συνάρτηση για έλεγχο αν ένας αριθμός είναι πρώτος
int isPrime(long long n) {
    if (n < 2) {
        return 0;  // Αν n είναι μικρότερο από 2, δεν είναι πρώτος
    }
    // Ελέγχουμε για ακέραιους αριθμούς από το 2 μέχρι την τετραγωνική ρίζα του n
    for (int i = 2; i * i <= n; i++) { // Αντικατέστησα το i * i <= n με το σωστό όριο
        if (n % i == 0) {
            return 0;  // Αν βρούμε παράγοντα, δεν είναι πρώτος
        }
    }
    return 1;  // Αν δεν βρεθεί παράγοντας, τότε είναι πρώτος
}

// Συνάρτηση για έλεγχο αν δύο αριθμοί είναι συγγενείς πρώτοι
long long coprime(long long a, long long b) {
    // Ελέγχουμε αν ο GCD των δύο αριθμών είναι 1 (αν είναι σχετικά πρώτοι)
    if (gcd(a, b) == 1) {
        return 1;  // Αν ναι, επιστρέφουμε 1
    } else {
        return 0;  // Αν όχι, επιστρέφουμε 0
    }
}

// Συνάρτηση για υπολογισμό της εκθετικής υπολοίπου με χρήση της μεθόδου "Binary Exponentiation"
long long mod_exp(long long base, long long exp, long long mod) {
    long long result = 1;
    while (exp > 0) {
        if (exp % 2 == 1) {
            result = (result * base) % mod;  // Αν το exp είναι περιττό, πολλαπλασιάζουμε το result με τη βάση
        }
        base = (base * base) % mod;  // Σημειώνω το τετράγωνο της βάσης
        exp /= 2;  // Διαιρώ την εκθετική τιμή με το 2
    }
    return result;  // Επιστρέφω το τελικό αποτέλεσμα
}

int main(int argc, char *argv[]) {
    // Έλεγχος για την σωστή χρήση του προγράμματος μέσω των ορισμάτων
    if (argc != 6) {
        printf("Usage: ./rsa enc|dec <exp_exp> <priv_exp> <prime1> <prime2>\n");
        return 1;  // Αν δεν υπάρχουν ακριβώς 5 ορίσματα, επιστρέφουμε σφάλμα
    }

    // Έλεγχος αν το πρώτο όρισμα είναι "enc" ή "dec" (κρυπτογράφηση ή αποκρυπτογράφηση)
    if (strcmp(argv[1], "enc") != 0 && strcmp(argv[1], "dec") != 0) {
        printf("First argument must be 'enc' or 'dec'\n");
        return 1;  // Αν το πρώτο όρισμα δεν είναι "enc" ή "dec", επιστρέφουμε σφάλμα
    }

    // Μετατροπή των ορισμάτων σε τύπους long long
    long long e = atoll(argv[2]);  // εκθέτης
    long long d = atoll(argv[3]);  // εκθέτης
    long long p = atoll(argv[4]);  // Πρώτος αριθμός p
    long long q = atoll(argv[5]);  // Πρώτος αριθμός q
    long long m;  // Το μήνυμα που θα κρυπτογραφηθεί ή αποκρυπτογραφηθεί

    // Έλεγχος αν τα ορίσματα είναι θετικοί αριθμοί
    if (e < 1 || d < 1 || p < 1 || q < 1) {
        printf("Negative numbers are not allowed\n");
        return 1;  // Αν υπάρχει αρνητικός αριθμός, επιστρέφουμε σφάλμα
    }

    // Έλεγχος αν οι p και q είναι πρώτοι
    if (!isPrime(p) || !isPrime(q)) {
        printf("p and q must be prime\n");
        return 1;  // Αν p ή q δεν είναι πρώτοι, επιστρέφουμε σφάλμα
    }

    // Υπολογισμός του Euler's Totient Function φ(N) για το N = p * q
    long long phi_N = totient(p, q);

    // Έλεγχος αν το e είναι σχετικά πρώτο με το φ(N)
    if (!coprime(e, phi_N)) {
        printf("e is not coprime with phi(N)\n");
        return 1;  // Αν το e δεν είναι σχετικά πρώτο με το φ(N), επιστρέφω σφάλμα
    }

    // Υπολογισμός του N = p * q
    long long N = p * q;

    // Έλεγχος αν το e * d mod φ(N) είναι ίσο με 1 (το οποίο επιβεβαιώνει ότι d είναι το αντίστροφο του e mod φ(N))
    if ((e * d) % phi_N != 1) {
        printf("e * d mod phi(N) is not 1\n");
        return 1;  // Αν δεν ισχύει αυτή η σχέση, επιστρέφουμε σφάλμα
    }

    // Ανάγνωση του μηνύματος προς κρυπτογράφηση ή αποκρυπτογράφηση
    if (scanf("%lld", &m) != 1) {
        return 1;  // Αν δεν διαβαστεί σωστά το μήνυμα, επιστρέφουμε σφάλμα
    }

    // Έλεγχος αν το μήνυμα είναι θετικό
    if (m < 1) {
        printf("Negative numbers are not allowed\n");
        return 1;  // Αν το μήνυμα είναι αρνητικό, επιστρέφουμε σφάλμα
    }

    // Έλεγχος αν το μήνυμα είναι μικρότερο από το N (αλλιώς δεν μπορεί να κρυπτογραφηθεί)
    if (m >= N) {
        printf("Message is larger than N\n");
        return 1;  // Αν το μήνυμα είναι μεγαλύτερο ή ίσο με το N, επιστρέφουμε σφάλμα
    }

    // Εκτέλεση της κρυπτογράφησης ή αποκρυπτογράφησης ανάλογα με το όρισμα "enc" ή "dec"
    if (strcmp(argv[1], "enc") == 0) {
        long long enc_message = mod_exp(m, e, N);  // Κρυπτογράφηση του μηνύματος
        printf("%lld\n", enc_message);  // Εκτύπωση του κρυπτογραφημένου μηνύματος
    } else if (strcmp(argv[1], "dec") == 0) {
        long long dec_message = mod_exp(m, d, N);  // Αποκρυπτογράφηση του μηνύματος
        printf("%lld\n", dec_message);  // Εκτύπωση του αποκρυπτογραφημένου μηνύματος
    }

    return 0;  // Επιτυχής εκτέλεση του προγράμματος
}