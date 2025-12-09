// dialog.h
#pragma once
#include "shared.h"

int create_dialog(SharedMemory* sh);
int join_dialog(SharedMemory* sh, int dialog_id);

Dialog* find_dialog_by_id(SharedMemory* sh, int dialog_id);
int find_my_index_in_dialog(Dialog* d, pid_t pid);

int send_message(SharedMemory* sh, int dialog_id, const char* text);
int receive_messages(SharedMemory* sh, int dialog_id);   // επιστρέφει αν είδε TERMINATE
