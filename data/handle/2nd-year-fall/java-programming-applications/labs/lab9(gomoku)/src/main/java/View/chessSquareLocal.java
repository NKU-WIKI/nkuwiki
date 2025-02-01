package View;

import Bean.ChessCondition;
import Controller.*;

import javax.swing.*;
import java.awt.*;
import java.awt.event.MouseAdapter;
import java.awt.event.MouseEvent;

class chessSquareLocal extends JPanel {
    private int row;
    private int col;
    private ChessCondition c;
    private ImageIcon icon;
    private Image img;

    public chessSquareLocal(int row, int col, ChessCondition c) {
        this.row = row;
        this.col = col;
        setBackground(null);
        setOpaque(false);
        this.c = c;
        switch (c) {
            case BLACK:
                icon = new ImageIcon("src/main/resource/img/black.png");
                img = icon.getImage();
                break;
            case WHITE:
                icon = new ImageIcon("src/main/resource/img/white.png");
                img = icon.getImage();
                break;
            default:
                img = null;
        }

        addMouseListener(new MouseAdapter(){
            @Override
            public void mousePressed(MouseEvent e) {
                ControllerLocal.getController().notifyBoardPress(row,col);
            }
        });
    }

    public int getCol() {
        return col;
    }

    public int getRow() {
        return row;
    }

    @Override
    public void paintComponent(Graphics g) {
        super.paintComponent(g);
        //下面这行是为了背景图片可以跟随窗口自行调整大小，可以自己设置成固定大小
        if (img != null)
            g.drawImage(img, 0, 0, this.getWidth(), this.getHeight(), this);
    }

    public void setChess(ChessCondition c) {
        this.c = c;
        switch (c) {
            case BLACK:
                icon = new ImageIcon("src/main/resource/img/black.png");
                System.out.println("set black");
                img = icon.getImage();
                break;
            case WHITE:
                icon = new ImageIcon("src/main/resource/img/white.png");
                System.out.println("set white");
                img = icon.getImage();
                break;
            default:
                System.out.println("set empty");
                img = null;
        }
        repaint();
    }
}
