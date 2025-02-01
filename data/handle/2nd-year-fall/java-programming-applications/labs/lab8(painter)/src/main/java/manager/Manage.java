package manager;

import viewer.Viewer;

import javax.swing.*;

public class Manage {

    private JFrame mainWindow;
    private Viewer viewer;

    void init(){
        mainWindow = new JFrame();
        viewer = new Viewer(mainWindow);
        viewer.init();
        viewer.show();


        while(true){
            //viewer.drawPanel.drawLine(200,200,100,100);
            viewer.update();
        }
    }

    public static void main(String[] args){
        Manage manage = new Manage();
        manage.init();

    }

}
