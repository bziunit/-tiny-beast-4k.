
import chess
import chess.engine
import sys

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
        print("Tiny Beast:", "White" if tiny_color == chess.WHITE else "Black")

        while not board.is_game_over() and board.fullmove_number <= 100:
            if board.turn == tiny_color:
                result = tiny.play(board, chess.engine.Limit(depth=3))
                move = result.move
            else:
                result = stockfish.play(board, chess.engine.Limit(depth=3))
                move = result.move

            if move is None or move not in board.legal_moves:
                print("Invalid move detected.")
                break

            print(board.fullmove_number, "White" if board.turn else "Black", move.uci())
            board.push(move)

        print("Result:", board.result(claim_draw=True))
        print("Reason:", board.outcome(claim_draw=True))

    finally:
        tiny.quit()
        stockfish.quit()


if __name__ == "__main__":
    play_match(chess.WHITE, 1)
    play_match(chess.BLACK, 2)
