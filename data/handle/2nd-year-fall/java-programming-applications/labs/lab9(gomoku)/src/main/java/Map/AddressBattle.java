package Map;

import org.apache.commons.lang3.tuple.ImmutablePair;

// AddressBattle 类用于存储和管理本地与远程地址信息，采用了单例模式（Singleton Pattern）。
// 该类提供了全局唯一的实例，可以存储和获取本地和远程的 IP 地址与端口。
// 通过使用 Apache Commons Lang 库的 `ImmutablePair` 类，存储地址信息（IP 和端口）为一对不变的值。
public class AddressBattle {
    
    // 单例模式：确保全局只有一个 AddressBattle 实例
    private static AddressBattle addressBattle = null;

    // 私有构造函数，防止外部直接实例化
    private AddressBattle(){}

    // 获取 AddressBattle 实例的静态方法
    // 如果实例不存在，则创建一个新的实例；如果已存在，则返回现有的实例
    public static AddressBattle getInstance(){
        if(addressBattle == null){
            addressBattle = new AddressBattle();  // 创建唯一实例
        }
        return addressBattle;  // 返回实例
    }

    // 存储本地地址的变量，类型为 ImmutablePair<String, Integer>，用于存储 IP 和端口。
    private static ImmutablePair<String, Integer> ADDRESS_LOCAL;

    // 存储远程地址的变量，类型为 ImmutablePair<String, Integer>，用于存储 IP 和端口。
    private static ImmutablePair<String, Integer> ADDRESS_REMOTE;

    // 获取本地地址（IP 和端口）的方法
    public static ImmutablePair<String, Integer> getAddressLocal() {
        return ADDRESS_LOCAL;  // 返回本地地址
    }

    // 设置本地地址（IP 和端口）的方法
    public static void setAddressLocal(ImmutablePair<String, Integer> addressLocal) {
        ADDRESS_LOCAL = addressLocal;  // 更新本地地址
    }

    // 获取远程地址（IP 和端口）的方法
    public static ImmutablePair<String, Integer> getAddressRemote() {
        return ADDRESS_REMOTE;  // 返回远程地址
    }

    // 设置远程地址（IP 和端口）的方法
    public static void setAddressRemote(ImmutablePair<String, Integer> addressRemote) {
        ADDRESS_REMOTE = addressRemote;  // 更新远程地址
    }

    // 设置本地地址（IP 和端口），通过直接传入 IP 和端口参数来构建 ImmutablePair 对象
    public void setAddressLocal(String ip, int port) {
        ADDRESS_LOCAL = new ImmutablePair<String, Integer>(ip, port);  // 创建并更新本地地址
    }

    // 设置远程地址（IP 和端口），通过直接传入 IP 和端口参数来构建 ImmutablePair 对象
    public void setAddressRemote(String ip, int port) {
        ADDRESS_REMOTE = new ImmutablePair<String, Integer>(ip, port);  // 创建并更新远程地址
    }
}
