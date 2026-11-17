
import chess
import chess.engine
import sys

DEPTH = 4
MAX_MOVES = 200
ENGINE_PATH = [sys.executable, "main.py", "--uci"]
STOCKFISH_PATH = "/usr/games/stockfish"


def play_match(tiny_color, game_number):
    board = chess.Board()

    tiny = chess.engine.SimpleEngine.popen_uci(ENGINE_PATH)
    stockfish = chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH)

    try:
        print(f"\n=== GAME {game_number} ===", flush=True)
        print(
            "Tiny Beast:",
            "White" if tiny_color == chess.WHITE else "Black",
            flush=True
        )
        print("Search depth:", DEPTH, flush=True)

        while (
            not board.is_game_over(claim_draw=True)
            and board.fullmove_number <= MAX_MOVES
        ):
            if board.turn == tiny_color:
                result = tiny.play(
                    board,
                    chess.engine.Limit(depth=DEPTH)
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
                print("Invalid move detected:", player, flush=True)
                break

            print(
                board.fullmove_number,
                "White" if board.turn == chess.WHITE else "Black",
                move.uci(),
                flush=True
            )

            board.push(move)

        outcome = board.outcome(claim_draw=True)

        if outcome is not None:
            print("Result:", outcome.result(), flush=True)
            print("Reason:", outcome.termination, flush=True)
        else:
            print("Result: *", flush=True)
            print("Reason: Move limit reached.", flush=True)

    finally:
        tiny.quit()
        stockfish.quit()


if __name__ == "__main__":
    play_match(chess.WHITE, 1)
    play_match(chess.BLACK, 2)
