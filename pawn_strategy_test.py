
import chess
import chess.engine

from loss_diagnostic import POSITIONS
from main import TinyBeast

STOCKFISH_PATH = "/usr/games/stockfish"
SCAN_DEPTH = 10
REPORT_DEPTH = 12
TINY_DEPTH = 4
TINY_MOVE_TIME = 1.0
TARGET_POSITIONS = 10
MAX_SCANNED = 100


def build_candidates():
    candidates = []

    for game_name, moves_text in POSITIONS:
        board = chess.Board()

        for ply, san in enumerate(moves_text.split()):
            if (
                board.fullmove_number >= 8
                and board.fullmove_number <= 45
                and ply % 3 == 0
                and len(board.piece_map()) >= 14
                and len(board.pieces(chess.PAWN, chess.WHITE)) >= 3
                and len(board.pieces(chess.PAWN, chess.BLACK)) >= 3
            ):
                candidates.append(
                    (game_name, ply + 1, board.copy())
                )

            move = board.parse_san(san)
            board.push(move)

    return candidates[:MAX_SCANNED]


def is_quiet_pawn_advance(board, move):
    if move is None or move not in board.legal_moves:
        return False

    piece = board.piece_at(move.from_square)

    if piece is None or piece.piece_type != chess.PAWN:
        return False

    if board.is_capture(move) or move.promotion:
        return False

    if board.gives_check(move):
        return False

    direction = 1 if board.turn == chess.WHITE else -1

    return (
        chess.square_rank(move.to_square)
        - chess.square_rank(move.from_square)
        == direction
    )


def score_cp(info, color):
    return info["score"].pov(color).score(mate_score=100000)


def main():
    candidates = build_candidates()

    print("========== TEST RUCHÓW PIONAMI ==========")
    print("Pozycji do sprawdzenia:", len(candidates))
    print("Stockfish — głębokość skanowania:", SCAN_DEPTH)
    print("Tiny Beast — głębokość:", TINY_DEPTH)
    print("Tiny Beast — czas na ruch:", TINY_MOVE_TIME, "s")

    if not candidates:
        raise RuntimeError("Nie znaleziono pozycji do analizy.")

    tiny = TinyBeast()
    stockfish = chess.engine.SimpleEngine.popen_uci(
        STOCKFISH_PATH
    )

    selected = []
    last_selected_ply = {}

    try:
        for number, (game_name, ply, board) in enumerate(
            candidates, start=1
        ):
            if len(selected) >= TARGET_POSITIONS:
                break

            info = stockfish.analyse(
                board,
                chess.engine.Limit(depth=SCAN_DEPTH)
            )

            pv = info.get("pv", [])

            if not pv:
                continue

            best_move = pv[0]

            if not is_quiet_pawn_advance(board, best_move):
                continue

            previous_ply = last_selected_ply.get(game_name)

            if (
                previous_ply is not None
                and ply - previous_ply < 8
            ):
                continue

            selected.append(
                (game_name, ply, board.copy())
            )

            last_selected_ply[game_name] = ply

            print(
                f"Znaleziono pozycję {len(selected)}/"
                f"{TARGET_POSITIONS}: "
                f"{game_name}, ruch nr {board.fullmove_number}, "
                f"Stockfish: {board.san(best_move)}",
                flush=True
            )

        print()
        print("========== PORÓWNANIE SILNIKÓW ==========")

        if not selected:
            print(
                "Nie znaleziono pozycji, w których "
                "Stockfish wskazał spokojne przesunięcie pionem."
            )
            return

        matches_top1 = 0
        matches_top3 = 0

        for number, (game_name, ply, board) in enumerate(
            selected, start=1
        ):
            print()
            print("-" * 60)
            print(f"POZYCJA {number}: {game_name}")
            print("Numer półruchu w partii:", ply)
            print("Numer ruchu:", board.fullmove_number)
            print(
                "Na ruchu:",
                "White" if board.turn == chess.WHITE else "Black"
            )
            print("FEN:", board.fen())

            lines = stockfish.analyse(
                board,
                chess.engine.Limit(depth=REPORT_DEPTH),
                multipv=3
            )

            stockfish_moves = [
                item["pv"][0]
                for item in lines
                if item.get("pv")
            ]

            print("\nStockfish TOP 3:")

            for rank, item in enumerate(lines, start=1):
                pv = item.get("pv", [])

                if not pv:
                    continue

                move = pv[0]
                score = score_cp(item, board.turn)

                print(
                    f"{rank}. {board.san(move)} "
                    f"| {score} cp"
                )

            tiny_move = tiny.best_move(
                board.copy(),
                depth=TINY_DEPTH,
                movetime=TINY_MOVE_TIME
            )

            if tiny_move is None:
                print("Tiny Beast: brak ruchu")
                continue

            tiny_san = board.san(tiny_move)
            top_san = [
                board.san(move)
                for move in stockfish_moves
            ]

            print("\nTiny Beast:", tiny_san)
            print(
                "Czas filtra bezpieczeństwa:",
                f"{tiny.safety_time:.3f} s"
            )
            print("Tiny Beast wybrał ruch pionem:",
                  is_quiet_pawn_advance(board, tiny_move))
            print("Tiny Beast w TOP 3 Stockfisha:",
                  tiny_san in top_san)

            if stockfish_moves and tiny_move == stockfish_moves[0]:
                matches_top1 += 1

            if tiny_move in stockfish_moves:
                matches_top3 += 1

        print()
        print("=" * 60)
        print("========== PODSUMOWANIE ==========")
        print("Pozycji znalezionych:", len(selected))
        print("Zgodność z TOP 1 Stockfisha:", matches_top1)
        print("Zgodność z TOP 3 Stockfisha:", matches_top3)

        if len(selected) < TARGET_POSITIONS:
            print(
                "UWAGA: baza partii dostarczyła mniej niż "
                f"{TARGET_POSITIONS} odpowiednich pozycji."
            )

        print("========== TEST ZAKOŃCZONY ==========")

    finally:
        stockfish.quit()


if __name__ == "__main__":
    main()
