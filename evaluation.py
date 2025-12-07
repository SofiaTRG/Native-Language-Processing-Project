import chess
import chess.engine
import numpy as np
def move_normalized_score(board: chess.Board, move_str: str, time_limit: float = 0.05):
    engine = chess.engine.SimpleEngine.popen_uci("stockfish-windows-x86-64-avx2")
    """
    Returns a normalized score (0-1) for a given move relative to all legal moves in the position.
    """
    legal_moves = {board.san(move): move for move in board.legal_moves}
    print (legal_moves)
    if move_str not in legal_moves:
        return 0
    print("yes")
    print(move_str)
    try:
        move = board.parse_san(move_str)
    except:
        return 0
    print("still here")
    legal_moves = list(board.legal_moves)
    scores = []

    for m in legal_moves:
        board.push(m)
        info = engine.analyse(board, chess.engine.Limit(time=time_limit))
        board.pop()
        score = info["score"].white().score(mate_score=100000)
        scores.append(score)

    scores_array = np.array(scores, dtype=float)
    min_score = scores_array.min()
    max_score = scores_array.max()

    if max_score - min_score > 0:
        normalized_scores = (scores_array - min_score) / (max_score - min_score)
    else:
        normalized_scores = np.ones_like(scores_array) * 0.5

    # Map moves to normalized scores
    move_to_score = {m: s for m, s in zip(legal_moves, normalized_scores)}
    return move_to_score.get(move, None)  # returns normalized score for given move