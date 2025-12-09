#include "dialog.h"
#include "ipc.h"
#include <pthread.h>
#include <string.h>
#include <unistd.h>
#include <stdio.h>

// ψάχνει έναν διάλογο στο shared memory με βάση το ID του.
// Επιστρέφει pointer στον διάλογο ή NULL αν δεν υπάρχει.
static Dialog* find_dialog(SharedMemory* sh, int id)
{
    for (int i = 0; i < MAX_DIALOGS; i++) {
        if (sh->dialogs[i].in_use && sh->dialogs[i].id == id)
            return &sh->dialogs[i];
    }
    return NULL;
}

// Επιστρέφει το index της διεργασίας μέσα στον πίνακα processes ενός διαλόγου.
// Αυτό χρειάζεται ώστε κάθε διεργασία να ξέρει τη θέση της για το read_by[].
static int find_my_index(Dialog* d, pid_t pid)
{
    for (int i = 0; i < d->num_processes; i++) {
        if (d->processes[i].pid == pid)
            return i;
    }
    return -1;
}

// Δημιουργία νέου διαλόγου.
// Κλειδώνουμε με semaphore (down/up) γιατί τροποποιούμε τη shared memory.
int create_dialog(SharedMemory* sh)
{
    down(); // Μπαίνουμε σε critical section.

    // Βρίσκουμε μια ελεύθερη θέση στον πίνακα διαλόγων
    int slot = -1;
    for (int i = 0; i < MAX_DIALOGS; i++) {
        if (!sh->dialogs[i].in_use) {
            slot = i;
            break;
        }
    }

    if (slot == -1) {   // Δεν υπάρχει χώρος για νέο διάλογο
        up();
        return -1;
    }

    // Αρχικοποίηση του νέου διαλόγου
    Dialog* d = &sh->dialogs[slot];
    d->in_use = 1;
    d->id = sh->next_dialog_id++;   // Δίνουμε μοναδικό ID
    
    // Ο δημιουργός του διαλόγου είναι αυτόματα και η πρωτη διεργασια
    d->num_processes = 1;
    d->processes[0].pid = getpid();
    d->processes[0].active = 1;

    int dialog_id = d->id;

    up(); // Τελειώσαμε με το critical section
    return dialog_id;
}

// Μια διεργασία προσπαθεί να κάνει join σε υπάρχον διάλογο.
int join_dialog(SharedMemory* sh, int dialog_id)
{
    down();

    // Βρίσκουμε τον διάλογο
    Dialog* d = find_dialog(sh, dialog_id);
    if (d == NULL) {
        up();
        return -1;  // Δεν υπάρχει τέτοιος διάλογος
    }

    // Αν είναι γεμάτος, δεν επιτρέπεται άλλη διεργασια
    if (d->num_processes >= MAX_PROCESSES) {
        up();
        return -1;
    }

    // Προσθέτουμε τη διεργασία στο τέλος του πίνακα processes
    int pos = d->num_processes;
    d->processes[pos].pid = getpid();
    d->processes[pos].active = 1;
    d->num_processes++;

    up();
    return 0;
}

// Αποστολή μηνύματος σε έναν διάλογο.
int send_message(SharedMemory* sh, int dialog_id, const char* text)
{
    down();

    // Βρίσκουμε τον διάλογο
    Dialog* d = find_dialog(sh, dialog_id);
    if (d == NULL) {
        up();
        return -1;
    }

    // Βρίσκουμε ελεύθερη θέση στο global message buffer
    int slot = -1;
    for (int i = 0; i < MAX_MESSAGES; i++) {
        if (!sh->messages[i].in_use) {
            slot = i;
            break;
        }
    }

    if (slot == -1) {
        up();
        return -1; // Δεν υπάρχει πλέον χώρος για αποθήκευση μηνυμάτων
    }

    // Γράφουμε το μήνυμα
    Message* m = &sh->messages[slot];
    m->in_use = 1;
    m->dialog_id = dialog_id;
    m->sender = getpid();

    strncpy(m->payload, text, MAX_PAYLOAD);
    m->payload[MAX_PAYLOAD - 1] = '\0';

    //μαρκαρουμε οτι κανένας δεν το έχει διαβάσει ακόμα αυτο το μηνυμα
    for (int i = 0; i < d->num_processes; i++)
        m->read_by[i] = 0;

    up();
    return 0;
}

// Λήψη μηνυμάτων (επιστρέφει 1 αν είδα TERMINATE)
int receive_messages(SharedMemory* sh, int dialog_id)
{
    int saw_terminate = 0;
    pid_t me = getpid();

    down();

    // Βρίσκουμε τον διάλογο
    Dialog* d = find_dialog(sh, dialog_id);
    if (d == NULL) {
        up();
        return 0;
    }

     // Βρίσκουμε τη θέση μας στο read_by[]
    int my_idx = find_my_index(d, me);
    if (my_idx == -1) {
        up();
        return 0;
    }

    // Διαβάζουμε όλα τα μηνύματα που ανήκουν στον διάλογο
    for (int i = 0; i < MAX_MESSAGES; i++) {
        Message* m = &sh->messages[i];

        if (!m->in_use) continue;
        if (m->dialog_id != dialog_id) continue;

        // Αν έχουμε ήδη διαβάσει το μήνυμα, το προσπερνάμε
        if (m->read_by[my_idx]) continue;

        // Τύπωσε μήνυμα
        extern pthread_mutex_t print_mutex;

        pthread_mutex_lock(&print_mutex);
        printf("\n[RECEIVER] Μήνυμα από %d: %s\n", m->sender, m->payload);
        fflush(stdout);
        pthread_mutex_unlock(&print_mutex);

        // Σημείωσε ότι το διάβασα
        m->read_by[my_idx] = 1;

       // Εάν το μήνυμα είναι TERMINATE, η διεργασια γίνεται inactive
        if (strcmp(m->payload, "TERMINATE") == 0) {
            saw_terminate = 1;
            d->processes[my_idx].active = 0;  
        }

        // Έλεγχος αν όλοι οι active διεγρασιες το διάβασαν
        int all_read = 1;
        for (int p = 0; p < d->num_processes; p++) {
            if (d->processes[p].active && !m->read_by[p]) {
                all_read = 0;
                break;
            }
        }

        if (all_read) {
            m->in_use = 0; // διαγραφή μηνύματος
        }
    }

    // Αν είδα TERMINATE, δες αν τελειώνει ο διάλογος
if (saw_terminate) {
    int active_left = 0;
    for (int p = 0; p < d->num_processes; p++) {
        if (d->processes[p].active) {
            active_left = 1;
            break;
        }
    }

    if (!active_left) {
        d->in_use = 0; // ο διάλογος τερματίστηκε

        //ΕΛΕΓΧΟΣ ΑΝ ΥΠΑΡΧΕΙ ΑΛΛΟΣ ΕΝΕΡΓΟΣ ΔΙΑΛΟΓΟΣ
        int any_dialog_left = 0;
        for (int i = 0; i < MAX_DIALOGS; i++) {
            if (sh->dialogs[i].in_use) {
                any_dialog_left = 1;
                break;
            }
        }

        //ΑΝ ΔΕΝ ΥΠΑΡΧΕΙ ΚΑΝΕΝΑΣ -> ΚΑΘΑΡΙΣΜΟΣ SHARED MEMORY
        if (!any_dialog_left) {
            destroy_shared_memory();
        }
    }
}

    up();
    return saw_terminate;
}