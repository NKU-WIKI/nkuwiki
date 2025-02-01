package View;

import Bean.*;

import javax.swing.*;
import java.awt.*;

public class ViewerLocal extends JFrame implements View {
    private static ViewerLocal viewer;
    private static GameInfo gameInfo;

    public static ViewerLocal getViewer(GameInfo _gameInfo) {
        if (viewer == null) {
            viewer = new ViewerLocal();
            gameInfo = _gameInfo;
            System.out.println("viewer");
        }
        return viewer;
    }

    public static void setGameInfo(GameInfo gameInfo) {
        ViewerLocal.gameInfo = gameInfo;
    }

    private String key;


    public void setKey(String key) {
        this.key = key;
    }

    @Override
    public void setChess(Chess chess) {
        chessBoard.setChess(chess.getRow(),chess.getCol(),chess.getCondition());
    }

    public void withdrawChess(Chess chess) {
        chessBoard.setChess(chess.getRow(),chess.getCol(),ChessCondition.EMPTY);
    }

    @Override
    public void setInfo(Player info) {

    }

    private BoardCondition boardCondition=BoardCondition.NOPE;
    private chessBoardLocal chessBoard;
    private RightPanel rightPanel;
    private TimerPanel timerPanel;

    public void init(){

        chessBoard=new chessBoardLocal();
        this.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setLayout(new BorderLayout());
        add(chessBoard,BorderLayout.CENTER);
        rightPanel=new RightPanel(gameInfo);
        RightPanel.setOnlineMode();
        add(rightPanel,BorderLayout.EAST);
        timerPanel=new TimerPanel();
        add(timerPanel,BorderLayout.WEST);
        this.setSize(900, 600);
        setLocationRelativeTo(null);
        this.setVisible(true);


    }

    public chessBoardLocal getChessBoard() {
        return chessBoard;
    }

    public void setBoardCondition(BoardCondition boardCondition) {
        this.boardCondition = boardCondition;
    }

    public InfoPanel getInfoPanel() {
        return rightPanel.getInfoPanel();
    }


    public ChessCondition selectSide() {
        //pop a message box let user choose black or white
        String[] options = {"black", "white"};
        int n = JOptionPane.showOptionDialog(null, "Choose your side", "Side",
                JOptionPane.YES_NO_OPTION, JOptionPane.QUESTION_MESSAGE, null, options, options[0]);
        if (n == 0) {
            return ChessCondition.BLACK;
        } else {
            return ChessCondition.WHITE;
        }
    }


    public void showFinishBox(boolean isWinner) {

        String[] options = {"OK"};
        if (isWinner) {
            JOptionPane.showMessageDialog(null, "YOU WIN! Game Over");
        }   else {
            JOptionPane.showMessageDialog(null, "YOU LOSE! Game Over");
        }
    }

    public void setChatText(String text) {
        RightPanel.getChatPanel().setText(text);
    }

    public RightPanel getRightPanel() {
        return rightPanel;
    }

    public void showFinishBox(String s) {
        String[] options = {"OK"};
        JOptionPane.showMessageDialog(null, s);
    }
}
