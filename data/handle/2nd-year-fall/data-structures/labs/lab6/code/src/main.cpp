#include <bits/stdc++.h>

using namespace std;

const int mod = 3119;  // 哈希表大小，使用质数

// 哈希表类模板
template <class T, class Hash = std::hash<T>>
class Hash_Table {
private:
    T str[mod];            // 哈希表的数组存储元素
    int counter, num;      // counter 统计哈希表操作次数，num 统计插入/查找的次数
    Hash h;                // 哈希函数对象，默认使用 std::hash<T>
public:
    Hash_Table() : counter(0), num(0) {
        fill(begin(str), end(str) - 1, ""); // 初始化哈希表为空字符串
    }

    // 插入方法，使用二次探测解决冲突
    void insert(const T &x) {
        int H = h(x) % mod; // 计算哈希值并取模使其适配表大小
        for (int i = 0; ; ++i) {  // 二次探测解决冲突
            if (str[(H + i * i) % mod] == "" || str[(H + i * i) % mod] == x) {
                H = (H + i * i) % mod; // 更新哈希位置
                break;
            }
        }
        str[H] = x; // 将元素插入到计算出来的位置
    }

    // 查找方法，使用二次探测
    void find(const T &x) {
        int H = h(x) % mod; // 计算哈希值用于查找
        ++num;               // 增加查找次数
        ++counter;           // 增加操作次数（探测次数）
        for (int i = 0; ; ++i, ++counter) { // 二次探测
            if (str[(H + i * i) % mod] == x) { // 如果找到元素，跳出
                H = (H + i * i) % mod;
                break;
            }
            else if (str[(H + i * i) % mod] == "") // 如果遇到空槽，跳出
                break;
        }
    }

    // 计算平均探测次数
    double ave() { 
        return (double)counter / num; // 计算平均探测次数
    }
};

// Hash1 哈希函数
class Hash1 {
public:
    size_t operator()(const std::string &x) {
        size_t res = 0;  // 初始化结果变量为 0
        for(int i = 0; i < x.length(); ++i) {  // 遍历每个字符
            res = (1ll * res * 131 + x[i]) % mod;  // 使用多项式滚动哈希方法更新哈希值
        }
        return res;  // 返回计算出的哈希值
    }
};

// Hash2 哈希函数
class Hash2 {
public:
    size_t operator()(const std::string &x) {
        size_t res = 1;  // 初始化结果变量为 1
        for(int i = 0; i < x.length(); ++i) {  // 遍历每个字符
            res = (1ll * res * x[i]) % mod;  // 使用字母乘积哈希方法更新哈希值
        }
        return res;  // 返回计算出的哈希值
    }
};

// 文件读取函数：读取文件内容并返回一个字符串
string read_file(const string &filename) {
    ifstream file(filename);  // 创建文件输入流
    if (!file.is_open()) {
        cerr << "无法打开文件: " << filename << endl;
        exit(1);  // 文件无法打开，程序退出
    }
    
    stringstream buffer;
    buffer << file.rdbuf();  // 读取文件内容到缓冲区
    return buffer.str();  // 返回文件内容的字符串
}

// 主程序：输入两篇文章，插入并查找单词
int main() {
    ios::sync_with_stdio(false);  // 提高输入输出效率

    // 读取文件内容
    string article1 = read_file("article1.txt");  // 读取第一篇文章
    string article2 = read_file("article2.txt");  // 读取第二篇文章

    // 分割字符串为单词
    auto split_words = [](const string &text) {
        vector<string> words;
        stringstream ss(text);
        string word;
        while (ss >> word) {
            words.push_back(word);
        }
        return words;
    };
    // 使用 Hash1 实现哈希表
    Hash_Table<string, Hash1> table1;
    auto words1 = split_words(article1);  // 分割文章1为单词
    for (const auto &word : words1) {
        table1.insert(word);  // 将单词插入哈希表
    }
   
    int find_count1 = 0;
    auto words2 = split_words(article2);  // 分割文章2为单词
    for (const auto &word : words2) {
        table1.find(word);  // 查找文章2中的单词
        ++find_count1;
    }
    // // 输出使用 Hash1 的平均探测次数
    cout << "Hash1 平均探测次数: " << table1.ave() << endl;

    // // 使用 Hash2 实现哈希表
    Hash_Table<string, Hash2> table2;
    for (const auto &word : words1) {
        table2.insert(word);  // 将单词插入哈希表
    }

    int find_count2 = 0;
    for (const auto &word : words2) {
        table2.find(word);  // 查找文章2中的单词
        ++find_count2;
    }

    // // 输出使用 Hash2 的平均探测次数
    cout << "Hash2 平均探测次数: " << table2.ave() << endl;

    return 0;
}
