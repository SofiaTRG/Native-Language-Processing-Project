import re
import ast
import google.generativeai as genai
import numpy as np
import chess
import chess.engine
from evaluation import move_normalized_score
engine = chess.engine.SimpleEngine.popen_uci("stockfish-windows-x86-64-avx2")
# === CONFIG ===
API_KEY = "AIzaSyAQrxYX6Zw_CwlhwoOnxiL4FG6zJiJgMrI"
#API_KEY = "AIzaSyCQJKvzXyVO_P2GyveEZ8_VNmnk6sbhKDs"
#API_KEY = "AIzaSyDWS_ScRCal-Jdp4ZC-JdwXVLlWKpW6Nzs"
#DATA_FILE_V = "datasets/easy_verbal.txt"  # Change to your file
#DATA_FILE_B="datasets/easy_turn_board.txt"

# === SETUP GEMINI ===
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")


def moves_to_position(moves_str):
    """
    Given a string of space-separated moves in algebraic notation,
    returns the board position as a 2D array of strings.
    """
    board = chess.Board()
    moves = moves_str.split()

    for move in moves:
        try:
            board.push_san(move)
        except ValueError:
            print(f"Invalid move: {move}")
            return None
    return board
# === UTILITIES ===
def extract_all_chess_moves(text):
    # Normalize text
    for char in '()*\n/':
        text = text.replace(char, ' ')

    pattern = r'(?:O-O(?:-O)?[+#]?|[KQRNB]?[a-h]?[1-8]?x?[a-h][1-8](?:=[QRNB])?[+#]?)(?=\s|[.,]|$)'
    return re.findall(pattern, text, re.IGNORECASE)


import json

def extract_history(file_path):
    """Extract only the move history from a *_history.jsonl file"""
    history_array = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            obj = json.loads(line)
            moves = obj.get("move_history_copy", "")
            history_array.append([moves])
    return history_array


def extract_board(file_path):
    """Extract board, turn, and move history from a *_turn_board.jsonl file"""
    history_array = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            obj = json.loads(line)
            board_str = obj.get("board", "")
            turn = obj.get("turn", None)
            moves = obj.get("move_history_copy", "")
            history_array.append([board_str, turn, moves])
    return history_array


def extract_verbal(file_path):
    """Extract verbal description and move history from a *_verbal.jsonl file"""
    result = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            obj = json.loads(line)
            description = obj.get("verbal", "")
            moves = obj.get("move_history_copy", "")
            if description:
                result.append([description, moves])
    return result

dif=1 # chose here
DATA_FILE_V = "data/easy_verbal.jsonl"  # Change to your file
DATA_FILE_B="data/easy_turn_board.jsonl"
DATA_FILE_H="data/easy_history.jsonl"
if dif==2:
    DATA_FILE_V = "data/normal_verbal.jsonl"  # Change to your file
    DATA_FILE_B="data/normal_turn_board.jsonl"
    DATA_FILE_H="data/normal_history.jsonl"
if dif==3:
    DATA_FILE_V = "data/hard_verbal.jsonl"  # Change to your file
    DATA_FILE_B="data/hard_turn_board.jsonl"
    DATA_FILE_H="data/hard_history.jsonl"
scoress=[]
txtss=[]
for j in range (1,4):
    DATA_FORMAT=j
    txt=""
    # === MAIN ===
    if(DATA_FORMAT==1):
        positions = extract_verbal(DATA_FILE_V)
        txt="verbel"
    if(DATA_FORMAT==2):
        positions = extract_board(DATA_FILE_B)
        txt="board"
    if(DATA_FORMAT==3):
        positions = extract_history(DATA_FILE_H)
        txt="history"
    sum_score = 0
    start=0
    #len(positions)
    for i in range(start, len(positions)):
        pos=positions[i]
        if(DATA_FORMAT==1):
            board = moves_to_position(pos[1])
        if DATA_FORMAT==2:

            board = moves_to_position(pos[2])
        if DATA_FORMAT==3:

            board = moves_to_position(pos[0])
        if (DATA_FORMAT==1):
            if(pos[1]==True):
                turn="white."
            else:
                turn="black."
            prompt= pos[0]+" turn of "+turn
        if(DATA_FORMAT==2):
            if(pos[1]==True):
                turn="white."
            else:
                turn="black."
            rows = pos[0].split("\n")  # split into 8 rows
    # convert each row into a list of characters, ignoring spaces
            board_2d = [row.split() for row in pos[0].split("\n")]
            prompt = f"the board is:\n{board_2d}\n\nturn of {turn}\n"
        if (DATA_FORMAT==3):
            prompt=pos[0]
        prompt="What would you play in this position just what move make sure it legal move: "+prompt
        # Build prompt depending on format
        #if DATA_FORMAT == 3:
        #  prompt = f"Here is the move list so far: {pos}. Suggest the next move."
        #else:
        #    prompt = f"Given this position:\n{pos}\nSuggest the next move."

        # Call Gemini
        response = model.generate_content(prompt)
        moves = extract_all_chess_moves(response.text)
        # Evaluate
        max=0
        for move in moves:
            score =move_normalized_score(board,move)
            if(score>max):
                max=score
        score=max
        sum_score += score
        print("round",i)
        print("avg score in game "+str(sum_score/(i+1-start)) + " in this format " + txt)
    scoress.append(sum_score/(i+1-start))
    txtss.append(txt)
for j in range (0,3):
    print("final avg score in date format "+ txtss[j]+" "+str(scoress[i]))
# Final average