package Controller;

import javax.swing.text.View;

import Bean.*;
import Map.Mapper;
import Map.MapperLocal;
import View.ViewerLocal;

public class ControllerLocal extends Controller {
    private static ControllerLocal controller;
    // private static InstanceManager instanceManager=InstanceManager.getInstanceManager();
    private static ViewerLocal viewer;
    private static MapperLocal mapper;

    private static BoardCondition boardCondition=BoardCondition.PLAY;

    // private static PutChess putChess=null;
    // private static WaitForNext waitForNext=null;
    private static ChessCondition side = ChessCondition.WHITE;
    private static ChessCondition winner = null;
    private static CheckWin winChecker;

    public static ControllerLocal getController() {
        if (controller == null) {
            controller = new ControllerLocal();
        }
        return controller;
    }

    private static String key;

    public void setKey(String k) {
        key = k;
    }

    public static ViewerLocal getViewerLocal() {
        return viewer;
    }

    public static MapperLocal getMapperLocal() {
        return mapper;
    }

    public void start(GameInfo gameInfo){
        viewer = ViewerLocal.getViewer(gameInfo);
        mapper = MapperLocal.getMapper();
        winChecker=CheckWin.getInstance(gameInfo);

        viewer.init();
        viewer.setBoardCondition(boardCondition);
        //viewer.getRightPanel().setLocalMode();

        //side=ChessCondition.BLACK;

        System.out.println("side: "+side);

        //gameLoopStart();

    }

    public void notifyBoardPress(int row, int col) {
        try {
            switch (boardCondition) {
                case NOPE:
                    break;
                case PLAY:
                    System.out.println("play");
                    viewer.setChess(new Chess(row, col, side));
                    //System.out.println("black");
                    //net.putChessRemote(new Chess(row, col, ChessCondition.BLACK),  new PlayerOnline("2", ChessCondition.WHITE, "localhost", 10001));
                    //MessageBuffer.getInstance().setBattleMessage(new BattleMessage(new Chess(row, col, side), Actions.NORM,""));
                    MapperLocal.addChess(new Chess(row, col, side));
                    if(winChecker.isWon()){

                        //MessageBuffer.getInstance().clear();
                        boardCondition=BoardCondition.FINISH;
                        //this.notifyBoardPress(-1,-1);
                        winner=side;
                        viewer.showFinishBox(side.toString()+" Win");
                    }
                    side=side==ChessCondition.BLACK?ChessCondition.WHITE:ChessCondition.BLACK;
                    break;
                case FINISH:
                    //show a message box
                    viewer.showFinishBox(winner.toString()+" Win");
                    boardCondition=BoardCondition.FINISH;
                    break;
                default:
                    break;
            }
        }catch (Exception e){
            e.printStackTrace();
        }

    }

    public void setBoardCondition(BoardCondition _boardCondition) {
        boardCondition = _boardCondition;
    }


    public static ChessCondition getSide() {
        return side;
    }

    public static BoardCondition getBoardCondition() {
        return boardCondition;
    }

}
