#include <iostream>
#include <fstream>
#include <string>
#include <unordered_map>
#include <vector>
#include <cctype>
#include <algorithm>

// 位置链表节点
struct Position {
    int fileId;       // 文件ID
    int lineNumber;   // 行号
    int columnNumber; // 列号，记录的是单词首字母的列号
    Position* next;   // 下一节点
// 构造函数，初始化成员变量
    Position(int fid, int line, int col) : fileId(fid), lineNumber(line), columnNumber(col), next(nullptr) {}
    
    ~Position() {
        delete next;  // 递归删除链表中的下一个节点
    }
};

// 保存单词及其索引信息
struct WordInfo {
    std::string word;  // 单词
    int frequency;     // 单词频次
    Position* head;    // 位置链表头指针
    Position* tail;    // 位置链表尾指针
    int dictRank;      // 字典序排名
    int freqRank;      // 频次排名

    WordInfo(std::string w, int fid, int line, int col) : word(w), frequency(1), dictRank(0), freqRank(0) {
        head = new Position(fid, line, col); // 记录单词首字母的列号
        tail = head;  // 初始化时头尾指针都指向同一个节点
    }

    // 添加位置到链表
    void addPosition(int fid, int line, int col) {
        Position* newPos = new Position(fid, line, col); // 记录单词首字母的列号
        tail->next = newPos;  // 使用尾指针直接添加到链表末尾
        tail = newPos;        // 更新尾指针
    }

    ~WordInfo() {
        delete head;  // 删除链表
    }
};

// 动态索引表
class IndexTable {
private:
    std::unordered_map<std::string, WordInfo*> wordMap;  // 使用unordered_map加速单词查找
    std::vector<WordInfo*> wordList;  // 按顺序存储单词信息，用于排序

public:
    // 添加单词，动态更新索引
    void addWord(const std::string& rawWord, int fid, int line, int startCol) {
        std::string word = rawWord;
        // 将单词转换为小写
        std::transform(word.begin(), word.end(), word.begin(), ::tolower);  

        if (word.empty()) return;  // 忽略空词项

        // 查找单词是否已经存在
        auto it = wordMap.find(word);
        if (it != wordMap.end()) {
            // 单词已存在，更新频次和位置
            it->second->frequency++;
            it->second->addPosition(fid, line, startCol); // 添加单词出现位置
        } else {
            // 新单词，插入unordered_map
            WordInfo* newWord = new WordInfo(word, fid, line, startCol); // 记录首字母的列号
            wordMap[word] = newWord;
            wordList.push_back(newWord);
        }

        // 更新排名
        updateRankings();
    }

    // 更新所有单词的字典序和频次排名
    void updateRankings() {
        // 字典序排名
        std::sort(wordList.begin(), wordList.end(), [](WordInfo* a, WordInfo* b) {
            return a->word < b->word;
        });

        for (size_t i = 0; i < wordList.size(); ++i) {
            wordList[i]->dictRank = i + 1; // 字典序排名从1开始
        }

        // 频次排名
        std::sort(wordList.begin(), wordList.end(), [](WordInfo* a, WordInfo* b) {
            return a->frequency > b->frequency; // 从高到低排序
        });

        for (size_t i = 0; i < wordList.size(); ++i) {
            wordList[i]->freqRank = i + 1; // 频次排名从1开始
        }

        // 恢复字典序排序以便输出
        std::sort(wordList.begin(), wordList.end(), [](WordInfo* a, WordInfo* b) {
            return a->word < b->word;
        });
    }

    // 按字母顺序打印索引表到文件
    void printIndexTable(const std::string& outputFile) {
        std::ofstream out(outputFile);
        if (!out) {
            std::cerr << "Error opening output file: " << outputFile << std::endl;
            return;
        }

        for (const auto& info : wordList) {
            out << info->word << ";" 
                << info->frequency << ";";
            
            Position* pos = info->head;
            while (pos != nullptr) {
                out << "(" << pos->fileId << "," << pos->lineNumber << "," << pos->columnNumber << ")";
                pos = pos->next;
                out << ";";  
            }
            out << std::endl;
        }
        out.close();
    }

    // 析构函数
    ~IndexTable() {
        for (auto& pair : wordMap) {
            delete pair.second;  // 释放动态分配的WordInfo对象
        }
    }
};

int main(int argc, char* argv[]) {
    if (argc < 2) {
        std::cerr << "Usage: " << "main" << " <input_file1> <input_file2> ..." << std::endl;
        return 1;
    }

    IndexTable indexTable;
    for (int i = 1; i < argc; ++i) {
        std::ifstream file(argv[i]);
        if (!file) {
            std::cerr << "Error opening input file: " << argv[i] << std::endl;
            return 1;
        }

        std::string word;
        int lineNumber = 1;
        int columnNumber = 0;
        char ch;
        int fileId = i;  // 文件ID从1开始

        // 逐字符读取文件以处理换行符
        while (file.get(ch)) {
            if (!std::isalpha(ch)) {
                // 如果当前已经有一个单词积累，处理它
                columnNumber++;
                if (!word.empty()) {
                    indexTable.addWord(word, fileId, lineNumber, columnNumber - word.length()); // 使用单词首字母的列号
                    word.clear();  // 清空单词
                }
                if (ch == '\n') {
                    lineNumber++;
                    columnNumber = 0;  // 新行从列号0开始
                } 
            } else {
                word += ch; // 将字符添加到单词中
                columnNumber++;
            }
        }
        // 处理文件结束时剩余的单词
        if (!word.empty()) {
            indexTable.addWord(word, fileId, lineNumber, columnNumber - word.length());
        }

        // 输出文件命名为 out1.txt, out2.txt 等
        std::string outputFile = "out" + std::to_string(i) + ".txt";
        indexTable.printIndexTable(outputFile);
    }

    return 0;
}
