package viewer;

import javax.swing.*;
import java.awt.*;
import java.awt.event.MouseListener;
import java.awt.event.MouseAdapter;
import java.awt.event.MouseEvent;
import java.awt.image.BufferedImage;
import java.io.File;
import java.io.IOException;
import javax.imageio.ImageIO;
import static java.lang.Math.abs;

public class drawPanel extends JPanel {
    public int x, x1, x2;
    public int y, y1, y2;
    private Color backcol; // 用来存储背景颜色
    private BufferedImage image; // 用于保存图形的BufferedImage
    private String currentShape; // 存储当前图形类型
    private Color currentLineColor; // 存储当前线条颜色
    private Color currentFillColor; // 新增的用于存储填充颜色
    private String currentText; // 新增: 存储文本内容
    private Font currentFont; // 新增: 存储字体类型

    // 图形类型常
    public static final String LINE = "Line";
    public static final String RECTANGLE = "Rectangle";
    public static final String OVAL = "Oval";
    public static final String TRIANGLE = "Triangle";
    public static final String ROUND = "Round";
    public static final String TEXT = "Text"; // 新增: 文本类型

    // Constructor
    public drawPanel() {
        super();
        backcol = Color.WHITE; // 默认背景颜色为白色
        currentLineColor = Color.BLACK; // 默认线条颜色为黑色
        currentFillColor = Color.YELLOW; // 默认填充颜色为黄色
        setPreferredSize(new java.awt.Dimension(1000, 500)); // 设置面板大小
        setBackground(backcol); // 初始化时设置背景颜色

        // 创建一个BufferedImage来保存图形
        image = new BufferedImage(1000, 500, BufferedImage.TYPE_INT_ARGB);
        Graphics g = image.getGraphics();
        g.setColor(backcol);
        g.fillRect(0, 0, 1000, 500); // 填充背景色

        // 初始化为默认的图形类型
        currentShape = LINE; // 默认绘制线条
        currentText = ""; // 默认文本为空
        currentFont = new Font("Arial", Font.PLAIN, 14); // 默认字体

        // 添加鼠标监听事件，用来捕获绘制的起始和结束位置
        addMouseListener(new MouseAdapter() {
            @Override
            public void mousePressed(MouseEvent e) {
                x1 = e.getX();
                y1 = e.getY();
            }

            @Override
            public void mouseReleased(MouseEvent e) {
                x2 = e.getX();
                y2 = e.getY();
                drawShape(); // 调用虚方法绘制图形
                repaint();
            }
        });
    }

    // 更新背景颜色的方法
    public void changebackcol(Color nColor) {
        backcol = nColor; // 更改背景颜色
        setBackground(backcol); // 设置面板背景色
        image = new BufferedImage(500, 500, BufferedImage.TYPE_INT_ARGB);
        Graphics g = image.getGraphics();
        g.setColor(backcol);
        g.fillRect(0, 0, 500, 500); // 填充新的背景色
        repaint(); // 重新绘制面板
    }

    // 设置当前绘制的图形类型
    public void setCurrentShape(String shapeType) {
        currentShape = shapeType; // 更新当前图形类型
    }

    // 设置线条的颜色
    public void setLineColor(Color color) {
        currentLineColor = color; // 更新线条颜色
    }

    // 设置填充颜色
    public void setFillColor(Color color) {
        currentFillColor = color; // 更新填充颜色
    }

    // 设置文本内容
    public void setText(String text) {
        currentText = text;
    }

    // 设置字体
    public void setFont(int size) {
        currentFont = new Font("Arial", Font.PLAIN, size); // 默认字体
    }

    // 使用 paintComponent 来绘制组件内容，确保背景颜色的正常显示
    @Override
    protected void paintComponent(Graphics g) {
        super.paintComponent(g); // 调用父类的方法，确保背景色正常显示
        g.drawImage(image, 0, 0, null); // 绘制保存的BufferedImage
    }

    // 保存绘制的图形到文件
    public void saveImage(File file) {
        try {
            ImageIO.write(image, "PNG", file); // 保存为PNG格式的文件
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    // 虚拟绘制方法
    private void drawShape() {
        Graphics g = image.getGraphics(); // 获取BufferedImage的Graphics对象
        g.setColor(currentLineColor); // 使用当前的线条颜色
        switch (currentShape) {
            case LINE:
                drawLine(g);
                break;
            case RECTANGLE:
                drawRectangle(g);
                break;
            case OVAL:
                drawOval(g);
                break;
            case TRIANGLE:
                drawTriangle(g);
                break;
            case ROUND:
                drawRound(g);
                break;
            case TEXT:
                // 文本绘制已经在这里进行
                g.setFont(currentFont);
                g.setColor(currentLineColor); // 使用当前线条颜色绘制文本
                g.drawString(currentText, x1, y1); // 绘制文本内容
                break;
            default:
                break;
        }
    }

    // 绘制线条
    private void drawLine(Graphics g) {
        g.drawLine(x1, y1, x2, y2);
    }

    // 绘制矩形
    private void drawRectangle(Graphics g) {
        // 填充矩形
        g.setColor(currentFillColor); // 设置填充颜色
        g.fillRect(x1, y1, abs(x1 - x2), abs(y1 - y2)); // 绘制填充矩形
        g.setColor(currentLineColor); // 设置回线条颜色
        g.drawRect(x1, y1, abs(x1 - x2), abs(y1 - y2)); // 绘制矩形边框
    }

    // 绘制椭圆 (Oval)
    private void drawOval(Graphics g) {
        // 填充椭圆
        g.setColor(currentFillColor); // 设置填充颜色
        g.fillOval(x1, y1, abs(x1 - x2), abs(y1 - y2)); // 绘制填充椭圆
        g.setColor(currentLineColor); // 设置回线条颜色
        g.drawOval(x1, y1, abs(x1 - x2), abs(y1 - y2)); // 绘制椭圆边框
    }

    // 绘制三角形
    private void drawTriangle(Graphics g) {
        int[] xPoints = {x1, x2, (2 * x1 - x2)}; // 三个顶点的x坐标
        int[] yPoints = {y1, y2, y2}; // 三个顶点的y坐标

        // 填充三角形
        g.setColor(currentFillColor); // 设置填充颜色
        g.fillPolygon(xPoints, yPoints, 3); // 绘制填充三角形
        
        // 设置线条颜色并绘制边框
        g.setColor(currentLineColor); // 设置回线条颜色
        g.drawPolygon(xPoints, yPoints, 3); // 绘制三角形边框
    }

    // 绘制圆角矩形
    private void drawRound(Graphics g) {
        // 填充圆角矩形
        g.setColor(currentFillColor); // 设置填充颜色
        g.fillRoundRect(x1, y1, abs(x1 - x2), abs(y1 - y2), 10, 10); // 绘制填充圆角矩形
        g.setColor(currentLineColor); // 设置回线条颜色
        g.drawRoundRect(x1, y1, abs(x1 - x2), abs(y1 - y2), 10, 10); // 绘制圆角矩形边框
    }
}
