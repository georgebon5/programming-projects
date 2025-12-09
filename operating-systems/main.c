#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <pthread.h>

#include "ipc.h"
#include "dialog.h"

// Mutex για να μην μπερδεύονται τα prints όταν το thread τυπώνει μηνύματα
pthread_mutex_t print_mutex = PTHREAD_MUTEX_INITIALIZER;

// Ασφαλές διάβασμα integer από stdin (καθαρίζει και το \n)
int read_int() {
    int x;
    if (scanf("%d", &x) != 1) return -1;
    getchar(); // καθαρίζουμε το newline
    return x;
}

// Διαβάζει γραμμή string με ασφάλεια και αφαιρεί το \n
void read_line(char* buf, int size) {
    if (fgets(buf, size, stdin) == NULL) {
        buf[0] = '\0';
        return;
    }
    buf[strcspn(buf, "\n")] = '\0';
}

// Global pointers ώστε το thread να έχει πρόσβαση στη shared memory και στο dialog_id
static SharedMemory* g_sh = NULL;
static int g_dialog_id = -1;

// Flag για να γνωρίζει το receiver thread πότε πρέπει να σταματήσει
static volatile int g_running = 1;

//
// Thread που ασχολείται ΜΟΝΟ με τη λήψη μηνυμάτων.
// Ελέγχει περιοδικά τη shared memory και εμφανίζει νέα μηνύματα.
// Έτσι ο χρήστης μπορεί ταυτόχρονα να γράφει μηνύματα χωρίς να χρειάζεται manual refresh.
//
void* receiver_thread(void* arg) {
    (void)arg;

    while (g_running) {
        // Καλούμε receive_messages που επιστρέφει 1 αν είδαμε TERMINATE
        int term = receive_messages(g_sh, g_dialog_id);

        if (term) {
            // Τυπώνουμε ενημέρωση ότι ο διάλογος έχει κλείσει
            pthread_mutex_lock(&print_mutex);
            printf("\n[RECEIVER] Ο διάλογος τερματίστηκε (TERMINATE)\n");
            fflush(stdout);
            pthread_mutex_unlock(&print_mutex);

            // Σταματάμε όλο το πρόγραμμα
            g_running = 0;
            break;
        }

        // Μικρή καθυστέρηση ώστε να μην κάνουμε spam τη shared memory
        usleep(200000); // 0.2 sec
    }
    return NULL;
}

int main() {
    int choice;

    // Αρχικό μενού: δημιουργία ή join σε διάλογο
    printf("1. Δημιουργία νέου διαλόγου\n");
    printf("2. Συμμετοχή σε υπάρχον διάλογο\n");
    fflush(stdout);

    choice = read_int();
    if (choice == -1) return 1;

    //
    // Επιλογή 1 δημιουργία διαλόγου
    //
    if (choice == 1) {

        // Προσπαθούμε να κάνουμε attach σε ήδη υπάρχουσα shared memory
        g_sh = attach_shared_memory(0);

        // Αν δεν υπάρχει, τη δημιουργούμε (create == 1)
        if (!g_sh) {
            g_sh = attach_shared_memory(1);
            if (!g_sh) {
                printf("Αδυναμία δημιουργίας shared memory.\n");
                return 1;
            }
        }

        // Δημιουργούμε τον διάλογο
        g_dialog_id = create_dialog(g_sh);
        if (g_dialog_id < 0) {
            detach_shared_memory(g_sh);
            return 1;
        }

        printf("Δημιουργήθηκε διάλογος με ID %d\n", g_dialog_id);
        fflush(stdout);
    }

    //
    // Επιλογή 2 join σε υπάρχον διάλογο
    //
    else if (choice == 2) {

        // Κάνουμε απλό attach, η shared memory πρέπει να υπάρχει ήδη
        g_sh = attach_shared_memory(0);
        if (!g_sh) return 1;

        // Εμφανίζουμε όλους τους ενεργούς διαλόγους
        down();
        printf("Διαθέσιμοι διάλογοι:\n");
        for (int i = 0; i < MAX_DIALOGS; i++) {
            if (g_sh->dialogs[i].in_use)
                printf("ID: %d\n", g_sh->dialogs[i].id);
        }
        up();
        fflush(stdout);

        // Ζητάμε από τον χρήστη ID
        printf("Δώσε ID διαλόγου: ");
        fflush(stdout);

        g_dialog_id = read_int();
        if (g_dialog_id < 0) return 1;

        // Προσπαθούμε να μπούμε στον διάλογο
        if (join_dialog(g_sh, g_dialog_id) < 0) {
            printf("Αποτυχία συμμετοχής στον διάλογο.\n");
            fflush(stdout);
            detach_shared_memory(g_sh);
            return 1;
        }
    }

    // Αν έβαλε κάτι άκυρο
    else {
        printf("Λάθος επιλογή.\n");
        return 1;
    }

    //
    // Ξεκινάμε το thread λήψης μηνυμάτων
    //
    pthread_t recv_tid;
    pthread_create(&recv_tid, NULL, receiver_thread, NULL);

    //
    // Κύριο loop όπου ο χρήστης γράφει μηνύματα
    //
    while (g_running) {
        printf("\n1. Στείλε μήνυμα\n");
        printf("2. Στείλε TERMINATE\n");
        printf("3. Έξοδος\n");
        printf("Επιλογή: ");
        fflush(stdout);

        choice = read_int();
        if (choice == -1) break;

        // Αποστολή απλού μηνύματος
        if (choice == 1) {
            char buf[MAX_PAYLOAD];

            printf("Μήνυμα: ");
            fflush(stdout);

            read_line(buf, sizeof(buf));
            send_message(g_sh, g_dialog_id, buf);
        }

        // Αποστολή TERMINATE
        else if (choice == 2) {
            send_message(g_sh, g_dialog_id, "TERMINATE");
            printf("Έστειλες TERMINATE\n");
            fflush(stdout);
        }

        // Χειροκίνητη έξοδος
        else if (choice == 3) {
            g_running = 0;
        }
    }

    // Περιμένουμε το thread να τελειώσει
    pthread_join(recv_tid, NULL);

    // Αποδεσμεύουμε τη shared memory
    detach_shared_memory(g_sh);

    return 0;
}