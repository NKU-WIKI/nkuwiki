#include<bits/stdc++.h>

using namespace std;
const int N = 105;
int n, m, k;
int a[N];
int main(){
    cin >> n >> m >> k;
    int ans = 0;
    int tot = 0;
    for(int i = 0; i < n; ++ i){
        int x = 0;
        int cnt = 0;
        for(int j = 0; j < m ; ++ j){
            char ch;
            cin >> ch;
            x <<= 1;
            if(ch == '1'){
                x |= 1;
                ++ cnt;
            }
        }
        if(k >= m - cnt && (k&1) == ((m - cnt) & 1))
            a[tot++] = x;
    }
    sort(a, a + tot);
    int cnt = 0;
    for(int i = 0; i < tot; ++ i){
        if(i == 0){
            ++ cnt;
        }else{
            if(a[i] ^ a[i - 1]){
                ans = max(ans, cnt);
                cnt = 1;
            }
            else
                ++ cnt;
            }
        }
    ans = max(ans, cnt);
    cout << ans << endl;
    return 0;
}
/*
6 5 3
1 0 0 1 0
1 1 0 0 0
0 1 1 1 0
0 0 0 1 1
1 0 1 0 1
1 1 0 0 0
*/