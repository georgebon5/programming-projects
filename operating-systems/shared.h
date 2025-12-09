// shared.h
#pragma once
#include <sys/types.h>

#define MAX_DIALOGS       10
#define MAX_PROCESSES     10
#define MAX_MESSAGES      100
#define MAX_PAYLOAD       256

typedef struct {
    pid_t pid;      // PID της διεργασίας
    int active;     // 1 = συμμετέχει ακόμη, 0 = έχει αποχωρήσει
} Process;

typedef struct {
    int in_use;                          // 0 = ελεύθερη θέση, 1 = διάλογος ενεργός
    int id;                              // μοναδικό ID διαλόγου
    Process processes[MAX_PROCESSES];
    int num_processes;
} Dialog;

typedef struct {
    int in_use;                          // υπάρχει μήνυμα σε αυτή τη θέση;
    int dialog_id;                       // ID διαλόγου
    pid_t sender;                        // PID αποστολέα
    char payload[MAX_PAYLOAD];          // κείμενο
    int read_by[MAX_PROCESSES];       // 0/1 για κάθε συμμετέχοντα του διαλόγου
} Message;

typedef struct {
    Dialog dialogs[MAX_DIALOGS];
    Message messages[MAX_MESSAGES];
    int next_dialog_id;                  // για παραγωγή νέων ID
} SharedMemory;
