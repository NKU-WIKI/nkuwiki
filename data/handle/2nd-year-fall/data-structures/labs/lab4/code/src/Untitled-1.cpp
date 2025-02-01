#include <bits/stdc++.h>

const int N = 1010;
const std::pair<int, int> d[] = {{0, 1}, {0, -1}, {1, 0}, {-1, 0}};
std::pair<int, int> operator + (const std::pair<int, int>&x, const std::pair<int, int>&y) 
{ return std::make_pair(x.first + y.first, x.second + y.second); }
int ans[N][N], num[N][N], n;
bool vis[N][N];
char ch[N][N];

bool chk_in(std::pair<int, int> x) { return x.first > 0 && x.first <= n && x.second > 0 && x.second <= n; }
char get_ch(std::pair<int, int> x) { return ch[x.first][x.second]; }
int& get_ans(std::pair<int, int> x) { return ans[x.first][x.second]; }
bool& get_vis(std::pair<int, int> x) { return vis[x.first][x.second]; }
int& get_num(std::pair<int, int> x) { return num[x.first][x.second]; }

int solve(void) {
std::deque<std::pair<int, int> > q;
for(int i = 1; i <= n; ++i)
q.push_back(std::make_pair(i, 0)),
q.push_back(std::make_pair(0, i)),
q.push_back(std::make_pair(n + 1, 0)),
q.push_back(std::make_pair(0, n + 1));
int res = 0;
while(!q.empty()) {
 std::pair<int, int> now = q.front(); q.pop_front();
for(int i = 0; i < 4; ++i) {
 std::pair<int, int> nxt = now + d[i];
if(get_ch(nxt) == '_' && !get_vis(nxt))
 q.push_front(nxt), get_vis(nxt) = 1;
else if(get_ch(nxt) == '#' && !get_ans(nxt))
if(++get_num(nxt) == 2)
 get_ans(nxt) = get_ans(now) + 1,
 q.push_back(nxt);
 res = std::max(res, get_ans(now));
 }
} return res;
}

int main(void) {
     freopen("D:\\Code\\Projects\\Project-Assignment\\data-structures\\lab4\\code\\src\\input5.txt","r",stdin);
std::cin >> n;
for(int i = 1; i <= n; ++i)
 std::cin >> ch[i] + 1;
std::cout << solve() << std::endl;
 return 0;
}