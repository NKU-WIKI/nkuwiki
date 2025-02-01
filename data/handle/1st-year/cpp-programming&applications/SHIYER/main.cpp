#include <iostream>
#include <string>
#include <vector>
#include <cctype>
#include "Stack.h"
#include "NorS.h"
#include <stdexcept>

using namespace std;

// 声明辅助函数
bool is_operator(const string& token);
bool is_unary_minus(const string& token);
bool is_invalid_token(const string& token);
int precedence(char op);

// 词法分析，将输入字符串分解成tokens
vector<string> tokenize(const string& expr) {
    vector<string> tokens;
    for (size_t i = 0; i < expr.length(); ++i) {
        if (isspace(expr[i])) continue;
        if (isdigit(expr[i]) || (expr[i] == '.' && i + 1 < expr.length() && isdigit(expr[i + 1]))) {
            size_t j = i;
            while (j < expr.length() && (isdigit(expr[j]) || expr[j] == '.')) ++j;
            tokens.push_back(expr.substr(i, j - i));
            i = j - 1;
        } else if (isalpha(expr[i])) {
            size_t j = i;
            while (j < expr.length() && isalpha(expr[j])) ++j;
            tokens.push_back(expr.substr(i, j - i));
            i = j - 1;
        } else {
            tokens.push_back(string(1, expr[i]));
        }
    }
    return tokens;
}

// 检查表达式的合法性
bool is_valid_expression(const vector<string>& tokens) {
    stack parentheses;
    for (size_t i = 0; i < tokens.size(); ++i) {
        const string& token = tokens[i];
        if (token == "(") {
            parentheses.push(NorS('('));
        } else if (token == ")") {
            if (parentheses.empty()) return false;
            parentheses.pop();
        } else if (is_operator(token) && (i == 0 || i == tokens.size() - 1 || is_operator(tokens[i - 1]) || is_operator(tokens[i + 1]))) {
            return false;
        } else if (is_unary_minus(token) && (i == 0 || is_operator(tokens[i - 1]) || tokens[i - 1] == "(")) {
            continue;
        } else if (is_invalid_token(token)) {
            return false;
        }
    }
    return parentheses.empty();
}

// 判断是否为运算符
bool is_operator(const string& token) {
    return token == "+" || token == "-" || token == "*" || token == "/";
}

// 判断是否为单目减号
bool is_unary_minus(const string& token) {
    return token == "-";
}

// 判断是否为无效的token
bool is_invalid_token(const string& token) {
    return token == "@" || token == "++" || token == "--";
}

// 运算符优先级
int precedence(char op) {
    switch (op) {
        case '+':
        case '-': return 1;
        case '*':
        case '/': return 2;
        default: return 0;
    }
}

// 计算表达式的值
double evaluate_expression(const vector<string>& tokens) {
    stack values;
    stack operators;

    for (const auto& token : tokens) {
        if (isdigit(token[0]) || (token[0] == '-' && token.length() > 1)) {
            values.push(NorS(stod(token)));
        } else if (isalpha(token[0])) {
            if (token == "x") values.push(NorS(0.0));
            else if (token == "y") values.push(NorS(0.0));
            else throw runtime_error("Unknown variable: " + token);
        } else if (token == "(") {
            operators.push(NorS('('));
        } else if (token == ")") {
            while (!operators.empty() && operators.gettop().getSym() != '(') {
                char op = operators.pop().getSym();
                double b = values.pop().getNum();
                double a = values.pop().getNum();
                switch (op) {
                    case '+': values.push(NorS(a + b)); break;
                    case '-': values.push(NorS(a - b)); break;
                    case '*': values.push(NorS(a * b)); break;
                    case '/': values.push(NorS(a / b)); break;
                }
            }
            if (operators.empty()) throw runtime_error("Mismatched parentheses");
            operators.pop();
        } else {
            while (!operators.empty() && precedence(operators.gettop().getSym()) >= precedence(token[0])) {
                char op = operators.pop().getSym();
                double b = values.pop().getNum();
                double a = values.pop().getNum();
                switch (op) {
                    case '+': values.push(NorS(a + b)); break;
                    case '-': values.push(NorS(a - b)); break;
                    case '*': values.push(NorS(a * b)); break;
                    case '/': values.push(NorS(a / b)); break;
                }
            }
            operators.push(NorS(token[0]));
        }
    }

    while (!operators.empty()) {
        char op = operators.pop().getSym();
        double b = values.pop().getNum();
        double a = values.pop().getNum();
        switch (op) {
            case '+': values.push(NorS(a + b)); break;
            case '-': values.push(NorS(a - b)); break;
            case '*': values.push(NorS(a * b)); break;
            case '/': values.push(NorS(a / b)); break;
        }
    }

    return values.pop().getNum();
}

int main() {
    string expr;
    //getline(cin, expr);
    expr = "3 + 4 * (2 – 1)+";
    vector<string> tokens = tokenize(expr);
    if (!is_valid_expression(tokens)) {
        cout << "False" << endl;
        return 0;
    }

    try {
        double result = evaluate_expression(tokens);
        cout << "True" << endl;
        cout << result << "+x+0*y" << endl;
        cout << result << "+x" << endl;
    } catch (const runtime_error& e) {
        cout << "False" << endl;
    }

    return 0;
}