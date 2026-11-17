
import chess
import chess.engine
import sys

DEPTH = 4
TINY_MOVE_TIME = 1.0
MAX_MOVES = 200


def play_match(tiny_color, game_number):
    board = chess.Board()

    tiny = chess.engine.SimpleEngine.popen_uci(
        [sys.executable, "main.py", "--uci"]
    )

    stockfish = chess.engine.SimpleEngine.popen_uci(
        "/usr/games/stockfish"
    )

    stopped_reason = None

    try:
        print(f"\n=== GAME {game_number} ===")
        print(
            "Tiny Beast:",
            "White" if tiny_color == chess.WHITE else "Black"
        )
        print("Search depth:", DEPTH)
        print("Tiny Beast time limit:", TINY_MOVE_TIME, "seconds")

        while (
            not board.is_game_over(claim_draw=True)
            and board.fullmove_number <= MAX_MOVES
        ):
            if board.turn == tiny_color:
                result = tiny.play(
                    board,
                    chess.engine.Limit(
                        depth=DEPTH,
                        time=TINY_MOVE_TIME
                    )
                )
                move = result.move
                player = "Tiny Beast"
            else:
                result = stockfish.play(
                    board,
                    chess.engine.Limit(depth=DEPTH)
                )
                move = result.move
                player = "Stockfish"

            if move is None or move not in board.legal_moves:
                stopped_reason = "Invalid move detected: " + player
                print(stopped_reason)
                break

            print(
                board.fullmove_number,
                "White" if board.turn else "Black",
                move.uci(),
                flush=True
            )

            board.push(move)

        outcome = board.outcome(claim_draw=True)

        if outcome:
            print("Result:", outcome.result())
            print("Reason:", outcome.termination)
        else:
            print("Result: *")
            print("Reason: Move limit reached.")

        if stopped_reason:
            print("Test warning:", stopped_reason)

    finally:
        tiny.quit()
        stockfish.quit()


if __name__ == "__main__":
    play_match(chess.WHITE, 1)
    play_match(chess.BLACK, 2)
