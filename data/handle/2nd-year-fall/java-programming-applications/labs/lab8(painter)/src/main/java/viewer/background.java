package viewer;

import javax.swing.*;
import java.awt.*;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.awt.event.MouseAdapter;
import java.awt.event.MouseEvent;

public class background extends JPanel {
    private JComboBox<String> comboBox; // JComboBox to select the color
    private JLabel label;
    public Color selectedColor; // Member variable to store selected color

    background() {
        setLayout(new GridLayout(1, 2)); // GridLayout to place label and combo box side by side
        setPreferredSize(new Dimension(200, 50));
        selectedColor = Color.RED; // Default color is white
        setBackground(selectedColor); // Set initial background color to white

        label = new JLabel("Fill Color");
        label.setHorizontalAlignment(JLabel.CENTER);
        add(label);
        // Initialize combo box and add color options
        comboBox = new JComboBox<>();
        comboBox.addItem("Red");
        comboBox.addItem("Green");
        comboBox.addItem("Blue");
        comboBox.addItem("Yellow");
        comboBox.addItem("White");
        comboBox.setSelectedItem("Red");
        // Add action listener to combo box to detect changes
        comboBox.addActionListener(new ActionListener() {
            @Override
            public void actionPerformed(ActionEvent e) {
                String selected = (String) comboBox.getSelectedItem(); // Get selected color
                
                switch (selected) {
                    case "Red":
                        selectedColor = Color.RED; // Set color to red
                        break;
                    case "Green":
                        selectedColor = Color.GREEN; // Set color to green
                        break;
                    case "Blue":
                        selectedColor = Color.BLUE; // Set color to blue
                        break;
                    case "Yellow":
                        selectedColor = Color.YELLOW; // Set color to yellow
                        break;
                    case "White":
                        selectedColor = Color.WHITE; // Set color to white
                        break;
                    default:
                        selectedColor = Color.WHITE; // Default to white
                        break;
                }
                setBackground(selectedColor); // Update background color
                repaint(); // Repaint the panel to reflect the color change
            }
        });

        add(comboBox);

        // Add mouse listener to panel for direct color selection via clicking
        this.addMouseListener(new MouseAdapter() {
            @Override
            public void mouseClicked(MouseEvent e) {
                // Open a color chooser dialog when the panel is clicked
                Color newColor = JColorChooser.showDialog(null, "Choose Background Color", selectedColor);
                if (newColor != null) {
                    selectedColor = newColor; // Update selected color
                    setBackground(selectedColor); // Set the new color as background
                    repaint(); // Repaint the panel to reflect the new color
                }
            }
        });
    }
}
