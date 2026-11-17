
import chess
import chess.engine
import sys


DEPTH = 4
MAX_MOVES = 200


def play_match(tiny_color, game_number):
    board = chess.Board()

    tiny = chess.engine.SimpleEngine.popen_uci(
        [sys.executable, "main.py", "--uci"]
    )

    stockfish = chess.engine.SimpleEngine.popen_uci(
        "/usr/games/stockfish"
    )

    try:
        print(f"\n=== GAME {game_number} ===")
        print(
            "Tiny Beast:",
            "White" if tiny_color == chess.WHITE else "Black"
        )
        print("Search depth:", DEPTH)

        while not board.is_game_over() and board.fullmove_number <= MAX_MOVES:
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
                print("Invalid move detected:", player)
                break

            print(
                board.fullmove_number,
                "White" if board.turn else "Black",
                move.uci()
            )

            board.push(move)

        print("Result:", board.result(claim_draw=True))
        print("Reason:", board.outcome(claim_draw=True))

        if not board.is_game_over():
            print("Game stopped at the 200-move limit.")

    finally:
        tiny.quit()
        stockfish.quit()


if __name__ == "__main__":
    play_match(chess.WHITE, 1)
    play_match(chess.BLACK, 2)
