package viewer;

import javax.swing.*;
import javax.swing.event.ChangeListener;
import java.awt.*;

public class fillRegion extends JPanel {
    public JCheckBox checkBox;
    public boolean isChecked;

    class fillRegionListener implements ChangeListener {
        public void stateChanged(javax.swing.event.ChangeEvent e) {
            isChecked = checkBox.isSelected();
        }
    }

    fillRegion(){
        setLayout(new GridLayout(1,1));
        setVisible(true);

        checkBox = new JCheckBox("Fill Region");
        checkBox.addChangeListener(new fillRegionListener());
        add(checkBox);
    }


}
