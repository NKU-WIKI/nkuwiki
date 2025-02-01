package Controller;

import Bean.BoardCondition;
import Map.Mapper;
import Map.MessageBuffer;

public class PutChessNet implements PutChess{
    //单例模式
    private static PutChessNet putChessNet = new PutChessNet();
    private PutChessNet(){}
    public static PutChessNet getPutChessNet(){
        if(putChessNet == null){
            putChessNet = new PutChessNet();
        }
        return putChessNet;
    }

    @Override
    public void putChess() {
        Controller.getController().setBoardCondition(BoardCondition.PLAY);
    }
}
