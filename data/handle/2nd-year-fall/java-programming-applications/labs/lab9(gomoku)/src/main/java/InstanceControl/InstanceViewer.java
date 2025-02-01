package InstanceControl;

import Bean.*;
import Util.*;
import java.util.Vector;
import javax.swing.*;
import java.awt.*;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.util.Map; 
import java.util.Collections;
public class InstanceViewer extends JFrame {
    private static InstanceViewer instanceViewer;
    private Image backgroundImage;  // 背景图片

    // 获取InstanceViewer唯一实例的方法（单例模式）
    public static InstanceViewer getInstance() {
        if (instanceViewer == null) {
            instanceViewer = new InstanceViewer();
        }
        return instanceViewer;
    }

    // 设置背景图片
    public void setBackgroundImage(String imagePath) {
        this.backgroundImage = new ImageIcon(imagePath).getImage();
    }

    // 更新房间列表的方法
    public void updataRoomList() {
        int index = 0;
        roomList.removeAll();  // 清空当前房间列表
        roomList.setLayout(new GridLayout(3, 3));  // 设置房间列表的布局为3x3的网格
        // 遍历房间列表，更新UI界面
        for (Map.Entry<String, GameInfo> room : InstanceMapper.getInstance().getRoomList().entrySet()) {
            roomContainer r = new roomContainer();  // 创建新的房间容器
            r.setRoom(room.getKey(), room.getValue());  // 设置房间信息
            roomList.add(r, index);  // 将房间添加到UI中
            index++;
        }
        // 如果房间数量不足9个，补充空的roomContainer组件
        for (int i = index; i < 9; i++) {
            roomList.add(new roomContainer());
        }
        roomList.revalidate();  // 重新验证布局
        repaint();  // 重绘UI
    }

    // 设置窗口标题的方法
    public void setTile(String condition) {
        // 设置标题
        setTitle(condition);
    }

    // roomList类表示房间列表面板，继承自JPanel
    class roomList extends JPanel {
        public roomList() {
            setLayout(new GridLayout(3, 3));
            setOpaque(false); // 确保roomList不覆盖背景
            for (int i = 0; i < 9; i++) {
                add(new roomContainer());
            }
        }
    }

    // 定义UI组件
    private JPanel roomList = new roomList();
    private JButton reviewLocal = new JButton("Local Replay");
    private JButton playLocal = new JButton("Local Game");
    private JButton music = new JButton("Music");



    // 初始化UI的方法
    public void init() {
        setIconImage(Toolkit.getDefaultToolkit().getImage("src\\main\\resource\\img\\title2.png"));
        setBackgroundImage("src/main/resource/img/background.jpg");  // 设置背景图片路径
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setSize(900, 600);
        setLocationRelativeTo(null);
        setLayout(new BorderLayout());

        // 设置主面板
        JPanel mainPanel = new JPanel(new BorderLayout()) {
            @Override
            protected void paintComponent(Graphics g) {
                super.paintComponent(g);
                if (backgroundImage != null) {
                    g.drawImage(backgroundImage, 0, 0, getWidth(), getHeight(), this);  // 绘制背景图片
                }
            }
        };

        music.setBackground(new Color(173, 216, 230));  // 浅蓝色背景
        music.setForeground(Color.BLACK);  // 字体颜色为黑色
        music.setBorder(null);
        // 设置按钮字体
        music.setFont(new Font("Times New Roman", Font.PLAIN, 18));  // Times New Roman 字体，18号
        // 设置按钮文本居中对齐
        music.setHorizontalAlignment(SwingConstants.CENTER);
        ImageIcon musicIcon = new ImageIcon("src\\main\\resource\\img\\music.png");
        // 设置按钮图标
        music.setIcon(musicIcon);
        music.setIconTextGap(10);  // 设置图标和文本之间的间距
        music.setVerticalTextPosition(SwingConstants.TOP);  // 设置文本在图标的下方
        music.setHorizontalTextPosition(SwingConstants.CENTER);  // 设置文本水平居中
        music.setFocusPainted(false);
        
        playLocal.setBackground(new Color(173, 216, 230));  // 浅蓝色背景
        playLocal.setForeground(Color.BLACK);  // 字体颜色为黑色
        playLocal.setBorder(null);
        playLocal.setFocusPainted(false);
        // 设置按钮字体
        playLocal.setFont(new Font("Times New Roman", Font.PLAIN, 18));  // Times New Roman 字体，18号
        // 设置按钮文本居中对齐
        playLocal.setHorizontalAlignment(SwingConstants.CENTER);
        playLocal.setIconTextGap(10);  // 设置图标和文本之间的间距
        playLocal.setVerticalTextPosition(SwingConstants.TOP);  // 设置文本在图标的下方
        playLocal.setHorizontalTextPosition(SwingConstants.CENTER);  // 设置文本水平居中
        playLocal.setFocusPainted(false);

        reviewLocal.setBackground(new Color(25, 124, 192));  // 浅蓝色背景
        // 设置按钮字体颜色
        reviewLocal.setForeground(Color.WHITE);  // 字体颜色为黑色
        // 设置按钮边框颜色
        reviewLocal.setBorder(null);
        // 设置按钮字体
        reviewLocal.setFont(new Font("Times New Roman", Font.PLAIN, 18));  // Times New Roman 字体，18号
        // 可选：设置按钮文本居中对齐
        reviewLocal.setHorizontalAlignment(SwingConstants.CENTER);
        reviewLocal.setIconTextGap(10);  // 设置图标和文本之间的间距
        reviewLocal.setVerticalTextPosition(SwingConstants.TOP);  // 设置文本在图标的下方
        reviewLocal.setHorizontalTextPosition(SwingConstants.CENTER);  // 设置文本水平居中
        reviewLocal.setFocusPainted(false);

        mainPanel.add(roomList, BorderLayout.CENTER);  // 将房间列表添加到主面板
        add(mainPanel, BorderLayout.CENTER);

        // 为本地复盘按钮添加点击事件监听器
        reviewLocal.addActionListener(new ActionListener() {
            @Override
            public void actionPerformed(ActionEvent e) {
                JFileChooser fileChooser = new JFileChooser("src\\main\\resource\\gameRecords");
                fileChooser.setFileSelectionMode(JFileChooser.FILES_ONLY);
                fileChooser.setDialogTitle("选择您要复盘的文件");
                int result = fileChooser.showOpenDialog(reviewLocal.getTopLevelAncestor());
                if (result == JFileChooser.APPROVE_OPTION) {
                    String filePath = fileChooser.getSelectedFile().getAbsolutePath();
                    Object[] objects = RestoreGameFromFile.readGameFromFile(filePath);
                    Player Player1 = (Player) objects[0];
                    Player Player2 = (Player) objects[1];
                    GameInfo gameInfo = new GameInfo(Player1, Player2);
                    Vector<Chess> chesses = (Vector<Chess>) objects[2];
                    Collections.reverse(chesses); 
                    InstanceManager.getInstanceManager().startBattleReview(gameInfo, chesses);
                }
            }
        });
        add(reviewLocal, BorderLayout.SOUTH);

        // 为本地游戏按钮添加点击事件监听器
        playLocal.addActionListener(new ActionListener() {
            @Override
            public void actionPerformed(ActionEvent e) {
                GameInfo gameInfo = new GameInfo(true);
                gameInfo.setP1(new Player("null", PlayerCondition.OFFLINE, ChessCondition.WHITE));
                gameInfo.setP2(new Player("null", PlayerCondition.OFFLINE, ChessCondition.BLACK));
                InstanceManager.getInstanceManager().startBattleLocal(gameInfo);
            }
        });
        add(playLocal, BorderLayout.NORTH);

        // 为音乐按钮添加点击事件监听器
        music.addActionListener(new ActionListener() {
            @Override
            public void actionPerformed(ActionEvent e) {
                JFileChooser fileChooser = new JFileChooser("src\\main\\resource\\music");
                fileChooser.setFileSelectionMode(JFileChooser.FILES_ONLY);
                fileChooser.setDialogTitle("选择您要播放的音乐");
                int result = fileChooser.showOpenDialog(music.getTopLevelAncestor());
                if (result == JFileChooser.APPROVE_OPTION) {
                    String filePath = fileChooser.getSelectedFile().getAbsolutePath();
                    new MusicPlayer(filePath);
                }
            }
        });
        add(music, BorderLayout.WEST);

        setVisible(true);  // 显示窗口
    }
}
