package viewer;

import javax.swing.*;
import java.awt.*;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.io.File;

public class TopPanel extends JPanel {
    public static shapeColor color;
    public static background background;
    public static textSetter textSetter;
    public static fillRegion fillRegion;
    
    private JButton saveButton; // 添加保存按钮
    
    TopPanel() {
        // 使用 GridBagLayout 布局
        setLayout(new GridBagLayout()); 
        setPreferredSize(new Dimension(900, 120)); // 增加面板的高度，以避免组件过于拥挤
        setBackground(Color.WHITE); // 设置面板背景颜色
        setBorder(BorderFactory.createMatteBorder(0, 0, 5, 0, Color.BLACK)); // 添加较小的下边框，减小底部边框的宽度

        // 创建 GridBagConstraints 对象，用于设置布局约束
        GridBagConstraints gbc = new GridBagConstraints();
        gbc.fill = GridBagConstraints.HORIZONTAL; // 组件填充水平方向
        gbc.insets = new Insets(10, 10, 0, 10); // 添加组件间的空白间隔

        // 左侧面板，用于放置颜色选择器和背景设置
        JPanel leftPanel = new JPanel();
        leftPanel.setLayout(new BoxLayout(leftPanel, BoxLayout.Y_AXIS)); // 使用 BoxLayout 垂直排列组件
        leftPanel.setPreferredSize(new Dimension(400, 50)); // 设置左侧面板的大小
        leftPanel.setBackground(Color.WHITE); // 设置背景颜色
        
        color = new shapeColor(); // 创建形状颜色设置组件
        leftPanel.add(color); // 将形状颜色设置组件添加到左侧面板
        background = new background(); // 创建背景设置组件
        leftPanel.add(background); // 将背景设置组件添加到左侧面板

        // 右侧面板，用于放置文本输入框和填充区域设置
        JPanel rightPanel = new JPanel();
        rightPanel.setLayout(new BoxLayout(rightPanel, BoxLayout.Y_AXIS)); // 垂直排列
        rightPanel.setPreferredSize(new Dimension(400, 50)); // 设置右侧面板的大小
        rightPanel.setBackground(Color.PINK); // 设置背景颜色
        
        textSetter = new textSetter(); // 创建文本设置组件
        rightPanel.add(textSetter); // 将文本设置组件添加到右侧面板
        fillRegion = new fillRegion(); // 创建填充区域设置组件
        rightPanel.add(fillRegion); // 将填充区域设置组件添加到右侧面板

        // 左侧面板添加到主面板
        gbc.gridx = 0;
        gbc.gridy = 0;
        gbc.gridwidth = 1; // 占一列
        gbc.weightx = 0.5; // 左侧面板占 50% 宽度
        this.add(leftPanel, gbc);

        // 右侧面板添加到主面板
        gbc.gridx = 1;
        gbc.gridy = 0;
        gbc.gridwidth = 1; // 占一列
        gbc.weightx = 0.5; // 右侧面板占 50% 宽度
        this.add(rightPanel, gbc);

        // 创建保存按钮面板，并将其放置在底部
        JPanel savePanel = new JPanel();
        savePanel.setLayout(new FlowLayout(FlowLayout.CENTER)); // 使用 FlowLayout 居中对齐保存按钮
        savePanel.setBackground(Color.WHITE); // 设置保存按钮面板的背景颜色
        
        saveButton = new JButton("Save"); // 创建保存按钮
        saveButton.setPreferredSize(new Dimension(100, 30)); // 调整保存按钮的大小
        saveButton.addActionListener(new SaveButtonListener()); // 为保存按钮添加事件监听器
        savePanel.add(saveButton); // 将保存按钮添加到保存面板
        
        // 设置保存按钮面板的布局，确保它在底部不遮挡其他组件
        gbc.gridx = 0;
        gbc.gridy = 1;
        gbc.gridwidth = 2; // 保存面板跨越两列
        gbc.weighty = 0.1; // 设置保存按钮的垂直间距
        this.add(savePanel, gbc); // 将保存面板放到底部
    }

    // 保存按钮的事件处理
    private class SaveButtonListener implements ActionListener {
        @Override
        public void actionPerformed(ActionEvent e) {
            // 弹出文件保存对话框
            JFileChooser fileChooser = new JFileChooser();
            fileChooser.setDialogTitle("Save Image"); // 设置对话框标题
            int userSelection = fileChooser.showSaveDialog(null); // 显示保存对话框

            if (userSelection == JFileChooser.APPROVE_OPTION) { // 如果用户选择了文件
                File fileToSave = fileChooser.getSelectedFile(); // 获取用户选择的文件
                // 在此处调用保存图像的方法（假设绘图面板有保存图像的方法）
                // drawPanel.saveImage(fileToSave); 
                JOptionPane.showMessageDialog(null, "Image saved to: " + fileToSave.getAbsolutePath()); // 提示用户保存路径
            }
        }
    }
}
