#include <stdio.h>
#include <string.h>

#define MAX_DIGITS 1000  // Ο μέγιστος αριθμός ψηφίων για το BigInt

// Ορισμός του τύπου BigInt
// Το BigInt χρησιμοποιείται για την αναπαράσταση μεγάλων ακέραιων αριθμών ως
// πίνακα ψηφίων
typedef struct {
  int digits[MAX_DIGITS];  // Αποθήκευση ψηφίων με το λιγότερο σημαντικό στο
                           // index 0
  int size;  // Μέγεθος του αριθμού (πόσα ψηφία χρησιμοποιούνται)
} BigInt;

// Αρχικοποίηση του BigInt από συμβολοσειρά
// Η συμβολοσειρά εισόδου αντιστρέφεται και κάθε χαρακτήρας μετατρέπεται σε
// ακέραιο
void BigInt_init(BigInt* num, const char* str) {
  int len = strlen(str);
  num->size = len;

  for (int i = 0; i < len; i++) {
    num->digits[i] =
        str[len - i - 1] - '0';  // Αντιστρέφουμε τη σειρά των ψηφίων
  }
}

// Εκτύπωση του BigInt
// Εκτυπώνεται ο αριθμός με τη σωστή σειρά (από το πιο σημαντικό ψηφίο)
void BigInt_print(BigInt* num) {
  for (int i = num->size - 1; i >= 0; i--) {
    printf("%d", num->digits[i]);
  }
}

// Έλεγχος αν το BigInt είναι διαιρετό με το n
// Υπολογίζουμε το υπόλοιπο μέσω διαδοχικής διαίρεσης κάθε ψηφίου
int BigInt_divisible(BigInt* num, int n) {
  int remainder = 0;
  for (int i = num->size - 1; i >= 0; i--) {
    remainder =
        remainder * 10 + num->digits[i];  // Προσθέτουμε το επόμενο ψηφίο
    remainder %= n;  // Υπολογίζουμε το υπόλοιπο
  }
  return remainder == 0;  // Επιστρέφει true αν το υπόλοιπο είναι 0
}

// Διαίρεση του BigInt με το n
// Ενημερώνει τα ψηφία του BigInt για να περιέχει το πηλίκο
void BigInt_divide(BigInt* num, int n) {
  int remainder = 0;
  for (int i = num->size - 1; i >= 0; i--) {
    remainder =
        remainder * 10 + num->digits[i];  // Προσθέτουμε το επόμενο ψηφίο
    num->digits[i] = remainder / n;  // Υπολογίζουμε το ψηφίο του πηλίκου
    remainder %= n;  // Ενημερώνουμε το υπόλοιπο
  }

  // Αφαιρούμε τα μη χρήσιμα μηδενικά από τα αριστερά
  while (num->size > 1 && num->digits[num->size - 1] == 0) {
    num->size--;
  }
}

// Συνάρτηση παραγοντοποίησης για BigInt
// Παράμετρος print_factors: αν είναι true, εκτυπώνει τους παράγοντες
// Επιστρέφει τον αριθμό των πρώτων παραγόντων
int factorize_and_check(BigInt* num, int print_factors) {
  int prime_count = 0;  // Μετρά τους πρώτους παράγοντες

  if (num->size == 1 && num->digits[0] == 1) {
    return prime_count;  // Επιστρέφει 0 αν το BigInt είναι 1
  }

  // Έλεγχος για τον παράγοντα 2
  while (BigInt_divisible(num, 2)) {
    if (print_factors) printf("2 ");  // Εκτύπωση αν χρειάζεται
    BigInt_divide(num, 2);
    prime_count++;
  }

  // Έλεγχος για τους περιττούς παράγοντες από το 3 και μετά
  for (int i = 3;; i += 2) {
    while (BigInt_divisible(num, i)) {
      if (print_factors) printf("%d ", i);  // Εκτύπωση αν χρειάζεται
      BigInt_divide(num, i);
      prime_count++;
    }

    // Αν το BigInt έχει φτάσει στο 1, σταματάμε
    if (num->size == 1 && num->digits[0] == 1) {
      break;
    }
  }

  // Αν απομένει αριθμός μεγαλύτερος από 1, τότε είναι πρώτος
  if (num->size > 0 && num->digits[0] > 1) {
    if (print_factors) BigInt_print(num);  // Εκτύπωση αν χρειάζεται
    prime_count++;
  }

  return prime_count;  // Επιστρέφει τον συνολικό αριθμό πρώτων παραγόντων
}

int main(int argc, char* argv[]) {
  // Έλεγχος αν η γραμμή εντολών έχει ακριβώς 2 ορίσματα
  if (argc != 2) {
    printf("Usage: %s <semiprime>\n", argv[0]);
    return 1;
  }

  // Έλεγχος αν το όρισμα είναι θετικός αριθμός
  for (int i = 0; argv[1][i] != '\0'; i++) {
    if (argv[1][i] < '0' || argv[1][i] > '9') {
      printf("Error: Argument must be a positive integer.\n");
      return 1;
    }
  }

  // Αρχικοποίηση του αριθμού BigInt από τη γραμμή εντολών
  BigInt num;
  BigInt_init(&num, argv[1]);

  // Έλεγχος αν είναι ημιπρώτος
  BigInt num_copy = num;  // Δημιουργία αντιγράφου για παραγοντοποίηση
  int prime_count = factorize_and_check(&num_copy, 0);  // Χωρίς εκτύπωση

  if (prime_count != 2) {
    printf("Error: The number is not semiprime.\n");
    return 1;
  }

  // Εκτύπωση παραγόντων μόνο αν είναι ημιπρώτος
  printf("Factors: ");
  factorize_and_check(&num, 1);  // Με εκτύπωση
  printf("\n");

  return 0;
}