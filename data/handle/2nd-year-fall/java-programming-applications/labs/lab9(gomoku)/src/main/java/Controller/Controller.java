package Controller;

import Bean.*;
import InstanceControl.InstanceManager;
import Map.AddressBattle;
import Map.Mapper;
import Map.MessageBuffer;
import Util.NetUDP;
import View.*;

public class Controller {
    // 单例模式：控制器类的唯一实例
    private static Controller controller;

    // 游戏实例管理器，用于管理游戏的实例
    private static InstanceManager instanceManager = InstanceManager.getInstanceManager();

    // 视图类，用于显示游戏界面
    private static Viewer viewer;

    // 数据映射器，用于处理游戏数据
    private static Mapper mapper;

    // 网络通信类，用于处理UDP通信
    private static NetUDP net;

    // 游戏板的当前状态（NOPE 表示未开始，PLAY 表示正在游戏中，WAIT 表示等待对方操作，FINISH 表示游戏结束）
    private static BoardCondition BoardCondition = Bean.BoardCondition.NOPE;

    // 游戏信息对象，包含游戏的基本信息
    private static GameInfo gameInfo;

    // 当前玩家
    private static Player currentPlayer;

    // 敌方玩家
    private static Player enemyPlayer;

    // 当前玩家的棋子颜色（例如：黑棋或白棋）
    private static ChessCondition side = ChessCondition.EMPTY;

    // 游戏胜利者
    private static Player winner = null;

    // 检查胜利条件的工具类
    private static CheckWin winChecker;

    // 用于发送游戏相关消息的线程
    private static Thread postThread = null;

    // 控制线程是否被终止的标志
    private static boolean threadKill = false;

    // 获取控制器的唯一实例（单例模式）
    public static Controller getController() {
        if (controller == null) {
            controller = new Controller(); // 如果实例为空，创建新的实例
        }
        return controller;
    }

    // 设置游戏信息
    public static void setGameInfo(GameInfo gameInfo) {
        Controller.gameInfo = gameInfo;
    }

    // 设置当前玩家，并根据当前玩家决定敌方玩家
    public static void setCurrentPlayer(Player currentPlayer) {
        Controller.currentPlayer = currentPlayer;
        // 判断当前玩家是哪一方，并确定敌方玩家
        if (currentPlayer.getName().equals(gameInfo.getP1().getName())) {
            enemyPlayer = (Player) gameInfo.getP2();
        } else {
            enemyPlayer = (Player) gameInfo.getP1();
        }
    }

    // 游戏开始时传入的游戏密钥
    private static String key;

    // 设置游戏密钥
    public void setKey(String k) {
        key = k;
    }

    // 获取视图实例
    public static Viewer getViewer() {
        return viewer;
    }

    // 获取数据映射器实例
    public static Mapper getMapper() {
        return mapper;
    }

    // 初始化并启动游戏
    public void start() {
        // 初始化视图和数据映射器
        // 初始化网络通信
        net = NetUDP.getNet();
        viewer = instanceManager.getViewer(key);
        mapper = instanceManager.getMapper(key);
        // 设置游戏信息
        Viewer.setGameInfo(gameInfo);
        Mapper.setGameInfo(gameInfo);
        // 初始化视图
        viewer.init();
        // 设置本地和远程地址
        AddressBattle.getInstance().setAddressLocal(currentPlayer.getIp(), currentPlayer.getPort());
        AddressBattle.getInstance().setAddressRemote(enemyPlayer.getIp(), enemyPlayer.getPort());
        System.out.println("currentPlayer");
        System.out.println(currentPlayer.toString());
        // 判断当前玩家并选择棋子
        if (currentPlayer.getName().equals(gameInfo.getP1().getName())) {
            side = net.selectSideA(AddressBattle.getAddressLocal(), AddressBattle.getAddressRemote());

        } else {
            side = net.selectSideB(AddressBattle.getAddressLocal(), AddressBattle.getAddressRemote());
        }
        // 输出当前选择的棋子颜色
        System.out.println("side: " + side);
        viewer.setBoardCondition(BoardCondition);
        // 获取胜利条件检查实例
        winChecker = CheckWin.getInstance(gameInfo);

        // 启动用于发送游戏消息的线程
        postThread = new Thread(new Runnable() {
            @Override
            public void run() {
                while (!threadKill && net.poster(AddressBattle.getAddressLocal(), AddressBattle.getAddressRemote())) {}
                System.out.println("poster exit");
            }
        });
        postThread.start();

        // 根据选择的棋子设置棋盘状态
        if (side == ChessCondition.BLACK) {
            BoardCondition = Bean.BoardCondition.PLAY;
        } else {
            BoardCondition = Bean.BoardCondition.NOPE;
        }
        System.out.println(BoardCondition);
        // 如果需要，可在此处启动游戏主循环
        // gameLoopStart();
    }

    // 处理本地玩家点击棋盘后的操作（下棋、撤回等）
    public void notifyBoardPress(int row, int col) {
        try {
            switch (BoardCondition) {
                case NOPE:
                    break;
                case PLAY:
                    // 设置当前棋子
                    System.out.println(row + " " + col + " " + side);
                    viewer.setChess(new Chess(row, col, side));
                    // 向远程玩家发送消息
                    MessageBuffer.setBattleMessage(new BattleMessage(new Chess(row, col, side), Actions.NORM, ""));
                    Mapper.addChess(new Chess(row, col, side));
                    BoardCondition = Bean.BoardCondition.WAIT; // 设置为等待状态
                    
                    // 检查是否获胜
                    if (winChecker.isWon()) {
                        winner = currentPlayer;
                        BoardCondition = Bean.BoardCondition.FINISH;
                        viewer.showFinishBox(true); // 显示游戏结束框
                        postThread.interrupt(); // 中断发送线程
                    }
                    break;
                case FINISH:
                    // 游戏结束后显示胜利框
                    viewer.showFinishBox(winner.equals(currentPlayer));
                    break;
                default:
                    break;
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    // 处理远程玩家的消息（下棋、撤回、退出、聊天等）
    public void notifyRemote(BattleMessage battleMessage) {
        try {
            switch (battleMessage.getAction()) {
                case NORM:
                    if (BoardCondition == Bean.BoardCondition.WAIT || BoardCondition == Bean.BoardCondition.NOPE) {
                        if (battleMessage.getChess().getCondition() != side) {
                            viewer.setChess(battleMessage.getChess());
                        }
                        BoardCondition = Bean.BoardCondition.PLAY;
                        Mapper.addChess(battleMessage.getChess());
                        
                        // 检查是否胜利
                        if (winChecker.isWon()) {
                            winner = enemyPlayer;
                            MessageBuffer.getInstance().clear();
                            BoardCondition = Bean.BoardCondition.FINISH;
                            viewer.showFinishBox(false);
                            postThread.interrupt();
                        }
                    }
                    break;
                case WITHDRAW:
                    if (battleMessage.getChess().getCondition() != side) {
                        viewer.withdrawChess(battleMessage.getChess());
                    }
                    BoardCondition = Bean.BoardCondition.WAIT;
                    Mapper.removeChess(battleMessage.getChess());
                    break;
                case QUIT:
                    BoardCondition = Bean.BoardCondition.FINISH;
                    setWinner(currentPlayer);
                    viewer.showFinishBox(true);
                    threadKill = true;
                    break;
                case TEXT:
                    if (battleMessage.getChess().getCondition() != side) {
                        viewer.setChatText(battleMessage.getText());
                    }
                    break;
                default:
                    break;
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    // 获取当前玩家
    public static Player getCurrentPlayer() {
        return currentPlayer;
    }

    // 获取敌方玩家
    public static Player getEnemyPlayer() {
        return enemyPlayer;
    }

    // 设置棋盘状态
    public void setBoardCondition(BoardCondition boardCondition) {
        BoardCondition = boardCondition;
    }

    // 设置游戏的胜利者
    public static void setWinner(Player winner) {
        Controller.winner = winner;
    }

    // 获取当前玩家的棋子颜色
    public static ChessCondition getSide() {
        return side;
    }

    // 获取当前棋盘状态
    public static BoardCondition getBoardCondition() {
        return BoardCondition;
    }

    // 获取发送消息的线程
    public static Thread getPostThread() {
        return postThread;
    }

    // 获取线程是否被终止的状态
    public static boolean isThreadKill() {
        return threadKill;
    }

    // 设置线程是否被终止
    public static void setThreadKill(boolean threadKill) {
        Controller.threadKill = threadKill;
    }
}
