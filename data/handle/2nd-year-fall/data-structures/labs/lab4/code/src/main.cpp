#include <iostream>
#include <vector>
#include <queue>
#include <set>
#include <algorithm>

using namespace std;
const int N = 1005;
const int dir[4][2] = {{-1, 0}, {1, 0}, {0, -1}, {0, 1}};  // 上、下、左、右方向
int a[N][N];
int vis[N][N];
// 计算金属融化所需时间
int meltTime(int n, vector<string>& grid) {
    for (int i = 0; i < n; ++i) {
        for (int j = 0; j < n; ++j) {
            if(grid[i][j] == '_') a[i][j] = 0;
            else a[i][j] = 1;
        }
    }
    auto marjin = [&](int i,int j)->bool{
        if(i == 0 || i == n - 1 || j == 0 || j == n - 1) return 1;
        return 0;
    };
    auto check = [&](int i,int j)->bool {
        if(i < 0 || i >= n || j < 0 || j >= n) return 0;
        return 1;
    };
    auto bfs1 = [&](int i,int j)->void{
        queue<pair<int,int>> q;
        q.push({i,j});
        while(q.size()){
            int x = q.front().first, y = q.front().second;
            q.pop();
            a[x][y] = 2;
            for(int i = 0; i < 4; ++ i){
                int nx = x + dir[i][0], ny = y + dir[i][1];
                if(!check(nx,ny)) continue;
                if(a[nx][ny] == 2) continue;
                if(a[nx][ny] == 1) continue;
                q.push({nx,ny});
            }
        }
    };
    for(int i = 0; i < n; ++ i){
        for(int j = 0; j < n; ++ j){
            if(a[i][j] == 0 && marjin(i,j)){
                bfs1(i,j);
            }
        }
    }
    queue<pair<int,int>> q;
    for(int i = 0; i < n; ++ i){
        for(int j = 0; j < n; ++ j){
            if(a[i][j] == 1){
                int cnt = 0;
                for(int k = 0; k < 4; ++ k){
                    int ni = i + dir[k][0], nj = j + dir[k][1];
                    if(!check(ni,nj) || a[ni][nj] == 2) ++ cnt; 
                }
                if(cnt >= 2){
                    q.push({i,j});
                }
            }
        }
    }
    auto print = [&]()->void{
        for(int i = 0 ; i< n; ++ i){
            for(int j = 0 ; j < n; ++ j){
                if(a[i][j] == 2 || a[i][j] == 0) cout << ' ';
                if(a[i][j] == 1) cout << '#';
            }
            cout << endl;
        }
    };
    int t = 0;
    while(q.size()){
        ++ t;
        queue<pair<int,int>> qq;
        auto bfs2 = [&](int i,int j)->void{
            queue<pair<int,int>> q;
            q.push({i,j});
            while(q.size()){
                int x = q.front().first, y = q.front().second;
                q.pop();
                a[x][y] = 2;
                for(int i = 0; i < 4; ++ i){
                    int nx = x + dir[i][0], ny = y + dir[i][1];
                    if(!check(nx,ny)) continue;
                    if(a[nx][ny] == 2) continue;
                    if(a[nx][ny] == 1){
                        qq.push({nx,ny});
                    }else{
                        q.push({nx,ny});
                    }
                }
            }
        };
        while(q.size()){
            int x = q.front().first, y = q.front().second;
            // cout << t << ' '<< x<<' '<<y<<endl;
            q.pop();
            bfs2(x, y);
        }
        while(qq.size()){
            int x = qq.front().first, y = qq.front().second;
            qq.pop();
            if(a[x][y]!=1) continue;
            int cnt = 0;
            for(int i = 0; i < 4; ++ i){
                int nx = x + dir[i][0], ny = y + dir[i][1];
                if(!check(nx,ny) || a[nx][ny] == 2) ++cnt;
            }
            if(cnt >= 2){
                q.push({x,y});
                a[x][y] = 2;
            }
        }
        // cout << "t:" << t << endl;
        // print();
    }
    return t;
}

int main() {
    // freopen("D:\\Code\\Projects\\Project-Assignment\\data-structures\\lab4\\code\\src\\input5.txt","r",stdin);
    // freopen("output.txt","w",stdout);
    int n;
    cin >> n;
    cout<<n<<endl;
    vector<string> grid(n + 1);
    for(int i = 0; i < n; ++ i){
        cin >> grid[i];
        // cout<<grid[i]<<endl;
    }
    cout << meltTime(n, grid) << endl;
    return 0;
}
