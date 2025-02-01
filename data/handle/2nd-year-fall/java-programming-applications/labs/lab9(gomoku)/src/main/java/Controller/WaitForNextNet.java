package Controller;

import Bean.BattleMessage;
import Bean.BoardCondition;
import Map.MessageBuffer;

public class WaitForNextNet implements WaitForNext{
    private static WaitForNextNet instance;
    private WaitForNextNet(){}
    public static WaitForNextNet getInstance(){
        if(instance == null)
            instance = new WaitForNextNet();
        return instance;
    }

    public void waitForNext() {
        Controller.getController().setBoardCondition(BoardCondition.WAIT);
//        BattleMessage nBM = null;
//        while(nBM == null) {
//            nBM = MessageBuffer.getInstance().getBattleMessage();
//            if (nBM != null) {
//                System.out.println("Received BattleMessage");
//                Controller.getController().notifyRemote(nBM);
//            }
//        }
//        MessageBuffer.getInstance().clear();
    }
}
