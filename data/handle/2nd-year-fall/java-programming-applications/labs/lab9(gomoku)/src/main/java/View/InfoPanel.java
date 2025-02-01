package View;

import Bean.ChessCondition;
import Bean.GameInfo;
import Bean.Player;
import Controller.Controller;

import javax.swing.*;
import java.awt.*;

public class InfoPanel extends JPanel {
    private static GameInfo gameInfo;
    private static JLabel sideLabel1, sideLabel2;
    private static JLabel player1Label, player2Label;
    private static ImageIcon black, white;

    public static void setGameInfo(GameInfo gameInfo) {
        InfoPanel.gameInfo = gameInfo;
    }

    public InfoPanel(GameInfo gameInfo) {
        InfoPanel.gameInfo = gameInfo;

        setLayout(new GridLayout(1, 2));
        JPanel p1, p2;
        p1 = new JPanel();
        p2 = new JPanel();
        p1.setLayout(new GridLayout(4, 1));
        p2.setLayout(new GridLayout(4, 1));
        ImageIcon originalIcon = new ImageIcon("src\\main\\resource\\img\\black.png");  // 替换为图标的路径
        Image originalImage = originalIcon.getImage();  // 获取原始图像
        // 缩小图标的大小，设置新的宽度和高度
        int newWidth = 30;  // 新的宽度
        int newHeight = 30; // 新的高度
        Image resizedImage = originalImage.getScaledInstance(newWidth, newHeight, Image.SCALE_SMOOTH);
        black = new ImageIcon(resizedImage);

        originalIcon = new ImageIcon("src\\main\\resource\\img\\white.png");  // 替换为图标的路径
        originalImage = originalIcon.getImage();  // 获取原始图像
        resizedImage = originalImage.getScaledInstance(newWidth, newHeight, Image.SCALE_SMOOTH);
        white = new ImageIcon(resizedImage);
        
        // 创建并设置 JLabel 的字体样式、大小和颜色
        sideLabel1 = new JLabel("Waiting");
        sideLabel1.setFont(new Font("Times", Font.PLAIN, 15));
        sideLabel1.setForeground(Color.BLACK);
        

        player1Label = new JLabel("Player 1",sideLabel1.getText() == "Black"?black:white,JLabel.LEFT);
        player1Label.setFont(new Font("Times", Font.PLAIN, 20));
        player1Label.setForeground(Color.BLACK);
        p1.add(player1Label);
        System.out.println(sideLabel1.getText());
        JLabel playerName1 = new JLabel(gameInfo.getP1().getName());
        playerName1.setFont(new Font("Times", Font.PLAIN, 24));
        playerName1.setForeground(Color.BLACK);
        p1.add(playerName1);

        JLabel playerInfo1 = new JLabel(((Player) gameInfo.getP1()).getPort() + "@" + ((Player) gameInfo.getP2()).getIp());
        playerInfo1.setFont(new Font("Times", Font.PLAIN, 15));
        playerInfo1.setForeground(Color.BLACK);
        p1.add(playerInfo1);
        p1.add(sideLabel1);


        sideLabel2 = new JLabel("Waiting");
        sideLabel2.setFont(new Font("Times", Font.PLAIN, 15));
        sideLabel2.setForeground(Color.BLACK);
        

        player2Label = new JLabel("Player 2",gameInfo.getP2().getChessCondition()==ChessCondition.BLACK?black:white,JLabel.LEFT);
        player2Label.setFont(new Font("Times", Font.PLAIN, 20));
        player2Label.setForeground(Color.BLACK);
        p2.add(player2Label);

        JLabel playerName2 = new JLabel(gameInfo.getP2().getName());
        playerName2.setFont(new Font("Times", Font.PLAIN, 24));
        playerName2.setForeground(Color.BLACK);
        p2.add(playerName2);

        JLabel playerInfo2 = new JLabel(((Player) gameInfo.getP2()).getPort() + "@" + ((Player) gameInfo.getP2()).getIp());
        playerInfo2.setFont(new Font("Times", Font.PLAIN, 15));
        playerInfo2.setForeground(Color.BLACK);
        p2.add(playerInfo2);
        p2.add(sideLabel2);


        add(p1);
        add(p2);
        setVisible(true);
    }

    public void setEnemySide(ChessCondition chose) {
        Player p = Controller.getEnemyPlayer();
        if (p.getName().equals(gameInfo.getP1().getName())) {
            sideLabel1.setText(chose.toString());
            player1Label.setIcon(sideLabel1.getText() == "Black"?black:white);
        } else {
            sideLabel2.setText(chose.toString());
            player2Label.setIcon(sideLabel2.getText() == "Black"?black:white);
        }
    }

    public void setCurrSide(ChessCondition chose) {
        if (gameInfo.getP1().getName().equals(Controller.getCurrentPlayer().getName())) {
            sideLabel1.setText(chose.toString());
            player1Label.setIcon(sideLabel1.getText() == "Black"?black:white);
        } else {
            sideLabel2.setText(chose.toString());
            player2Label.setIcon(sideLabel2.getText() == "Black"?black:white);
        }
    }
}
