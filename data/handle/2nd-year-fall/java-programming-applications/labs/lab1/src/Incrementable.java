public class Incrementable {
    class StaticTest{
        static int i = 47;
    }
    public static void increment(){ StaticTest.i ++;}
    public static void main(String[] args){
        Incrementable.increment();
        System.out.println(StaticTest.i);
        Incrementable i = new Incrementable();
        Incrementable.StaticTest x = i.new StaticTest();
        x.i ++;
        System.out.println(x.i);
        Incrementable.StaticTest y = i.new StaticTest();
        y.i ++;
        System.out.println(y.i);
        Incrementable.StaticTest z = i.new StaticTest();
        z.i ++;
        System.out.println(z.i);
    }
}
