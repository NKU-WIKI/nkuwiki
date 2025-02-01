package View;

import Bean.*;
import javax.swing.*;
import java.awt.*;

public class Viewer extends JFrame implements View {
    // 单例模式：Viewer 类的唯一实例
    private static Viewer viewer;
    
    // 游戏信息
    private static GameInfo gameInfo;

    // 获取 Viewer 实例（单例模式）
    public static Viewer getViewer() {
        if (viewer == null) {
            viewer = new Viewer(); // 如果实例为空，创建新的实例
            System.out.println("viewer");
        }
        return viewer;
    }

    // 设置游戏信息
    public static void setGameInfo(GameInfo gameInfo) {
        Viewer.gameInfo = gameInfo;
    }

    // 游戏的唯一标识（如房间号等）
    private String key;

    // 设置游戏的密钥
    public void setKey(String key) {
        this.key = key;
    }

    // 设置棋盘上棋子的状态（实现了 View 接口中的 setChess 方法）
    @Override
    public void setChess(Chess chess) {
        chessBoard.setChess(chess.getRow(), chess.getCol(), chess.getCondition());
    }

    // 撤销棋子的操作
    public void withdrawChess(Chess chess) {
        chessBoard.setChess(chess.getRow(), chess.getCol(), ChessCondition.EMPTY);
    }

    // 设置玩家信息（该方法暂时未实现）
    @Override
    public void setInfo(Player info) {
        // 当前未实现此方法
    }

    // 当前游戏的状态（如 NOPE 表示未开始，PLAY 表示正在进行中）
    private BoardCondition boardCondition = BoardCondition.NOPE;
    
    // 棋盘、右侧面板、计时器面板实例
    private chessBoard chessBoard;
    public RightPanel rightPanel;
    private TimerPanel timerPanel;

    // 初始化界面
    public void init() {
        // 创建棋盘实例
        chessBoard = new chessBoard();
        
        // 设置窗口的默认关闭操作
        this.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        
        // 设置布局为边界布局
        setLayout(new BorderLayout());
        
        // 将棋盘面板添加到窗口的中央
        add(chessBoard, BorderLayout.CENTER);
        
        // 创建右侧面板并设置为在线模式，添加到窗口右侧
        rightPanel = new RightPanel(gameInfo);
        RightPanel.setOnlineMode();
        add(rightPanel, BorderLayout.EAST);
        
        // 创建计时器面板并添加到窗口左侧
        timerPanel = new TimerPanel();
        add(timerPanel, BorderLayout.WEST);
        
        // 设置窗口的大小
        this.setSize(900, 600);
        
        // 将窗口置于屏幕中央
        setLocationRelativeTo(null);
        
        // 显示窗口
        this.setVisible(true);
    }

    // 获取棋盘实例
    public chessBoard getChessBoard() {
        return chessBoard;
    }

    // 设置棋盘状态
    public void setBoardCondition(BoardCondition boardCondition) {
        this.boardCondition = boardCondition;
    }

    // 获取右侧面板中的信息面板
    public InfoPanel getInfoPanel() {
        return rightPanel.getInfoPanel();
    }

    // 选择棋子（黑棋或白棋）
    public ChessCondition selectSide() {
        // 弹出消息框让用户选择棋子颜色
        String[] options = {"black", "white"};
        int n = JOptionPane.showOptionDialog(null, "Choose your side", "Side",
                JOptionPane.YES_NO_OPTION, JOptionPane.QUESTION_MESSAGE, null, options, options[0]);
        
        // 根据选择返回黑棋或白棋
        if (n == 0) {
            return ChessCondition.BLACK;
        } else {
            return ChessCondition.WHITE;
        }
    }

    // 显示游戏结束提示框，提示用户是否获胜
    public void showFinishBox(boolean isWinner) {
        String[] options = {"OK"};
        if (isWinner) {
            JOptionPane.showMessageDialog(null, "YOU WIN! Game Over");
        } else {
            JOptionPane.showMessageDialog(null, "YOU LOSE! Game Over");
        }
    }

    // 设置聊天文本（在聊天面板中显示消息）
    public void setChatText(String text) {
        RightPanel.getChatPanel().setText(text);
    }

    // 获取右侧面板实例
    public RightPanel getRightPanel() {
        return rightPanel;
    }
}
