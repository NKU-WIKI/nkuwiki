package Map;

import Bean.BattleMessage;

// MessageBuffer 类用于存储战斗消息，采用单例模式。
// 它提供了一个全局唯一的实例，用来保存和操作 `BattleMessage` 对象。
// 该类的设计允许在多个地方共享相同的 `BattleMessage` 实例，简化了消息的管理和传递。
public class MessageBuffer {
    // 单例模式：确保全局只有一个 MessageBuffer 实例
    private static MessageBuffer instance = null;

    // 私有构造函数，防止外部实例化
    private MessageBuffer(){}

    // 获取 MessageBuffer 实例的静态方法
    // 如果实例不存在，则创建一个新的实例；如果已存在，则返回现有的实例
    public static MessageBuffer getInstance(){
        if(instance == null){
            instance = new MessageBuffer();  // 创建唯一实例
        }
        return instance;  // 返回实例
    }

    // 存储战斗消息的变量
    private static BattleMessage BattleMessage = null;

    // 获取当前存储的 BattleMessage 对象
    public BattleMessage getBattleMessage(){
        return BattleMessage;  // 返回存储的战斗消息对象
    }

    // 设置或更新当前的 BattleMessage 对象
    public static void setBattleMessage(BattleMessage battleMessage){
        BattleMessage = battleMessage;  // 更新战斗消息对象
    }

    // 清空当前存储的 BattleMessage 对象
    public void clear(){
        BattleMessage = null;  // 将战斗消息对象设为 null，表示清空
    }
}
