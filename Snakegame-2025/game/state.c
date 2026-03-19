
#include <stdlib.h>
#include <math.h>

#include "ADTVector.h"
#include "ADTList.h"
#include "state.h"

// Σταθερές για το παιχνίδι
#define MIN_DIST 100
#define MAX_DIST 400

#define APPLE_SIZE 30
#define EAGLE_SIZE 30

#define MIN_APPLES_NUM 3
#define MIN_EAGLES_NUM 2

#define UPDATE_STATE_FRAMES 4  // κάθε πόσα frames θα κινείται το φίδι

#define EAGLE_TURN_PROB 0.1     // πιθανότητα να αλλάξει κατεύθυνση ο αετός (10%)
#define EAGLE_SPEED 20          // πόσο γρήγορα κινείται ο αετός



// Οι ολοκληρωμένες πληροφορίες της κατάστασης του παιχνιδιού.
// Ο τύπος State είναι pointer σε αυτό το struct, αλλά το ίδιο το struct
// δεν είναι ορατό στον χρήστη.




// Bοηθητικές συναρτήσεις /////////////////////////////////////////////////////////////////////////////////
//
// Δημιουργεί και επιστρέφει ένα αντικείμενο
static Object create_object(ObjectType type, Vector2 position, double size, Direction direction) {
	Object obj = malloc(sizeof(*obj));
	obj->type = type;
	obj->position = position;
	obj->size = size;
	obj->direction = direction;
	return obj;
}
// υπολογιζει την αποσταση δυο διανυσματων
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
	    // Τυχαία θέση και κατεύθυνση
	    Vector2 position = move_in_direction(head_pos, randi(0, 3), randf(MIN_DIST, MAX_DIST));
	    Direction dir = randi(0, 3);
	    int size = type == APPLE ? APPLE_SIZE : EAGLE_SIZE;
	    Object obj = create_object(type, position, size, dir);
	    vector_insert_last(state->objects, obj);
	}
}
/////////////////////////////////////////////////////////////////////////////////////////////////////


// Δημιουργεί και επιστρέφει την αρχική κατάσταση του παιχνιδιού
State state_create() {
	// Δημιουργία του state
	State state = malloc(sizeof(*state));

	// Γενικές πληροφορίες
	state->info.playing = true;			// Το παιχνίδι ξεκινάει αμέσως
	state->info.paused = false;			// Χωρίς να είναι paused
	state->info.score = 0;				// Αρχικό σκορ 0
	state->frame_counter = 0;			// Αρχικό frame 0

	// Δημιουργούμε το φίδι
	state->info.snake = list_create(free);													// αυτόματη αποδέσμευση μνήμης
	list_insert_next(state->info.snake, LIST_BOF, create_vector((Vector2){0, 0}));			// κεφάλι
	list_insert_next(state->info.snake, LIST_BOF, create_vector((Vector2){-SNAKE_SIZE, 0}));// ουρά

	state->info.snake_direction = RIGHT;	// Αρχική κίνηση προς τα δεξιά

	// Δημιουργούμε το vector των αντικειμένων, και προσθέτουμε αντικείμενα
	state->objects = vector_create(0, NULL);

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
	for(int i=0; i<vector_size(state->objects); i++){
		Object obj = vector_get_at(state->objects, i);
		float x = obj->position.x;
		float y = obj->position.y;
		if (x >= top_left.x && x <= bottom_right.x && y >= top_left.y && y <= bottom_right.y){
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
		
		// Ανανεώνω το position του φιδιου
		List snake = state->info.snake;
			// Αν πατηθουν κουμπια μετακινηται το φιδακι και αποτρεπουμε την αναστροφη
		if(keys->right && state->info.snake_direction != LEFT)
			state->info.snake_direction = RIGHT;
		if(keys->left && state->info.snake_direction != RIGHT)
			state->info.snake_direction = LEFT;
		if(keys->up && state->info.snake_direction != DOWN)
			state->info.snake_direction = UP;
		if(keys->down && state->info.snake_direction != UP)
			state->info.snake_direction = DOWN;


		// με τα παρακατω προκυπτει πολυπλοκοτητα Ο(1)
		//παιρνω το κεφαλι
		Vector2* head_pos = list_node_value(snake, list_last(snake));

		//δεσμευω μνημη για να αποθηκευσω τα στοιχεια της καινουριας θεσης
		Vector2* new_head = malloc(sizeof(Vector2));
		
		//υπολογιζω το καινουριο κεφαλι
		*new_head = move_in_direction(*head_pos, state->info.snake_direction, SNAKE_SIZE);

		//βγαζω την ουρα απο την λιστα
		list_remove_next(snake, LIST_BOF);

		//προσθετω το καινουριου στην αρχη
		list_insert_next(snake, list_last(snake), new_head);
	}

	// Κάνω iterate και ανανεώνω τις θέσεις για όλα τα αντικείμενα
	List snake = state->info.snake;
	int apple_no = 0;
	int eagle_no = 0;
	for(int i=0; i<vector_size(state->objects); i++){
		Object obj = vector_get_at(state->objects, i);
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

	//οταν τα μηλα ή οι αετοι ειναι λιγοι προσθετω 
	if(apple_no < MIN_APPLES_NUM){
		add_random_objects(state, APPLE, MIN_APPLES_NUM - apple_no);
	}
	if(eagle_no < MIN_EAGLES_NUM){
		add_random_objects(state, EAGLE, MIN_EAGLES_NUM - eagle_no);
	}

	
	//Τα updates γίνονται κάθε UPDATE_STATE_FRAMES 
	if(state->frame_counter % UPDATE_STATE_FRAMES == 0){
		// Κάνω iterate και ανανεώνω τις θέσεις για τα αντικείμενα
		for(int i=0; i<vector_size(state->objects); i++){
			Object obj = vector_get_at(state->objects, i);
			if(obj->type == EAGLE){
				if ((rand() % 1000) < (int)(EAGLE_TURN_PROB * 1000)) {
					Direction new_dir = rand() % 4;  // 0 ως 3: UP, DOWN, LEFT, RIGHT
					obj->direction = new_dir;
					obj->position = move_in_direction(obj->position, obj->direction, EAGLE_SPEED);
				}
			}
		}
	}

	//ελενχος για συγκρουσεις
	int size = vector_size(state->objects);
	Vector2 head_pos = snake_head_pos(state->info.snake);
	Vector2 new_pos = move_in_direction(head_pos, state->info.snake_direction, SNAKE_SIZE);

        for (int i = 0; i < size; i++) {
            Object obj = vector_get_at(state->objects, i);
            double dist = vec_distance(new_pos, obj->position);

            if (dist < (SNAKE_SIZE / 2 + obj->size / 2)) {
                if (obj->type == APPLE) {
                    state->info.score += 1;

					list_insert_next(snake, list_last(snake), create_vector(move_in_direction(snake_head_pos(snake), state->info.snake_direction, SNAKE_SIZE)));

                    // Αντικαθιστούμε το αντικείμενο στο i με το τελευταίο και αφαιρούμε το τελευταίο
                    int last_index = vector_size(state->objects) - 1;
                    vector_set_at(state->objects, i, vector_get_at(state->objects, last_index));
                    vector_remove_last(state->objects);
                    add_random_objects(state, APPLE, 1);
                    size--;  // Επειδή μικρύναμε το vector
                    i--;     // Για να ελέγξουμε το αντικείμενο που ήρθε στη θέση i
                } else if (obj->type == EAGLE) {
                    state->info.playing = false;  // GAME OVER
                }
            }
		// ελενχος για συγκρουσεις με σωμα
		for(
			ListNode node = list_first(snake);
			node != list_last(snake);
			node = list_next(snake, node)
		){
			Vector2 node_pos = *(Vector2*)list_node_value(snake, node);
			if(snake_head_pos(snake).x == node_pos.x && snake_head_pos(snake).y ==  node_pos.y){
				state->info.playing = false;
			}
		}	
	}

}

// Καταστρέφει την κατάσταση state ελευθερώνοντας τη δεσμευμένη μνήμη.
void state_destroy(State state) {
	// Προς υλοποίηση
}
