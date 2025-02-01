package Interface;

import cacu.Caculor;

import javax.swing.*;
import java.awt.*;
import java.awt.event.*;
import javax.swing.border.LineBorder;

public class Interface extends JFrame {

    public Interface(String title) {
        super(title);

        // 设置文本区域的字体大小
        GridLayout textLayout = new GridLayout(2, 1);
        JPanel textPanel = new JPanel(textLayout);
        JTextField preTextField = new JTextField("0");
        preTextField.setEditable(false);
        preTextField.setHorizontalAlignment(JTextField.RIGHT);
        preTextField.setFont(new Font("宋体", Font.BOLD, 20)); // 增加字体大小
        preTextField.setBounds(0, 0, 500, 20);

        JTextField numlineField = new JTextField("0");
        numlineField.setBounds(22, 22, 500, 50);
        numlineField.setHorizontalAlignment(JTextField.RIGHT);
        numlineField.setFont(new Font("Times New Roman", Font.BOLD, 50)); // 增加字体大小

        textPanel.add(preTextField);
        textPanel.add(numlineField);

        // 设置按钮区域的布局
        GridLayout butGridLayout = new GridLayout(6, 4);
        JPanel butPanel = new JPanel(butGridLayout);
        butPanel.setPreferredSize(new Dimension(600, 600));

        // 定义按钮文本
        String[] buttonLabels = {
            "+/-", "C", "CE", "backspace", "(", ")", "^", "/",
            "7", "8", "9", "*", "4", "5", "6", "-",
            "1", "2", "3", "+", "%", "0", ".", "="
        };

        // 创建按钮数组
        JButton[] buttons = new JButton[24];
        for (int i = 0; i < 24; i++) {
            buttons[i] = new JButton(buttonLabels[i]);
            buttons[i].setFont(new Font("Arial", Font.BOLD, 20)); // 设置字体大小
            butPanel.add(buttons[i]);
        }

        // 为不同类型的按钮设置背景色
        for (int i = 0; i < buttons.length; i++) {
            String label = buttonLabels[i];
            switch (label) {
                case "=":
                    buttons[i].setBackground(new Color(34, 139, 34)); // 绿色
                    buttons[i].setForeground(Color.WHITE);
                    break;
                case "+":
                case "-":
                case "*":
                case "/":
                case "^":
                case "%":
                    buttons[i].setBackground(new Color(255, 165, 0)); // 橙色
                    buttons[i].setForeground(Color.WHITE);
                    break;
                case "C":
                case "CE":
                case "backspace":
                    buttons[i].setBackground(new Color(255, 69, 0)); // 红色
                    buttons[i].setForeground(Color.WHITE);
                    break;
                case "(":
                case ")":
                    buttons[i].setBackground(new Color(173, 216, 230)); // 淡蓝色
                    break;
                default:
                    if (label.equals("0")) {
                        buttons[i].setBackground(new Color(240, 248, 255)); // 淡灰色
                    } else {
                        buttons[i].setBackground(new Color(240, 248, 255)); // 淡灰色
                    }
                    buttons[i].setForeground(Color.BLACK);
                    break;
            }

            // 设置按钮的默认边框
            buttons[i].setBorder(new LineBorder(Color.DARK_GRAY, 2));
            buttons[i].setFocusPainted(false); // 去掉按钮的边框

            // 添加鼠标悬停事件：鼠标悬停时改变按钮背景色
            buttons[i].addMouseListener(new MouseAdapter() {
                @Override
                public void mouseEntered(MouseEvent e) {
                    JButton sourceButton = (JButton) e.getSource(); // 获取当前按钮
                    sourceButton.setBackground(sourceButton.getBackground().darker()); // 鼠标悬停时变暗
                    sourceButton.setBorder(new LineBorder(Color.BLUE, 2)); // 增加蓝色边框
                }

                @Override
                public void mouseExited(MouseEvent e) {
                    JButton sourceButton = (JButton) e.getSource(); // 获取当前按钮
                    String label = sourceButton.getText();
                    // 根据按钮类型恢复背景颜色
                    if (label.equals("=")) {
                        sourceButton.setBackground(new Color(34, 139, 34)); // 绿色
                    } else if (label.equals("+") || label.equals("-") || label.equals("*") || label.equals("/") || label.equals("^") || label.equals("%")) {
                        sourceButton.setBackground(new Color(255, 165, 0)); // 橙色
                    } else if (label.equals("C") || label.equals("CE") || label.equals("backspace")) {
                        sourceButton.setBackground(new Color(255, 69, 0)); // 红色
                    } else if (label.equals("(") || label.equals(")")) {
                        sourceButton.setBackground(new Color(173, 216, 230)); // 淡蓝色
                    } else {
                        sourceButton.setBackground(new Color(240, 248, 255)); // 淡灰色
                    }
                    sourceButton.setBorder(new LineBorder(Color.DARK_GRAY, 2)); // 恢复边框
                }

                @Override
                public void mousePressed(MouseEvent e) {
                    JButton sourceButton = (JButton) e.getSource(); // 获取当前按钮
                    sourceButton.setBackground(sourceButton.getBackground().brighter()); // 点击时变亮
                }

                @Override
                public void mouseReleased(MouseEvent e) {
                    JButton sourceButton = (JButton) e.getSource(); // 获取当前按钮
                    sourceButton.setBackground(sourceButton.getBackground().darker()); // 释放时变暗
                }
            });
        }

        // 按钮事件监听器
        class buttonListener implements ActionListener {
            @Override
            public void actionPerformed(ActionEvent e) {
                String what = ((JButton) e.getSource()).getText();

                preTextField.setText(numlineField.getText() + "=");
                switch (what) {
                    case "CE":
                        numlineField.setText("0"); // 清空输入框
                        break;
                    case "C":
                        numlineField.setText("0");
                        break;
                    case "+/-":
                        numlineField.setText(numlineField.getText().equals("0") ? "0" : "-" + numlineField.getText());
                        break;
                    case "=":
                        numlineField.setText(new Caculor().caculate(numlineField.getText()));
                        break;
                    case "backspace":
                        if (numlineField.getText().length() == 1) {
                            numlineField.setText("0");
                            break;
                        }
                        numlineField.setText(numlineField.getText().equals("0") ? "0" : numlineField.getText().substring(0, numlineField.getText().length() - 1));
                        break;
                    default:
                        numlineField.setText(numlineField.getText().equals("0") ? what : numlineField.getText() + what);
                }
            }
        }

        this.add(BorderLayout.NORTH, textPanel);
        this.add(BorderLayout.SOUTH, butPanel);

        // 为所有按钮添加监听器
        for (int i = 0; i < 24; i++) {
            ((JButton) butPanel.getComponent(i)).addActionListener(new buttonListener());
        }
    }

    public static void main(String[] args) {
        Interface startInterface = new Interface("Calculator");
        startInterface.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        startInterface.setSize(600, 800);
        startInterface.setUndecorated(true); // 去掉窗口的装饰
        startInterface.getRootPane().setWindowDecorationStyle(JRootPane.PLAIN_DIALOG); // 采用指定的窗口装饰风格

        startInterface.setVisible(true);
    }
}
