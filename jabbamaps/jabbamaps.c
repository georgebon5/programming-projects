#include <stdio.h>
#include <stdlib.h>
#include <limits.h>
#include <string.h>

#define MAX_CITIES 64 // Μέγιστος αριθμός πόλεων που μπορούν να υποστηριχθούν

// Ορισμός της δομής City για να αποθηκεύονται τα ονόματα των πόλεων
typedef struct {
    char name[50]; // Το όνομα της πόλης (μέγιστο μήκος 50 χαρακτήρες)
} City;

// Συνάρτηση που επιστρέφει τον δείκτη μιας πόλης από τον πίνακα `cities`
int find_city_index(City *cities, int cityCount, const char *city) {
    for (int i = 0; i < cityCount; i++) {
        if (strcmp(cities[i].name, city) == 0) { // Αν βρεθεί η πόλη, επιστρέφουμε τον δείκτη της
            return i;
        }
    }
    return -1; // Επιστρέφει -1 αν η πόλη δεν βρεθεί
}

// Συνάρτηση για την εκτύπωση της διαδρομής και του συνολικού κόστους
void print_route(int *path, int cityCount, int **distances, City *cities, long long best_cost) {
    printf("We will visit the cities in the following order:\n");

    for (int i = 0; i < cityCount - 1; i++) {
        int current_city = path[i];
        int next_city = path[i + 1];
        // Εκτυπώνουμε την πόλη, την απόσταση μέχρι την επόμενη πόλη και τη σύνδεση
        printf("%s -(%d)-> ", cities[current_city].name, distances[current_city][next_city]);
    }

    // Εκτυπώνουμε την τελευταία πόλη της διαδρομής
    printf("%s\n", cities[path[cityCount - 1]].name);
    // Εκτυπώνουμε το συνολικό κόστος της διαδρομής
    printf("Total cost: %lld\n", best_cost);
}

// Συνάρτηση που υλοποιεί τον αλγόριθμο Nearest Neighbor
void nearest_neighbor(int cityCount, int **distances, int *best_path, long long *best_cost) {
    int *visited = (int *)malloc(sizeof(int) * cityCount); // Πίνακας για τις επισκέψεις στις πόλεις
    int *path = (int *)malloc(sizeof(int) * cityCount); // Πίνακας για τη διαδρομή που ακολουθείται

    // Αρχικοποίηση των πόλεων ως μη επισκεμμένες
    for (int i = 0; i < cityCount; i++) {
        visited[i] = 0;
    }

    int current_city = 0; // Ξεκινάμε από την πρώτη πόλη
    visited[current_city] = 1; // Σημειώνουμε ότι επισκεφθήκαμε την πρώτη πόλη
    path[0] = current_city; // Καταγράφουμε την πρώτη πόλη στη διαδρομή

    long long total_cost = 0; // Αρχικοποίηση συνολικού κόστους διαδρομής

    // Εύρεση διαδρομής μέσω της κοντινότερης πόλης που δεν έχει επισκεφθεί
    for (int i = 1; i < cityCount; i++) {
        int next_city = -1;
        int min_distance = INT_MAX;

        // Εύρεση της πλησιέστερης πόλης
        for (int j = 0; j < cityCount; j++) {
            if (!visited[j] && distances[current_city][j] < min_distance) {
                min_distance = distances[current_city][j];
                next_city = j;
            }
        }

        visited[next_city] = 1; // Σημειώνουμε την πόλη ως ηδη επισκεψιμη
        path[i] = next_city; // Καταγράφουμε τη νέα πόλη στη διαδρομή
        total_cost += min_distance; // Προσθέτουμε την απόσταση στο συνολικό κόστος
        current_city = next_city; // Μετακινούμαστε στην επόμενη πόλη
    }

    *best_cost = total_cost; // Ενημερώνουμε το συνολικό κόστος της βέλτιστης διαδρομής
    memcpy(best_path, path, sizeof(int) * cityCount); // Αντιγράφουμε τη βέλτιστη διαδρομή

    free(visited); // Αποδέσμευση μνήμης για τον πίνακα επισκέψεων
    free(path); // Αποδέσμευση μνήμης για την τρέχουσα διαδρομή
}

int main(int argc, char *argv[]) {
    if (argc != 2) { // Έλεγχος σωστού αριθμού ορισμάτων αλλιως εκτυπωση και τερματισμος προγραμματος
        fprintf(stderr, "Usage: %s <filename>\n", argv[0]);
        return 1;
    }

    char *filename = argv[1];
    FILE *file = fopen(filename, "r"); // Άνοιγμα αρχείου για ανάγνωση
    if (!file) { // Έλεγχος αν το αρχείο άνοιξε με επιτυχία αλλιως εκτυπωση μηνυματος και τερματισμος προγραμματος
        fprintf(stderr, "Error opening file\n");
        return 1;
    }

    // Έλεγχος αν το αρχείο είναι κενό
    fseek(file, 0, SEEK_END);       // Μετακινεί τον δείκτη αρχείου (file pointer) στο τέλος του αρχείου
    long file_size = ftell(file);   // Επιστρέφει τη τρέχουσα θέση του δείκτη αρχείου, δηλαδή το σημείο όπου βρίσκεται ο δείκτης αφού μετακινήθηκε με το fseek
    if (file_size == 0) {
        fprintf(stderr, "Error: The file is empty.\n");
        fclose(file);
        return 1;
    }
    rewind(file); // Επιστροφή στην αρχή του αρχείου

    char line[128]; // Γραμμή για την αποθήκευση των δεδομένων από το αρχείο
    City *cities = (City *)malloc(sizeof(City) * MAX_CITIES); // Δυναμική δέσμευση πίνακα πόλεων
    int cityCount = 0;
    int **distances = (int **)malloc(sizeof(int *) * MAX_CITIES); // Δυναμική δέσμευση πίνακα αποστάσεων

    // Αρχικοποίηση του πίνακα αποστάσεων
    for (int i = 0; i < MAX_CITIES; i++) {
        distances[i] = (int *)malloc(sizeof(int) * MAX_CITIES);
        for (int j = 0; j < MAX_CITIES; j++) {
            distances[i][j] = INT_MAX; // Οι αρχικές αποστάσεις είναι πολύ μεγάλες
        }
    }

    // Διαβάζουμε τα δεδομένα από το αρχείο και ενημερώνουμε τον πίνακα πόλεων και αποστάσεων
    while (fgets(line, sizeof(line), file)) {
        char city1[32], city2[32];
        int distance;
        sscanf(line, "%[^-]-%[^:]: %d", city1, city2, &distance);   // διαβαζει το αρχειο εκτος απο τις - και :

        // Εύρεση ή εισαγωγή της πρώτης πόλης
        int index1 = find_city_index(cities, cityCount, city1);
        if (index1 == -1) {
            strcpy(cities[cityCount].name, city1);
            index1 = cityCount++;
        }

        // Εύρεση ή εισαγωγή της δεύτερης πόλης
        int index2 = find_city_index(cities, cityCount, city2);
        if (index2 == -1) {
            strcpy(cities[cityCount].name, city2);
            index2 = cityCount++;
        }

        // Ενημέρωση της απόστασης μεταξύ των δύο πόλεων
        distances[index1][index2] = distance;
        distances[index2][index1] = distance;
    }

    fclose(file); // Κλείσιμο του αρχείου

    // Δέσμευση πίνακα για την αποθήκευση της βέλτιστης διαδρομής
    int *best_path = (int *)malloc(sizeof(int) * cityCount);
    long long best_cost = 0;

    // Εκτέλεση του αλγορίθμου Nearest Neighbor
    nearest_neighbor(cityCount, distances, best_path, &best_cost);

    // Εκτύπωση της βέλτιστης διαδρομής
    print_route(best_path, cityCount, distances, cities, best_cost);

    // Αποδέσμευση της δεσμευμένης μνήμης
    free(cities);
    for (int i = 0; i < MAX_CITIES; i++) {
        free(distances[i]);
    }
    free(distances);
    free(best_path);

    return 0;
}