import chess
import chess.engine

from loss_diagnostic import POSITIONS

STOCKFISH_PATH = "/usr/games/stockfish"
STOCKFISH_DEPTH = 10
BLUNDER_THRESHOLD = 150

TINY_COLORS = {
    "RUY LOPEZ": chess.BLACK,
    "SICILIAN": chess.BLACK,
    "QUEEN'S GAMBIT": chess.WHITE,
    "RETI": chess.BLACK,
}


def analyse_score(board, engine, tiny_color):
    """Ocena Stockfisha z zachowaniem rozróżnienia mat / centypiony."""
    if board.is_checkmate():
        mate = -100000 if board.turn == tiny_color else 100000
        return chess.engine.PovScore(chess.engine.Mate(mate), tiny_color)

    if (
        board.is_stalemate()
        or board.is_insufficient_material()
        or board.can_claim_threefold_repetition()
        or board.can_claim_fifty_moves()
    ):
        return chess.engine.PovScore(chess.engine.Cp(0), tiny_color)

    info = engine.analyse(
        board,
        chess.engine.Limit(depth=STOCKFISH_DEPTH)
    )
    return info["score"].pov(tiny_color), info


def score_text(score):
    mate = score.mate()
    if mate is not None:
        return f"MATE+{mate}" if mate > 0 else f"MATE-{abs(mate)}"

    cp = score.score()
    return f"{cp:+d} cp" if cp is not None else "brak oceny"


def score_loss(before, after):
    """Matów nie zamienia na sztuczne 99 000 centypionów."""
    before_mate = before.mate()
    after_mate = after.mate()

    if before_mate is not None or after_mate is not None:
        if before_mate is not None and after_mate is not None:
            if before_mate > 0 and after_mate < 0:
                return "MATE_LOST", None
            if before_mate < 0 and after_mate > 0:
                return "MATE_GAINED", None
            if before_mate < 0 and after_mate < 0:
                if abs(after_mate) < abs(before_mate):
                    return "MATE_DELAYED", None
                if abs(after_mate) > abs(before_mate):
                    return "MATE_CLOSER", None
            return "MATE_LINE_CHANGED", None

        if after_mate is not None and after_mate < 0:
            return "ENTERED_FORCED_MATE", None
        if before_mate is not None and before_mate < 0 and after_mate is None:
            return "ESCAPED_FORCED_MATE", None
        return "MATE_STATUS_CHANGED", None

    before_cp = before.score()
    after_cp = after.score()
    if before_cp is None or after_cp is None:
        return "UNKNOWN", None

    return "CP", before_cp - after_cp


def scan_game(name, moves_text, tiny_color, engine):
    board = chess.Board()
    records = []

    print("\n" + "=" * 72)
    print(name)
    print("Kolor Tiny Beast:",
          "White" if tiny_color == chess.WHITE else "Black")
    print("=" * 72)

    for ply, san in enumerate(moves_text.split(), start=1):
        try:
            move = board.parse_san(san)
        except ValueError as error:
            raise ValueError(
                f"{name}: nielegalny ruch {ply}: {san}; FEN: {board.fen()}"
            ) from error

        if board.turn == tiny_color:
            move_number = board.fullmove_number
            move_san = board.san(move)
            before_fen = board.fen()

            before_result = analyse_score(board, engine, tiny_color)
            if isinstance(before_result, tuple):
                before, before_info = before_result
            else:
                before, before_info = before_result, {}

            pv = before_info.get("pv", [])
            best_move = pv[0] if pv else None
            best_san = board.san(best_move) if best_move else "brak"

            board.push(move)
            after_result = analyse_score(board, engine, tiny_color)
            after = after_result[0] if isinstance(after_result, tuple) else after_result

            kind, loss = score_loss(before, after)
            record = {
                "game": name,
                "number": move_number,
                "move": move_san,
                "best_move": best_san,
                "before": score_text(before),
                "after": score_text(after),
                "kind": kind,
                "loss": loss,
                "fen": before_fen,
            }
            records.append(record)

            if kind == "CP" and loss is not None:
                marker = "  <<< BLUNDER" if loss >= BLUNDER_THRESHOLD else ""
                print(
                    f"{move_number}. {move_san:8} "
                    f"przed: {record['before']:>10}  "
                    f"po: {record['after']:>10}  "
                    f"strata: {loss:5} cp  Stockfish: {best_san}{marker}",
                    flush=True
                )
            else:
                print(
                    f"{move_number}. {move_san:8} "
                    f"przed: {record['before']:>10}  "
                    f"po: {record['after']:>10}  "
                    f"typ: {kind:24} Stockfish: {best_san}",
                    flush=True
                )
        else:
            board.push(move)

    suspicious = [
        item for item in records
        if item["kind"] == "CP"
        and item["loss"] is not None
        and item["loss"] >= BLUNDER_THRESHOLD
    ]

    print("\nPodejrzane straty centypionów:")
    if suspicious:
        for item in suspicious:
            print(
                f"{item['number']}. {item['move']} | strata {item['loss']} cp | "
                f"Stockfish: {item['best_move']} | FEN: {item['fen']}"
            )
    else:
        print("Nie znaleziono straty >= 150 cp.")

    mate_events = [
        item for item in records
        if item["kind"] not in ("CP", "UNKNOWN")
    ]
    if mate_events:
        print("\nZmiany statusu mata (osobno):")
        for item in mate_events:
            print(
                f"{item['number']}. {item['move']} | "
                f"{item['before']} -> {item['after']} | {item['kind']}"
            )

    return records


def main():
    engine = chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH)
    all_records = []

    try:
        engine.configure({"Threads": 1, "Hash": 256})
        print("========== BLUNDER SCAN v2 ==========")
        print("Stockfish depth:", STOCKFISH_DEPTH)
        print("Próg zwykłej straty:", BLUNDER_THRESHOLD, "cp")
        print("Pozycje matowe są klasyfikowane oddzielnie.")

        for name, moves_text in POSITIONS:
            tiny_color = None
            for key, color in TINY_COLORS.items():
                if key in name.upper():
                    tiny_color = color
                    break

            if tiny_color is None:
                raise ValueError(
                    "Nie rozpoznano koloru Tiny Beast dla: " + name
                )

            all_records.extend(scan_game(name, moves_text, tiny_color, engine))

        biggest = sorted(
            [
                item for item in all_records
                if item["kind"] == "CP" and item["loss"] is not None
            ],
            key=lambda item: item["loss"],
            reverse=True
        )[:10]

        print("\n========== NAJWIĘKSZE STRATY CP ==========")
        for item in biggest:
            print(
                f"{item['game']} | {item['number']}. {item['move']} | "
                f"{item['loss']} cp | Stockfish: {item['best_move']} | "
                f"FEN: {item['fen']}"
            )

        print("\n========== BLUNDER SCAN v2 ZAKOŃCZONY ==========")

    finally:
        engine.quit()


if __name__ == "__main__":
    main()
