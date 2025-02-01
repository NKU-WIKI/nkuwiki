package Util;

import java.io.FileInputStream;
import java.io.ObjectInputStream;

public class RestoreGameFromFile {
    public static Object[] readGameFromFile(String filePath) {
        Object[] game = new Object[3];
        try {
            ObjectInputStream in = new ObjectInputStream(new FileInputStream(filePath));
            game[0] = in.readObject();
            game[1] = in.readObject();
            game[2] = in.readObject();
            in.close();
        } catch (Exception e) {
            e.printStackTrace();
        }
        return game;
    }
}
