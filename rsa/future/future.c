#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define DEFAULT_WINDOW 50   // σταθερά σε περίπτωση που ο χρήστης δεν δώσει στο terminal το μέγεθος του παραθύρου

int main (int argc, char **argv) {
    if (argc < 2 || argc > 4) {     // αν δοθούν λιγότερα από 2 ορίσματα ή περισσότερα από 4 να εκτυπώνει αντίστοιχο μήνυμα και να τερματίζει με κωδικό 1
        printf("Usage: ./future <filename> [--window N (default: 50)]\n");
        return 1;
    }

    const char *filename = argv[1];     // αρχικοποίηση του δεύτερου ορίσματος σε σταθερά τύπου char 
    int window = DEFAULT_WINDOW;

    // Ελέγχω για το παράθυρο που δίνεται ως παράμετρος
    if (argc == 4) {
       if (strcmp(argv[2], "--window") != 0) {      // σε περίπτωση που ο χρήστης πληκτρολογήσει λάθος το "--window" να εμφανιστεί αντίστοιχο μήνυμα και το πρόγραμμα να τερματίσει με κωδικό εξόδου 1
            fprintf(stderr, "Usage: ./future <filename> [--window N (default: 50)]\n");
            return 1;
        }
        window = atoi(argv[3]);     // μετατροπή του ορίσματος που απεικονίζει το μέγεθος του παραθύρου σε ακέραιο από χαρακτήρα που βρίσκεται
        if (window < 1) {   // αν το παράθυρο είναι μικρότερο από 1 να εμφανίζει αντίστοιχο μήνυμα και να τερματίζει το πρόγραμμα με κωδικό εξόδου 1
            fprintf(stderr, "Window too small!\n");
            return 1;
        }
    }

    // Άνοιγμα αρχείου για διάβασμα του περιεχομένου του 
    FILE *file = fopen(filename, "r");
    if (!file) {    // σε περίπτωση που το αρχείο δεν ανοίξει να εμφανίζει αντίστοιχο μήνυμα και να τερματίζει με κωδικό 1
        fprintf(stderr, "Error opening file\n");
        return 1;
    }

    double *data = NULL;    
    int capacity = 10;
    int size = 0;
    data = malloc(capacity * sizeof(double));   // δυναμική δέσμευση μνήμης 

    if (!data) {    // σε περίπτωση που δεν λειτουργήσει η malloc να εμφανίζει αντίστοιχο μήνυμα, να κλείσει το αρχείο και να τερματίσει με κωδικό 1
        fprintf(stderr, "Memory allocation failed\n");
        fclose(file);
        return 1;
    }

    double value;
    // Ανάγνωση των τιμών από το αρχείο και προσθήκη στον πίνακα
    while (fscanf(file, "%lf", &value) == 1) {      // τερματισμός επανάληψης όταν διαβαστούν όλα τα δεδομένα του αρχείου 
        // Αν ο πίνακας φτάσει στο μέγιστο μέγεθος, διπλασιάζουμε τη χωρητικότητα
        if (size == capacity) {
            capacity *= 2;      // διπλασιασμός μεγέθους 
            data = realloc(data, capacity * sizeof(double));    // αλλαγή του μεγέθους του πίνακα
            if (!data) {
                perror("Memory allocation failed");     // η perror κάνει ακριβώς το ίδιο πράγμα με την fprintf(stderr, "...")
                fclose(file);       // κλείσιμο αρχείου 
                return 1;       // τερματισμός προγράμματος 
            }
        }
        data[size] = value;  // Προσθήκη της τιμής στον πίνακα
        ++size;     // αύξηση του μεγέθους 
    }

    fclose(file);       // κλείσιμο αρχείου

    if (window > size) {        // αν το παράθυρο είναι μεγαλύτερο του μεγέθους του πίνακα τότε να εκτυπώνει αντίστοιχο μήνυμα, να κάνει αποδέσμευση της μνήμης του πίνακα και να τερματίζει το πρόγραμμα με κωδικό 1
        fprintf(stderr, "Window too large!\n");
        free(data);
        return 1;
    }

    // Υπολογισμός του κινούμενου μέσου όρου για τις τελευταίες 'window' τιμές
    double sum = 0;
    for (int i = size - window; i < size; i++) {
         sum += data[i];
    }

    double avg = sum / window;
    printf("%.2f\n", avg);      // εκτύπωση του μέσου όρου 

    free(data);     // αποδέσμευση μνήμης 
    return 0;       // επιτυχής τερματισμός προγράμματος 
}