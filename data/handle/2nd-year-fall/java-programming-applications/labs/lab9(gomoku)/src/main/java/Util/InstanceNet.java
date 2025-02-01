package Util;

import Bean.GameInfo;
import Bean.PlayerCondition;
import InstanceControl.InstanceManager;
import InstanceControl.InstanceMapper;
import InstanceControl.InstanceViewer;
import org.apache.commons.lang3.tuple.ImmutablePair;
import org.apache.commons.lang3.tuple.MutablePair;

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.ObjectInputStream;
import java.io.ObjectOutputStream;
import java.net.DatagramPacket;
import java.net.DatagramSocket;
import java.net.InetAddress;
import java.util.Vector;

public class InstanceNet {
    private static InstanceNet net;

    // 获取单例InstanceNet实例
    public static InstanceNet getNet() {
        if(net == null){
            net = new InstanceNet();
        }
        return net;
    }

   // 检查服务器是否在运行
public boolean checkRunningServer(MutablePair<String, Integer> serverAddress, ImmutablePair<String, Integer> localAddress) {
    boolean result = false;  // 默认结果是false，表示服务器未运行
    DatagramSocket socket = null;  // 声明一个DatagramSocket对象，用于发送和接收UDP数据包

    try {
        // 根据传入的服务器地址（IP地址）解析出InetAddress对象
        InetAddress address = InetAddress.getByName(serverAddress.getLeft());
        
        // 构建一个检查服务器状态的消息
        String message = "checkRunningServer";
        byte[] data = message.getBytes();  // 将消息转换为字节数组
        
        // 创建一个DatagramPacket对象，将数据、目标地址和端口封装在包中
        DatagramPacket packet = new DatagramPacket(data, data.length, address, serverAddress.getRight());
        
        // 创建DatagramSocket对象并绑定到本地地址的端口上
        socket = new DatagramSocket(localAddress.getRight());
        
        // 发送请求包到服务器
        socket.send(packet);

        // 准备接收服务器的响应
        byte[] data2 = new byte[1024];  // 创建一个字节数组来存储服务器的响应
        DatagramPacket packet2 = new DatagramPacket(data2, data2.length);  // 创建接收数据包

        System.out.println("checkRunningServer");  // 打印调试信息，表示正在进行服务器检查
        
        socket.setSoTimeout(1000);  // 设置Socket的超时时间为1000毫秒（1秒），避免死锁等待
        
        // 等待接收服务器的响应
        socket.receive(packet2);  // 接收来自服务器的响应数据包

        // 将接收到的数据转换为字符串
        String reply = new String(data2, 0, packet2.getLength());
        
        // 如果服务器返回"running"的消息，表示服务器正在运行
        if (reply.equals("running")) {
            result = true;  // 设置result为true，表示服务器正在运行
        }
        
        // 关闭Socket连接
        socket.close();
        
    } catch (Exception e) {
        // 如果发生异常，表示服务器未响应或发生错误，将result设置为false
        result = false;
        e.printStackTrace();  // 打印异常信息
    } finally {
        // 无论如何，确保Socket被关闭，释放资源
        if (socket != null) {
            socket.close();
        }
    }

    return result;  // 返回检查结果，true表示服务器在运行，false表示服务器未响应或发生错误
}


// 向服务器报告本地实例的条件（端口和ID）
public void putInstanceCondition(MutablePair<String, Integer> serverAddress, ImmutablePair<String, Integer> localAddress) {
    DatagramSocket socket = null;  // 初始化 DatagramSocket 对象，用于网络通信
    try {
        // 获取服务器的 IP 地址，通过 serverAddress.getLeft() 获取服务器的地址（IP）
        InetAddress address = InetAddress.getByName(serverAddress.getLeft());

        // 构造消息，内容为 "putInstanceCondition:本地IP:本地端口"，报告本地实例的条件
        String message = "putInstanceCondition:" + localAddress.getLeft() + ":" + localAddress.getRight();

        // 将消息转换为字节数组，准备发送
        byte[] data = message.getBytes();

        // 创建一个 DatagramPacket，封装要发送的消息、目标地址和目标端口
        DatagramPacket packet = new DatagramPacket(data, data.length, address, serverAddress.getRight());

        // 创建一个 DatagramSocket，并绑定到本地端口（通过 localAddress.getRight() 获取）
        socket = new DatagramSocket(localAddress.getRight());

        // 通过 socket 发送消息到服务器
        socket.send(packet);

        // 为接收服务器的响应准备一个 DatagramPacket 对象
        byte[] data2 = new byte[1024];  // 创建一个 1024 字节大小的数组来存放接收到的数据
        DatagramPacket packet2 = new DatagramPacket(data2, data2.length);

        // 接收来自服务器的响应，阻塞等待直到收到数据或超时
        socket.receive(packet2);

        // 将接收到的字节数组转换为字符串
        String reply = new String(data2, 0, packet2.getLength());

        // 输出服务器的回复信息，用于调试或记录
        System.out.println(reply);

        // 解析返回的端口号
        int port;  
        // 判断返回的消息是否包含 "port: "，如果包含，则提取端口号
        if(reply.substring(0, 6).equals("port: ")) {
            // 提取端口号，去掉 "port: " 和可能的空格部分，转换为整数
            port = Integer.parseInt(reply.substring(reply.indexOf(":") + 2));
        } else {
            // 如果返回的消息不是以 "port: " 开头，则设置端口为 -1，表示无效端口
            port = -1;
        }

        // 将解析出来的端口号设置到 InstanceManager 中，作为新连接的端口
        InstanceManager.getInstanceManager().setServerPort(port);

        // 关闭 socket，释放资源
        socket.close();
    } catch (Exception e) {
        // 捕获并处理任何异常，打印堆栈跟踪，便于调试
        e.printStackTrace();
    } finally {
        // 在 finally 块中关闭 socket，确保无论是否发生异常，socket 都会被关闭
        if (socket != null && !socket.isClosed()) {
            socket.close();
        }
    }
}


// 监听房间列表的更新
public boolean listenToRoomList(MutablePair<String, Integer> serverAddress, ImmutablePair<String, Integer> localAddress) {
    DatagramSocket socket = null;  // 用于发送和接收UDP数据包的Socket对象

    try {
        // 创建DatagramSocket并绑定到指定端口
        socket = new DatagramSocket(serverAddress.getRight() + 1);

        // 设置接收超时时间为1000ms
        socket.setSoTimeout(1000);

        byte[] data = new byte[1024];  // 定义接收数据的缓冲区
        DatagramPacket packet = new DatagramPacket(data, data.length);  // 用于接收数据的DatagramPacket对象

        try {
            // 接收来自服务器的房间更新信息
            socket.receive(packet);
        } catch (Exception e) {
            // 如果超时或没有接收到数据，打印信息并将packet设为null
            System.out.println("No Room Update");
            packet = null;
        }

        // 获取InstanceMapper实例，用于管理房间信息
        InstanceMapper mapper = InstanceMapper.getInstance();

        // 用于序列化房间信息并发送的流
        ByteArrayOutputStream byteArrayOutStream = new ByteArrayOutputStream();
        ObjectOutputStream objectOutStream = new ObjectOutputStream(byteArrayOutStream);

        if (packet != null) {
            // 如果成功接收到房间更新数据包，开始处理数据
            
            System.out.println("Received Room Update");

            // 反序列化接收到的数据，获取房间名称和游戏信息
            ByteArrayInputStream byteArrayInStream = new ByteArrayInputStream(data);
            ObjectInputStream objectInStream = new ObjectInputStream(byteArrayInStream);
            Object obj = objectInStream.readObject();
            MutablePair<String, GameInfo> recieved = new MutablePair<String, GameInfo>();
            try{
                recieved = (MutablePair<String, GameInfo>) obj;
                String rooms = recieved.getLeft();
                GameInfo gameInfo = (GameInfo)recieved.getRight();
                // 更新或记录房间信息
                mapper.addRoom(rooms, gameInfo);
                InstanceViewer.getInstance().updataRoomList();  // 更新房间列表视图
                // 如果是新的在线对战信息，启动对战
                if (gameInfo.getP1().getCondition() == PlayerCondition.ONLINE && gameInfo.getP2().getCondition() == PlayerCondition.ONLINE) {
                    System.out.println("ONLINE");
                    InstanceManager.getInstanceManager().startBattle(gameInfo);  // 启动新的对战
                }
            }catch (Exception e) {
                System.out.println("Error in Recieving Room Update");
            }
            // 关闭输入流
            objectInStream.close();
            byteArrayInStream.close();
        }

        // 如果有消息缓冲，发送缓冲中的房间信息
        if (mapper.getRoomBuffer().getLeft() != null) {
            System.out.println("Send from Buffer");

            // 获取缓冲区中的房间信息
            String rooms = mapper.getRoomBuffer().getLeft();
            GameInfo gameInfo = mapper.getRoomBuffer().getRight();

            // 序列化房间信息并发送给服务器
            objectOutStream.writeObject(new MutablePair<>(rooms, gameInfo));
            byte[] data2 = byteArrayOutStream.toByteArray();
            DatagramPacket packet2 = new DatagramPacket(data2, data2.length, InetAddress.getByName(serverAddress.getLeft()), serverAddress.getRight());
            socket.send(packet2);  // 发送数据包到服务器

            objectOutStream.reset();  // 重置输出流
            mapper.clearRoomBuffer();  // 清空缓冲区
        }

        // 关闭输出流和字节输出流
        objectOutStream.close();
        byteArrayOutStream.close();

    } catch (Exception e) {
        e.printStackTrace();
    } finally {
        // 确保在处理完成后关闭Socket，释放资源
        if (socket != null) socket.close();
    }

    // 返回true，表示房间监听过程完成
    return true;
}


   // 服务器是否在运行的响应
public boolean serverRunning(MutablePair<String, Integer> serverAddress) {
    DatagramSocket socket = null;  // 声明一个DatagramSocket对象，用于发送和接收UDP数据包

    try {
        // 创建一个DatagramSocket对象，并绑定到指定的端口
        socket = new DatagramSocket(serverAddress.getRight());
        
        byte[] data = new byte[1024];  // 创建一个字节数组，作为接收数据的缓存
        DatagramPacket packet = new DatagramPacket(data, data.length);  // 创建DatagramPacket，用于接收数据
        
        socket.setSoTimeout(1000);  // 设置Socket的超时时间为1000ms，超过这个时间如果没有接收到数据，则抛出异常
        socket.receive(packet);  // 接收来自客户端的数据包
        String reply = new String(data, 0, packet.getLength());  // 将接收到的数据转换为字符串
        System.out.println(reply);  // 打印接收到的消息，方便调试

        InetAddress address = packet.getAddress();  // 获取发送数据包的客户端地址
        int portSend = packet.getPort();  // 获取发送数据包的客户端端口
        
        // 如果收到的消息是"checkRunningServer"，表示客户端在检查服务器是否运行
        if (reply.equals("checkRunningServer")) {
            System.out.println("reply server running");

            // 向客户端返回"running"，表示服务器正在运行
            String message = "running";
            byte[] data2 = message.getBytes();  // 将消息转换为字节数组
            DatagramPacket packet2 = new DatagramPacket(data2, data2.length, address, portSend);  // 创建一个数据包发送回客户端
            socket.send(packet2);  // 发送数据包到客户端
            socket.close();  // 关闭Socket连接
        } 
        // 如果收到的消息是"putInstanceCondition"，表示客户端在请求分配新的端口
        else if (reply.substring(0, reply.indexOf(":")).equals("putInstanceCondition")) {
            // 提取出客户端的IP地址
            String ip = reply.substring(reply.indexOf(":") + 1);
            ip = ip.substring(0, ip.indexOf(":"));
            System.out.println(ip);  // 打印客户端的IP地址，方便调试

            // 分配新的端口号
            int port;
            // 从10002开始查找可用端口，端口号每次增加2，直到找到一个空闲端口
            for (port = 10002; port <= 65535; port += 2) {
                boolean isPortAvailable = true;
                // 检查该端口是否已经被占用
                for (Object o : InstanceMapper.getInstance().getRemoteList()) {
                    if (((ImmutablePair<String, Integer>) o).getValue() == port) {
                        isPortAvailable = false;  // 如果端口已被占用，则标记为不可用
                        break;
                    }
                }
                if (isPortAvailable) {
                    break;  // 如果找到一个空闲端口，退出循环
                }
            }
            System.out.println(port);  // 打印分配的端口号，方便调试

            // 创建一个新的ImmutablePair对象，保存客户端的IP地址和分配的端口号
            ImmutablePair<String, Integer> clientAddress = new ImmutablePair<>(ip, port);
            // 将客户端的地址信息添加到InstanceMapper的客户端列表中
            InstanceMapper.getInstance().addClient(clientAddress);

            // 向客户端返回分配的端口号
            String message = "port: " + port;
            System.out.println(message);  // 打印返回给客户端的消息，方便调试
            byte[] data2 = message.getBytes();  // 将消息转换为字节数组
            DatagramPacket packet2 = new DatagramPacket(data2, data2.length, address, portSend);  // 创建一个数据包
            socket.send(packet2);  // 发送数据包到客户端
            socket.close();  // 关闭Socket连接
        }

    } catch (Exception e) {
        e.printStackTrace();  // 如果发生异常，打印异常信息
    } finally {
        if (socket != null) {
            socket.close();  // 最终关闭Socket连接，释放资源
        }
    }

    return true;  // 返回true，表示方法执行成功
}

// 监听房间更新
public boolean listenToRoomUpdata(MutablePair<String, Integer> serverAddress) {
    DatagramSocket socket = null;  // 用于发送和接收UDP数据包的Socket对象
    InstanceMapper mapper = InstanceMapper.getInstance();  // 获取实例映射器，用于管理房间与实例的数据
    try {
        // 获取服务器的IP地址
        InetAddress address = InetAddress.getByName(serverAddress.getLeft());

        byte[] data = new byte[1024];  // 定义接收数据的缓冲区
        DatagramPacket packet = null;  // 用于接收数据的DatagramPacket对象

        // 向所有客户端监听房间更新信息
        for (Object o : mapper.getRemoteList()) {
            packet = new DatagramPacket(data, data.length);  // 初始化接收数据的包

            // 获取每个客户端的地址和端口
            InetAddress address2 = InetAddress.getByName(((ImmutablePair<String, Integer>) o).getLeft());
            int tmpPort = ((ImmutablePair<String, Integer>) o).getRight();
            System.out.println(address2.getHostAddress() + ":" + tmpPort);

            try {
                // 为每个客户端创建一个新的DatagramSocket，并绑定到客户端端口
                socket = new DatagramSocket(tmpPort);
                socket.setSoTimeout(2000);  // 设置超时为500ms
                socket.receive(packet);  // 等待接收数据包
            } catch (Exception e) {
                packet = null;  // 如果没有接收到数据包，则继续监听下一个客户端
            } finally {
                socket.close();  // 无论是否收到数据包，都关闭Socket
            }

            // 如果接收到数据包，则跳出循环
            if (packet != null) {
                break;
            }
        }
        // 创建一个新的DatagramSocket，准备发送房间更新信息
        socket = new DatagramSocket(serverAddress.getRight() + 100);
        ByteArrayOutputStream byteArrayOutStream = new ByteArrayOutputStream();
        ObjectOutputStream objectOutStream = new ObjectOutputStream(byteArrayOutStream);
        // 反序列化接收到的数据，获取房间和游戏信息
        // 如果成功接收到房间更新数据包，开始处理数据
        if (packet != null) {
            ByteArrayInputStream byteArrayInStream = new ByteArrayInputStream(data);
            ObjectInputStream objectInStream = new ObjectInputStream(byteArrayInStream);
            Object obj = objectInStream.readObject();
            MutablePair<String, GameInfo> recieved = (MutablePair<String, GameInfo>) obj;

            System.out.println("recevied room update");

            System.out.println(obj.toString());
            String rooms = recieved.getLeft();
            GameInfo gameInfo = recieved.getRight();

            // 如果游戏信息中的房间号为-1，表示新房间，分配一个新的房间号
            if (gameInfo.getIndex() == -1)
                gameInfo.setIndex(mapper.getRoomList().size() + 1);  // 为新房间分配新的房间号

            // 将新的房间信息添加到房间列表中
            mapper.addRoom(rooms, gameInfo);
            InstanceViewer.getInstance().updataRoomList();  // 更新房间列表视图


            if (gameInfo.getP1().getCondition() == PlayerCondition.ONLINE && gameInfo.getP2().getCondition() == PlayerCondition.ONLINE) {
                System.out.println("ONLINE");

                // 为玩家分配端口
                int port1 = 10000 - 2 * gameInfo.getIndex(), port2 = 10000 - 2 * gameInfo.getIndex() + 1;
                gameInfo.getP1().setPort(port1);
                gameInfo.getP2().setPort(port2);
                // 获取房间基准端口和IP地址
                Object obasePort = mapper.getPortFromRoomNumber(gameInfo.getIndex());
                int basePort = obasePort == null ? -1 : (Integer) obasePort;
                Object obaseIp = mapper.getClientFromPort(basePort);
                String baseIp = obaseIp == null ? null : (String) obaseIp;

                // 将更新后的游戏信息发送给对方
                objectOutStream.writeObject(new MutablePair<>(rooms, gameInfo));
                byte[] data2 = byteArrayOutStream.toByteArray();
                DatagramPacket packet2 = new DatagramPacket(data2, data2.length, packet.getAddress(), packet.getPort());
                socket.send(packet2);

                // 如果房间不属于本地服务器，将更新后的游戏信息发送给基准IP
                if (baseIp != null) {
                    DatagramPacket packet3 = new DatagramPacket(data2, data2.length, InetAddress.getByName(baseIp), basePort);
                    socket.send(packet3);
                } else {
                    //启动本地对战
                    InstanceManager.getInstanceManager().startBattle(gameInfo);
                }

                objectOutStream.reset();
            }
            // 向每个slave端发送房间更新信息
            for (Object o : mapper.getRemoteList()) {  // 遍历所有的remote地址列表
                // 将当前的对象强制转换为ImmutablePair<String, Integer>类型
                ImmutablePair<String, Integer> clientAddress = (ImmutablePair<String, Integer>) o;  
                // 输出调试信息，表示正在发送数据到slave
                System.out.println("send to slave");                 
                // 将对象序列化为字节流，并发送到客户端
                objectOutStream.writeObject(new MutablePair<String, GameInfo>(rooms,gameInfo));  // 发送客户端信息
                byte[] data3 = byteArrayOutStream.toByteArray();  // 将字节流转换成字节数组
                objectOutStream.reset();  // 重置输出流，以便下次使用
                System.out.println(data3.toString());// 输出当前要发送的数据对象
                // 创建UDP数据包，指定数据内容、目标IP地址和端口号
                DatagramPacket packet3 = new DatagramPacket(data3, data3.length, 
                                                                InetAddress.getByName(clientAddress.getLeft()), 
                                                                clientAddress.getRight() + 1);  // 目标端口号加1
                // 发送UDP数据包到对应的客户端
                socket.send(packet3);  
            }
            objectInStream.close();  // 关闭输入流
            byteArrayInStream.close();  // 关闭输入流
                
        }
        // 如果缓冲区中有房间信息，发送缓冲区中的房间数据
        if (mapper.getRoomBuffer().getLeft() != null) {
            System.out.println("Send from Buffer");

            // 从缓冲区获取房间信息
            String rooms = mapper.getRoomBuffer().getLeft();
            GameInfo gameInfo = mapper.getRoomBuffer().getRight();
            gameInfo.setIndex(mapper.getRoomList().size() + 1);  // 分配新的房间号
            mapper.addRoom(rooms, gameInfo);
            InstanceViewer.getInstance().updataRoomList();  // 更新房间列表

            // 将房间号添加到PortRoomMap
            if (mapper.getPortRoomMap().containsKey(-1)) {
                mapper.getPortRoomMap().get(-1).add(gameInfo.getIndex());
            } else {
                Vector<Integer> list = new Vector<>();
                list.add(gameInfo.getIndex());
                mapper.getPortRoomMap().put(-1, list);
            }

            // 向每个slave端发送缓冲区中的房间信息
            for (Object o : mapper.getRemoteList()) {
                ImmutablePair<String, Integer> clientAddress = (ImmutablePair<String, Integer>) o;
                objectOutStream.writeObject(mapper.getRoomBuffer());
                byte[] data2 = byteArrayOutStream.toByteArray();
                objectOutStream.reset();
                System.out.println("Send to " + clientAddress.getLeft() + ":" + clientAddress.getRight());
                // 发送UDP数据包到每个客户端
                DatagramPacket packet2 = new DatagramPacket(data2, data2.length, InetAddress.getByName(clientAddress.getLeft()), clientAddress.getRight() + 1);
                socket.send(packet2);
            }
            mapper.clearRoomBuffer();  // 清空房间缓冲区
        }
        objectOutStream.close();  // 关闭输出流
        byteArrayOutStream.close();  // 关闭字节流  
    } catch (Exception e) {
        e.printStackTrace();
    } finally {
        socket.close();  // 关闭Socket，释放资源
    }
    return true;
}
}