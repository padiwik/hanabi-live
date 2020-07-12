#!/usr/bin/env python3
# (the "dotenv" module does not work in Python 2)

# We need to swap Genius' consecutive color and rank clues, since the server will no longer accept
# the old order

import sys

if sys.version_info < (3, 0):
    print("This script requires Python 3.x.")
    sys.exit(1)

# Imports
import os
import dotenv
import psycopg2

# Configuration
debug = False

# Import environment variables
dotenv.load_dotenv(dotenv.find_dotenv())

# Variables
user = os.getenv("DB_USER")
password = os.getenv("DB_PASS")
host = os.getenv("DB_HOST")
if host == "":
    host = "localhost"
port = os.getenv("DB_PORT")
if port == "":
    port = "5432"
database = os.getenv("DB_NAME")

# Connect to the PostgreSQL database
conn = psycopg2.connect(
    host=host, port=port, user=user, password=password, database=database,
)

# Get a list of every game ID
cursor = conn.cursor()
query = (
    "SELECT id, name FROM games WHERE id > 130000 AND name LIKE '!replay%' ORDER BY id"
)
cursor.execute(query)

games = []  # (game_id, last_turn_old, last_turn_combined)
for (game_id, game_name) in cursor:
    old_game_id = int(
        game_name.split()[1]
    )  # text after first space, but before second (if any)

    cursor2 = conn.cursor()
    cursor2.execute(
        "SELECT MAX(turn) FROM game_actions WHERE game_id = %s", (old_game_id,)
    )
    row = cursor2.fetchone()
    cursor2.close()
    last_turn_old = row[0]

    cursor2 = conn.cursor()
    cursor2.execute("SELECT MAX(turn) FROM game_actions WHERE game_id = %s", (game_id,))
    row = cursor2.fetchone()
    cursor2.close()
    last_turn_combined = row[0]

    games.append((game_id, last_turn_old, last_turn_combined))

cursor.close()
print("LOADED " + str(len(games)) + " GAMES!", flush=True)
print(games)

if debug:
    games = [(132993, 1, 30)]
for (game_id, last_turn_old, last_turn_combined) in games:
    num_turns_real = last_turn_combined - last_turn_old
    for i in range(last_turn_old + 1, last_turn_combined + 1):
        cursor = conn.cursor()
        query = """UPDATE game_actions
        SET type = (SELECT type FROM game_actions WHERE game_id = %(game_id)s AND turn = %(recorded_turn)s),
        target = (SELECT target FROM game_actions WHERE game_id = %(game_id)s AND turn = %(recorded_turn)s),
        value = (SELECT value FROM game_actions WHERE game_id = %(game_id)s AND turn = %(recorded_turn)s)
        WHERE game_id = %(game_id)s AND turn = %(real_turn)s;"""
        cursor.execute(
            query,
            {
                "game_id": game_id,
                "recorded_turn": i,
                "real_turn": i - last_turn_old - 1,
            },
        )
        cursor.close()
    for i in range(num_turns_real, last_turn_combined + 1):
        cursor = conn.cursor()
        query = "DELETE FROM game_actions WHERE game_id = %s AND turn = %s;"
        cursor.execute(query, (game_id, i))
        cursor.close()

conn.commit()
conn.close()
