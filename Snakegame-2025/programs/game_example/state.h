#pragma once

#include "ADTList.h"
#include "ADTVector.h"
#include "raylib.h"

// Δηλώσεις types
typedef struct state* State;

typedef struct keystate {
    bool up, down, left, right;
    bool enter, p, n;
}* KeyState;

// Δημιουργεί την αρχική κατάσταση του παιχνιδιού
State state_create();

// Καταστρέφει την κατάσταση και ελευθερώνει τη μνήμη
void state_destroy(State state);

// Ενημερώνει την κατάσταση μετά από 1 frame
void state_update(State state, KeyState keys);

// Δομή με βασικές πληροφορίες του παιχνιδιού
typedef struct state_info {
    List snake;             // λίστα με τα μέρη του φιδιού
    Direction snake_direction;
    bool playing;
    bool paused;
    int score;
} *StateInfo;

// Επιστρέφει βασικές πληροφορίες του παιχνιδιού
StateInfo state_info(State state);

// Επιστρέφει τα αντικείμενα που είναι εντός περιοχής
List state_objects(State state, Vector2 top_left, Vector2 bottom_right);

