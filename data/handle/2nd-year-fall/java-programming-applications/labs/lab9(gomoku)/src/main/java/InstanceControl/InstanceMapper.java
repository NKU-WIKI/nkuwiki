package InstanceControl;

import Bean.GameInfo;
import Controller.Controller;
import View.Viewer;
import Map.Mapper;
import org.apache.commons.lang3.tuple.ImmutablePair;
import org.apache.commons.lang3.tuple.MutablePair;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Vector;

public class InstanceMapper {
    private InstanceMapper(){}

    private static InstanceMapper instanceMapper;

    public static InstanceMapper getInstance() {
        if(instanceMapper == null){
            instanceMapper = new InstanceMapper();
        }
        return instanceMapper;
    }

    //本地实际运行的实例的管理
    private static int instanceNum=0;

    public static void addInstance(String key, Controller controller, Viewer viewer, Mapper mapper) {
        controllerMap.put(key, controller);
        viewerMap.put(key, viewer);
        mapperMap.put(key, mapper);
    }

    public int getInstanceNum() {
        return instanceNum;
    }

    public void incInstanceNum(){
        instanceNum++;
    }


    private static Map<String, Controller> controllerMap=new HashMap<String, Controller>();

    public void addController(String key, Controller controller){
        controllerMap.put(key, controller);
    }


    public Controller getController(String key){
        return controllerMap.get(key);
    }

    //removecontrl
    public void removeController(String key){
        controllerMap.remove(key);
    }

    private static Map<String, Viewer> viewerMap=new HashMap<String, Viewer>();

    //addviewer
    public void addViewer(String key,Viewer viewer){
        viewerMap.put(key, viewer);
    }

    //getviewer
    public Viewer getViewer(String key){
        return viewerMap.get(key);
    }

    //removeviewer
    public void removeViewer(String key){
        viewerMap.remove(key);
    }

    private static Map<String, Mapper> mapperMap=new HashMap<String, Mapper>();

    //addmapper
    public void addMapper(String key,Mapper mapper){
        mapperMap.put(key, mapper);
    }

    //getmapper
    public Mapper getMapper(String key){
        return mapperMap.get(key);
    }

    //removemapper
    public void removeMapper(String key){
        mapperMap.remove(key);
    }

    //-----------------远程房间列表管理-----------------------------//
    private static Map<String, GameInfo> roomList =new HashMap<String, GameInfo>();
    private static MutablePair<String, GameInfo> roomBuffer =new MutablePair<String, GameInfo>();

    public void addRoom(String key, GameInfo gameInfo){
        roomList.put(key, gameInfo);
    }

    public GameInfo getRoom(String key){
        return roomList.get(key);
    }

    public void removeRoom(String key){
        roomList.remove(key);
    }

    public Map<String, GameInfo> getRoomList() {
        return roomList;
    }

    public void resetRoomList(Map<String, GameInfo> roomList) {
        InstanceMapper.roomList.clear();
        InstanceMapper.roomList.putAll(roomList);
    }

    //getRoomBuffer
    public MutablePair<String, GameInfo> getRoomBuffer() {
        return roomBuffer;
    }

    //setRoomBuffer
    public void setRoomBuffer(String key, GameInfo gameInfo){
        System.out.println(key);
        roomBuffer.setLeft(key);
        roomBuffer.setRight(gameInfo);
    }

    //clearroomBuffer
    public void clearRoomBuffer(){
        roomBuffer.setLeft(null);
        roomBuffer.setRight(null);
    }

    //-----------------远程端口和ip-----------------------------//
    private static Vector<ImmutablePair<String,Integer>> remoteList;

    public void setRemoteList(Vector<ImmutablePair<String,Integer>> remoteList) {
        InstanceMapper.remoteList = remoteList;
    }

    public List<ImmutablePair<String,Integer>> getRemoteList() {
        return remoteList;
    }

    public void initClientList() {
        remoteList=new Vector<>(0);

    }
    //adding client
    public void addClient(ImmutablePair<String,Integer> client){
        remoteList.add(client);
    }
    //use the Integer to find the string
    public ImmutablePair<String,Integer> getClientFromPort(Integer port){
        if(port <0){
            return null;
        }

        for(ImmutablePair<String,Integer> client:remoteList){
            if(client.getRight().equals(port)){
                return client;
            }
        }
        return null;
    }

    //----------------远程端口和房间号绑定-----------------------//
    private static Map<Integer,Vector<Integer>> portRoomMap=new HashMap<Integer, Vector<Integer>>();
    //get portRoomMap
    public Map<Integer, Vector<Integer>> getPortRoomMap() {
        return portRoomMap;
    }
    //return the Integer whose vector contains the wanted number
    public Integer getPortFromRoomNumber(int roomNum){
        if(roomNum<0)
            return null;

        for(Integer port:portRoomMap.keySet()){
            if(portRoomMap.get(port).contains(roomNum)){
                return port;
            }
        }
        return null;
    }

}
