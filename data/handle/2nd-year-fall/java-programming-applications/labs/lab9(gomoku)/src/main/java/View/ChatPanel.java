package View;

import Bean.Actions;
import Bean.BattleMessage;
import Bean.Chess;
import Controller.Controller;
import Map.MessageBuffer;

import javax.swing.*;
import java.awt.*;

public class ChatPanel extends JPanel {
    private JTextArea chatArea;
    private JTextField chatField;
    private JButton sendButton;
    private JPanel sendPanel;

    public ChatPanel() {
        setLayout(new BorderLayout());

        chatArea = new JTextArea();
        chatArea.setEditable(false);
        chatArea.setLineWrap(true);
        chatArea.setWrapStyleWord(true);
        chatArea.setBorder(BorderFactory.createTitledBorder("Chat"));
        add(chatArea, BorderLayout.CENTER);

        sendPanel = new JPanel();
        sendPanel.setLayout(new GridLayout(1, 2));
        chatField = new JTextField();
        chatField.setBorder(BorderFactory.createTitledBorder("Message"));
        sendPanel.add(chatField);

        sendButton = new JButton("Send");
        sendButton.addActionListener(e -> {
            String message = chatField.getText();
            chatField.setText("");
            String playerName = Controller.getCurrentPlayer().getName();
            chatArea.append(playerName+": "+message + "\n");

            MessageBuffer.getInstance().setBattleMessage(new BattleMessage(new Chess(Controller.getSide()),Actions.TEXT,message));
        });
        sendPanel.add(sendButton);
        add(sendPanel, BorderLayout.SOUTH);
        sendButton.setBackground(new Color(22,125,192));
        sendButton.setFocusPainted(false);
    }

    public JTextArea getChatArea() {
        return chatArea;
    }

    public JTextField getChatField() {
        return chatField;
    }

    public JButton getSendButton() {
        return sendButton;
    }

    public void setText(String text) {
        String playerName = Controller.getEnemyPlayer().getName();
        String allText = chatArea.getText();
        // 将文本按行分割
        String[] lines = allText.split("\n");
        // 获取最后一行
        if (lines.length > 0) {
            String lastLine = lines[lines.length - 1];
            if(lastLine.equals(playerName+": "+text)) return ;
        }
        chatArea.append(playerName+": "+text+ "\n");
    }
}
