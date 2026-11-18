
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


def evaluate(board, engine, tiny_color):
    if board.is_checkmate():
        return -100000 if board.turn == tiny_color else 100000

    if (
        board.is_stalemate()
        or board.is_insufficient_material()
        or board.can_claim_threefold_repetition()
        or board.can_claim_fifty_moves()
    ):
        return 0

    info = engine.analyse(
        board,
        chess.engine.Limit(depth=STOCKFISH_DEPTH)
    )

    return info["score"].pov(tiny_color).score(
        mate_score=100000
    )


def scan_game(name, moves_text, tiny_color, engine):
    board = chess.Board()
    records = []

    print("\n" + "=" * 65)
    print(name)
    print(
        "Kolor Tiny Beast:",
        "White" if tiny_color == chess.WHITE else "Black"
    )
    print("=" * 65)

    for ply, san in enumerate(moves_text.split(), start=1):
        try:
            move = board.parse_san(san)
        except ValueError as error:
            raise ValueError(
                f"{name}: nielegalny ruch {ply}: {san}; "
                f"FEN: {board.fen()}"
            ) from error

        if board.turn == tiny_color:
            move_number = board.fullmove_number
            move_san = board.san(move)

            before = evaluate(board, engine, tiny_color)
            board.push(move)
            after = evaluate(board, engine, tiny_color)

            loss = before - after

            record = {
                "number": move_number,
                "move": move_san,
                "before": before,
                "after": after,
                "loss": loss,
            }
            records.append(record)

            marker = (
                "  <<< BLUNDER"
                if loss >= BLUNDER_THRESHOLD
                else ""
            )

            print(
                f"{move_number}. {move_san:8} "
                f"przed: {before:7} cp  "
                f"po: {after:7} cp  "
                f"strata: {loss:7} cp"
                f"{marker}",
                flush=True
            )

        else:
            board.push(move)

    suspicious = [
        item for item in records
        if item["loss"] >= BLUNDER_THRESHOLD
    ]

    print("\nPierwszy podejrzany ruch:")

    if suspicious:
        first = suspicious[0]
        print(
            f"{first['number']}. {first['move']} "
            f"(strata {first['loss']} cp)"
        )
    else:
        print("Nie znaleziono straty >= 150 cp.")

    return records


def main():
    engine = chess.engine.SimpleEngine.popen_uci(
        STOCKFISH_PATH
    )

    all_records = []

    try:
        print("========== BLUNDER SCAN ==========")
        print("Stockfish depth:", STOCKFISH_DEPTH)
        print("Próg podejrzanego ruchu:", BLUNDER_THRESHOLD, "cp")

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

            records = scan_game(
                name,
                moves_text,
                tiny_color,
                engine
            )

            for item in records:
                item["game"] = name
                all_records.append(item)

        print("\n========== NAJWIĘKSZE STRATY ==========")

        biggest = sorted(
            all_records,
            key=lambda item: item["loss"],
            reverse=True
        )[:10]

        for item in biggest:
            print(
                f"{item['game']} | "
                f"{item['number']}. {item['move']} | "
                f"strata: {item['loss']} cp"
            )

        print("\n========== BLUNDER SCAN ZAKOŃCZONY ==========")

    finally:
        engine.quit()


if __name__ == "__main__":
    main()
