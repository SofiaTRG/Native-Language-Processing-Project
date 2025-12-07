import chess
import chess.engine

import requests
import io
import time
import chess
import chess.pgn
import os
import re
import json

def parse_positions(file_content):
    """Parse positions from file content and return a list of position dictionaries."""
    positions = []

    # Split content by position markers
    pos_blocks = re.split(r'pos \d+:', file_content)

    for block in pos_blocks[1:]:  # Skip the first empty split
        block = block.strip()
        if not block:
            continue

        lines = block.split('\n')

        # Store the raw block content and extract move_history_copy for deduplication
        position_data = {
            'raw_content': block,
            'lines': [line.strip() for line in lines if line.strip()]
        }

        move_sequence = ""

        # Find the move_history_copy line for deduplication
        for line in lines:
            line = line.strip()
            if line.startswith('move_history_copy:'):
                move_sequence = line.replace('move_history_copy:', '').strip()
                break

        # Use move sequence as the unique identifier
        position_data['unique_key'] = move_sequence
        positions.append(position_data)

    return positions


def remove_duplicates(positions):
    """Remove duplicate positions based on move sequences."""
    seen_sequences = set()
    unique_positions = []

    for pos in positions:
        if pos['unique_key'] not in seen_sequences:
            seen_sequences.add(pos['unique_key'])
            unique_positions.append(pos)

    return unique_positions


def format_output(positions):
    """Format positions back to the original file format."""
    output = []

    for i, pos in enumerate(positions, 1):
        output.append(f"pos {i}:")

        # Add all the lines from the original position
        for line in pos['lines']:
            output.append(line)

        output.append("")  # Empty line between positions

    return '\n'.join(output)


def process_file(input_file_path, output_file_path=None):
    """Process a single file to remove duplicates."""

    # Read input file
    try:
        with open(input_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: File '{input_file_path}' not found.")
        return False
    except Exception as e:
        print(f"Error reading file '{input_file_path}': {e}")
        return False

    # Parse positions
    positions = parse_positions(content)
    print(f"Found {len(positions)} total positions in {input_file_path}")

    # Remove duplicates
    unique_positions = remove_duplicates(positions)
    duplicates_removed = len(positions) - len(unique_positions)
    print(f"Removed {duplicates_removed} duplicate positions")
    print(f"Final count: {len(unique_positions)} unique positions")

    # Generate output filename if not provided
    if output_file_path is None:
        base_name = os.path.splitext(input_file_path)[0]
        output_file_path = f"{base_name}_clean.txt"

    # Write output file
    try:
        formatted_output = format_output(unique_positions)
        with open(output_file_path, 'w', encoding='utf-8') as f:
            f.write(formatted_output)
        print(f"Output written to: {output_file_path}")
        return True
    except Exception as e:
        print(f"Error writing output file '{output_file_path}': {e}")
        return False


def process_multiple_files(file_paths, output_dir=None):
    """Process multiple files and remove duplicates from each."""

    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for file_path in file_paths:
        print(f"\nProcessing: {file_path}")

        if output_dir:
            filename = os.path.basename(file_path)
            base_name = os.path.splitext(filename)[0]
            output_path = os.path.join(output_dir, f"{base_name}_clean.txt")
        else:
            output_path = None

        process_file(file_path, output_path)



USERNAME = "magnuscarlsen"
BASE_URL = f"https://api.chess.com/pub/player/{USERNAME}/games/archives"
HEADERS = {
    "User-Agent": "my-chess-tool/1.0 (user: yaron; contact: your_email@example.com)"
}

def get_archives():
    resp = requests.get(BASE_URL, headers=HEADERS)
    resp.raise_for_status()
    return resp.json().get("archives", [])

def download_month_pgn(archive_url):
    url = archive_url + "/pgn"
    resp = requests.get(url, headers=HEADERS)
    resp.raise_for_status()
    return io.StringIO(resp.text)

def parse_games(pgn_str_io, max_games=None):
    games = []
    while True:
        game = chess.pgn.read_game(pgn_str_io)
        if game is None:
            break
        games.append(game)
        if max_games and len(games) >= max_games:
            break
    return games

def game_quality_metric(game):
    h = game.headers
    white = (h.get("White","") or "").lower()
    black = (h.get("Black","") or "").lower()
    # opponent rating (whichever side is NOT Magnus)
    try:
        if white == USERNAME.lower():
            opp_elo = int(h.get("BlackElo", 0) or 0)
        else:
            opp_elo = int(h.get("WhiteElo", 0) or 0)
    except:
        opp_elo = 0
    # tie-break by number of moves
    return (opp_elo, len(list(game.mainline_moves())))

def fetch_and_select_top_games(top_n=10):
    archives = get_archives()
    all_games = []
    for archive in archives:
        print(f"Fetching: {archive}")
        pgn_io = download_month_pgn(archive)
        games = parse_games(pgn_io)
        all_games.extend(games)
        time.sleep(1)  # be polite
    all_games.sort(key=game_quality_metric, reverse=True)
    return all_games[:top_n]

def format_game_as_lines(game):
    """Return one string:
    game
    1. e4
    e5
    2. Nf3
    Nc6
    ...
    """
    board = game.board()
    out = ["game"]
    move_no = 1
    for move in game.mainline_moves():
        san = board.san(move)
        if board.turn == chess.WHITE:
            # White to move => print numbered white line
            out.append(f"{move_no}. {san}")
        else:
            # Black to move => print black line
            out.append(san)
            move_no += 1
        board.push(move)
    return "\n".join(out)

def export_games_as_custom(games, filename="formatted_games.txt"):
    with open(filename, "w", encoding="utf-8") as f:
        first = True
        for g in games:
            s = format_game_as_lines(g)
            if not first:
                # no blank line between games to match your example
                f.write("\n")
            f.write(s)
            first = False
    print(f"Exported {len(games)} games to {filename}")







engine = chess.engine.SimpleEngine.popen_uci("stockfish-windows-x86-64-avx2")
def get_top_3_moves(board):

    infos = engine.analyse(board, chess.engine.Limit(time=0.1), multipv=3)
    # Return top 3 or less if fewer candidate
    scores = []
    for info in infos:
        score = info['score']
        if not score.is_mate():  # ignore mate scores
            scores.append(score.white().score() / 100)  # convert to centipawns


    return scores[:3]



def is_interesting_position(pos, threshold_hard=1, threshold_normal=0.5, threshold_easy=0):
    moves=get_top_3_moves(pos)
    if(len(moves)<3):
        return -1

    gap = abs(moves[0] - moves[2]) + abs(moves[0] - moves[1])
    if gap >= threshold_hard:
        return 2
    elif gap >= threshold_normal:
        return 1
    elif gap >= threshold_easy:
        return 0
    else:
        return -1

def board_to_array(board):
    """Convert python-chess board to 8x8 array format."""
    board_str = str(board)
    rows = board_str.split("\n")
    arr = []
    for row in rows:
        arr.append([c if c != "." else "." for c in row.split(" ")])
    return arr

def print_board_array(board):
    arr = board_to_array(board)
    for row in arr:
        print(row)
    print()


def describe_position(board: chess.Board, turn: str):
    # Mapping from piece letter to name
    piece_names = {
        'P': 'pawn', 'N': 'knight', 'B': 'bishop',
        'R': 'rook', 'Q': 'queen', 'K': 'king',
        'p': 'pawn', 'n': 'knight', 'b': 'bishop',
        'r': 'rook', 'q': 'queen', 'k': 'king'
    }

    # Separate storage for white and black
    white_pieces = {}
    black_pieces = {}

    for square in chess.SQUARES:  # iterate over all 64 squares
        piece = board.piece_at(square)
        if piece is None:
            continue

        symbol = piece.symbol()
        name = piece_names[symbol]
        sq_name = chess.square_name(square)

        if piece.color == chess.WHITE:   # White pieces
            white_pieces.setdefault(name, []).append(sq_name)
        else:                            # Black pieces
            black_pieces.setdefault(name, []).append(sq_name)

    # Helper to format descriptions
    def format_desc(color_pieces, color_name):
        if not color_pieces:
            return f"{color_name} has no pieces"
        parts = []
        for piece_type, squares in color_pieces.items():
            parts.append(f"{piece_type}s on {', '.join(squares)}")
        return f"{color_name} has " + "; ".join(parts)

    white_desc = format_desc(white_pieces, "White")
    black_desc = format_desc(black_pieces, "Black")

    return white_desc + ". " + black_desc + ". " + turn + "."


def play_game(moves,depth=3):
    global board
    move_history = []
    positions_hard = []
    positions_normal = []
    positions_easy = []
    white_to_move = True
    board = chess.Board()

    print_board_array(board)
    turn="true"
    for move in moves:
        move_history.append(move)
        try:
            copy_h=move_history.copy()
            board.push_san(move)
            copyB=board_to_array(board)
            interest_level=is_interesting_position(board)
            if interest_level == 2:
                verbal=describe_position(board,turn)
                positions_hard.append([copyB,turn,copy_h,verbal])
            elif interest_level == 1:
                verbal=describe_position(board,turn)
                positions_normal.append([copyB,turn,copy_h,verbal])

            elif interest_level == 0:
                verbal=describe_position(board,turn)
                positions_easy.append([copyB,turn,copy_h,verbal])
            if turn=="true":
                turn="false"
            else:
                turn="true"
        except ValueError as e:
               x=1
    return(positions_hard,positions_normal,positions_easy)






def parse_games_from_file(path):
    with open(path, 'r') as f:
        lines = [line.strip() for line in f if line.strip()]

    games = []
    current_game = []

    for line in lines:
        if line.lower() == 'game':
            if current_game:
                games.append(current_game)
                current_game = []
        else:
            # Strip off move numbers like "1.", "2." etc.
            if '.' in line:
                parts = line.split()
                for p in parts:
                    if '.' not in p:
                        current_game.append(p)
            else:
                current_game.append(line)

    if current_game:
        games.append(current_game)

    return games

def save_positions_to_jsonl(positions_hard, positions_normal, positions_easy, output_dir="data"):
    import os, json
    os.makedirs(output_dir, exist_ok=True)

    def format_board(b):
        if isinstance(b, str):
            return b
        if isinstance(b, list):
            return "\n".join(" ".join(str(cell) for cell in row) for row in b)
        return str(b)

    def format_text(x):
        if isinstance(x, (list, tuple)):
            try:
                return " ".join(map(str, x))
            except Exception:
                return json.dumps(x, ensure_ascii=False)
        return str(x)

    def unpack(rec):
        if isinstance(rec, dict):
            pos_value = rec.get("pos") or rec.get("position") or ""
            board = rec.get("board")
            wtm = rec.get("white_to_move") or rec.get("turn") or rec.get("wtm")
            move_hist = rec.get("move_history") or rec.get("history") or rec.get("moves") or ""
            verbal = rec.get("verbal") or rec.get("description") or ""
            return pos_value, board, wtm, move_hist, verbal

        try:
            n = len(rec)
        except TypeError:
            return "", rec, None, "", ""

        if n == 4:
            board, wtm, move_hist, verbal = rec
            return "", board, wtm, move_hist, verbal

        if n == 5:
            a0, a1, a2, a3, a4 = rec
            looks_like_board = isinstance(a0, list) or (isinstance(a0, str) and (a0.count("\n") >= 7 or a0.count("[") >= 2))
            if looks_like_board:
                board, wtm, move_hist, verbal, pos_value = rec
            else:
                pos_value, board, wtm, move_hist, verbal = rec
            return pos_value, board, wtm, move_hist, verbal

        seq = list(rec)
        wtm_idx = next((i for i, x in enumerate(seq) if isinstance(x, bool)), None)
        wtm = seq.pop(wtm_idx) if wtm_idx is not None else None
        board = next((x for x in seq if isinstance(x, list) or (isinstance(x, str) and (x.count("\n") >= 7 or x.count("[") >= 2))), None)
        if board is not None:
            seq.remove(board)
        move_hist = seq[0] if len(seq) > 0 else ""
        verbal = seq[1] if len(seq) > 1 else ""
        pos_value = seq[2] if len(seq) > 2 else ""
        return pos_value, board, wtm, move_hist, verbal

    def write_dataset(positions, difficulty_name):
        turn_board_file = os.path.join(output_dir, f"{difficulty_name}_turn_board.jsonl")
        history_file    = os.path.join(output_dir, f"{difficulty_name}_history.jsonl")
        verbal_file     = os.path.join(output_dir, f"{difficulty_name}_verbal.jsonl")

        with open(turn_board_file, "w", encoding="utf-8") as tb_f, \
                open(history_file,    "w", encoding="utf-8") as hist_f, \
                open(verbal_file,     "w", encoding="utf-8") as verb_f:

            for i, rec in enumerate(positions, start=1):
                pos_value, board, white_to_move, move_history, verbal = unpack(rec)

                move_history_copy = move_history  # duplicate

                tb_obj = {
                    "pos_id": i,
                    "position": pos_value,
                    "turn": white_to_move,
                    "board": format_board(board),
                    "move_history_copy": format_text(move_history_copy)
                }
                hist_obj = {
                    "pos_id": i,
                    "position": pos_value,
                    "move_history": format_text(move_history),
                    "move_history_copy": format_text(move_history_copy)
                }
                verb_obj = {
                    "pos_id": i,
                    "position": pos_value,
                    "verbal": format_text(verbal),
                    "move_history_copy": format_text(move_history_copy)
                }

                tb_f.write(json.dumps(tb_obj, ensure_ascii=False) + "\n")
                hist_f.write(json.dumps(hist_obj, ensure_ascii=False) + "\n")
                verb_f.write(json.dumps(verb_obj, ensure_ascii=False) + "\n")

    write_dataset(positions_hard, "hard")
    write_dataset(positions_normal, "normal")
    write_dataset(positions_easy, "easy")

def save_positions_to_txt(positions_hard, positions_normal, positions_easy, output_dir="data"):
    import os, json
    os.makedirs(output_dir, exist_ok=True)

    def format_board(b):
        if isinstance(b, str):
            return b
        if isinstance(b, list):
            return "\n".join(" ".join(str(cell) for cell in row) for row in b)
        return str(b)

    def format_text(x):
        if isinstance(x, (list, tuple)):
            try:
                return " ".join(map(str, x))
            except Exception:
                return json.dumps(x, ensure_ascii=False)
        return str(x)

    def unpack(rec):
        if isinstance(rec, dict):
            pos_value = rec.get("pos") or rec.get("position") or ""
            board = rec.get("board")
            wtm = rec.get("white_to_move") or rec.get("turn") or rec.get("wtm")
            move_hist = rec.get("move_history") or rec.get("history") or rec.get("moves") or ""
            verbal = rec.get("verbal") or rec.get("description") or ""
            return pos_value, board, wtm, move_hist, verbal

        try:
            n = len(rec)
        except TypeError:
            return "", rec, None, "", ""

        if n == 4:
            board, wtm, move_hist, verbal = rec
            return "", board, wtm, move_hist, verbal

        if n == 5:
            a0, a1, a2, a3, a4 = rec
            looks_like_board = isinstance(a0, list) or (isinstance(a0, str) and (a0.count("\n") >= 7 or a0.count("[") >= 2))
            if looks_like_board:
                board, wtm, move_hist, verbal, pos_value = rec
            else:
                pos_value, board, wtm, move_hist, verbal = rec
            return pos_value, board, wtm, move_hist, verbal

        seq = list(rec)
        wtm_idx = next((i for i, x in enumerate(seq) if isinstance(x, bool)), None)
        wtm = seq.pop(wtm_idx) if wtm_idx is not None else None
        board = next((x for x in seq if isinstance(x, list) or (isinstance(x, str) and (x.count("\n") >= 7 or x.count("[") >= 2))), None)
        if board is not None:
            seq.remove(board)
        move_hist = seq[0] if len(seq) > 0 else ""
        verbal = seq[1] if len(seq) > 1 else ""
        pos_value = seq[2] if len(seq) > 2 else ""
        return pos_value, board, wtm, move_hist, verbal

    def write_dataset(positions, difficulty_name):
        turn_board_file = os.path.join(output_dir, f"{difficulty_name}_turn_board.txt")
        history_file    = os.path.join(output_dir, f"{difficulty_name}_history.txt")
        verbal_file     = os.path.join(output_dir, f"{difficulty_name}_verbal.txt")

        with open(turn_board_file, "w", encoding="utf-8") as tb_f, \
                open(history_file,    "w", encoding="utf-8") as hist_f, \
                open(verbal_file,     "w", encoding="utf-8") as verb_f:

            for i, rec in enumerate(positions, start=1):
                pos_value, board, white_to_move, move_history, verbal = unpack(rec)

                # Duplicate move_history
                move_history_copy = move_history

                # Turn + Board file (with extra history)
                tb_f.write(f"pos {i}:\n")
                tb_f.write(f'position={json.dumps(pos_value, ensure_ascii=False)}\n')
                tb_f.write(f"turn: {white_to_move}\n")
                tb_f.write(f"board:\n{format_board(board)}\n")
                tb_f.write(f"move_history_copy: {format_text(move_history_copy)}\n\n")

                # Move history file (still includes duplicate)
                hist_f.write(f"pos {i}:\n")
                hist_f.write(f'position={json.dumps(pos_value, ensure_ascii=False)}\n')
                hist_f.write(f"{format_text(move_history)}\n")
                hist_f.write(f"move_history_copy: {format_text(move_history_copy)}\n\n")

                # Verbal file (with extra history)
                verb_f.write(f"pos {i}:\n")
                verb_f.write(f'position={json.dumps(pos_value, ensure_ascii=False)}\n')
                verb_f.write(f"{format_text(verbal)}\n")
                verb_f.write(f"move_history_copy: {format_text(move_history_copy)}\n\n")

    write_dataset(positions_hard, "hard")
    write_dataset(positions_normal, "normal")
    write_dataset(positions_easy, "easy")



top_games = fetch_and_select_top_games(10)
export_games_as_custom(top_games, "formatted_games.txt")
games = parse_games_from_file("formatted_games.txt")

all_hard, all_normal, all_easy = [], [], []

for i, moves in enumerate(games):
    print(i)
    hard, normal, easy = play_game(moves,5)
    all_hard.extend(hard)
    all_normal.extend(normal)
    all_easy.extend(easy)
print(len(all_hard), len(all_normal), len(all_easy))
save_positions_to_jsonl(all_hard, all_normal, all_easy)

engine.quit()

datasets_folder = "data"

# List of all your files (in the datasets folder)
file_names = [
    "easy_history.txt",
    "easy_turn_board.txt",
    "easy_verbal.txt",
    "hard_history.txt",
    "hard_turn_board.txt",
    "hard_verbal.txt",
    "normal_history.txt",
    "normal_turn_board.txt",
    "normal_verbal.txt"
]

# Create full paths to the files
file_list = [os.path.join(datasets_folder, filename) for filename in file_names]

print("Starting deduplication process for all files in 'data' folder...")
print("=" * 60)

# Check if datasets folder exists
if not os.path.exists(datasets_folder):
    print(f"Error: '{datasets_folder}' folder not found!")
    print("Please make sure the 'datasets' folder exists in the same directory as this script.")
    exit(1)

# Process each file
for file_path in file_list:
    filename = os.path.basename(file_path)
    print(f"\n{'=' * 25}")
    print(f"Processing: {filename}")
    print('=' * 25)

    # Check if file exists before processing
    if os.path.exists(file_path):
        # Generate output path in the same datasets folder
        base_name = os.path.splitext(file_path)[0]
        output_path = f"{base_name}_clean.txt"

        success = process_file(file_path, output_path)
        if success:
            print(f"✓ Successfully processed {filename}")
        else:
            print(f"✗ Failed to process {filename}")
    else:
        print(f"✗ File not found: {file_path}")

print(f"\n{'=' * 60}")
print("Deduplication process completed!")
print("Check the 'datasets' folder for '_clean.txt' files.")

def txt_to_jsonl(txt_file, jsonl_file):
    with open(txt_file, "r", encoding="utf-8") as infile, open(jsonl_file, "w", encoding="utf-8") as outfile:
        for i, line in enumerate(infile, start=1):
            obj = {"id": i, "text": line.strip()}
            outfile.write(json.dumps(obj) + "\n")
    print(f"Converted {txt_file} → {jsonl_file}")


def parse_jsonl_positions(file_content):
    """Parse positions from JSONL file content and return a list of position dictionaries."""
    positions = []

    for line_num, line in enumerate(file_content.strip().split('\n'), 1):
        line = line.strip()
        if not line:
            continue

        try:
            json_obj = json.loads(line)

            # Store the original JSON object
            position_data = {
                'json_object': json_obj,
                'line_number': line_num
            }

            # Extract move_history_copy for deduplication key
            move_sequence = ""
            if 'move_history_copy' in json_obj:
                move_sequence = json_obj['move_history_copy']
            elif 'move_history' in json_obj:
                move_sequence = json_obj['move_history']
            else:
                # If no move history field found, use the entire JSON as key
                move_sequence = json.dumps(json_obj, sort_keys=True)

            position_data['unique_key'] = move_sequence
            positions.append(position_data)

        except json.JSONDecodeError as e:
            print(f"Warning: Invalid JSON on line {line_num}: {e}")
            print(f"Skipping line: {line[:100]}...")
            continue

    return positions


def remove_duplicates(positions):
    """Remove duplicate positions based on move sequences."""
    seen_sequences = set()
    unique_positions = []

    for pos in positions:
        if pos['unique_key'] not in seen_sequences:
            seen_sequences.add(pos['unique_key'])
            unique_positions.append(pos)

    return unique_positions


def format_jsonl_output(positions):
    """Format positions back to JSONL format."""
    output_lines = []

    for pos in positions:
        json_line = json.dumps(pos['json_object'], ensure_ascii=False)
        output_lines.append(json_line)

    return '\n'.join(output_lines)


def process_jsonl_file(input_file_path, overwrite=True):
    """Process a single JSONL file to remove duplicates."""

    # Read input file
    try:
        with open(input_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: File '{input_file_path}' not found.")
        return False
    except Exception as e:
        print(f"Error reading file '{input_file_path}': {e}")
        return False

    # Parse positions
    positions = parse_jsonl_positions(content)
    print(f"Found {len(positions)} total positions in {input_file_path}")

    # Remove duplicates
    unique_positions = remove_duplicates(positions)
    duplicates_removed = len(positions) - len(unique_positions)
    print(f"Removed {duplicates_removed} duplicate positions")
    print(f"Final count: {len(unique_positions)} unique positions")

    # Skip writing if no duplicates were found
    if duplicates_removed == 0:
        print("No duplicates found - file unchanged")
        return True

    # Determine output path
    if overwrite:
        output_file_path = input_file_path
        print(f"Overwriting original file: {input_file_path}")
    else:
        base_name = os.path.splitext(input_file_path)[0]
        output_file_path = f"{base_name}_clean.jsonl"
        print(f"Writing to new file: {output_file_path}")

    # Write output file
    try:
        formatted_output = format_jsonl_output(unique_positions)
        with open(output_file_path, 'w', encoding='utf-8') as f:
            f.write(formatted_output)
        print(f"✓ File updated successfully")
        return True
    except Exception as e:
        print(f"Error writing output file '{output_file_path}': {e}")
        return False


def process_multiple_jsonl_files(file_paths, output_dir=None):
    """Process multiple JSONL files and remove duplicates from each."""

    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for file_path in file_paths:
        print(f"\nProcessing: {file_path}")

        if output_dir:
            filename = os.path.basename(file_path)
            base_name = os.path.splitext(filename)[0]
            output_path = os.path.join(output_dir, f"{base_name}_clean.jsonl")
        else:
            output_path = None

        process_jsonl_file(file_path, output_path)


def remove_dup_jsonl():
    datasets_folder = "data"

    # List of all your JSONL files (in the datasets folder)
    file_names = [
        "easy_history.jsonl",
        "easy_turn_board.jsonl",
        "easy_verbal.jsonl",
        "hard_history.jsonl",
        "hard_turn_board.jsonl",
        "hard_verbal.jsonl",
        "normal_history.jsonl",
        "normal_turn_board.jsonl",
        "normal_verbal.jsonl"
    ]

    # Create full paths to the files
    file_list = [os.path.join(datasets_folder, filename) for filename in file_names]

    print("Starting deduplication process for all JSONL files in 'datasets' folder...")
    print("=" * 60)

    # Check if datasets folder exists
    if not os.path.exists(datasets_folder):
        print(f"Error: '{datasets_folder}' folder not found!")
        print("Please make sure the 'datasets' folder exists in the same directory as this script.")
        exit(1)

    # Process each file
    for file_path in file_list:
        filename = os.path.basename(file_path)
        print(f"\n{'=' * 25}")
        print(f"Processing: {filename}")
        print('=' * 25)

        # Check if file exists before processing
        if os.path.exists(file_path):
            # Generate output path in the same datasets folder
            base_name = os.path.splitext(file_path)[0]
            output_path = f"{base_name}_clean.jsonl"

            success = process_jsonl_file(file_path, output_path)
            if success:
                print(f"✓ Successfully processed {filename}")
            else:
                print(f"✗ Failed to process {filename}")
        else:
            print(f"✗ File not found: {file_path}")

    print(f"\n{'=' * 60}")
    print("Deduplication process completed!")
    print("Check the 'data' folder for '_clean.jsonl' files.")

remove_dup_jsonl()
