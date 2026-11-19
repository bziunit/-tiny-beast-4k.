
import chess
import chess.engine
import time

from contextlib import redirect_stdout
from loss_diagnostic import POSITIONS
from main import TinyBeast

STOCKFISH_PATH = "/usr/games/stockfish"

SCAN_DEPTH = 10
REPORT_DEPTH = 12
TINY_DEPTH = 4
TINY_MOVE_TIME = 3.0

TARGET_POSITIONS = 10
MAX_SCANNED = 300
MIN_POSITION_GAP = 8


class TimedCapture:
    def __init__(self):
        self.start = time.monotonic()
        self.buffer = ""
        self.lines = []

    def write(self, text):
        self.buffer += text

        while "\n" in self.buffer:
            line, self.buffer = self.buffer.split("\n", 1)
            elapsed = time.monotonic() - self.start
            self.lines.append((elapsed, line))

        return len(text)

    def flush(self):
        pass


def build_candidates():
    candidates = []
    seen_fens = set()

    for game_name, moves_text in POSITIONS:
        board = chess.Board()

        for ply, san in enumerate(moves_text.split(), start=1):
            if (
                8 <= board.fullmove_number <= 45
                and len(board.piece_map()) >= 14
                and len(board.pieces(chess.PAWN, chess.WHITE)) >= 3
                and len(board.pieces(chess.PAWN, chess.BLACK)) >= 3
                and not board.is_check()
            ):
                fen = board.fen()

                if fen not in seen_fens:
                    candidates.append(
                        (game_name, ply, board.copy())
                    )
                    seen_fens.add(fen)

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
    return info["score"].pov(color).score(
        mate_score=100000
    )


def select_positions(stockfish, candidates):
    selected = []
    last_selected_ply = {}
    scanned = 0

    for game_name, ply, board in candidates:
        if len(selected) >= TARGET_POSITIONS:
            break

        scanned += 1

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
            and ply - previous_ply < MIN_POSITION_GAP
        ):
            continue

        selected.append(
            (game_name, ply, board.copy())
        )

        last_selected_ply[game_name] = ply

        print(
            f"Znaleziono pozycję {len(selected)}/"
            f"{TARGET_POSITIONS}: "
            f"{game_name}, ruch {board.fullmove_number}, "
            f"Stockfish: {board.san(best_move)}",
            flush=True
        )

    print("Przeskanowanych pozycji:", scanned)

    return selected


def compare_engines(tiny, stockfish, selected):
    matches_top1 = 0
    matches_top3 = 0
    pawn_moves = 0

    for number, (game_name, ply, board) in enumerate(
        selected, start=1
    ):
        print()
        print("-" * 60)
        print(f"POZYCJA {number}: {game_name}")
        print("Numer półruchu:", ply)
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

        capture = TimedCapture()
        total_start = time.monotonic()

        with redirect_stdout(capture):
            tiny_move = tiny.best_move(
                board.copy(),
                depth=TINY_DEPTH,
                movetime=TINY_MOVE_TIME
            )

        total_time = time.monotonic() - total_start

        print("\nPOMIAR CZASU TINY BEAST:")

        safety_elapsed = 0.0

        for elapsed, line in capture.lines:
            if "safety_filter_time" in line:
                parts = line.split()

                try:
                    safety_elapsed = float(parts[3])
                except (ValueError, IndexError):
                    pass

                print(
                    f"Filtr bezpieczeństwa: "
                    f"{safety_elapsed:.3f} s"
                )

            elif line.startswith("info depth"):
                search_elapsed = max(
                    0.0, elapsed - safety_elapsed
                )

                print(
                    f"  {line} "
                    f"| czas wyszukiwania: "
                    f"{search_elapsed:.3f} s"
                )

        print(f"Łączny czas: {total_time:.3f} s")

        if tiny_move is None:
            print("Tiny Beast: brak ruchu")
            continue

        tiny_san = board.san(tiny_move)
        in_top3 = tiny_move in stockfish_moves

        is_pawn = is_quiet_pawn_advance(
            board, tiny_move
        )

        if is_pawn:
            pawn_moves += 1

        print("\nTiny Beast:", tiny_san)
        print("Spokojny ruch pionem:", is_pawn)
        print("Ruch w TOP 3 Stockfisha:", in_top3)

        if stockfish_moves and tiny_move == stockfish_moves[0]:
            matches_top1 += 1

        if in_top3:
            matches_top3 += 1

    print()
    print("=" * 60)
    print("========== PODSUMOWANIE ==========")
    print("Pozycji przeanalizowanych:", len(selected))
    print("Zgodność z TOP 1:", matches_top1)
    print("Zgodność z TOP 3:", matches_top3)
    print("Spokojne ruchy pionami Tiny Beast:", pawn_moves)
    print("========== TEST ZAKOŃCZONY ==========")


def main():
    candidates = build_candidates()

    print("========== TEST STRATEGII PIONÓW ==========")
    print("Dostępne unikalne pozycje:", len(candidates))
    print("Cel:", TARGET_POSITIONS)
    print("Stockfish — skanowanie:", SCAN_DEPTH)
    print("Stockfish — raport:", REPORT_DEPTH)
    print("Tiny Beast — głębokość:", TINY_DEPTH)
    print("Tiny Beast — czas:", TINY_MOVE_TIME, "s")

    if not candidates:
        raise RuntimeError(
            "Nie znaleziono odpowiednich pozycji."
        )

    tiny = TinyBeast()

    stockfish = chess.engine.SimpleEngine.popen_uci(
        STOCKFISH_PATH
    )

    try:
        selected = select_positions(
            stockfish,
            candidates
        )

        if len(selected) < TARGET_POSITIONS:
            raise RuntimeError(
                f"Znaleziono tylko {len(selected)} "
                f"z wymaganych {TARGET_POSITIONS} pozycji. "
                "Trzeba rozszerzyć bazę lub kryteria."
            )

        print()
        print("========== PORÓWNANIE SILNIKÓW ==========")

        compare_engines(
            tiny,
            stockfish,
            selected
        )

    finally:
        stockfish.quit()


if __name__ == "__main__":
    main()
