package Bean;

public class Watcher extends Player{
    private String ip;
    private int port;

    public Watcher(String name, String ip, int port){
        super(name);
        this.ip = ip;
        this.port = port;
    }

    public String getIp(){
        return ip;
    }

    public int getPort(){
        return port;
    }
}
