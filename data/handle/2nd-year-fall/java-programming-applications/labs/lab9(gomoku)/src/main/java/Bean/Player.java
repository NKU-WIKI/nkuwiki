package Bean;

import java.io.Serializable;

// Player 类表示一个玩家的基本信息，包含玩家的姓名和状态。
// 该类实现了 Serializable 接口，允许对象序列化，便于保存、传输或网络通信。
public class Player implements Serializable {
    private String name = "";  // 存储玩家的名字
    private PlayerCondition conditionPlayer = PlayerCondition.OFFLINE;  // 存储玩家的状态，默认为 OFFLINE（离线）
    private ChessCondition condition = ChessCondition.EMPTY;
    private String ip = "localhost";  // 存储玩家的 IP 地址
    private int port = 0;   // 存储玩家的端口号
    // 默认构造函数，初始化一个无名玩家
    public Player(){}

    // 构造函数，使用玩家的名字初始化 Player 对象
    public Player(String name) {
        this.name = name;
    }
    public Player(String name, PlayerCondition condition, ChessCondition conditionChess) {
        this.name = name;
        this.conditionPlayer = condition;
        this.condition = conditionChess;
    }
    public Player(String name, PlayerCondition condition, ChessCondition conditionChess, String ip, int port){
        this.name = name;
        this.conditionPlayer = condition;
        this.condition = conditionChess;
        this.ip = ip;
        this.port = port;
    }
    // 获取玩家的名字
    public String getName() {
        return name;
    }

    // 设置玩家的名字
    public void setName(String name) {
        this.name = name;
    }

    // 获取玩家的状态
    public PlayerCondition getCondition() {
        return conditionPlayer;
    }

    // 设置玩家的状态
    public void setCondition(PlayerCondition condition) {
        this.conditionPlayer = condition;  // 更新玩家状态
    }
    public void setChessCondition(ChessCondition condition){
        this.condition = condition;
    }
    // 重写 toString 方法，返回玩家对象的字符串表示
    @Override
    public String toString() {
        return "Player{" +
                "name='" + name + '\'' +  // 玩家姓名
                '}';
    }

    // 静态方法 parseString，将字符串 "Player{name='name'}" 解析为 Player 对象
    public static Player parseString(String str){
        // 按单引号拆分字符串，提取玩家名字
        String[] strs = str.split("'");
        
        // 创建新的 Player 对象并设置其名字
        Player player = new Player();
        player.setName(strs[1]);  // 设置玩家名字
        
        // 返回解析后的 Player 对象
        return player;
    }
    // 获取本地玩家的棋局状态
    
    public ChessCondition getChessCondition() {
        return this.condition;
    }
    public String getIp() {
        return ip;
    }

    // 获取玩家的端口号
    public int getPort() {
        return port;
    }

    // 设置玩家的 IP 地址
    public void setIp(String ip) {
        this.ip = ip;
    }

    // 设置玩家的端口号
    public void setPort(int port) {
        this.port = port;
    }
}
