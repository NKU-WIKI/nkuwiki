public class Fibonacci {
    public static void main(String[] args) {
        int n = Integer.parseInt(args[0]);
        int a = 1, b = 1;
        for(int i = 1; i <= n; ++ i){
            if(i <= 2){
                System.out.print(a);
                if(i != n) System.out.print("、");
                continue;
            }
            int c = a + b;
            a = b;
            b = c;
            System.out.print(b);
            if(i != n) System.out.print("、");
        }
    }
}
