// ipc.c
#include "ipc.h"
#include <sys/shm.h>
#include <sys/shm.h>
#include <semaphore.h>
#include <fcntl.h>
#include <stdio.h>

// Όνομα semaphore
#define SEM_NAME  "dialog_shm_sem"

// Shared memory key
#define SHM_KEY   0x1234

static sem_t* shm_sem = NULL;
static int shmid = -1;

// Συνδέει τη διεργασία στη shared memory.
// Αν create_if_missing = 1 τοτε δημιουργεί τη shared memory.
SharedMemory* attach_shared_memory(int create_if_missing)
{
    int flags;
    if (create_if_missing) // Δημιουργησε shared memory αν δεν υπάρχει
        flags = IPC_CREAT | 0666;
    else
        flags = 0666;

    //Δημιουργία ή άνοιγμα του shared memory segment
    shmid = shmget(SHM_KEY, sizeof(SharedMemory), flags);
    if (shmid == -1) {
        perror("shmget");
        return NULL;
    }

    //Κάνουμε attach και παίρνουμε pointer προς τη shared memory
    SharedMemory* sh = (SharedMemory*) shmat(shmid, NULL, 0);
    if (sh == (void*) -1) {
        perror("shmat");
        return NULL;
    }

    //Άνοιγμα ή δημιουργία semaphore
    if (create_if_missing) {
        // Δημιουργία semaphore (αρχική τιμή 1 → unlocked)
        shm_sem = sem_open(SEM_NAME, O_CREAT, 0666, 1);
    } else {
        //Άνοιγμα ήδη δημιουργημένου semaphore
        shm_sem = sem_open(SEM_NAME, 0);
    }

    if (shm_sem == SEM_FAILED) {
        perror("sem_open");
        return NULL;
    }

    //Αν δημιουργήσαμε τη shared memory για πρώτη φορά, αρχικοποίησέ την
    if (create_if_missing) {
        down();

        sh->next_dialog_id = 1;

        // Μηδενισμός όλων των διαλόγων
        for (int i = 0; i < MAX_DIALOGS; i++)
            sh->dialogs[i].in_use = 0;

        // Μηδενισμός όλων των μηνυμάτων
        for (int i = 0; i < MAX_MESSAGES; i++)
            sh->messages[i].in_use = 0;

        up();
    }

    // Επιστροφή pointer στη shared memory
    return sh;
}

// Αποσυνδέει τη διεργασία από τη shared memory
void detach_shared_memory(SharedMemory* sh)
{
    if (sh != NULL)
        shmdt(sh);   // detach

    if (shm_sem != NULL)
        sem_close(shm_sem);   // close semaphore
}

// Σβήνει εντελως τη shared memory από το σύστημα.
// Πρέπει να καλείται μόνο όταν δεν υπάρχουν άλλες διεργασίες.
void destroy_shared_memory()
{
    int id = shmget(SHM_KEY, sizeof(SharedMemory), 0666);
    if (id != -1)
        shmctl(id, IPC_RMID, NULL);   // delete shared memory

    sem_unlink(SEM_NAME);             // delete semaphore
}

// Κλείδωμα shared memory (με semaphore)
void down()
{
    sem_wait(shm_sem);  // περιμένει μέχρι να πάρει το lock
}

// ξεκλείδωμα shared memory (με semaphore)
void up()
{
    sem_post(shm_sem);  // απελευθερώνει το lock
}
