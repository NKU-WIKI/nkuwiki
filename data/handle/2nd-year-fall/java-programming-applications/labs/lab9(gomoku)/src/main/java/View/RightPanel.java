package View;

import Bean.GameInfo;

import javax.swing.*;
import java.awt.*;

public class RightPanel extends JPanel {
    private static InfoPanel infoPanel;
    private static ControlPanel controlPanel;
    private static ChatPanel chatPanel;
    public RightPanel(GameInfo gameInfo) {
        setLayout(new GridLayout(3,1));
        if(gameInfo.isLOCAL() == false){
            infoPanel = new InfoPanel(gameInfo);
            chatPanel = new ChatPanel();
            add(infoPanel);
            add(chatPanel);
        }
        controlPanel = new ControlPanel(gameInfo);
        add(controlPanel);
        setVisible(true);
    }

    public static InfoPanel getInfoPanel() {
        return infoPanel;
    }

    public static ControlPanel getControlPanel() {
        return controlPanel;
    }

    public static ChatPanel getChatPanel() {
        return chatPanel;
    }

    public static void setOnlineMode() {
        controlPanel.setOnlineMode();
    }

    public static void setOfflineMode() {
        controlPanel.setOfflineMode();
        chatPanel.setVisible(false);
    }

    public void setLocalMode() {
        chatPanel.setVisible(false);
        infoPanel.setVisible(false);
    }
}
