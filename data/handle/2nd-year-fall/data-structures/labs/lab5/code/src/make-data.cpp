#include<bits/stdc++.h>

using namespace std;

int main(){
    freopen("in2.txt","w",stdout);
    srand(time(0));
    int n = 100, m = 4, k = 2;
    cout << n << ' ' << m <<' '<< k << endl;
    for(int i = 0; i < n; ++ i){
        string s = "";
        for(int j  = 0; j < m; ++ j){
            if(rand()%2==1) s += "0";
            else s += "1";
        }
        cout << s << endl;
    }
}