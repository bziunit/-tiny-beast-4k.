
import chess
import chess.engine
import sys

GAMES = 20
DEPTH = 3
MOVE_TIME = 0.2
MAX_MOVES = 50


def play_game(tiny, stockfish, tiny_color, game_number):
    board = chess.Board()
    game_token = object()

    print(f"\n=== GAME {game_number}/{GAMES} ===", flush=True)
    print("Tiny Beast:", "White" if tiny_color else "Black", flush=True)
    print("Depth:", DEPTH, "| Time per move:", MOVE_TIME, "seconds", flush=True)

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
            move.uci(),
            flush=True,
        )
        board.push(move)

    outcome = board.outcome(claim_draw=True)
    if outcome is None:
        print(f"Result: unfinished (reached {MAX_MOVES}-move limit)", flush=True)
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
            tiny_color = chess.WHITE if game_number % 2 == 1 else chess.BLACK
            result = play_game(tiny, stockfish, tiny_color, game_number)
            results[result] += 1
    finally:
        tiny.quit()
        stockfish.quit()

    print("\n========== MATCH SUMMARY ==========", flush=True)
    print("Games:", GAMES, flush=True)
    print("Tiny Beast wins:", results["Tiny Beast"], flush=True)
    print("Stockfish wins:", results["Stockfish"], flush=True)
    print("Draws:", results["draw"], flush=True)
    print("Unfinished:", results["unfinished"], flush=True)
    print(
        "Tiny Beast score:",
        f"{results['Tiny Beast'] + results['draw'] / 2}/{GAMES}",
        flush=True,
    )


if __name__ == "__main__":
    main()
