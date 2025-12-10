#include<stdio.h>
#include <stdlib.h>
#include <math.h>
#include <ADTMap.h>
#include "ADTVector.h"
#include "ADTList.h"
#include "state_alt.h"

// Πρωτότυπο για τη vec_distance (για να μπορείς να τη χρησιμοποιείς παντού)
static double vec_distance(Vector2 v1, Vector2 v2);

// Σταθερές για το παιχνίδι
#define MIN_DIST 100
#define MAX_DIST 400

#define APPLE_SIZE 30
#define EAGLE_SIZE 30

#define MIN_APPLES_NUM 3
#define MIN_EAGLES_NUM 2

#define UPDATE_STATE_FRAMES 4 // κάθε πόσα frames θα κινείται το φίδι

#define EAGLE_TURN_PROB 0.1     // πιθανότητα να αλλάξει κατεύθυνση ο αετός (10%)
#define EAGLE_SPEED 20          // πόσο γρήγορα κινείται ο αετός


// Οι ολοκληρωμένες πληροφορίες της κατάστασης του παιχνιδιού.
// Ο τύπος State είναι pointer σε αυτό το struct, αλλά το ίδιο το struct
// δεν είναι ορατό στον χρήστη.

// Ελέγχει αν η θέση position είναι πάνω στο φίδι (κεφάλι ή σώμα)
static bool is_on_snake(List snake, Vector2 position) {
    for (ListNode node = list_first(snake);
         node != LIST_EOF;
         node = list_next(snake, node)) {
        Vector2 snake_pos = *(Vector2*)list_node_value(snake, node);
        if (vec_distance(position, snake_pos) < SNAKE_SIZE) {
            return true;
        }
    }
    return false;
}


typedef struct {
    int x;  // Συντεταγμένη στον άξονα X
    int y;  // Συντεταγμένη στον άξονα Y
} GridCoord;



// Bοηθητικές συναρτήσεις /////////////////////////////////////////////////////////////////////////////////
//
// Δημιουργεί και επιστρέφει ένα αντικείμενομμ
static Object create_object(ObjectType type, Vector2 position, double size, Direction direction) {
    Object obj = malloc(sizeof(*obj));
    obj->type = type;
    obj->position = position;
    obj->size = size;
    obj->direction = direction;
    return obj;
}
// 
static double vec_distance(Vector2 v1, Vector2 v2){
    double sum = (v1.x - v2.x)*(v1.x - v2.x) + (v1.y - v2.y)*(v1.y - v2.y);
    return sqrt(sum);
}

// Δημιουργεί και επιστρέφει ένα διάνυσμα
static Vector2* create_vector(Vector2 value) {
    Vector2* res = malloc(sizeof(*res));
    *res = value;
    return res;
}

// Επιστρέφει ένα διάνυσμα μετατοπισμένο κατά distance στην κατεύθυνση dir σε σχέση με το vec
static Vector2 move_in_direction(Vector2 vec, Direction dir, float distance) {
    Vector2 res = vec;
    switch (dir) {
        case UP:    res.y -= distance; break;
        case DOWN:  res.y += distance; break;
        case RIGHT: res.x += distance; break;
        case LEFT:  res.x -= distance; break;
    }
    return res;
}

// Επιστρέφει τη θέση του κεφαλιού του φιδιού
Vector2 snake_head_pos(List snake) {
    return *(Vector2*)list_node_value(snake, list_last(snake));
}

// Επιστρέφει έναν τυχαίο πραγματικό αριθμό στο διάστημα [min,max]
static double randf(double min, double max) {
    return min + (double)rand() / RAND_MAX * (max - min);
}

// Επιστρέφει έναν τυχαίο ακέραιο αριθμό στο διάστημα [min,max]
static int randi(int min, int max) {
    return min + rand() % (max - min + 1);
}

// Δημιουργεί num αντικείμενα σε τυχαία απόσταση από το φίδι, και με τυχαία κατεύθυνση κίνησης
static void add_random_objects(State state, ObjectType type, int num) {
    Vector2 head_pos = snake_head_pos(state->info.snake);

    for (int i = 0; i < num; i++) {
        Vector2 position;
        do {
            position = move_in_direction(head_pos, randi(0, 3), randf(MIN_DIST, MAX_DIST));
        } while (is_on_snake(state->info.snake, position));  // ΕΛΕΓΧΟΣ σε όλο το σώμα του φιδιού

        Direction dir = randi(0, 3);
        int size = type == APPLE ? APPLE_SIZE : EAGLE_SIZE;
        Object obj = create_object(type, position, size, dir);
        GridCoord* coord = malloc(sizeof(GridCoord));
        coord->x = (int)obj->position.x;
        coord->y = (int)obj->position.y;

        map_insert(state->objects, coord, obj);
    }
}


/////////////////////////////////////////////////////////////////////////////////////////////////////


int grid_compare(Pointer a, Pointer b) {
    GridCoord* g1 = a;
    GridCoord* g2 = b;
    if (g1->x != g2->x)
        return g1->x - g2->x;
    return g1->y - g2->y;
}

// Δημιουργεί και επιστρέφει την αρχική κατάσταση του παιχνιδιού
State state_create() {
    // Δημιουργία του state
    State state = malloc(sizeof(*state));

    // Γενικές πληροφορίες
    state->info.playing = true;         // Το παιχνίδι ξεκινάει αμέσως
    state->info.paused = false;         // Χωρίς να είναι paused
    state->info.score = 0;              // Αρχικό σκορ 0
    state->frame_counter = 0;           // Αρχικό frame 0

    // Δημιουργούμε το φίδι
    state->info.snake = list_create(free);                                                  // αυτόματη αποδέσμευση μνήμης
    list_insert_next(state->info.snake, LIST_BOF, create_vector((Vector2){0, 0}));          // κεφάλι
    list_insert_next(state->info.snake, LIST_BOF, create_vector((Vector2){-SNAKE_SIZE, 0}));// ουρά

    state->info.snake_direction = RIGHT;    // Αρχική κίνηση προς τα δεξιά

    // Δημιουργούμε το vector των αντικειμένων, και προσθέτουμε αντικείμενα
    state->objects = map_create(grid_compare, free, free);


    add_random_objects(state, APPLE, MIN_APPLES_NUM);
    add_random_objects(state, EAGLE, MIN_EAGLES_NUM);

    state->prev_p = false; //προηγουμενη τιμη του p

    return state;
}

// Επιστρέφει τις βασικές πληροφορίες του παιχνιδιού στην κατάσταση state
StateInfo state_info(State state) {
    return &state->info;
}

// Επιστρέφει μια λίστα με όλα τα αντικείμενα του παιχνιδιού στην κατάσταση state,
// των οποίων η θέση position βρίσκεται εντός του παραλληλογράμμου με πάνω αριστερή
// γωνία top_left και κάτω δεξιά bottom_right.
List state_objects(State state, Vector2 top_left, Vector2 bottom_right) {
    List result = list_create(NULL);
    for (MapNode node1 =map_first(state->objects);
        node1 != MAP_EOF; 
        node1 = map_next(state->objects, node1)){
        Object obj = map_node_value(state->objects, node1);
        float x = obj->position.x;
        float y = obj->position.y;
        if(x >= top_left.x && x <= bottom_right.x && y >= top_left.y && y <= bottom_right.y){
            list_insert_next(result, LIST_BOF, obj);
        }
    }
    return result;
}

// Ενημερώνει την κατάσταση state του παιχνιδιού μετά την πάροδο 1 frame.
// Το keys περιέχει τα πλήκτρα τα οποία ήταν πατημένα κατά το frame αυτό.

void state_update(State state, KeyState keys) {
   // paused
	if (keys->p && !state->prev_p)
    state->info.paused = !state->info.paused;

	state->prev_p = keys->p;

	if (!state->info.playing)
		return;
	// ενημερωση frame
	if (state->info.paused && !keys->n)
		return;

    // αυξανω το frame counter σε καθε κληση
    state->frame_counter++;

    //Προσοχή: λόγω της ιδιαίτερης κίνησης του φιδιού,
    //η μεταβολή της κίνησης του πρέπει να γίνεται κάθε UPDATE_STATE_FRAMES
    //(όχι σε κάθε frame). Για να γίνει αυτό πρέπει να χρησιμοποιήσετε τη μεταβλητή
    //frame_counter του state.

    if(state->frame_counter % UPDATE_STATE_FRAMES == 0){
        
        // Ανανεωνω το position του φιδιου
        List snake = state->info.snake;
        for(
            ListNode node = list_first(snake);
            node != list_last(snake);
            node = list_next(snake, node)
        ){
            Vector2 *nheadpos = list_node_value(snake, node);
            *nheadpos = *(Vector2*)list_node_value(snake, list_next(snake, node));
        }

        // Αν πατηθουν κουμπια μετακινητε το φιδακι
        if(keys->right && state->info.snake_direction != LEFT)
            state->info.snake_direction=RIGHT;
        if(keys->left && state->info.snake_direction != RIGHT)
            state->info.snake_direction=LEFT;
        if(keys->up && state->info.snake_direction !=DOWN)
            state->info.snake_direction=UP;
        if(keys->down && state->info.snake_direction !=UP)
            state->info.snake_direction=DOWN;

        // παιρνω την διευθυνση του κεφαλιου
        Vector2* head_pos = list_node_value(snake, list_last(snake));

        // δεσμευω χειροκινητα μνημη για να αποθηκευσω τα στοιχεια της καινουργιας 
        Vector2* new_head = malloc(sizeof(Vector2));

        // υπολογιζω το καινουργιο κεφαλι
        *new_head = move_in_direction(*head_pos, state->info.snake_direction, SNAKE_SIZE);

        // βγαζω την ουρα απο την λιστα
        list_remove_next(snake, LIST_BOF);

        // προσθετω το καινουριου στην αρχη
        list_insert_next(snake, list_last(snake), new_head);

    }

    // Κάνω iterate και ανανεώνω τις θέσεις για όλα τα αντικείμενα
    List snake = state->info.snake;
    int apple_no = 0;
    int eagle_no = 0;
    for (MapNode node1 =map_first(state->objects);
        node1 != MAP_EOF; 
        node1 = map_next(state->objects, node1)){
        Object obj = map_node_value(state->objects, node1);
        if(obj->type == APPLE){
            double dist_from_snake = vec_distance(obj->position, snake_head_pos(snake));
            if(dist_from_snake <= MAX_DIST){
                apple_no++;
            }
        }
        if(obj->type == EAGLE){
            double dist_from_snake = vec_distance(obj->position, snake_head_pos(snake));
            if(dist_from_snake <= MAX_DIST){
                eagle_no++;
            }
        }
    }
    if(apple_no < MIN_APPLES_NUM){
        add_random_objects(state, APPLE, MIN_APPLES_NUM - apple_no);
    }
    if(eagle_no < MIN_EAGLES_NUM){
        add_random_objects(state, EAGLE, MIN_EAGLES_NUM - eagle_no);
    }

    
    //Τα updates γίνονται κάθε UPDATE_STATE_FRAMES 
    if(state->frame_counter % UPDATE_STATE_FRAMES == 0){
        // Κάνω iterate και ανανεώνω τις θέσεις για τα αντικείμενα
        for (MapNode node1 =map_first(state->objects);
        node1 != MAP_EOF; 
        node1 = map_next(state->objects, node1)){
        Object obj = map_node_value(state->objects, node1);
            if(obj->type == EAGLE){
                if ((rand() % 1000) < (int)(EAGLE_TURN_PROB * 1000)) {
                    Direction new_dir = rand() % 4;  // 0 ως 3: UP, DOWN, LEFT, RIGHT
                    obj->direction = new_dir;
                    // Αφαιρούμε από το Map με το παλιό key
					map_remove(state->objects, map_node_key(state->objects, node1));

					// Υπολογίζουμε τη νέα θέση
					obj->position = move_in_direction(obj->position, obj->direction, EAGLE_SPEED);

					// Φτιάχνουμε το νέο key (GridCoord)
					GridCoord* new_coord = malloc(sizeof(GridCoord));
					new_coord->x = (int)obj->position.x;
					new_coord->y = (int)obj->position.y;

					// Ξαναβάζουμε το αντικείμενο στο Map
					map_insert(state->objects, new_coord, obj);

                }
            }
        }
    }

    // Συγκρουσεις με αετους
    if (state->frame_counter % UPDATE_STATE_FRAMES == 0) {
    // Δημιουργούμε μια προσωρινή λίστα για να αποθηκεύσουμε τα keys των αετών που θα γυρίσουν
    List to_update = list_create(NULL);

    // Πρώτο πέρασμα: βρίσκουμε ποιους αετούς θα γυρίσουμε
    for (MapNode node1 = map_first(state->objects);
         node1 != MAP_EOF;
         node1 = map_next(state->objects, node1)) {
        Object obj = map_node_value(state->objects, node1);
        if (obj->type == EAGLE) {
            if ((rand() % 1000) < (int)(EAGLE_TURN_PROB * 1000)) {
                // Βάζουμε το key στη λίστα (χωρίς αντιγραφή, το Map κρατάει το pointer του key)
                list_insert_next(to_update, LIST_BOF, map_node_key(state->objects, node1));
            }
        }
    }

    // Δεύτερο πέρασμα: μετακινούμε όσους βρήκαμε
    for (ListNode node = list_first(to_update);
         node != LIST_EOF;
         node = list_next(to_update, node)) {
        GridCoord* old_key = list_node_value(to_update, node);
        Object obj = map_find(state->objects, old_key);
        map_remove(state->objects, old_key);
        free(old_key);  // Μην ξεχνάς να κάνεις free το παλιό key!

        obj->direction = rand() % 4;
        obj->position = move_in_direction(obj->position, obj->direction, EAGLE_SPEED);

        // Φτιάχνουμε νέο key για τη νέα θέση
        GridCoord* new_key = malloc(sizeof(GridCoord));
        new_key->x = (int)obj->position.x;
        new_key->y = (int)obj->position.y;

        // Ξαναβάζουμε τον αετό στο Map στη νέα θέση
        map_insert(state->objects, new_key, obj);
    }

    // Καθαρίζουμε τη λίστα to_update
    list_destroy(to_update);
}


	// Ελεγχος συγκρουσης με το ΣΩΜΑ του φιδιού (όχι το κεφάλι!)
	Vector2 head = snake_head_pos(snake);
	for (
			ListNode node = list_first(snake);
			node != list_last(snake);  // Δεν ελέγχουμε το κεφάλι
			node = list_next(snake, node)
		) {
		Vector2 bodyposition = *(Vector2*)list_node_value(snake, node);
		if (head.x == bodyposition.x && head.y == bodyposition.y) {
			state->info.playing = false;  // Game over αν χτυπήσει το σώμα του
		}
	}


    // συγκρουσεις με μηλα, μεγαλωνει το φιδι και αυξανεται το σκορ
    // Δημιουργώ μια λίστα για να αποθηκεύσω τα keys των μήλων που πρέπει να αφαιρεθούν
	List keys_to_remove = list_create(NULL);  // ΟΧΙ free, γιατί δεν κάνεις malloc
// Ελέγχω για συγκρούσεις με μήλα
for (MapNode node1 = map_first(state->objects);
     node1 != MAP_EOF;
     node1 = map_next(state->objects, node1)) {
    Object obj = map_node_value(state->objects, node1);
    if (obj->type == APPLE) {
        Vector2 appleposition = obj->position;

        if (snake_head_pos(snake).x == appleposition.x && snake_head_pos(snake).y == appleposition.y) {
            // Αυξανεται το σκορ
            state->info.score++;

            // Προσθετω νεο κεφαλι στο φιδι
            list_insert_next(snake, list_last(snake),
                create_vector(move_in_direction(snake_head_pos(snake), state->info.snake_direction, SNAKE_SIZE)));

            // Κάνω copy το key και το βάζω στη λίστα για να το αφαιρέσω μετά
			GridCoord* key = map_node_key(state->objects, node1);
		GridCoord* key_copy = malloc(sizeof(GridCoord));   // κάνεις δικό σου αντίγραφο!
		*key_copy = *key;
		list_insert_next(keys_to_remove, LIST_BOF, key_copy);  // σωστά βάζεις το copy!

        }
    }
}

// Αφαιρώ τα μήλα που αποθηκεύτηκαν για διαγραφή
	for (ListNode node = list_first(keys_to_remove);
		node != LIST_EOF;
		node = list_next(keys_to_remove, node)) {
		GridCoord* key = list_node_value(keys_to_remove, node);
		map_remove(state->objects, key);
	}
	list_destroy(keys_to_remove);  // Ελευθερώνω τη λίστα με τα keys

}

// Καταστρέφει την κατάσταση state ελευθερώνοντας τη δεσμευμένη μνήμη.
void state_destroy(State state) {
	map_destroy(state->objects);               // Ελευθερώνει και keys και values (λόγω των free που έδωσες στο map_create)
    list_destroy(state->info.snake);           // Ελευθερώνει το φίδι
    free(state);           
}