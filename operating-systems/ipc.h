// ipc.h
#pragma once
#include "shared.h"

SharedMemory* attach_shared_memory(int create_if_missing);
void detach_shared_memory(SharedMemory* sh);
void destroy_shared_memory();

void down();
void up();
