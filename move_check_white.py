
import chess
import chess.engine

from loss_diagnostic import POSITIONS

STOCKFISH_PATH = "/usr/games/stockfish"
DEPTH = 18
TARGET_MOVE = "Qf3"
TARGET_FULLMOVE = 12


def score_cp(info):
    return info["score"].pov(chess.WHITE).score(mate_score=100000)


def show_pv(board, pv, max_plies=12):
    position = board.copy()
    moves = []

    for move in pv[:max_plies]:
        moves.append(position.san(move))
        position.push(move)

    return " ".join(moves)


def find_position():
    for name, moves_text in POSITIONS:
        if "RUY LOPEZ" not in name.upper():
            continue

        board = chess.Board()

        for san in moves_text.split():
            move = board.parse_san(san)

            if (
                board.fullmove_number == TARGET_FULLMOVE
                and board.turn == chess.WHITE
                and board.san(move) == TARGET_MOVE
            ):
                return board, move

            board.push(move)

    raise RuntimeError("Nie znaleziono pozycji przed 12.Qf3.")


def main():
    board, played_move = find_position()

    engine = chess.engine.SimpleEngine.popen_uci(
        STOCKFISH_PATH
    )

    try:
        print("========== ANALIZA 12.Qf3 ==========")
        print("Stockfish depth:", DEPTH)
        print("Kolor oceny: białe")
        print("FEN:", board.fen())
        print("Zagrany ruch:", board.san(played_move))
        print("Liczba legalnych ruchów:", board.legal_moves.count())

        print("\n========== 5 NAJLEPSZYCH RUCHÓW ==========")

        best_lines = engine.analyse(
            board,
            chess.engine.Limit(depth=DEPTH),
            multipv=5
        )

        for index, info in enumerate(best_lines, start=1):
            pv = info.get("pv", [])
            first_move = pv[0] if pv else None

            print(
                f"{index}. "
                f"{board.san(first_move) if first_move else '?'} "
                f"| ocena: {score_cp(info)} cp "
                f"| wariant: {show_pv(board, pv)}",
                flush=True
            )

        print("\n========== OSOBNA OCENA 12.Qf3 ==========")

        played_info = engine.analyse(
            board,
            chess.engine.Limit(depth=DEPTH),
            root_moves=[played_move]
        )

        print("Ruch:", board.san(played_move))
        print("Ocena:", score_cp(played_info), "cp")
        print("Wariant:", show_pv(board, played_info.get("pv", [])))

        best_score = score_cp(best_lines[0])
        played_score = score_cp(played_info)

        print("\n========== PORÓWNANIE ==========")
        print("Najlepsza ocena dla białych:", best_score, "cp")
        print("Ocena 12.Qf3:", played_score, "cp")
        print("Różnica:", best_score - played_score, "cp")

        print("\n========== ANALIZA ZAKOŃCZONA ==========")

    finally:
        engine.quit()


if __name__ == "__main__":
    main()
