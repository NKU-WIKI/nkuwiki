package Map;

import Bean.Chess;
import Bean.GameInfo;

import java.util.Vector;

public class Mapper {
    public static Mapper mapper;
    private static GameInfo gameInfo;
    private static Vector<Chess> chessStore=new Vector<Chess>();

    public static Mapper getMapper() {
        if (mapper == null) {
            mapper = new Mapper();
        }
        return mapper;
    }

    public static void setGameInfo(GameInfo gameInfo) {
        Mapper.gameInfo = gameInfo;
    }

    private String key;

    public void setKey(String key) {
        this.key = key;
    }

    public static Vector<Chess> getChesses() {
        return chessStore;
    }

    public static void addChess(Chess chess){
        chessStore.add(chess);
    }

    public static void removeChess(Chess chess){
        chessStore.remove(chess);
    }

    public static void setChessStore(Vector<Chess> chessStore) {
        Mapper.chessStore = chessStore;
    }
}
