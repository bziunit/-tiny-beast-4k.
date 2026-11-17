
import chess
import chess.engine
import sys

DEPTH = 4
MOVE_TIME = 1.0
MAX_MOVES = 60


def play_match(tiny_color, game_number):
    board = chess.Board()

    tiny = chess.engine.SimpleEngine.popen_uci(
        [sys.executable, "main.py", "--uci"]
    )

    stockfish = chess.engine.SimpleEngine.popen_uci(
        "/usr/games/stockfish"
    )

    try:
        print(f"\n=== GAME {game_number} ===", flush=True)
        print("Tiny Beast:", "White" if tiny_color else "Black", flush=True)
        print("Depth:", DEPTH, flush=True)
        print("Time per move:", MOVE_TIME, "seconds", flush=True)

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
                chess.engine.Limit(
                    depth=DEPTH,
                    time=MOVE_TIME
                )
            )

            move = result.move

            if move is None or move not in board.legal_moves:
                print("INVALID MOVE:", player, flush=True)
                break

            print(
                board.fullmove_number,
                "White" if board.turn else "Black",
                player,
                move.uci(),
                flush=True
            )

            board.push(move)

        outcome = board.outcome(claim_draw=True)

        if outcome:
            print("Result:", outcome.result(), flush=True)
            print("Reason:", outcome.termination, flush=True)
        else:
            print("Result: *", flush=True)
            print("Reason: 60-move limit reached.", flush=True)

    finally:
        tiny.quit()
        stockfish.quit()


if __name__ == "__main__":
    play_match(chess.WHITE, 1)
    play_match(chess.BLACK, 2)
