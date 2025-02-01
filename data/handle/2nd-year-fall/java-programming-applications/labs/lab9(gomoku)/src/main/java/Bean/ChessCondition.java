package Bean;

public enum ChessCondition {
    WHITE,BLACK, EMPTY, OUT_OF_BOUNDS;

    @Override
    public String toString() {
        switch (this) {
            case WHITE:
                return "White";
            case BLACK:
                return "Black";
            case EMPTY:
                return "Empty";
            case OUT_OF_BOUNDS:
                return "Out of bounds";
            default:
                return "";
        }
    }
}
