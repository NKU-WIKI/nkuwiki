#ifndef NORS_H
#define NORS_H

#include <string>
#include <cctype>

class NorS {
private:
    union {
        double number;
        char symbol;
    } value;
    bool isNumber;

public:
    NorS(double num);
    NorS(char sym);
    bool isNum() const;
    double getNum() const;
    char getSym() const;

    // 添加别名方法
    double getDouble() const { return getNum(); }
    char getChar() const { return getSym(); }

    friend std::ostream& operator<<(std::ostream& os, const NorS& ns);
};

#endif // NORS_H