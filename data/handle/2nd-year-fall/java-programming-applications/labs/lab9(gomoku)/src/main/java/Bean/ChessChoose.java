package Bean;

import java.util.concurrent.atomic.AtomicReference;

// ChessChoose 类表示一个玩家选择棋子的时间和棋子状态
// 该类实现了 Serializable 接口，允许对象序列化，以便保存或传输
public class ChessChoose implements java.io.Serializable {
    // 存储选择的时间
    private long time;
    // 存储棋子的状态（例如黑棋或白棋）
    private ChessCondition chessCondition;

    // 构造函数，接受时间和 AtomicReference 类型的棋子状态作为参数
    // AtomicReference 用于线程安全地获取和更新棋子状态
    public ChessChoose(long time, AtomicReference<ChessCondition> chessCondition) {
        this.time = time;  // 设置选择的时间
        this.chessCondition = chessCondition.get();  // 从 AtomicReference 获取棋子的状态
    }

    // 构造函数，接受时间和棋子状态作为参数
    public ChessChoose(long time, ChessCondition chose) {
        this.time = time;  // 设置选择的时间
        this.chessCondition = chose;  // 设置棋子的状态
    }

    // 获取选择的时间
    public long getTime() {
        return time;
    }

    // 获取棋子的状态
    public ChessCondition getChessCondition() {
        return chessCondition;
    }
}
