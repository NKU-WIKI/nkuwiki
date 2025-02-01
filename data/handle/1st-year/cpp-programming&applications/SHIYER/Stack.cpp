#include "Stack.h"
#include "NorS.h"
#include <stdexcept>

stack::stack() : topNode(nullptr), length(0) {}

stack::~stack() {
    while (!empty()) {
        pop();
    }
}

void stack::init() {
    while (!empty()) {
        pop();
    }
}

bool stack::empty() const {
    return topNode == nullptr;
}

void stack::push(const NorS& c) {
    Node* newNode = new Node{c, topNode};
    topNode = newNode;
    length++;
}

NorS stack::pop() {
    if (empty()) {
        throw std::runtime_error("Stack is empty");
    }
    Node* temp = topNode;
    NorS topValue = topNode->value;
    topNode = topNode->next;
    delete temp;
    length--;
    return topValue;
}

NorS stack::gettop() const {
    if (empty()) {
        throw std::runtime_error("Stack is empty");
    }
    return topNode->value;
}

int stack::getsize() const {
    return length;
}