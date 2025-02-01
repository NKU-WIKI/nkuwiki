package Util;

import Bean.*;  // 导入与游戏相关的Bean类
import Controller.Controller;  // 导入Controller类，用于控制游戏逻辑
import View.Viewer;  // 导入Viewer类，用于展示游戏界面
import Map.*;  // 导入地图相关的类
import org.apache.commons.lang3.tuple.ImmutablePair;  // 导入不可变的键值对类，作为地址和端口的封装

import java.io.*;  // 导入输入输出流相关的类
import java.net.*;  // 导入网络相关的类
import java.util.concurrent.atomic.AtomicReference;  // 导入原子引用类，用于线程间共享数据

public class NetUDP {
    private static NetUDP net;  // 单例模式，NetUDP实例

    // 获取NetUDP单例实例
    public static NetUDP getNet() {
        if(net == null) {
            net = new NetUDP();  // 如果实例为空，则创建一个新的实例
        }
        return net;  // 返回NetUDP实例
    }

    // 向远程发送棋盘对象的状态
    public void putChessRemote(Chess chess, Player Player) throws IOException {
        // 向远程的玩家发送棋盘对象，使用UDP协议
        InetAddress address = InetAddress.getByName(Player.getIp());  // 获取玩家的IP地址
        int port = Player.getPort();  // 获取玩家的端口号
        DatagramSocket socket = new DatagramSocket(port);  // 创建一个UDP套接字

        byte[] data = chess.getBytes();  // 获取棋盘对象的字节数据
        DatagramPacket packet = new DatagramPacket(data, data.length, address, port);  // 构造数据包
        System.out.println("send chess to remote");  // 输出调试信息
        socket.send(packet);  // 发送数据包
        socket.close();  // 关闭套接字
    }

    // 选择并返回A方的棋子颜色，A方是本地玩家
    public ChessCondition selectSideA(ImmutablePair<String, Integer> addressLocal, ImmutablePair<String, Integer> addressRemote) {
        AtomicReference<Viewer> v = new AtomicReference<>(Viewer.getViewer());  // 获取Viewer实例
        AtomicReference<ChessCondition> chose = new AtomicReference<>();  // 存储选择的棋子颜色
        AtomicReference<ChessChoose> chessChoose = new AtomicReference<>();  // 存储本地选择的棋子信息
        ChessChoose chessChooseReceive = null;  // 接收到的远程棋子选择信息
        
        new Thread(() -> {
            // 线程中执行选择棋子的操作
            chose.set(v.get().selectSide());  // 本地选择棋子颜色
            long time = System.currentTimeMillis();  // 获取系统当前时间
            chessChoose.set(new ChessChoose(time, chose));  // 构建ChessChoose对象
        }).start();
        
        try {
            // 构建发送和接收的数据流
            ByteArrayOutputStream byteArrayOutStream = new ByteArrayOutputStream();
            ObjectOutputStream objectOutStream = new ObjectOutputStream(byteArrayOutStream);
            System.out.println(addressLocal.getRight());
            DatagramSocket socket = new DatagramSocket(addressLocal.getRight());  // 创建UDP套接字，监听本地端口
            byte[] buffer = new byte[1024];  // 缓存区，用于接收数据
            DatagramPacket packetReceive = new DatagramPacket(buffer, buffer.length);  // 创建接收数据包
            System.out.println("1st Receive@" + addressLocal.getRight() + "for" + addressRemote.getRight() + addressLocal.getLeft());
            socket.receive(packetReceive);  // 接收数据包

            // 解析接收到的数据包
            ByteArrayInputStream byteArrayInStream = new ByteArrayInputStream(buffer);
            ObjectInputStream objectInStream = new ObjectInputStream(byteArrayInStream);
            chessChooseReceive = (ChessChoose) objectInStream.readObject();
            objectInStream.close();

            while(chessChoose.get() == null) {}  // 等待本地选择的棋子信息

            // 将本地选择的棋子信息发送到远程
            InetAddress address = InetAddress.getByName(addressRemote.getLeft());
            int port = addressRemote.getRight();
            objectOutStream.writeObject(chessChoose.get());  // 写入选择信息
            byte[] data = byteArrayOutStream.toByteArray();  // 获取字节数据
            objectOutStream.reset();  // 重置输出流
            DatagramPacket packet = new DatagramPacket(data, data.length, address, port);  // 创建数据包
            socket.send(packet);  // 发送数据包

            socket.close();  // 关闭套接字
        } catch (Exception e) {
            e.printStackTrace();
        }

        // 比较本地和远程选择的棋子颜色，如果本地选择的颜色与远程相同且时间较晚，则改变当前颜色
        if(chessChoose.get().getChessCondition().equals(chessChooseReceive.getChessCondition()) &&
           chessChoose.get().getTime() > chessChooseReceive.getTime()) {

            Viewer.getViewer().getInfoPanel().setEnemySide(chose.get());  // 设置敌方棋子颜色
            if(chose.get() == ChessCondition.BLACK) {
                Viewer.getViewer().getInfoPanel().setCurrSide(ChessCondition.WHITE);  // 设置当前棋子颜色
                chose.set(ChessCondition.WHITE);
            } else {
                Viewer.getViewer().getInfoPanel().setCurrSide(ChessCondition.BLACK);
                chose.set(ChessCondition.BLACK);
            }
        } else {
            // 如果选择不同，则反转棋子颜色
            Viewer.getViewer().getInfoPanel().setEnemySide(chose.get() == ChessCondition.BLACK ? ChessCondition.WHITE : ChessCondition.BLACK);
            Viewer.getViewer().getInfoPanel().setCurrSide(chose.get());
        }

        return chose.get();  // 返回选择的棋子颜色
    }

    // 选择并返回B方的棋子颜色，B方是远程玩家
    public ChessCondition selectSideB(ImmutablePair<String, Integer> addressLocal, ImmutablePair<String, Integer> addressRemote) {
        ChessCondition chose = Viewer.getViewer().selectSide();  // 本地选择棋子颜色
        long time = System.currentTimeMillis();  // 获取系统时间
        ChessChoose chessChoose = new ChessChoose(time, chose);  // 构建ChessChoose对象
        ChessChoose chessChooseReceive = null;  // 接收到的远程棋子选择信息

        try {
            // 构建发送和接收的数据流
            ByteArrayOutputStream byteArrayOutStream = new ByteArrayOutputStream();
            ObjectOutputStream objectOutStream = new ObjectOutputStream(byteArrayOutStream);
            DatagramSocket socket = new DatagramSocket(addressLocal.getRight());  // 创建UDP套接字，监听本地端口
            byte[] buffer = new byte[1024];  // 缓存区，用于接收数据

            // 发送棋子选择信息到远程
            InetAddress address = InetAddress.getByName(addressRemote.getLeft());
            int port = addressRemote.getRight();
            objectOutStream.writeObject(chessChoose);  // 写入选择信息
            byte[] data = byteArrayOutStream.toByteArray();  // 获取字节数据
            objectOutStream.reset();  // 重置输出流
            DatagramPacket packet = new DatagramPacket(data, data.length, address, port);  // 创建数据包
            socket.send(packet);  // 发送数据包

            // 接收远程的选择信息
            DatagramPacket packetReceive = new DatagramPacket(buffer, buffer.length);  
            System.out.println("2nd Receive@" + addressLocal.getRight() + "for" + addressRemote.getRight() + addressLocal.getLeft());
            socket.receive(packetReceive);  // 接收数据包
            ByteArrayInputStream byteArrayInStream = new ByteArrayInputStream(buffer);
            ObjectInputStream objectInStream = new ObjectInputStream(byteArrayInStream);
            chessChooseReceive = (ChessChoose) objectInStream.readObject();
            objectInStream.close();

            socket.close();  // 关闭套接字
        } catch (Exception e) {
            e.printStackTrace();
        }

        // 比较本地和远程选择的棋子颜色，如果本地选择的颜色与远程相同且时间较晚，则改变当前颜色
        if(chessChoose.getChessCondition().equals(chessChooseReceive.getChessCondition()) &&
           chessChoose.getTime() > chessChooseReceive.getTime()) {

            Viewer.getViewer().getInfoPanel().setEnemySide(chose);
            if(chose == ChessCondition.BLACK) {
                Viewer.getViewer().getInfoPanel().setCurrSide(ChessCondition.WHITE);
                chose = ChessCondition.WHITE;
            } else {
                Viewer.getViewer().getInfoPanel().setCurrSide(ChessCondition.BLACK);
                chose = ChessCondition.BLACK;
            }
        } else {
            Viewer.getViewer().getInfoPanel().setEnemySide(chose == ChessCondition.BLACK ? ChessCondition.WHITE : ChessCondition.BLACK);
            Viewer.getViewer().getInfoPanel().setCurrSide(chose);
        }

        return chose;  // 返回选择的棋子颜色
    }

    // 向远程发送战斗信息，并监听本地端口接收信息
    public boolean poster(ImmutablePair<String, Integer> addressLocal, ImmutablePair<String, Integer> addressRemote) {
        try {
            DatagramSocket socket = new DatagramSocket(addressLocal.getRight());  // 创建UDP套接字，监听本地端口
            byte[] buffer = new byte[1024];  // 缓存区，用于接收数据
            DatagramPacket packet = new DatagramPacket(buffer, buffer.length);
            socket.setSoTimeout(50);  // 设置超时时间

            try {
                socket.receive(packet);  // 接收数据包
                System.out.println("Received");
            } catch (Exception e) {
                packet = null;  // 超时或没有接收到数据
            }

            if (packet != null) {
                // 解析接收到的数据包
                ByteArrayInputStream byteArrayInStream = new ByteArrayInputStream(buffer);
                ObjectInputStream objectInStream = new ObjectInputStream(byteArrayInStream);
                BattleMessage battleMessage = (BattleMessage) objectInStream.readObject();  // 读取战斗信息
                objectInStream.close();
                Controller.getController().notifyRemote(battleMessage);  // 通知控制器处理战斗信息
            }

            // 如果MessageBuffer中有战斗信息，发送到远程
            if (MessageBuffer.getInstance().getBattleMessage() != null) {
                InetAddress address = InetAddress.getByName(addressRemote.getLeft());
                int port = addressRemote.getRight();
                ByteArrayOutputStream byteArrayOutStream = new ByteArrayOutputStream();
                ObjectOutputStream objectOutStream = new ObjectOutputStream(byteArrayOutStream);
                objectOutStream.writeObject(MessageBuffer.getInstance().getBattleMessage());  // 写入战斗信息
                MessageBuffer.getInstance().clear();  // 清空缓存
                byte[] data = byteArrayOutStream.toByteArray();  // 获取字节数据
                objectOutStream.reset();  // 重置输出流
                DatagramPacket packetSend = new DatagramPacket(data, data.length, address, port);  // 创建数据包
                socket.send(packetSend);  // 发送数据包
                Thread.sleep(10);  // 等待10ms
                socket.send(packetSend);  // 重发数据包
                Thread.sleep(10);  // 等待10ms
                socket.send(packetSend);  // 再次重发数据包
                System.out.println("buffer sent");  // 输出调试信息
            }

            socket.close();  // 关闭套接字
            return true;
        } catch (Exception e) {
            e.printStackTrace();
        }
        return true;  // 返回true，表示操作成功
    }
}
