# Το Makefile αυτό βρίσκεται στο root ολόκληρου του project

# Paths
LIB = lib
INCLUDE = include

# Raylib paths (homebrew installation)
RAYLIB_PATH = /opt/homebrew/Cellar/raylib/5.5
RAYLIB_INCLUDE = $(RAYLIB_PATH)/include
RAYLIB_LIB = $(RAYLIB_PATH)/lib

# Compiler settings
CC = gcc
CFLAGS = -Wall -Werror -g -I. -I$(INCLUDE) -I$(RAYLIB_INCLUDE)
LDFLAGS = -L$(RAYLIB_LIB) -lraylib -lm -framework CoreVideo -framework IOKit

# Game files
GAME_DIR = game
GAME_OBJS = $(GAME_DIR)/game.o $(GAME_DIR)/state.o $(GAME_DIR)/interface.o
GAME_EXEC = $(GAME_DIR)/game

# Targets
.PHONY: all game clean run

all: game

# Build game
game: $(GAME_EXEC)

$(GAME_EXEC): $(GAME_OBJS)
	$(CC) $(GAME_OBJS) -o $(GAME_EXEC) $(LDFLAGS) $(LIB)/k08_macos.a

$(GAME_DIR)/%.o: $(GAME_DIR)/%.c
	$(CC) $(CFLAGS) -c -o $@ $<

clean:
	rm -f $(GAME_OBJS) $(GAME_EXEC)

run: $(GAME_EXEC)
	cd $(GAME_DIR) && bash -c './game'