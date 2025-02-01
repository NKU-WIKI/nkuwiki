package viewer;

import javax.swing.*;
import java.awt.*;

public class Viewer {
    private JFrame mainFrame;
    private TopPanel topPanel;
    private leftControlBar leftControlBar;
    private buttonSet buttonSet;
    private drawPanel drawPanel;

    public Viewer(JFrame main) {
        mainFrame = main;
    }

    public void update() {
        drawPanel.setLineColor(topPanel.color.getColor());
        drawPanel.setFillColor(topPanel.background.selectedColor);
        drawPanel.setText(topPanel.textSetter.getEnteredText());
        drawPanel.setFont(topPanel.textSetter.getTextSize());
        switch(buttonSet.selected.getText()){
            case "Line":
                System.out.println("draw Line");
                drawPanel.setCurrentShape("Line");
                break;
                case "Rectangle":
                    System.out.println("draw Rectangle");
                drawPanel.setCurrentShape("Rectangle");
                break;
                case "Oval":
                drawPanel.setCurrentShape("Oval");
                break;
                case "Triangle":
                drawPanel.setCurrentShape("Triangle");
                break;
                case"Round":
                drawPanel.setCurrentShape("Round");
                break;
                case"Text":
                drawPanel.setCurrentShape("Text");
                break;

            default:
        }
        // mainFrame.repaint();
    }

    public void init() {
        mainFrame.setTitle("Painter");
        mainFrame.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        mainFrame.setSize(800, 690);
        mainFrame.setLocationRelativeTo(null);

        // mainFrame.setBackground(new java.awt.Color(255, 255, 255));
        mainFrame.setBackground(Color.BLUE);
        mainFrame.setLayout(new BorderLayout());

        topPanel = new TopPanel();
        mainFrame.add(topPanel, BorderLayout.NORTH);

        leftControlBar = new viewer.leftControlBar();
        mainFrame.add(leftControlBar, BorderLayout.WEST);

        drawPanel = new drawPanel();
        mainFrame.add(drawPanel, BorderLayout.CENTER);
    }

    public void show() {
        mainFrame.setVisible(true);
    }
}
