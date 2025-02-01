package viewer;

import javax.swing.*;
import java.util.Vector;

public class leftControlBar extends JPanel {
    public static buttonSet buttonSet;

    public void addAll(Vector buttons){
        for(Object button : buttons){
            this.add((JComponent)button);
        }
    }

    leftControlBar(){
        this.setPreferredSize(new java.awt.Dimension(100, 550));
        this.setBackground(new java.awt.Color(108, 108, 108));

        //this.setVerticalScrollBarPolicy(JScrollPane.VERTICAL_SCROLLBAR_NEVER);
        //this.setHorizontalScrollBarPolicy(JScrollPane.HORIZONTAL_SCROLLBAR_AS_NEEDED);

        buttonSet = new buttonSet();
        this.addAll(viewer.buttonSet.buttons);

    }
}
