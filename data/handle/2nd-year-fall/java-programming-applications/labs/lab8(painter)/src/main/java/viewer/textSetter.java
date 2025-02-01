package viewer;

import javax.swing.*;
import java.awt.*;

public class textSetter extends JPanel {

    // 成员变量存储文本
    private String enteredText;
    private int textSize = 14; // 添加文本大小成员变量

    textSetter() {
        setLayout(new GridLayout(1, 3)); // GridLayout with 3 components

        // 创建并添加第一个文本框用于输入文本
        JTextField textField = new JTextField();
        textField.setText("Enter text here");  // 默认文本
        enteredText = textField.getText();  // 初始化成员变量为文本框的默认内容
        textField.addActionListener(e -> {
            enteredText = textField.getText();  // 更新成员变量为文本框的当前内容
        });
        add(textField);

        // 创建并添加一个标签
        JLabel label = new JLabel("Size:");
        add(label);

        // 创建并添加字体大小文本框
        JTextField fontSize = new JTextField("14"); // 默认字体大小为14
        fontSize.addActionListener(e -> {
            try {
                // 当用户按下回车时，尝试设置字体大小
                textSize = Integer.parseInt(fontSize.getText()); // 更新文本大小成员变量
                textField.setFont(new Font("Arial", Font.PLAIN, textSize)); // 设置文本框字体大小
            } catch (NumberFormatException ex) {
                // 如果输入的不是有效数字，则显示错误信息
                JOptionPane.showMessageDialog(this, "Invalid font size. Please enter a number.");
            }
        });
        
        add(fontSize);
    }

    // 获取存储的文本
    public String getEnteredText() {
        return enteredText;
    }

    // 获取文本大小
    public int getTextSize() {
        return textSize;
    }
}
