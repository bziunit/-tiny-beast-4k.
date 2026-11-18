
import chess
import chess.engine
import sys

GAMES = 20
DEPTH = 3
MOVE_TIME = 0.5
MAX_MOVES = 100

OPENINGS = [
    ("Ruy Lopez", [
        "e2e4", "e7e5", "g1f3",
        "b8c6", "f1b5", "a7a6"
    ]),
    ("Sicilian Defense", [
        "e2e4", "c7c5", "g1f3",
        "d7d6", "d2d4", "c5d4"
    ]),
    ("Queen's Gambit", [
        "d2d4", "d7d5", "c2c4",
        "e7e6", "b1c3", "g8f6"
    ]),
    ("French Defense", [
        "e2e4", "e7e6", "d2d4",
        "d7d5", "b1c3", "g8f6"
    ]),
    ("English Opening", [
        "c2c4", "e7e5", "b1c3",
        "g8f6", "g2g3", "d7d5"
    ]),
    ("Reti Opening", [
        "g1f3", "d7d5", "d2d4",
        "g8f6", "c2c4", "e7e6"
    ]),
]


def make_opening(opening_index):
    name, moves = OPENINGS[opening_index % len(OPENINGS)]
    board = chess.Board()
    san_moves = []

    for move_text in moves:
        move = chess.Move.from_uci(move_text)

        if move not in board.legal_moves:
            raise ValueError(
                f"Illegal opening move: {move_text} in {name}"
            )

        san_moves.append(board.san(move))
        board.push(move)

    return board, name, san_moves


def play_game(tiny, stockfish, tiny_color, game_number, opening_index):
    board, opening_name, opening_moves = make_opening(opening_index)
    game_token = object()

    print(f"\n=== GAME {game_number}/{GAMES} ===", flush=True)
    print("Tiny Beast:", "White" if tiny_color else "Black", flush=True)
    print("Opening:", opening_name, flush=True)
    print("Opening moves:", " ".join(opening_moves), flush=True)
    print("Depth:", DEPTH, "| Time:", MOVE_TIME, "seconds", flush=True)

    while (
        not board.is_game_over(claim_draw=True)
        and board.fullmove_number <= MAX_MOVES
    ):
        if board.turn == tiny_color:
            player = "Tiny Beast"
            engine = tiny
        else:
            player = "Stockfish"
            engine = stockfish

        result = engine.play(
            board,
            chess.engine.Limit(depth=DEPTH, time=MOVE_TIME),
            game=game_token,
        )

        move = result.move

        if move is None or move not in board.legal_moves:
            print("INVALID MOVE:", player, flush=True)
            winner = "Stockfish" if player == "Tiny Beast" else "Tiny Beast"
            print("Result:", winner, "wins by invalid move", flush=True)
            return winner

        print(
            board.fullmove_number,
            "White" if board.turn else "Black",
            player,
            board.san(move),
            flush=True,
        )
        board.push(move)

    outcome = board.outcome(claim_draw=True)

    if outcome is None:
        print(
            f"Result: unfinished (reached {MAX_MOVES}-move limit)",
            flush=True
        )
        return "unfinished"

    print("Result:", outcome.result(), flush=True)
    print("Reason:", outcome.termination, flush=True)

    if outcome.winner is None:
        return "draw"

    return "Tiny Beast" if outcome.winner == tiny_color else "Stockfish"


def main():
    tiny = chess.engine.SimpleEngine.popen_uci(
        [sys.executable, "main.py", "--uci"]
    )
    stockfish = chess.engine.SimpleEngine.popen_uci("/usr/games/stockfish")

    results = {
        "Tiny Beast": 0,
        "Stockfish": 0,
        "draw": 0,
        "unfinished": 0,
    }

    try:
        for game_number in range(1, GAMES + 1):
            tiny_color = (
                chess.WHITE if game_number % 2 == 1 else chess.BLACK
            )

            opening_index = ((game_number - 1) // 2) % len(OPENINGS)

            result = play_game(
                tiny,
                stockfish,
                tiny_color,
                game_number,
                opening_index,
            )
            results[result] += 1

    finally:
        tiny.quit()
        stockfish.quit()

    score = results["Tiny Beast"] + results["draw"] / 2

    print("\n========== MATCH SUMMARY ==========", flush=True)
    print("Games:", GAMES, flush=True)
    print("Tiny Beast wins:", results["Tiny Beast"], flush=True)
    print("Stockfish wins:", results["Stockfish"], flush=True)
    print("Draws:", results["draw"], flush=True)
    print("Unfinished:", results["unfinished"], flush=True)
    print(f"Tiny Beast score: {score}/{GAMES}", flush=True)


if __name__ == "__main__":
    main()
