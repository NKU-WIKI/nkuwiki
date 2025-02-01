package Bean;

import java.io.Serializable;

// BattleMessage 类表示在游戏中传递的战斗消息
// 该类实现了 Serializable 接口，允许对象序列化，便于保存、传输或网络通信
public class BattleMessage implements Serializable {
    private Chess chess = new Chess(-1, -1, ChessCondition.EMPTY);  // 存储棋子的信息，默认值为空棋子
    private Actions action = Actions.NONE;  // 存储战斗消息中的动作，默认为 NONE
    private String text = "";  // 存储附加的文本信息，默认为空字符串

    // 默认构造函数，初始化 BattleMessage 对象
    public BattleMessage() {
    }

    // 构造函数，仅初始化动作，text 和 chess 保持默认值
    public BattleMessage(Actions action) {
        this.action = action;
    }

    // 构造函数，初始化动作和文本，棋子保持默认值
    public BattleMessage(Actions action, String text) {
        this.action = action;
        this.text = text;
    }

    // 构造函数，初始化棋子、动作和文本
    public BattleMessage(Chess chess, Actions action, String text) {
        this.chess = chess;  // 设置棋子信息
        this.action = action;  // 设置动作
        this.text = text;  // 设置附加文本
    }

    // 获取棋子信息
    public Chess getChess() {
        return chess;
    }

    // 设置棋子信息
    public void setChess(Chess chess) {
        this.chess = chess;  
    }
    // 获取动作
    public Actions getAction() {
        return action;
    }

    // 设置动作
    public void setAction(Actions action) {
        this.action = action;  
    }

    // 获取附加的文本信息
    public String getText() {
        return text;
    }

    // 设置附加的文本信息
    public void setText(String text) {
        this.text = text;  
    }
}
