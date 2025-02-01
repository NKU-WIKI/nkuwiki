package viewer;

import javax.swing.*;
import java.awt.*;
import java.awt.event.ActionListener;
import java.util.HashMap;
import java.util.Map;

public class shapeColor extends JPanel {
    private Color color = Color.RED; // 默认颜色为红色
    private JComboBox<String> comboBox;
    private Map<String, Color> colorMap;

    public shapeColor() {
        // 初始化颜色映射
        colorMap = new HashMap<>();
        colorMap.put("Red", Color.RED);
        colorMap.put("Green", Color.GREEN);
        colorMap.put("Blue", Color.BLUE);
        colorMap.put("Yellow", Color.YELLOW);
        colorMap.put("Black", Color.BLACK);
        colorMap.put("White", Color.WHITE);

        // 设置布局和面板大小
        setLayout(new GridLayout(1, 2));
        setBackground(Color.WHITE);
        setPreferredSize(new Dimension(200, 50));

        // 标签设置
        JLabel label = new JLabel("Line Color");
        label.setHorizontalAlignment(JLabel.CENTER);
        add(label);

        // 创建下拉框
        comboBox = new JComboBox<>(colorMap.keySet().toArray(new String[0]));
        comboBox.setSelectedItem("Red"); // 设置默认选择为红色
        comboBox.addActionListener(e -> updateColor());
        add(comboBox);
        setBackground(color);
    }

    // 根据选择的颜色更新color属性
    private void updateColor() {
        String colorName = (String) comboBox.getSelectedItem();
        color = colorMap.getOrDefault(colorName, Color.RED); // 默认为红色
        setBackground(color);
    }

    // 获取当前选择的颜色
    public Color getColor() {
        return color;
    }
}
