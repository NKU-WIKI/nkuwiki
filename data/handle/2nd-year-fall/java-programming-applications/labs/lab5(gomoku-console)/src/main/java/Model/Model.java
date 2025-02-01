package Model;

public class Model {
	public static final int WIDTH=19;
	public static final int BLACK=1;
	public static final int SPACE=0;
	public static final int WHITE=-1;
	
	private static int data[][]=new int[WIDTH][WIDTH];
	
	private static Model instance;
	public static Model getinstance(){
		if(instance==null){
			instance=new Model();
		}
		return instance;
	}
	public boolean putChess(int row,int col,int color){
		if(row>=0&&row<WIDTH&&col>=0&&col<WIDTH&&data[row][col]==SPACE){
			data[row][col]=color;
			return true;
		}else{
			throw(new IllegalArgumentException("参数不合法"));
		}
		//return false;
	}
	public int getchess(int row, int col) {
		return data[row][col];
	}
	public int whoWin() {
		// 遍历每个位置，检查四个方向的连线
		for (int row = 0; row < WIDTH; row++) {
			for (int col = 0; col < WIDTH; col++) {
				int color = data[row][col];
				if (color == SPACE) continue; // 空位不需要判断
	
				// 检查四个方向
				if (checkDirection(row, col, 1, 0, color) || // 水平
					checkDirection(row, col, 0, 1, color) || // 垂直
					checkDirection(row, col, 1, 1, color) || // 正对角线
					checkDirection(row, col, 1, -1, color)) { // 反对角线
					return color; // 返回获胜颜色
				}
			}
		}
		return SPACE; // 无胜利方
	}
	
	// 辅助方法，用于检查指定方向是否有连续五个相同颜色的棋子
	private boolean checkDirection(int row, int col, int dRow, int dCol, int color) {
		int count = 0;
		for (int i = 0; i < 5; i++) {
			int newRow = row + i * dRow;
			int newCol = col + i * dCol;
	
			// 检查坐标是否超出边界或棋子颜色是否匹配
			if (newRow < 0 || newRow >= WIDTH || newCol < 0 || newCol >= WIDTH || data[newRow][newCol] != color) {
				return false;
			}
			count++;
		}
		return count == 5;
	}
	
}
