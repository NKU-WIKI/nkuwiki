package Util;

import Bean.GameInfo;
import Bean.PlayerCondition;
import Bean.Player;
import InstanceControl.InstanceManager;
import InstanceControl.InstanceMapper;

import javax.swing.*;
import javax.swing.border.Border;
import javax.swing.border.LineBorder;

import java.awt.*;
import java.awt.event.ActionListener;


public class roomContainer extends JPanel {
    // 定义UI组件
    private JLabel roomName;  // 显示房间名称的标签
    private JButton function;  // 操作按钮，控制"ADD"或"JOIN!"的功能
    private JPanel infoPanel;  // 显示玩家信息的面板
    private JTextField player1, player2;  // 玩家1和玩家2的名字输入框


    // roomContainer构造函数，初始化UI组件并设置布局
    public roomContainer() {
        setLayout(new BorderLayout());  // 设置面板布局为BorderLayout

        // 设置背景透明，防止覆盖背景图
        setOpaque(false);  // 关键：设置为透明
        // Border border = BorderFactory.createEmptyBorder(10, 10, 10, 10);  // 上右下左各 10 像素的空白边距
        // Border border = BorderFactory.createEtchedBorder(EtchedBorder.RAISED);  // 凸起的雕刻效果
        // Border border = BorderFactory.createBevelBorder(BevelBorder.RAISED);  // 突出的立体效果
         // 设置边框颜色为深蓝色
        Border border = new LineBorder(new Color(255, 255, 255), 1);  // 浅蓝色边框
        setBorder(border);  // 设置边框

        // 初始化并设置房间名称标签
        roomName = new JLabel("New Room");
        roomName.setOpaque(true);  // 使标签背景不透明
        roomName.setBackground(new Color(173, 216, 230));  // 设置背景色为浅蓝色
        // roomName.setOpaque(false);  // 设置为透明
        // roomName.setForeground(new Color(255, 255, 255, 128));  // 设置文字颜色为白色，透明度为128
        add(roomName, BorderLayout.NORTH);  // 将房间名称标签添加到北部（顶部）

        // 设置按钮为透明背景，并且保持半透明效果
        function = new JButton("ADD");
        function.setOpaque(false);  // 让按钮背景透明
        function.setContentAreaFilled(false);  // 去掉按钮的填充颜色
                // 初始化功能按钮
                
        // function.setBackground(new Color(173, 216, 230));  // 设置按钮背景为浅蓝色
        function.setForeground(Color.BLUE);  // 设置按钮文本为深蓝色
        // function.setBorder(new LineBorder(new Color(173, 216, 230), 1));  // 设置按钮边框为浅蓝色
                
        function.setBorderPainted(false);  // 去掉按钮的边框
        add(function, BorderLayout.SOUTH);

        function.addActionListener(new ActionListener() {
            @Override
            public void actionPerformed(java.awt.event.ActionEvent e) {
                // 根据按钮文本执行不同的操作
                switch(function.getText()) {
                    case "ADD":
                        // 如果按钮文本是"ADD"，创建一个新的房间
                        String name = InstanceManager.getInstanceManager().assignRoomKey();  // 生成房间名
                        Player one = new Player(player1.getText());  // 创建玩家1
                        Player two = new Player(player2.getText());  // 创建玩家2
                        if(one.getName()!=""){
                            one.setCondition(PlayerCondition.ONLINE);
                            one.setIp(InstanceManager.localip);
                            one.setPort(InstanceManager.getServerPort());
                            // isplayer1 = true;
                        }
                        else{
                            two.setCondition(PlayerCondition.ONLINE);
                            two.setIp(InstanceManager.localip);
                            two.setPort(InstanceManager.getServerPort());
                            // isplayer1 = false;
                        }
                        GameInfo gameInfo = new GameInfo(one, two);  // 创建游戏信息对象
                        gameInfo.setOwner(InstanceManager.getServerPort());  // 设置房主为当前服务器端口
                        InstanceMapper.getInstance().setRoomBuffer(name, gameInfo);  // 将新房间添加到房间列表
                        roomName.setText(name);  // 设置房间名称标签为房间名
                        function.setText("ADDING");  // 将按钮文本改为"ADDING"
                        function.setEnabled(false);  // 禁用按钮，防止再次点击
                        break;
                    case "JOIN!":
                        // 如果按钮文本是"JOIN!"，加入现有房间
                        String room = roomName.getText();  // 获取房间名称
                        GameInfo gameInfo2 = InstanceMapper.getInstance().getRoomList().get(room);
                        Player second = gameInfo2.getP2();
                        second.setName(player2.getText());
                        second.setIp(InstanceManager.localip);
                        second.setPort(InstanceManager.SERVER_PORT);
                        second.setCondition(PlayerCondition.ONLINE);  // 设置玩家2为在线状态
                        InstanceMapper.getInstance().setRoomBuffer(room, gameInfo2);  // 将房间更新到房间列表
                        break;
                }
            }
        });
        add(function, BorderLayout.SOUTH);  // 将功能按钮添加到南部（底部）

        // 初始化并设置信息面板，用于显示玩家信息
        infoPanel = new JPanel(new GridLayout(2, 2));  // 设置网格布局（2行2列）
        infoPanel.setOpaque(false);  // 设置信息面板透明
        // 设置标签字体为黑色，Times New Roman，大字体

        ImageIcon originalIcon = new ImageIcon("src\\main\\resource\\img\\black.png");  // 替换为图标的路径
        Image originalImage = originalIcon.getImage();  // 获取原始图像
        // 缩小图标的大小，设置新的宽度和高度
        int newWidth = 30;  // 新的宽度
        int newHeight = 30; // 新的高度
        Image resizedImage = originalImage.getScaledInstance(newWidth, newHeight, Image.SCALE_SMOOTH);
        
        // 创建新的 ImageIcon
        ImageIcon resizedIcon = new ImageIcon(resizedImage);

        ImageIcon originalIcon2 = new ImageIcon("src\\main\\resource\\img\\white.png");  // 替换为图标的路径
        Image originalImage2 = originalIcon2.getImage();  // 获取原始图像
        // 缩小图标的大小，设置新的宽度和高度
        Image resizedImage2 = originalImage2.getScaledInstance(newWidth, newHeight, Image.SCALE_SMOOTH);
        
        // 创建新的 ImageIcon
        ImageIcon resizedIcon2 = new ImageIcon(resizedImage2);

        // ImageIcon icon1 = new ImageIcon("src\\main\\resource\\black.png");  // 替换为图标的路径
        JLabel player1Label = new JLabel("Player1",resizedIcon,JLabel.LEFT);
        player1Label.setFont(new Font("Times New Roman", Font.PLAIN, 20));  // 设置字体为 Times New Roman，大小为 20px
        player1Label.setForeground(Color.BLACK);  // 设置字体颜色为黑色

        // ImageIcon icon2 = new ImageIcon("src\\main\\resource\\white.png");  // 替换为图标的路径
        JLabel player2Label = new JLabel("Player2",resizedIcon2,JLabel.LEFT);
        player2Label.setFont(new Font("Times New Roman", Font.PLAIN, 20));  // 设置字体为 Times New Roman，大小为 20px
        player2Label.setForeground(Color.BLACK);  // 设置字体颜色为黑色
       
       
        // 添加标签到面板
        infoPanel.add(player1Label);
        infoPanel.add(player2Label);

        player1 = new JTextField();  // 玩家1输入框
        player2 = new JTextField();  // 玩家2输入框

        // 设置文本框为透明背景并去掉边框
        player1.setOpaque(false);  // 设置透明
        player1.setBackground(new Color(0, 0, 0, 0));  // 设置背景透明
        player1.setBorder(BorderFactory.createEmptyBorder());  // 去掉文本框边框
        player1.setFont(new Font("Times New Roman", Font.PLAIN, 30));  // 设置字体大小为 18px
        player1.setForeground(Color.BLACK);  // 设置字体颜色为深黑色
        player2.setOpaque(false);  // 设置透明
        player2.setBackground(new Color(0, 0, 0, 0));  // 设置背景透明
        player2.setBorder(BorderFactory.createEmptyBorder());  // 去掉文本框边框
        player2.setFont(new Font("Times New Roman", Font.PLAIN, 30));  // 设置字体大小为 18px
        player2.setForeground(Color.BLACK);  // 设置字体颜色为深黑色
        infoPanel.add(player1);  // 将玩家1输入框添加到面板
        infoPanel.add(player2);  // 将玩家2输入框添加到面板
        add(infoPanel, BorderLayout.CENTER);  // 将信息面板添加到中部（中央）

        setVisible(true);  // 设置面板可见
    }

    // 设置房间信息的方法
    public void setRoom(String name, GameInfo gameInfo) {
        roomName.setText(name);  // 设置房间名称标签的文本
        player1.setText(gameInfo.getP1().getName());  // 设置玩家1的名字
        player2.setText(gameInfo.getP2().getName());  // 设置玩家2的名字

        // 根据玩家的状态调整UI组件
        if (gameInfo.getP1().getCondition() == PlayerCondition.OFFLINE || gameInfo.getP2().getCondition() == PlayerCondition.OFFLINE) {
            if (gameInfo.getOwner() == InstanceManager.getServerPort()) {
                function.setText("WAITING");
                function.setEnabled(false);
            } else {
                function.setText("JOIN!");
            }
        } else {
            function.setText("ON BATTLE");  // 如果玩家2也在线，按钮文本改为"ON BATTLE"
            function.setEnabled(false);  // 禁用按钮，表示游戏已经开始
        }
    }
}




