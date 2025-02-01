package Bean;

import java.io.Serializable;

// GameInfo 类表示一个游戏的信息，主要包含两个玩家以及一些其他的游戏状态信息。
// 该类实现了 Serializable 接口，允许对象序列化，便于保存、传输或网络通信。
public class GameInfo implements Serializable {
    private Player p1, p2;  // 存储两个玩家的信息，p1 和 p2 分别表示玩家 1 和玩家 2
    private int index = -1;  // 存储游戏的索引，默认为 -1（未设置）
    private int owner = 0;  // 存储游戏的所有者，通常表示房间的创建者
    private boolean LOCAL = false;
    // 默认构造函数，初始化两个玩家为默认的 Player 对象
    public GameInfo(boolean local){
        LOCAL = local;
        this.p1 = new Player();  // 初始化玩家 1
        this.p2 = new Player();  // 初始化玩家 2
    }

    // 构造函数，传入两个玩家对象 p1 和 p2 来初始化游戏信息
    public GameInfo(Player p1, Player p2){
        this.p1 = p1;
        this.p2 = p2;
    }
    public boolean isLOCAL(){
        return LOCAL;
    }
    // 获取玩家 1 的信息
    public Player getP1(){
        return p1;
    }

    // 获取玩家 2 的信息
    public Player getP2(){
        return p2;
    }
    
    public void setP1(Player p){
        p1 = p;
    }
    public void setP2(Player p){
        p2 = p;
    }
    // 获取游戏的索引
    public int getIndex() {
        return index;
    }

    // 设置游戏的索引
    public void setIndex(int index) {
        this.index = index;
    }

    // 重写 toString 方法，返回游戏信息的字符串表示
    @Override
    public String toString() {
        return "GameInfo{" +
                "p1=" + p1 +  // 玩家 1 信息
                ", p2=" + p2 +  // 玩家 2 信息
                ", index=" + index +  // 游戏索引
                '}';
    }

    // 静态方法 parseString，解析字符串并将其转换为 GameInfo 对象
    // 该方法假设输入字符串是 toString 方法的返回值，并从中提取玩家和索引信息来创建 GameInfo 对象
    // public static GameInfo parseString(String s){
    //     // 使用逗号分割字符串，得到玩家信息和索引
    //     String[] strs = s.split(",");
        
    //     // 解析玩家 1 和玩家 2 的信息
    //     Player p11 = Player.parseString(strs[0].substring(strs[0].indexOf("p1=") + 4, strs[0].length() - 1));
    //     Player p22 = Player.parseString(strs[1].substring(strs[1].indexOf("p2=") + 4, strs[1].length() - 1));
    //     Player p1 = new Player(p11.getName(),ChessCondition.WHITE);
    //     Player p2 = new Player(p22.getName(),ChessCondition.BLACK);
    //     // 创建 GameInfo 对象并设置玩家信息
    //     GameInfo gi = new GameInfo(p1, p2);
        
    //     // 解析并设置游戏索引
    //     gi.setIndex(Integer.parseInt(strs[2].substring(strs[2].indexOf("index=") + 6, strs[2].length() - 1)));
        
    //     // 返回创建的 GameInfo 对象
    //     return gi;
    // }

    // 获取游戏的所有者（房间创建者）
    public int getOwner() {
        return owner;
    }

    // 设置游戏的所有者（房间创建者）
    public void setOwner(int owner) {
        this.owner = owner;
    }
}
