package View;

import Bean.Chess;
import Bean.Player;

public interface View {
    void setKey(String key);
    void setChess(Chess chess);
    void setInfo(Player info);
}
