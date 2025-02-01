#include "NorS.h"
#include <iostream>

NorS::NorS(double num) : isNumber(true) {
    value.number = num;
}

NorS::NorS(char sym) : isNumber(false) {
    value.symbol = sym;
}

bool NorS::isNum() const {
    return isNumber;
}

double NorS::getNum() const {
    return value.number;
}

char NorS::getSym() const {
    return value.symbol;
}

std::ostream& operator<<(std::ostream& os, const NorS& ns) {
    if (ns.isNum()) {
        os << ns.getNum();
    } else {
        os << ns.getSym();
    }
    return os;
}