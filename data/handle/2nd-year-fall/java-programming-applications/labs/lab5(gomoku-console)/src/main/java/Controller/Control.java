package Controller;
import Model.*;
import View.*;

public class Control {
	private static Control instance;
	public static Control getIntance(){
		if(instance==null){
			instance=new Control();
		}
		return instance;
	}
	private int color=Model.BLACK;
	public void report(int row, int col) {
		boolean success=Model.getinstance().putChess(row, col, color);
		if(success){
			color=-color;
			View.getinstance().repaint();
			int winner=Model.getinstance().whoWin();
			if(winner==Model.BLACK){
				System.out.println("black win");
			}
			else if(winner==Model.WHITE)
				System.out.println("white win");
		}
	}
	public static void main(String[] args){
		Model m=Model.getinstance();
		View.getinstance().repaint();
		while(m.whoWin()==Model.SPACE){
			View.input();
		}
	}
}
