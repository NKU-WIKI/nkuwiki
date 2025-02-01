package Util;

import javazoom.jl.player.*;

import java.io.FileInputStream;

public class MusicPlayer {

    private Player player;
    private Thread thread;
    private FileInputStream stream;


    public MusicPlayer(String path) {
        try {
            stream = new FileInputStream(path);
            player = new Player(stream);
            thread = new Thread(() -> {
                try {
                    player.play();
                } catch (Exception e) {
                    e.printStackTrace();
                }
            });
            thread.start();
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}
