#ifndef STACK_H
#define STACK_H

#include "NorS.h" // 包含 NorS 的完整定义

class stack {
private:
    struct Node {
        NorS value;
        Node* next;
    };
    Node* topNode;
    int length;

public:
    stack();
    ~stack();
    void init();
    bool empty() const;
    void push(const NorS& c);
    NorS pop();
    NorS gettop() const;
    int getsize() const;
};

#endif // STACK_H