package View;

import Bean.BoardInfo;
import Bean.ChessCondition;

import javax.swing.*;
import java.awt.*;

class chessBoardLocal extends JPanel {
    private static ImageIcon icon;
    private static Image img;

    // 围棋棋盘
    public chessBoardLocal() {
        icon = new ImageIcon("src/main/resource/img/chessboard.png");
        img = icon.getImage();

        setLayout(new GridLayout(BoardInfo.BOARD_SIZE, BoardInfo.BOARD_SIZE));
        setSize(300, 300);
        setLocation(0, 0);
        setBackground(Color.BLACK);
        setVisible(true);
        for (int i = 1; i <= BoardInfo.BOARD_SIZE; i++) {
            for (int j = 1; j <= BoardInfo.BOARD_SIZE; j++) {
                add(new chessSquareLocal(i, j, ChessCondition.EMPTY));
            }
        }
    }

    @Override
    public void paintComponent(Graphics g) {
        super.paintComponent(g);
        //下面这行是为了背景图片可以跟随窗口自行调整大小，可以自己设置成固定大小
        g.drawImage(img, 0, 0, this.getWidth(), this.getHeight(), this);
    }

    public void setChess(int row, int col, ChessCondition c) {
        ((chessSquareLocal) getComponent((row-1) * BoardInfo.BOARD_SIZE + (col-1))).setChess(c);
        //System.out.println(chess.getRow() + " " + chess.getCol());

        //repaint();
    }
}
