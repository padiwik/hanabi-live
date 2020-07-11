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

data = "13725 0 13725 8 13725 12 13725 20 13739 2 13808 0 13808 3 13808 6 13815 0 14074 2 14236 0 14238 25 14238 31 14238 46 14262 1 14262 4 14304 0 14304 4 14304 8 14304 28 14304 32 14588 8 14588 23 15047 0 15047 6 20254 1 20254 7 30047 2 30047 5 30070 0 30070 3 30070 33 30072 35 30072 41 30074 2 30074 11 30074 41 30973 2 30973 8 30973 50 39544 10 39544 34 45015 0 49074 11 49074 21 49074 31 49818 17 50571 2 50571 5 56286 0 56286 40 77384 1 81889 14 81889 26 90472 3 90472 5 91077 0 91077 2 91077 18 91077 20 91077 22 91077 32 91077 42 91077 46 91077 48 91077 54 91077 58 91229 34 94094 0 98102 1 98102 5 98102 11 98102 13 98102 29 98102 45 98102 49 98102 57 98673 1 102843 1 102843 3 104019 7 104019 12 104019 22 108716 7 108716 15 108716 19 108716 33 108716 47 108716 59 108731 0 115946 0 115946 2 115946 8 115946 14 115946 16 115946 26 115946 30 115946 54 119277 0 119277 10 119336 3 119336 5 119336 13 119336 17 119336 27 119336 31 119336 33 119336 41 119336 45 119336 59 123635 0 123635 2 123635 4 125078 0 125078 4 125078 10 125078 18 125078 30 125078 32 125078 46 125078 48 125078 56 125208 0 125208 9 125208 18 125208 33 125208 36 125208 39 125208 54 126806 0 126806 6 126806 21 126806 42 126870 3 126870 11 126870 23 126870 35 131133 7 131133 37 131133 43 131133 51 134315 0 134315 10 135363 0 135363 2 135363 14 135363 22 135363 24 135363 46 137538 3 137538 7 137538 19 137538 23 137538 47 137538 51 138732 2 138732 50 140962 2 140962 7 140962 22 140962 47 141378 3 141378 5 141378 7 141378 11 141378 19 141378 23 141398 0 141398 2 141398 4 141398 8 141398 12 141398 18 142473 3 142473 7 143723 3 143723 11 145375 0 145375 3 145375 6 145375 15 145375 21 145375 42 145671 0 145671 2 145671 4 146429 0 146429 28 150286 1 150520 0 150520 20 150520 56 153263 0 153263 4 159793 19 162154 0 163105 3 163495 3 166007 3 166162 1 167853 1"
data_arr = data.split()

if debug:
    data_arr = [13725, 0]

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

i = 0
while i < len(data_arr):
    game_id = int(data_arr[i])
    first_turn = int(data_arr[i + 1])
    second_turn = first_turn + 1

    cursor = conn.cursor()
    query = """UPDATE game_actions
	SET type = CASE turn
		WHEN %(first_turn)s THEN (SELECT type FROM game_actions WHERE game_id = %(game_id)s AND turn = %(second_turn)s)
		WHEN %(second_turn)s THEN (SELECT type FROM game_actions WHERE game_id = %(game_id)s AND turn = %(first_turn)s)
	END,
	target = CASE turn
		WHEN %(first_turn)s THEN (SELECT target FROM game_actions WHERE game_id = %(game_id)s AND turn = %(second_turn)s)
		WHEN %(second_turn)s THEN (SELECT target FROM game_actions WHERE game_id = %(game_id)s AND turn = %(first_turn)s)
	END,
	value = CASE turn
		WHEN %(first_turn)s THEN (SELECT value FROM game_actions WHERE game_id = %(game_id)s AND turn = %(second_turn)s)
		WHEN %(second_turn)s THEN (SELECT value FROM game_actions WHERE game_id = %(game_id)s AND turn = %(first_turn)s)
	END
    WHERE game_id = %(game_id)s AND turn IN (%(first_turn)s, %(second_turn)s);"""
    cursor.execute(
        query,
        {"game_id": game_id, "first_turn": first_turn, "second_turn": second_turn},
    )
    i += 2

conn.commit()
conn.close()
