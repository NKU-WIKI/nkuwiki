public class Vampire {
    public static void main(String[] args) {
        for(int i = 1000; i <= 9999; ++ i){
            int[] a = new int[]{i % 10, i / 10 % 10, i / 100 % 10, i / 1000 % 10};
            boolean fg = false;
            if(a[0] + a[1] > 0){
                for(int j = 0; j < 4 && !fg; ++ j){
                    int x = a[j];
                    for(int k = 0; k < 4; ++ k){
                        if(k == j) continue;
                        x = x * 10 + a[k];
                        int[] y = new int[2];
                        int cnt = 0;
                        for(int g = 0; g < 4; ++ g){
                            if(g == j || g == k) continue; 
                            y[cnt ++] = a[g];
                        }
                        int[] z = new int[]{y[0] * 10 + y[1], y[1] * 10 + y[0]};
                        if(x * z[0] == i || x * z[1] == i){
                            fg = true;
                            break;
                        }
                    }
                }
            }
            if(fg) System.out.print(i + " ");
        }
    }
}
