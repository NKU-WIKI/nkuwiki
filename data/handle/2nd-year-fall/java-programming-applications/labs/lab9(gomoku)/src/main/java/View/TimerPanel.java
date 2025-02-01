package View;

import javax.swing.*;
import java.util.Calendar;

public class TimerPanel extends JPanel {
    private JLabel countDown;
    private JLabel systemTime;
    private int setTime;
    private Calendar cal=Calendar.getInstance();


    public TimerPanel() {
        setTime = 300;

        countDown = new JLabel("00:00");
        countDown.setHorizontalAlignment(SwingConstants.CENTER);
        systemTime = new JLabel("00:00:00");
        systemTime.setHorizontalAlignment(SwingConstants.CENTER);
        setLayout(new BoxLayout(this, BoxLayout.Y_AXIS));
        add(countDown);
        add(systemTime);
        startTimer();
    }

    private void startTimer() {
        Timer timer = new Timer(1000, e -> {
            setTime--;
            if(setTime != 0)
                countDown.setText(String.format("%02d:%02d", setTime / 60 % 60, setTime % 60));
            cal=Calendar.getInstance();
            systemTime.setText(String.format("%02d:%02d:%02d", cal.get(Calendar.HOUR_OF_DAY), cal.get(Calendar.MINUTE), cal.get(Calendar.SECOND)));
        });
        timer.start();
    }
}
