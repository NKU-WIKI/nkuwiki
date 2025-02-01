#include <iostream>
#include <fstream>
#include <string>
#include <cstring>
#include "BTree.h"

// void usage(char *prompt = nullptr) {
//     if (prompt)
//         std::cerr << prompt << ",";
//     std::cerr << "---------------------------------------" << std::endl;
//     std::cerr << "windows : --input *.*" << std::endl;
//     std::cerr << "linux   : ./* --input *.*" << std::endl;
//     std::cerr << "其中 *.* 为数据文件名, ./* 表示执行该程序" << std::endl;
//     std::cerr << "---------------------------------------" << std::endl;
// }

inline void Trim(char* str, unsigned len) {
    if (!str || !*str)
        return;

    char* p = str, * q = &str[len - 1];
    while (*p && (*p == ' ' || *p == '\t' || *p == '\n' || *p == '\r'))
        ++p;
    while (*q == ' ' || *q == '\t' || *q == '\n' || *q == '\r')
        --q;
    *(++q) = 0;
    memmove(str, p, q - p + 1);
    return;
}

inline void ClearState(std::istream& fin) {
    if (fin.eof())
        return;
    if (fin.fail())
        fin.clear();
    return;
}

void ReadSpace(std::istream& fin) {
    if (fin.eof())
        return;
    ClearState(fin);
    while (fin.peek() == '\t' || fin.peek() == ' ')
        fin.get();
    ClearState(fin);
    return;
}

void ClearLine(std::istream& fin) {
    if (fin.eof())
        return;
    ClearState(fin);
    fin.ignore(INT16_MAX, '\n');
    if (fin.peek() == '\r' || fin.peek() == '\n')
        fin.get();
    ClearState(fin);
    return;
}

template <typename KeyType>
void Test(BTree<KeyType> &t, std::istream &fin) {
    const char* ord = "m";
    const char* ins = "insert";
    const char* del = "delete";
    const char* sea = "find";
    bool OrderSeted = false;
    char OpeCmd[16];

    while (!fin.eof()) {
        if (!(fin.getline(OpeCmd, sizeof(OpeCmd), ' '))) {
            ClearLine(fin);
            continue;
        }
        Trim(OpeCmd, strlen(OpeCmd));
        if (OpeCmd[0] == '#') {
            ClearLine(fin);
            continue;
        }
        if (!strncmp(OpeCmd, ord, 1)) {
            int m;
            if (!(fin >> m)) {
                ClearLine(fin);
                continue;
            }
            if (!OrderSeted) {
                BTree<KeyType>::SetOrder(m);
                OrderSeted = true;
            }
            ClearLine(fin);
        }
        else if (!strncmp(OpeCmd, ins, 6)) {
            int key;
            if (!(fin >> key)) {
                ClearLine(fin);
                continue;
            }
            if (t.Insert(key) == BTree<KeyType>::EXISTED) {
                std::cout << "关键字 " << key << " 已存在，插入失败" << std::endl;
            } else {
                t.FormatPrint((std::string("插入") + std::to_string(key) + "后的B-Tree").c_str());
            }
            ClearLine(fin);
        }
        else if (!strncmp(OpeCmd, del, 6)) {
            int key;
            if (!(fin >> key)) {
                ClearLine(fin);
                continue;
            }
            if (t.Delete(key) == BTree<KeyType>::NOTFOUND) {
                std::cout << "关键字 " << key << " 不存在，删除失败" << std::endl;
            } else {
                t.FormatPrint((std::string("删除") + std::to_string(key) + "后的B-Tree").c_str());
            }
            ClearLine(fin);
        }
        else if (!strncmp(OpeCmd, sea, 4)) {
            int key;
            if (!(fin >> key)) {
                ClearLine(fin);
                continue;
            }
            if (!t.Search(key).tag) {
                std::cout << "关键字 " << key << " 不存在，查找失败" << std::endl;
            } else {
                t.SearchPath((std::string("查找") + std::to_string(key) + "的路径").c_str());
                std::cout << std::endl;
            }
            ClearLine(fin);
        }
        else {
            ClearLine(fin);
        }
    }
}

int main() {
    BTree<int> t;
    Test(t, std::cin);
    return 0;
}
