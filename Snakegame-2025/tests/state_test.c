//////////////////////////////////////////////////////////////////
//
// Test για το state.h module
//
//////////////////////////////////////////////////////////////////

#include <stdlib.h>
#include <math.h>
#include "acutest.h"			// Απλή βιβλιοθήκη για unit testing

#include "state.h"


///// Βοηθητικές συναρτήσεις ////////////////////////////////////////
//
// Ελέγχει την (προσεγγιστική) ισότητα δύο double
// (λόγω λαθών το a == b δεν είναι ακριβές όταν συγκρίνουμε double).
static bool double_equal(double a, double b) {
	return fabs(a-b) < 1e-6;
}

// Ελέγχει την ισότητα δύο διανυσμάτων
static bool vec2_equal(Vector2 a, Vector2 b) {
	return double_equal(a.x, b.x) && double_equal(a.y, b.y);
}

// Επιστρέφει τη θέση του κεφαλιού του φιδιού
static Vector2 snake_head_pos(State state) {
	List snake = state_info(state)->snake;
	return *(Vector2*)list_node_value(snake, list_last(snake));
}
/////////////////////////////////////////////////////////////////////


void test_state_create() {
	State state = state_create();
	TEST_ASSERT(state != NULL);

	StateInfo info = state_info(state);
	TEST_ASSERT(info != NULL);

	TEST_ASSERT(info->playing);
	TEST_ASSERT(!info->paused);
	TEST_ASSERT(info->score == 0);

	// Αρχική θέση φιδιού
	TEST_ASSERT( vec2_equal( snake_head_pos(state), (Vector2){0,0}) );

	// Προσθέστε επιπλέον ελέγχους
}

void test_state_update() {
	State state = state_create();
	TEST_ASSERT(state != NULL && state_info(state) != NULL);

	// Πληροφορίες για τα πλήκτρα (αρχικά κανένα δεν είναι πατημένο)
	struct key_state keys = { false, false, false, false, false, false };
	
	// Χωρίς κανένα πλήκτρο, το φίδι μετακινείται προς τα δεξιά
	for (int i = 0; i < UPDATE_STATE_FRAMES; i++)
		state_update(state, &keys);	// χρειαζόμαστε πολλαπλά updates για να κινηθεί το φίδι

	TEST_ASSERT( vec2_equal( snake_head_pos(state), (Vector2){SNAKE_SIZE,0}) );
	TEST_ASSERT( state_info(state)->snake_direction == RIGHT );

	// Προσθέστε επιπλέον ελέγχους
}



// Λίστα με όλα τα tests προς εκτέλεση
TEST_LIST = {
	{ "test_state_create", test_state_create },
	{ "test_state_update", test_state_update },

	{ NULL, NULL } // τερματίζουμε τη λίστα με NULL
};
