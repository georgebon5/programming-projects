#include <stdio.h>
#include <stdbool.h>
#include <stdlib.h>
#include "raylib.h"

#include "interface.h"
#include "state.h"

State state;
    // Game loop
 void update_and_draw() {
    while (!WindowShouldClose()) {
        // Δημιουργία struct για πατημένα πλήκτρα
        KeyState keys = malloc(sizeof(*keys));
        keys->up = IsKeyDown(KEY_UP);
        keys->down = IsKeyDown(KEY_DOWN);
        keys->left = IsKeyDown(KEY_LEFT);
        keys->right = IsKeyDown(KEY_RIGHT);
        keys->enter = IsKeyDown(KEY_ENTER);
        keys->p = IsKeyDown(KEY_P);
        keys->n = IsKeyDown(KEY_N);

        if (!state_info(state)->playing && keys->enter) {
            StopMusicStream(game_song);        // Σταματάει το τραγούδι
            PlayMusicStream(game_song);        // Ξεκινάει το τραγούδι από την αρχή
            state_destroy(state);
            state = state_create();
            free(keys);
            continue; 
        }
        // Ενημέρωση και σχεδίαση
        state_update(state, keys);
        interface_draw_frame(state);

        // Απελευθέρωση μνήμης των keys
        free(keys);
    }
 }
int main() {
    // Δημιουργία αρχικής κατάστασης και γραφικού περιβάλλοντος
    state = state_create();
    interface_init();

    SetTargetFPS(60);  // Σταθερό 60 FPS
    start_main_loop(update_and_draw);


    // Καθαρισμός και έξοδος
    interface_close();
    return 0;
}
