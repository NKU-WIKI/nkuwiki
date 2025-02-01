package Bean;

import java.io.Serializable;
import java.util.Objects;

// Chess 类表示棋盘上的一个棋子
// 该类实现了 Serializable 接口，以便该对象可以被序列化并保存/传输
public class Chess implements Serializable {
    private int row;  // 棋子所在的行位置，取值范围为1到19
    private int col;  // 棋子所在的列位置，取值范围为1到19
    private ChessCondition condition;  // 棋子的状态（例如，黑子或白子）

    // 构造函数，初始化棋子的行、列和状态
    public Chess(int row, int col, ChessCondition condition){
        this.row = row;  // 设置棋子的行
        this.col = col;  // 设置棋子的列
        this.condition = condition;  // 设置棋子的状态
    }

    // 构造函数，只有棋子的状态作为参数
    public Chess(ChessCondition condition) {
        this.condition = condition;  // 只初始化棋子的状态
    }

    // 获取棋子的行位置
    public int getRow() {
        return row;
    }

    // 设置棋子的行位置
    public void setRow(int row) {
        this.row = row;
    }

    // 获取棋子的列位置
    public int getCol() {
        return col;
    }

    // 设置棋子的列位置
    public void setCol(int col) {
        this.col = col;
    }

    // 获取棋子的状态
    public ChessCondition getCondition() {
        return condition;
    }

    // 设置棋子的状态
    public void setCondition(ChessCondition condition) {
        this.condition = condition;
    }

    // 将棋子的信息转换为字节数组，通常用于网络传输或存储
    public byte[] getBytes() {
        byte[] bytes = new byte[3];  // 创建一个字节数组，长度为3
        bytes[0] = (byte) row;  // 将行位置转换为字节并存储
        bytes[1] = (byte) col;  // 将列位置转换为字节并存储
        bytes[2] = (byte) condition.ordinal();  // 将棋子状态转换为字节并存储，使用 ordinal() 获取状态的索引值
        return bytes;
    }

    // 重写equals方法，比较两个棋子对象是否相等
    @Override
    public boolean equals(Object o) {
        if (this == o) return true;  // 如果是同一个对象，直接返回true
        if (o == null || getClass() != o.getClass()) return false;  // 如果o为空或类型不一致，返回false
        Chess chess = (Chess) o;  // 将对象o转换为Chess类型
        return row == chess.row && col == chess.col && condition == chess.condition;  // 比较行、列和状态是否相等
    }

    // 重写hashCode方法，返回棋子对象的哈希值
    @Override
    public int hashCode() {
        return Objects.hash(row, col, condition);  // 使用Objects.hash()生成基于行、列和状态的哈希值
    }
}
