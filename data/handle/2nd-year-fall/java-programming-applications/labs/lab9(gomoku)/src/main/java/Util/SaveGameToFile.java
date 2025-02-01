package Util;

import Bean.Chess;
import Bean.Player;

import java.io.FileOutputStream;
import java.io.ObjectOutputStream;
import java.util.Vector;

public class SaveGameToFile {
    //单例模式
    private static SaveGameToFile instance = null;
    private SaveGameToFile() {
    }
    public static SaveGameToFile getInstance() {
        if (instance == null) {
            instance = new SaveGameToFile();
        }
        return instance;
    }

    private String path="src\\main\\resource\\gameRecords\\";
    private String fileName="";

    //save 2*Player+Mapper.chesses to file
    public void saveGame(Player Player1,Player Player2, Vector<Chess> chesses) {
        try {
            fileName=Player1.getName()+"_"+Player2.getName()+".txt";
            ObjectOutputStream oos = new ObjectOutputStream(new FileOutputStream(path+fileName));

            //save Player
            oos.writeObject(Player1);
            oos.writeObject(Player2);

            //save chesses
            oos.writeObject(chesses);
            oos.close();

        }catch (Exception e) {
            e.printStackTrace();
        }

    }

}
