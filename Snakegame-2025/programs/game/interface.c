#include "raylib.h"

#include "state.h"
#include <string.h>
#include "interface.h"

// Assets
Texture bird_img;
Sound game_over_snd;
Music game_song;
Texture apple_img;
Texture eagle_img;
short game_over_played = 0;



void interface_init() {
	// Αρχικοποίηση του παραθύρου
	InitWindow(SCREEN_WIDTH, SCREEN_HEIGHT, "My Snake Game");
	SetTargetFPS(60);
	InitAudioDevice();

	// Φόρτωση εικόνων και ήχων
	bird_img = LoadTextureFromImage(LoadImage("assets/bird.png"));
	apple_img = LoadTextureFromImage(LoadImage("assets/apple.png"));
	eagle_img = LoadTextureFromImage(LoadImage("assets/eagle.png"));
	game_over_snd = LoadSound("assets/game_over.ogg"); // το ogg παίζει καλύτερα σε web
    game_song = LoadMusicStream("assets/gamesong.mp3");
    PlayMusicStream(game_song);
}

void interface_close() {
	CloseAudioDevice();
	CloseWindow();
}

void interface_draw_frame(State state) {
    BeginDrawing();
    UpdateMusicStream(game_song);
    // Καθαρισμός, θα τα σχεδιάσουμε όλα από την αρχή
	ClearBackground(DARKGRAY);

    // Υποθέτοντας πως η κάμερα είναι κεντραρισμένη στο κεφάλι του φιδιού:
    Vector2 snake_head = snake_head_pos(state->info.snake);

    float offset_x = snake_head.x - SCREEN_WIDTH / 2;
    float offset_y = snake_head.y - SCREEN_HEIGHT / 2;

    // Παίρνουμε όλα τα αντικείμενα που είναι στην οθόνη
    Vector2 top_left = (Vector2){ offset_x, offset_y };
    Vector2 bottom_right = (Vector2){ offset_x + SCREEN_WIDTH, offset_y + SCREEN_HEIGHT };
    List visible_objects = state_objects(state, top_left, bottom_right);

    // Ζωγραφίζουμε τα αντικείμενα
    for (
        ListNode node = list_first(visible_objects);
        node != LIST_EOF;
        node = list_next(visible_objects, node)
    ){
        Object obj = list_node_value(visible_objects, node);

        // Μετατροπή συντεταγμένων πίστας → οθόνης
        float screen_x = obj->position.x - offset_x;
        float screen_y = obj->position.y - offset_y;

        if (obj->type == APPLE)
            DrawTexture(apple_img, screen_x - bird_img.width/2, screen_y - bird_img.height/2, WHITE);
        else if (obj->type == EAGLE)
            DrawTexture(eagle_img, screen_x - bird_img.width/2, screen_y - bird_img.height/2, WHITE);

    }

    // Ζωγραφίζουμε το φίδι
    for (ListNode node = list_first(state->info.snake); node != LIST_EOF; node = list_next(state->info.snake, node)) {
        Vector2* part = list_node_value(state->info.snake, node);

        float screen_x = part->x - offset_x;
        float screen_y = part->y - offset_y;

        DrawCircle(screen_x, screen_y, SNAKE_SIZE / 2, GREEN);
    }
    for (
        ListNode node = list_first(visible_objects);
        node != LIST_EOF;
        node = list_next(visible_objects, node)
    ){
        Object obj = list_node_value(visible_objects, node);

        // Μετατροπή συντεταγμένων πίστας → οθόνης
        float screen_x = obj->position.x - offset_x;
        float screen_y = obj->position.y - offset_y;

        if (obj->type == APPLE)
            DrawTexture(apple_img, screen_x - bird_img.width/2, screen_y - bird_img.height/2, WHITE);
        else if (obj->type == EAGLE)
            DrawTexture(eagle_img, screen_x - bird_img.width/2, screen_y - bird_img.height/2, WHITE);

    }
    // Αν το παιχνίδι έχει τελειώσει, σχεδιάζομαι το μήνυμα για να ξαναρχίσει
	if (!state->info.playing) {
        if (game_over_played == 0) {
            StopMusicStream(game_song);         
            PlaySound(game_over_snd);           
            game_over_played = 1;                // Σημειώνουμε ότι έπαιξε
        }

        const int gameOverFontSize = 60;
        const int pressEnterFontSize = 24;

        const char* gameOverMsg = "GAME OVER";
        const char* pressEnterMsg = "PRESS [ENTER] TO PLAY AGAIN!";

        int screenWidth = GetScreenWidth();
        int screenHeight = GetScreenHeight();

        StopMusicStream(game_song);             // Σταμάτα τη μουσική
        PlaySound(game_over_snd);               // Παίξε τον ήχο game over (μια φορά)


        DrawText(
            gameOverMsg,
            screenWidth / 2 - MeasureText(gameOverMsg, gameOverFontSize) / 2,
            screenHeight / 2 - 80,
            gameOverFontSize,
            RED
        );

        DrawText(
            pressEnterMsg,
            screenWidth / 2 - MeasureText(pressEnterMsg, pressEnterFontSize) / 2,
            screenHeight / 2,
            pressEnterFontSize,
            RED
        );
	}
    

    // Σχεδιάζουμε το σκορ και το FPS counter
	DrawText(TextFormat("size %2i", state->info.score), 20, 20, 40, YELLOW);
	DrawFPS(SCREEN_WIDTH - 100, 20);


    // Ηχος, αν είμαστε στο frame που συνέβη το game_over


    EndDrawing();
}
