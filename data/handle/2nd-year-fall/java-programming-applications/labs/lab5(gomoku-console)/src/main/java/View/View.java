package View;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;

import Controller.Control;
import Model.Model;

public class View {
	private static View instance;
	public static View getinstance(){
		if(instance==null){
			instance=new View();
		}
		return instance;
	}
	public void repaint(){
		Model m=Model.getinstance();
		for(int row=0;row<Model.WIDTH;row++){
			for(int col=0;col<Model.WIDTH;col++){
				int color=m.getchess(row,col);
				if(color==Model.SPACE){
					System.out.print("+");
				}else if(color==Model.BLACK){
					System.out.print("*");
				}else if(color==Model.WHITE){
					System.out.print("O");
				}
			}
			System.out.println();
		}
	}
	public static void input() {
		BufferedReader in = new BufferedReader(new InputStreamReader(System.in));
		int row = -1;
		int col = -1;
		boolean validInput = false;
	
		while (!validInput) {
			try {
				// Prompt for row coordinate
				System.out.println("Please enter the row number (0-18):");
				String line = in.readLine();
				row = Integer.parseInt(line);
				
				// Check if row coordinate is within valid range
				if (row < 0 || row >= Model.WIDTH) {
					System.out.println("Invalid row number. Please enter a number between 0 and 18.");
					continue;  // Prompt for input again
				}
	
				// Prompt for column coordinate
				System.out.println("Please enter the column number (0-18):");
				line = in.readLine();
				col = Integer.parseInt(line);
	
				// Check if column coordinate is within valid range
				if (col < 0 || col >= Model.WIDTH) {
					System.out.println("Invalid column number. Please enter a number between 0 and 18.");
					continue;  // Prompt for input again
				}
	
				// Check if the position is already occupied
				if (Model.getinstance().getchess(row, col) != Model.SPACE) {
					System.out.println("This position is already occupied. Please choose another position.");
					continue;  // Prompt for input again
				}
	
				// Valid input; exit loop
				validInput = true;
			} catch (NumberFormatException e) {
				System.out.println("Invalid input. Please enter a valid integer.");
			} catch (IOException e) {
				System.out.println("Input/output error. Please try again.");
			}
		}
	
		// Pass the coordinates to Control class when input is valid and position is empty
		Control.getIntance().report(row, col);
	}
	
	
}
