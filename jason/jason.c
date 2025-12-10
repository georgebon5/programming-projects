#include "neurolib.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <ctype.h>
#include <unistd.h> // Περιλαμβάνεται για την συνάρτηση unlink()
#define BUFFER_SIZE 1024


// Συνάρτηση που ελέγχει αν το όνομα αρχείου έχει κατάληξη ".json"
int has_json_extension(const char *filename) {
    const char *dot = strrchr(filename, '.'); // Εντοπισμός της τελευταίας εμφάνισης της τελείας στο όνομα αρχείου
    return (dot && strcmp(dot, ".json") == 0); // Επιστροφή αν τελειώνει με ".json"
}

// Συνάρτηση που ελέγχει αν ένα αρχείο JSON είναι έγκυρο 
int is_valid_json(const char *filename) {
    FILE *file = fopen(filename, "r"); // Άνοιγμα αρχείου για ανάγνωση
    if (!file) {
        perror("Could not open file");  // Εκτύπωση μηνύματος σφάλματος αν αποτύχει το άνοιγμα
        return 0;
    }

    int braces = 0, brackets = 0;  // Μετρητές για αγκύλες {} και []
    char c, prev = 0;  // Μεταβλητές για τρέχοντα και προηγούμενο χαρακτήρα
    int in_string = 0;   // Flag για το αν είμαστε μέσα σε συμβολοσειρά

    while ((c = fgetc(file)) != EOF) {
       // Έλεγχος για εισαγωγικά
        if (c == '"') {
            if (prev != '\\') { // Εναλλαγή κατάστασης μόνο αν δεν είναι διαφυγόμενο εισαγωγικό
                in_string = !in_string;
            }
        }

       // Παράβλεψη περιεχομένου μέσα σε συμβολοσειρές
        if (in_string) {
            prev = c;
            continue;
        }

        // Αύξηση ή μείωση των μετρητών για αγκύλες
        if (c == '{') braces++;
        if (c == '}') braces--;
        if (c == '[') brackets++;
        if (c == ']') brackets--;

        // Έλεγχος για μη έγκυρη δομή (αρνητικές τιμές στους μετρητές)
        if (braces < 0 || brackets < 0) {
            fclose(file);
            return 0; // Μη έγκυρη JSON
        }

        prev = c;
    }

    fclose(file);

    // Έλεγχος ότι οι αγκύλες και οι συμβολοσειρές έχουν κλείσει σωστά
    return braces == 0 && brackets == 0 && !in_string;
}

// Συνάρτηση που αφαιρεί τα κενά από την αρχή μιας συμβολοσειράς
char *trim_leading_spaces(char *str) {
    while (isspace(*str)) {
        str++;
    }
    return str;
}

// Συνάρτηση που επεξεργάζεται escape sequences, όπως \n
void process_escape_sequences(char *str) {
    char *src = str, *dest = str;
    while (*src) {
        if (*src == '\\' && *(src + 1) == 'n') {  // Αντικατάσταση του \n με πραγματικό νέο χαρακτήρα γραμμής

            *dest++ = '\n'; 
            src += 2;     
        } else {
            if (*src == '\n') {  // Αντικατάσταση ανεπιθύμητων νέων γραμμών με κενό
                *dest++ = ' ';
            } else {
                *dest++ = *src; // Αντιγραφή του χαρακτήρα
            }
            src++;
        }
    }
    *dest = '\0'; // Τερματισμός συμβολοσειράς
}

// Συνάρτηση που βρίσκει το "choices[0].message.content" μέσα σε ένα αρχείο JSON
char *find_content_in_json(const char *filename){
    FILE *file = fopen(filename, "r");  // Άνοιγμα αρχείου για ανάγνωση
    if (!file) {
        perror("Error opening file");
        return NULL;
    }

    char buffer[BUFFER_SIZE];  // Buffer για ανάγνωση γραμμών
    char content[BUFFER_SIZE * 10] = ""; // Μεταβλητή για το περιεχόμενο
    int in_content = 0;                 // Flag για το αν βρισκόμαστε μέσα στο κλειδί "content"


    while (fgets(buffer, BUFFER_SIZE, file)) {
        
        trim_leading_spaces(content);  // Αφαίρεση κενών από την αρχή
        if (in_content) {
            char *end_quote = strchr(buffer, '\"');  // Εύρεση του κλεισίματος εισαγωγικού
            if (end_quote) {
                *end_quote = '\0'; 
                strcat(content, trim_leading_spaces(buffer));
                break; 
            } else {
                strcat(content, trim_leading_spaces(buffer));  // Συγκέντρωση περιεχομένου πολλαπλών γραμμών
            }
        } else {
            // Εύρεση του κλειδιού "content"
            char *key = strstr(buffer, "\"content\"");
            if (key) {
                // Εύρεση του ':' μετά το "content"
                char *colon = strchr(key, ':');
                if (colon) {
                    char *value_start = colon + 1;
                    while (*value_start == ' ' || *value_start == '\"') {
                        value_start++;
                    }

                    char *end_quote = strchr(value_start, '\"');
                    if (end_quote) {
                        *end_quote = '\0'; 
                        strcpy(content, trim_leading_spaces(value_start));
                        fclose(file);
                        process_escape_sequences(content); // Επεξεργασία escape sequences
                        return strdup(content);           // Επιστροφή αντιγραμμένου περιεχομένου
                    } else {
                        strcpy(content, trim_leading_spaces(value_start));
                        in_content = 1; 
                    }
                }
            }
        }
    }

    fclose(file);
    process_escape_sequences(content);
    return (strlen(content) > 0) ? strdup(content) : NULL;
}

// Κύρια συνάρτηση
int main(int argc, char **argv){
    neurosym_init();  // Αρχικοποίηση βιβλιοθήκης

    if(argc < 2 || argc > 3){
        fprintf(stderr, "Usage:./jason <API_KEY> [filename]\n");
        return 1;
    }

    // Λειτουργία "bot" με χρήση μόνο ενός ορίσματος
    if(argc == 2){
        if(strcmp(argv[1], "--bot") == 0){
            while(1){
                printf("> What would you like to know? ");  // Ερώτηση στον χρήστη
                char prompt[1024];
                if (fgets(prompt, sizeof(prompt), stdin)) {  // Ανάγνωση εισόδου
                    // Αφαίρεση του χαρακτήρα νέας γραμμής
                    prompt[strcspn(prompt, "\n")] = '\0';

                    // Λήψη απόκρισης από το API
                    char *api_response = response(prompt);

                    if (api_response == NULL) {  // Έλεγχος αν η απόκριση είναι άδεια
                    printf("Error: No response received from the API.\n");
                    continue;
                    }

                    // Προσωρινό αρχείο
                    const char *temp_filename = "temp_response.json";
                    FILE *temp_file = fopen(temp_filename, "w");
                    if (temp_file == NULL) {
                        perror("Error creating temp file");
                        free(api_response);
                        continue;
                    }

                    fprintf(temp_file, "%s", api_response);  // Γράψιμο της απόκρισης στο αρχείο
                    fclose(temp_file);

                    // Εύρεση περιεχομένου από JSON
                    char *response_message = find_content_in_json(temp_filename);

                    if (response_message != NULL) {
                        // Εκτύπωση περιεχομένου
                        printf("%s\n", response_message);
                        free(response_message);  // Don't forget to free memory!
                    } else {
                        printf("Failed to find content in the JSON response.\n");
                    }

                    unlink(temp_filename);  // Διαγραφή προσωρινού αρχείου
                    free(api_response);  // Αποδέσμευση μνήμης
                } else {
                    printf("Terminating\n");
                    return 1;
                }
            }
            
        }else{
            fprintf(stderr, "Usage:./jason <API_KEY> [filename]\n");
            return 1;  // Τερματισμός σε περίπτωση σφάλματος
        }

    }else if(argc == 3){
        if(strcmp(argv[1], "--extract") == 0){   // Ελέγχουμε αν το πρώτο όρισμα είναι "--extract"
            if(has_json_extension(argv[2])){ // Ελέγχουμε αν το δεύτερο όρισμα έχει κατάληξη ".json"
                if(!is_valid_json(argv[2])){ // Ελέγχουμε αν το αρχείο JSON είναι έγκυρο
                    fprintf(stderr, "Not an accepted JSON!\n");  // Μήνυμα σφάλματος για μη έγκυρο JSON
                    return 1;  // Τερματισμός με κωδικό αποτυχίας
                }
                char *content= find_content_in_json(argv[2]);
                printf("%s\n", content);
               
            // Σφάλμα αν δεν βρεθεί περιεχόμενο
            } else {
                fprintf(stderr, "The file does not have a '.json' extension\n");  // Μήνυμα σφάλματος για λάθος κατάληξη αρχείου
                return 1;  // Τερματισμός με κωδικό αποτυχίας

            }
        }else{
            fprintf(stderr, "Usage:./jason <API_KEY> [filename]\n");  // Σφάλμα για λανθασμένο όρισμα
            return 1;  // Τερματισμός με κωδικό αποτυχίας
        }
    }

}