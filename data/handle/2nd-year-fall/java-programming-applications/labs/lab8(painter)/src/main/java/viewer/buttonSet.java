package viewer;

import javax.swing.*;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.util.Vector;

// 各种形状按钮类
class triangularButton extends JButton {
    triangularButton() {
        super("Triangle");
        setPreferredSize(new java.awt.Dimension(100, 80));
        setContentAreaFilled(true);
        setVisible(true);
    }
}

class rectangularButton extends JButton {
    rectangularButton(){
        super("Rectangle");
        setPreferredSize(new java.awt.Dimension(100, 80));
        setContentAreaFilled(true);
        setVisible(true);
    }
}

class ovalButton extends JButton {
    ovalButton(){
        super("Oval");
        setPreferredSize(new java.awt.Dimension(100, 80));
        setContentAreaFilled(true);
        setVisible(true);
    }
}

class roundButton extends JButton {
    roundButton(){
        super("Round");
        setPreferredSize(new java.awt.Dimension(100, 80));
        setContentAreaFilled(true);
        setVisible(true);
    }
}

class lineButton extends JButton {
    lineButton(){
        super("Line");
        setPreferredSize(new java.awt.Dimension(100, 80));
        setContentAreaFilled(true);
        setVisible(true);
    }
}

// 文本按钮类
class textButton extends JButton {
    textButton() {
        super("Text");
        setPreferredSize(new java.awt.Dimension(100, 80));
        setContentAreaFilled(true);
        setVisible(true);
    }
}

// 按钮集合类
public class buttonSet {
    public static Vector<JButton> buttons;
    public static JButton selected = new JButton();

    class buttonListener implements ActionListener {
        @Override
        public void actionPerformed(ActionEvent e) {
            selected = (JButton) e.getSource();
            System.out.println("Selected: " + selected.getText());
        }
    }

    public buttonSet() {
        buttons = new Vector<JButton>();
        // 添加各种按钮
        buttons.add(new triangularButton());
        buttons.add(new rectangularButton());
        buttons.add(new ovalButton());
        buttons.add(new roundButton());
        buttons.add(new lineButton());
        buttons.add(new textButton());  // 添加文本按钮

        // 为每个按钮添加监听器
        for (JButton b : buttons) {
            b.addActionListener(new buttonListener());
        }
    }
}
