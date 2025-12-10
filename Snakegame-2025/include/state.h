#pragma once

#include "ADTVector.h"
#include "ADTList.h"
#include "raylib.h"

// Οι τύποι του παιχνιδιού
typedef enum { UP, DOWN, LEFT, RIGHT } Direction;

// Πλήκτρα
typedef struct key_state {
    bool up;
    bool down;
    bool left;
    bool right;
    bool enter;
    bool p;
    bool n;
} *KeyState;

// Δηλώσεις τύπων
typedef struct state* State;
typedef struct state_info* StateInfo;

// Δομή πληροφοριών του παιχνιδιού
struct state_info {
    List snake;
    Direction snake_direction;
    bool playing;
    bool paused;
    int score;
};

// Βασική δομή του state
struct state {
    Vector objects;                  // Περιέχει τα αντικείμενα (μήλα, αετοί)
    struct state_info info;          // Γενικές πληροφορίες του παιχνιδιού
    int frame_counter;               // Μετρητής frames
    bool prev_p;                     // προηγουμενη τιμη του p
};

// Δηλώσεις συναρτήσεων
Vector2 snake_head_pos(List snake);
State state_create();
void state_destroy(State state);
StateInfo state_info(State state);
List state_objects(State state, Vector2 top_left, Vector2 bottom_right);
void state_update(State state, KeyState keys);

// Σταθερές του παιχνιδιού
#define SCREEN_WIDTH 800
#define SCREEN_HEIGHT 600
#define SNAKE_SIZE 20


typedef struct object* Object;

typedef enum { APPLE = 1, EAGLE = 2 } ObjectType;

struct object {
    ObjectType type;
    Vector2 position;
    double size;
    Direction direction;
};


