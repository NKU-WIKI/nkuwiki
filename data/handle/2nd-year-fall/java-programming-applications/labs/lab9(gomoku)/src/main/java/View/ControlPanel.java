package View;

import Bean.*;
import Controller.*;
import Map.Mapper;
import Map.MapperLocal;
import Map.MessageBuffer;
import Util.SaveGameToFile;

import javax.swing.*;
import java.awt.*;
import java.awt.event.ActionListener;

public class ControlPanel extends JPanel {
    private JButton withdrawButton;
    private JButton quitButton;
    private JButton previousButton;
    private JButton nextButton;
    private JButton saveToFile;
    
    public ControlPanel(GameInfo gameInfo) {
        this.setLayout(new GridLayout(2,3));
        this.setBorder(BorderFactory.createEmptyBorder(10, 10, 10, 10));
        withdrawButton = new JButton("Withdraw");
        // withdrawButton.setBorderPainted(false);
        
        withdrawButton.addActionListener(new ActionListener() {
           @Override
           public void actionPerformed(java.awt.event.ActionEvent e) {
            Chess toSend=null;
           
            if(gameInfo.isLOCAL() == true){
                // System.out.println(gameInfo.isLOCAL());
                if(MapperLocal.getChesses().size() == 0) {
                    return;
                }
               
                for(int i=MapperLocal.getChesses().size()-1;i>=0;i--){
                    if(MapperLocal.getChesses().get(i).getCondition().equals(ControllerLocal.getSide())){
                        toSend=MapperLocal.getChesses().get(i);
                        MapperLocal.getChesses().remove(i);
                        ViewerLocal.getViewer(gameInfo).withdrawChess(toSend);
                        break;
                    }
                }
            }else{
                if(Mapper.getChesses().size() == 0) {
                    return;
                }
                for(int i=Mapper.getChesses().size()-1;i>=0;i--){
                    if(Mapper.getChesses().get(i).getCondition().equals(Controller.getSide())){
                        toSend=Mapper.getChesses().get(i);
                        Mapper.getChesses().remove(i);
                        Viewer.getViewer().withdrawChess(toSend);
                        break;
                    }
                }
                Controller.getController().setBoardCondition(BoardCondition.PLAY);
            }
               MessageBuffer.getInstance().setBattleMessage(new BattleMessage(toSend,Actions.WITHDRAW,""));
           }
        });
        add(withdrawButton);

        quitButton = new JButton("Quit");
        quitButton.addActionListener(new ActionListener() {
           @Override
           public void actionPerformed(java.awt.event.ActionEvent e) {
               MessageBuffer.getInstance().setBattleMessage(new BattleMessage(Actions.QUIT));
               Controller.setWinner(Controller.getEnemyPlayer());
               Controller.getController().setBoardCondition(BoardCondition.FINISH);
               Controller.getController().notifyBoardPress(-1,-1);

               Controller.setThreadKill(true);
           }
        });
        add(this.quitButton);

        saveToFile = new JButton("Save to File");
        saveToFile.addActionListener(new ActionListener() {
            @Override
            public void actionPerformed(java.awt.event.ActionEvent e) {
                if(gameInfo.isLOCAL() == true){
                    SaveGameToFile.getInstance().saveGame(gameInfo.getP1(),gameInfo.getP2(),MapperLocal.getChesses());
                }else{
                    SaveGameToFile.getInstance().saveGame(Controller.getCurrentPlayer(),Controller.getEnemyPlayer(),Mapper.getChesses());
                }
            }
        });
        add(this.saveToFile);

        previousButton = new JButton("Previous");
        previousButton.addActionListener(new ActionListener() {
            @Override
            public void actionPerformed(java.awt.event.ActionEvent e) {
                if(Mapper.getChesses().size() == 0) {
                    return;
                }else{
                    Chess removed =Mapper.getChesses().remove(Mapper.getChesses().size()-1);
                    ControllerReview.getChessVector().add(removed);
                    Viewer.getViewer().withdrawChess(removed);
                }
            }
        });
        add(this.previousButton);

        nextButton = new JButton("Next");
        nextButton.addActionListener(new ActionListener() {
            @Override
            public void actionPerformed(java.awt.event.ActionEvent e) {
                if(ControllerReview.getChessVector().size() == 0) {
                    return;
                }else {
                    
                    Chess toSet=ControllerReview.getChessVector().remove(ControllerReview.getChessVector().size()-1);
                    Mapper.getChesses().add(toSet);
                    Viewer.getViewer().setChess(toSet);
                    // System.out.println(toSet.getRow());
                    // System.out.println(toSet.getCol());
                    // System.out.println(toSet.getCondition());
                    
                }
            }
        });
        add(this.nextButton);
        
        withdrawButton.setBackground(new Color(173, 216, 230));
        quitButton.setBackground(new Color(230,97,94));
        saveToFile.setBackground(new Color(124, 203, 240));
        previousButton.setBackground(new Color(145, 211, 240));
        nextButton.setBackground(new Color(106, 201, 241));
        withdrawButton.setFocusPainted(false);
        quitButton.setFocusPainted(false);
        saveToFile.setFocusPainted(false);
        previousButton.setFocusPainted(false);
        withdrawButton.setFocusPainted(false);
    }

    public void setOnlineMode(){
        this.withdrawButton.setEnabled(true);
        this.quitButton.setEnabled(true);
        this.previousButton.setEnabled(false);
        this.nextButton.setEnabled(false);
    }

    public void setOfflineMode() {
        this.withdrawButton.setEnabled(false);
        this.quitButton.setEnabled(false);
        this.saveToFile.setEnabled(false);
        this.previousButton.setEnabled(true);
        this.nextButton.setEnabled(true);

    }
}
