package Controller;

import Bean.BoardInfo;
import Bean.Chess;
import Bean.ChessCondition;
import Bean.GameInfo;
import Map.Mapper;
import Map.MapperLocal;

import java.util.Vector;

public class CheckWin {
    private Vector<Chess> chesses;
    private static GameInfo gameInfo;
    //单例模式
    private CheckWin(){}
    private static CheckWin instance;
    public static CheckWin getInstance(GameInfo _gameInfo){
        if(instance == null){
            instance = new CheckWin();
            gameInfo = _gameInfo;
        }
        return instance;
    }

    private ChessCondition checkPositions(int x, int y) {
        // check the ChessCondition of the chess at (x, y)
        //synchronized(this) {
            System.out.println("checkPositions: " + x + ", " + y);
            for (int i = 0; i < chesses.size(); i++) {
                Chess c = chesses.get(i);
                if (c.getCol() == x && c.getRow() == y) {
                    System.out.println("CheckWin: checkPositions: " + c.getCol() + " " + c.getRow());
                    return c.getCondition();
                }
            }
        //}
        return ChessCondition.EMPTY;
    }

    public boolean isWon(){
        System.out.println("CheckWin.isWon()");
        if(gameInfo.isLOCAL() == true){
            chesses = MapperLocal.getChesses();
        }else{
            chesses = Mapper.getChesses();
        }
        if(chesses.isEmpty()) {
            System.out.println("CheckWin.isWon(): chesses is empty");
            return false;
        }

        int count = 1;      //本身一点为 1
        int posX = 0;
        int posY = 0;

        int WinSteps= BoardInfo.STEP_TO_WIN;
        //x列 y行
        int x=chesses.lastElement().getCol();
        int y=chesses.lastElement().getRow();
        ChessCondition color = chesses.lastElement().getCondition();
        System.out.println("CheckWin.isWon(): x="+x+" y="+y+" color="+color);
        /**判断水平方向上的胜负
         /* 将水平方向以传入的点x上的y轴作为分隔线分为两部分
         * 先向左边遍历，判断到的相同的连续的点  count++
         */
        System.out.println("CheckWin.isWon(): check horizontal");
        for(posX = x - 1; posX > 0 ; posX--) {
            //Position tmPosition=new Position(posX, y);
            if (checkPositions(posX,y)== color) {
                count++;
                if (count >= WinSteps) {
                    return true;
                }
            }else {
                break;
            }
        }    //向右边遍历
        for(posX = x + 1; posX <= BoardInfo.BOARD_SIZE; posX++) {
            //Position tmPosition=new Position(posX, y);
            if (checkPositions(posX,y) == color) {
                count++;
                if (count >= WinSteps) {
                    return true;
                }
            }else {
                break;
            }
        }
        count=1;
        /**判断垂直方向上的胜负
         /* 将垂直方向以传入的点y上的x轴作为分隔线分为两部分
         * 先向上遍历，判断到的相同的连续的点  count++
         */
        System.out.println("CheckWin.isWon(): check vertical");
        for(posY = y - 1; posY > 0; posY--) {
            //Position tmPosition=new Position(x, posY);
            if (checkPositions(x,posY) == color) {
                count++;
                if (count >= WinSteps) {
                    return true;
                }
            }else {
                break;
            }
        }//向下遍历
        for(posY = y + 1; posY <= BoardInfo.BOARD_SIZE; posY++) {
            //Position tmPosition=new Position(x, posY);
            if (checkPositions(x,posY)  == color) {
                count++;
                if (count >= WinSteps) {
                    return true;
                }
            }else {
                break;
            }
        }
        count=1;
        /**判断左上右下方向上的胜负
         * 以坐标点为分割线，将棋盘分为左右两个等腰三角形
         * 先判断左边的
         */
        System.out.println("CheckWin.isWon(): check left-up-right-down");
        for(posX = x - 1, posY = y - 1; posX > 0 && posY > 0; posX--, posY--) {
            //Position tmPosition=new Position(posX, posY);
            if (checkPositions(posX,posY) == color) {
                count++;
                if (count >= WinSteps) {
                    count = 1;
                    return true;
                }
            }else {
                break;
            }
        }//判断右边的
        for(posX = x + 1, posY = y + 1; posX <= BoardInfo.BOARD_SIZE && posY <= BoardInfo.BOARD_SIZE; posX++, posY++) {
            //Position tmPosition=new Position(posX, posY);
            if (checkPositions(posX,posY) == color) {
                count++;
                if (count >= WinSteps) {
                    count = 1;
                    return true;
                }
            }else {
                break;
            }
        }
        count=1;
        /**判断右下左下方向上的胜负
         * 以坐标点为分割线，将棋盘分为左右两个等腰三角形
         * 先判断左边的
         */
        for(posX = x + 1, posY = y - 1; posX <= BoardInfo.BOARD_SIZE && posY > 0; posX++, posY--) {
            //Position tmPosition=new Position(posX, posY);
            if (checkPositions(posX,posY) == color) {
                count++;
                if (count >= WinSteps) {
                    return true;
                }
            }else {
                break;
            }
        }//判断右边的
        for(posX = x - 1, posY = y + 1; posX > 0 && posY <= BoardInfo.BOARD_SIZE; posX--, posY++) {
            //Position tmPosition=new Position(posX, posY);
            if (checkPositions(posX,posY) == color) {
                count++;
                if (count >= WinSteps) {
                    return true;
                }
            }else {
                break;
            }
        }

        return false;
    }
}
