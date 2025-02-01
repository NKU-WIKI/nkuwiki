package InstanceControl;

import Bean.*;
import Controller.*;
import Map.*;
import Util.InstanceNet;
import View.Viewer;
import org.apache.commons.lang3.tuple.ImmutablePair;
import org.apache.commons.lang3.tuple.MutablePair;
import java.util.HashMap;
import java.util.Map;
import java.util.Vector;

public class InstanceManager {

    // 私有构造函数，防止外部实例化
    private InstanceManager() {}

    // 单例模式：InstanceManager 的唯一实例
    private static InstanceManager im = new InstanceManager();
    
    private static InstanceMapper instanceMapper = InstanceMapper.getInstance();
    
    // 实例查看器，负责管理实例的查看
    private static InstanceViewer instanceViewer = InstanceViewer.getInstance();
    
    // 网络实例，负责与其他实例的网络通信
    private static InstanceNet net = InstanceNet.getNet();

    // 服务器地址信息
    private static final String SERVER_IP = "localhost";
    public static String localip = "127.0.0.1"; 
    public static int SERVER_PORT = 10000;
    public static final String LOCAL_IP = "localhost";
    private static final int LOCAL_PORT = 10001;
    private static final MutablePair<String, Integer> SERVER_ADDRESS = new MutablePair<>(SERVER_IP, SERVER_PORT);
    private static final ImmutablePair<String, Integer> LOCAL_ADDRESS = new ImmutablePair<>(LOCAL_IP, LOCAL_PORT);

    // 获取 InstanceManager 实例（单例模式）
    public static InstanceManager getInstanceManager() {
        if (im == null) {
            im = new InstanceManager();
        }
        return im;
    }

    // 根据 instanceMapper 中的实例编号分配唯一的密钥
    public String assignKey() {
        String key = "Group" + instanceMapper.getInstanceNum();
        return key;
    }

    // 获取控制器实例
    public Controller getController(String instanceName) {
        return instanceMapper.getController(instanceName);
    }

    // 获取查看器实例
    public Viewer getViewer(String instanceName) {
        return instanceMapper.getViewer(instanceName);
    }

    // 获取映射器实例
    public Mapper getMapper(String instanceName) {
        return instanceMapper.getMapper(instanceName);
    }

    // 分配一个房间的唯一密钥
    public String assignRoomKey() {
        StringBuilder key = new StringBuilder();
        key.append("Room");
        key.append(instanceMapper.getInstanceNum());
        key.append("@").append(LOCAL_IP);
        instanceMapper.incInstanceNum();
        return key.toString();
    }

    // 设置服务器的端口
    public void setServerPort(int port) {
        System.out.println("setServerPort " + port);
        SERVER_PORT = port;
        SERVER_ADDRESS.setValue(SERVER_PORT);
    }

    // 获取服务器端口
    public static int getServerPort() {
        return SERVER_PORT;
    }
    // 获取当前房间列表
    public String getRoomList() {
        Map<String, GameInfo> roomList = instanceMapper.getRoomList();
        StringBuilder sb = new StringBuilder();
        for (Map.Entry<String, GameInfo> entry : roomList.entrySet()) {
            sb.append(entry.getKey()).append(" ").append(entry.getValue().getP1().toString()).append(" ")
              .append(entry.getValue().getP2().toString()).append("\n");
        }
        return sb.toString();
    }

    // 更新房间列表
    public void setRoomList(String roomList) {
        // 解析房间列表并更新实例映射器中的房间信息
        Map<String, GameInfo> rooms = new HashMap<String, GameInfo>();
        String[] roomListArray = roomList.split("\n");
        for (String room : roomListArray) {
            String[] roomInfo = room.split(" ");
            String roomName = roomInfo[0];
            String p1 = roomInfo[1];
            String p2 = roomInfo[2];
            GameInfo gameInfo = new GameInfo(new Player(p1), new Player(p2));
            rooms.put(roomName, gameInfo);
        }
        instanceMapper.resetRoomList(rooms);
    }

    // 初始化方法，判断是否为客户端模式或服务器模式
    private void init() {
        // 检查是否为客户端模式
        if (net.checkRunningServer(SERVER_ADDRESS, LOCAL_ADDRESS)) {
            // 客户端模式
            InstanceViewer.getInstance().setTile("Gomoku(client)");
            System.out.println("running mode: slave");
            net.putInstanceCondition(SERVER_ADDRESS, LOCAL_ADDRESS); // 更改服务端和本地连接的端口

            // 启动线程监听房间列表更新
            new Thread(() -> {
                while (net.listenToRoomList(SERVER_ADDRESS, LOCAL_ADDRESS)) {}
            }).start();
        } else {
            // 服务器模式
            System.out.println("running mode: master");
            InstanceViewer.getInstance().setTile("Gomoku(server)");
            instanceMapper.initClientList();

            // 启动服务器线程，监听客户端连接
            new Thread(() -> {
                while (net.serverRunning(SERVER_ADDRESS)) {}
            }).start();

            // 启动线程监听房间更新
            new Thread(() -> {
                while (net.listenToRoomUpdata(SERVER_ADDRESS)) {}
            }).start();
        }
        instanceViewer.init();
    }

    // 主方法，启动实例管理器并初始化
    public static void main(String[] args) {
        im.init();
    }

    // 开始一场对战（与远程玩家对战）
    public void startBattle(GameInfo newGameInfo) {
        System.out.println("start battle");
        System.out.println(newGameInfo.toString());
        System.out.println(((Player) newGameInfo.getP1()).getPort() + " " + ((Player) newGameInfo.getP2()).getPort());
        new Thread(() -> {
            Controller controller = Controller.getController();
            Viewer viewer = Viewer.getViewer();
            Mapper mapper = Mapper.getMapper();
            String key = InstanceManager.getInstanceManager().assignKey();
            InstanceMapper.addInstance(key, controller, viewer, mapper);

            controller.setKey(key);
            viewer.setKey(key);
            mapper.setKey(key);

            instanceMapper.incInstanceNum();

            System.out.println(SERVER_PORT);
            System.out.println(newGameInfo.getOwner());
            controller.setGameInfo(newGameInfo);
            if (newGameInfo.getOwner() != InstanceManager.getServerPort()) {
                controller.setCurrentPlayer((Player) newGameInfo.getP2());
            } else {
                controller.setCurrentPlayer((Player) newGameInfo.getP1());
            }

            controller.start();
        }).start();
    }

    // 开始一场本地对战（没有网络对战）
    public void startBattleLocal(GameInfo gameInfo) {
        System.out.println("start battle");

        new Thread(() -> {
            ControllerLocal controller = ControllerLocal.getController();
            // ViewerLocal viewer = ViewerLocal.getViewer();
            // MapperLocal mapper = MapperLocal.getMapper();
            instanceMapper.incInstanceNum();
            controller.start(gameInfo);
        }).start();
    }

    // 开始一场回顾对战（加载历史对战数据进行回放）
    public void startBattleReview(GameInfo newGameInfo, Vector<Chess> chesses) {
        System.out.println("start battle");
        System.out.println(newGameInfo.toString());
        // if(newGameInfo.getP1() == null){
        //     newGameInfo.setP1(new Player("null", ChessCondition.BLACK));
        // }
        // if(newGameInfo.getP2() == null){
        //     newGameInfo.setP2(new Player("null",ChessCondition.WHITE));
        // }    
        System.out.println(((Player) newGameInfo.getP1()).getPort() + " " + ((Player) newGameInfo.getP2()).getPort());
        new Thread(() -> {
            ControllerReview controller = ControllerReview.getController();
            // Viewer viewer = Viewer.getViewer();
            // Mapper mapper = Mapper.getMapper();
            // String key = InstanceManager.getInstanceManager().assignKey();
            // InstanceMapper.addInstance(key, controller, viewer, mapper);

            // controller.setKey(key);
            // viewer.setKey(key);
            // mapper.setKey(key);

            instanceMapper.incInstanceNum();

            ControllerReview.setGameInfo(newGameInfo);
            ControllerReview.setChessVector(chesses);

            controller.start();
        }).start();
    }
}
