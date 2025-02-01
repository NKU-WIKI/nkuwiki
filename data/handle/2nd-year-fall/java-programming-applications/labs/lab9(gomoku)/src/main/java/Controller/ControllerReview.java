package Controller;

import Bean.*;
import InstanceControl.InstanceManager;
import Map.AddressBattle;
import Map.Mapper;
import Map.MessageBuffer;
import Util.NetUDP;
import View.Viewer;

import java.util.Vector;

public class ControllerReview extends Controller {
    private static ControllerReview controller;
    private static InstanceManager instanceManager = InstanceManager.getInstanceManager();
    private static Viewer viewer;
    private static Mapper mapper;
    private static BoardCondition boardCondition = BoardCondition.NOPE;
    private static GameInfo gameInfo;
    private static Player currentPlayer;
    private static Player enemyPlayer;
    private static Vector<Chess> chessVector;

    private static ChessCondition side = ChessCondition.EMPTY;

    public static ControllerReview getController() {
        if (controller == null) {
            controller = new ControllerReview();
        }
        return controller;
    }

    public static void setGameInfo(GameInfo gameInfo) {
        ControllerReview.gameInfo = gameInfo;

    }

    public static void setCurrentPlayer(Player currentPlayer) {
        ControllerReview.currentPlayer = currentPlayer;
        //decide which player is enemy player
        if (currentPlayer.getName().equals(gameInfo.getP1().getName())) {
            enemyPlayer = (Player) gameInfo.getP2();
        } else {
            enemyPlayer = (Player) gameInfo.getP1();
        }
    }

    private static String key;

    public void setKey(String k) {
        key = k;
    }

    public static Viewer getViewer() {
        return viewer;
    }

    public static Mapper getMapper() {
        return mapper;
    }

    public void start() {
        viewer = Viewer.getViewer();
        mapper = Mapper.getMapper();
        viewer.setGameInfo(gameInfo);
        mapper.setGameInfo(gameInfo);
        // Mapper.setChessStore(chessVector);
        viewer.init();
        viewer.setBoardCondition(boardCondition);
        viewer.getRightPanel().setOfflineMode();
        

    }

    public static Vector<Chess> getChessVector() {
        return chessVector;
    }

    public static void setChessVector(Vector<Chess> chessVector) {
        ControllerReview.chessVector = chessVector;
    }
}


