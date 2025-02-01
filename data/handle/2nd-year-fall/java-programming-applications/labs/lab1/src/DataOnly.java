public class DataOnly {
    int i;
    double d;
    boolean b;

    public DataOnly(int i, double d, boolean b){
        this.i = i;
        this.d = d;
        this.b = b;
    }
    public static void main(String[] arg){
        DataOnly x = new DataOnly(0, 0.0, false);
        System.out.println(x.i);
        System.out.println(x.d);
        System.out.println(x.b);
    }
}
