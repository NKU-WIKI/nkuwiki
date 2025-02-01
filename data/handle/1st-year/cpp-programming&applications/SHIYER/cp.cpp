#include <stdio.h>
#include <stdlib.h>

// 多项式的项结构体
typedef struct PolyNode {
    int coef; // 系数
    int exp; // 指数
    struct PolyNode* next;
} PolyNode;

// 创建多项式
PolyNode* createPolynomial() {
    PolyNode* head = (PolyNode*)malloc(sizeof(PolyNode));
    head->next = NULL;
    PolyNode* rear = head;
    int coef, exp;
    printf("输入多项式的系数和指数，以系数为 0 结束输入：\n");
    while (1) {
        scanf("%d%d", &coef, &exp);
        if ((coef == 0)) break;
        PolyNode* newNode = (PolyNode*)malloc(sizeof(PolyNode));
        newNode->coef = coef;
        newNode->exp = exp;
        newNode->next = NULL;
        rear->next = newNode;
        rear = newNode;
    }
    return head;
}

// 打印多项式
void printPolynomial(PolyNode* head) {
    if (head == NULL) {
        printf("0\n");
        return;
    }
    PolyNode* p = head;
    while (p != NULL) {
        if (p != head && p->coef > 0) printf("+");
        if (p->coef == 0) {
            printf("0");
        } else if (p->exp == 0) {
            printf("%d", p->coef);
        } else if (p->exp == 1) {
            printf("%dx", p->coef);
        } else {
            printf("%dx^%d", p->coef, p->exp);
        }
        p = p->next;
    }
    printf("\n");
}

// 销毁多项式
void destroyPolynomial(PolyNode* head) {
    PolyNode* p = head;
    while (p!= NULL) {
        PolyNode* temp = p;
        p = p->next;
        free(temp);
    }
}

// 多项式相加
PolyNode* addPolynomial(PolyNode* poly1, PolyNode* poly2) {
    PolyNode* result = (PolyNode*)malloc(sizeof(PolyNode));
    result->next = NULL;
    PolyNode* rear = result;
    PolyNode* p1 = poly1->next;
    PolyNode* p2 = poly2->next;
    while (p1!= NULL && p2!= NULL) {
        PolyNode* newNode = (PolyNode*)malloc(sizeof(PolyNode));
        if (p1->exp > p2->exp) {
            newNode->coef = p1->coef;
            newNode->exp = p1->exp;
            p1 = p1->next;
        } else if (p1->exp < p2->exp) {
            newNode->coef = p2->coef;
            newNode->exp = p2->exp;
            p2 = p2->next;
        } else {
            newNode->coef = p1->coef + p2->coef;
            newNode->exp = p1->exp;
            p1 = p1->next;
            p2 = p2->next;
        }
        newNode->next = NULL;
        rear->next = newNode;
        rear = newNode;
    }
    while (p1!= NULL) {
        PolyNode* newNode = (PolyNode*)malloc(sizeof(PolyNode));
        newNode->coef = p1->coef;
        newNode->exp = p1->exp;
        newNode->next = NULL;
        rear->next = newNode;
        rear = newNode;
        p1 = p1->next;
    }
    while (p2!= NULL) {
        PolyNode* newNode = (PolyNode*)malloc(sizeof(PolyNode));
        newNode->coef = p2->coef;
        newNode->exp = p2->exp;
        newNode->next = NULL;
        rear->next = newNode;
        rear = newNode;
        p2 = p2->next;
    }
PolyNode* current = result;
while (current != NULL) {
    PolyNode** ptr = &current->next; // 使用指针的指针来更新next指针
    PolyNode* next = current->next;
    while (next != NULL) {
        if (current->exp == next->exp) {
            current->coef += next->coef;
            *ptr = next->next; // 更新指针
            free(next);
            next = *ptr; // 移动到下一个节点
        } else {
            ptr = &next->next; // 移动指针到下一个节点
            next = next->next;
        }
    }
    current = current->next; // 移动到current的下一个节点
}
return result;
}

// 多项式相减
PolyNode* subtractPolynomial(PolyNode* poly1, PolyNode* poly2) {
    PolyNode* result = (PolyNode*)malloc(sizeof(PolyNode));
    result->next = NULL;
    PolyNode* rear = result;
    PolyNode* p1 = poly1->next;
    PolyNode* p2 = poly2->next;
    while (p1!= NULL && p2!= NULL) {
        PolyNode* newNode = (PolyNode*)malloc(sizeof(PolyNode));
        if (p1->exp > p2->exp) {
            newNode->coef = p1->coef;
            newNode->exp = p1->exp;
            p1 = p1->next;
        } else if (p1->exp < p2->exp) {
            newNode->coef = -p2->coef;
            newNode->exp = p2->exp;
            p2 = p2->next;
        } else {
            newNode->coef = p1->coef - p2->coef;
            newNode->exp = p1->exp;
            p1 = p1->next;
            p2 = p2->next;
        }
        newNode->next = NULL;
        rear->next = newNode;
        rear = newNode;
    }
    while (p1!= NULL) {
        PolyNode* newNode = (PolyNode*)malloc(sizeof(PolyNode));
        newNode->coef = p1->coef;
        newNode->exp = p1->exp;
        newNode->next = NULL;
        rear->next = newNode;
        rear = newNode;
        p1 = p1->next;
    }
    while (p2!= NULL) {
        PolyNode* newNode = (PolyNode*)malloc(sizeof(PolyNode));
        newNode->coef = -p2->coef;
        newNode->exp = p2->exp;
        newNode->next = NULL;
        rear->next = newNode;
        rear = newNode;
        p2 = p2->next;
    }
PolyNode* current = result;
while (current != NULL) {
    PolyNode** ptr = &current->next; // 使用指针的指针来更新next指针
    PolyNode* next = current->next;
    while (next != NULL) {
        if (current->exp == next->exp) {
            current->coef += next->coef;
            *ptr = next->next; // 更新指针
            free(next);
            next = *ptr; // 移动到下一个节点
        } else {
            ptr = &next->next; // 移动指针到下一个节点
            next = next->next;
        }
    }
    current = current->next; // 移动到current的下一个节点
}
    return result;
}
PolyNode* createNode(int coef, int exp) {
    PolyNode* newNode = (PolyNode*)malloc(sizeof(PolyNode));
    if (newNode == NULL) {
        printf("Memory allocation failed.\n");
        exit(1);
    }
    newNode->coef = coef;
    newNode->exp = exp;
    newNode->next = NULL;
    return newNode;
}

// 将两个多项式相乘并返回结果多项式
PolyNode* multiplyPolynomial(PolyNode* poly1, PolyNode* poly2) {
    if (poly1 == NULL || poly2 == NULL) return NULL;

    PolyNode* result = NULL; // 创建一个哑头节点
    PolyNode* tail = NULL;

    PolyNode* p1 = poly1->next;
    while (p1 != NULL) {
        PolyNode* p2 = poly2->next;
        while (p2 != NULL) {
            int newCoef = p1->coef * p2->coef;
            int newExp = p1->exp + p2->exp;
            PolyNode* newNode = createNode(newCoef, newExp);

            // 将新节点插入到结果多项式的末尾
            if (result == NULL) {
                result = newNode;
                tail = newNode;
            } else {
                tail->next = newNode;
                tail = newNode;
            }
            p2 = p2->next;
        }
        p1 = p1->next;
    }

    // 合并同类项
PolyNode* current = result;
while (current != NULL) {
    PolyNode** ptr = &current->next; // 使用指针的指针来更新next指针
    PolyNode* next = current->next;
    while (next != NULL) {
        if (current->exp == next->exp) {
            current->coef += next->coef;
            *ptr = next->next; // 更新指针
            free(next);
            next = *ptr; // 移动到下一个节点
        } else {
            ptr = &next->next; // 移动指针到下一个节点
            next = next->next;
        }
    }
    current = current->next; // 移动到current的下一个节点
}

    return result;
}


// 多项式求商和余式
void dividePolynomial(PolyNode* poly1, PolyNode* poly2, PolyNode** quotient, PolyNode** remainder) {
    *quotient = (PolyNode*)malloc(sizeof(PolyNode));
    (*quotient)->next = NULL;
    *remainder = poly1;
    PolyNode* qRear = *quotient;
    PolyNode* dividend = *remainder;
    PolyNode* divisor = poly2;
    while (dividend->next!= NULL && dividend->next->exp >= divisor->next->exp) {
        PolyNode* newNode = (PolyNode*)malloc(sizeof(PolyNode));
        newNode->coef = dividend->next->coef / divisor->next->coef;
        newNode->exp = dividend->next->exp - divisor->next->exp;
        newNode->next = NULL;
        qRear->next = newNode;
        qRear = newNode;
        PolyNode* tempDivisor = divisor;
        PolyNode* tempDividend = dividend;
        PolyNode* tempResult = (PolyNode*)malloc(sizeof(PolyNode));
        tempResult->next = NULL;
        PolyNode* tempRear = tempResult;
        while (tempDivisor!= NULL) {
            int coef = newNode->coef * tempDivisor->next->coef;
            int exp = newNode->exp + tempDivisor->next->exp;
            PolyNode* newTempNode = (PolyNode*)malloc(sizeof(PolyNode));
            newTempNode->coef = coef;
            newTempNode->exp = exp;
            newTempNode->next = NULL;
            tempRear->next = newTempNode;
            tempRear = newTempNode;
            tempDivisor = tempDivisor->next;
        }
        PolyNode* temp = tempDividend->next;
        tempDividend->next = subtractPolynomial(tempDividend->next, tempResult->next)->next;
        destroyPolynomial(tempResult);
    }
}


int main() {
    int choice;
    PolyNode* poly1 = NULL;
    PolyNode* poly2 = NULL;
    PolyNode* result = NULL;
    do {
        printf("\n一元多项式运算器菜单：\n");
        printf("1. 创建多项式 1\n");
        printf("2. 创建多项式 2\n");
        printf("3. 打印多项式 1\n");
        printf("4. 打印多项式 2\n");
        printf("5. 求两个多项式的和\n");
        printf("6. 求两个多项式的差\n");
        printf("7. 求两个多项式的积\n");
        printf("8. 求两个多项式的商和余式\n");
        printf("0. 退出\n");
        printf("请输入你的选择：");
        scanf("%d", &choice);
        switch (choice) {
            case 1:
                if (poly1!= NULL) destroyPolynomial(poly1);
                poly1 = createPolynomial();
                break;
            case 2:
                if (poly2!= NULL) destroyPolynomial(poly2);
                poly2 = createPolynomial();
                break;
            case 3:
                if (poly1!= NULL) {
                    printf("多项式 1：");
                    printPolynomial(poly1->next);
                } else {
                    printf("多项式 1 未创建。\n");
                }
                break;
            case 4:
                if (poly2!= NULL) {
                    printf("多项式 2：");
                    printPolynomial(poly2->next);
                } else {
                    printf("多项式 2 未创建。\n");
                }
                break;
            case 5:
                if (poly1!= NULL && poly2!= NULL) {
                    result = addPolynomial(poly1, poly2);
                    printf("两多项式之和：");
                    printPolynomial(result->next);
                    destroyPolynomial(result);
                } else {
                    printf("请先创建两个多项式。\n");
                }
                break;
            case 6:
                if (poly1!= NULL && poly2!= NULL) {
                    result = subtractPolynomial(poly1, poly2);
                    printf("两多项式之差：");
                    printPolynomial(result->next);
                    destroyPolynomial(result);
                } else {
                    printf("请先创建两个多项式。\n");
                }
                break;
            case 7:
                if (poly1!= NULL && poly2!= NULL) {
                    result = multiplyPolynomial(poly1, poly2);
                    printf("两多项式之积：");
                    printPolynomial(result);
                    destroyPolynomial(result);
                } else {
                    printf("请先创建两个多项式。\n");
                }
                break;
            case 8:
                if (poly1!= NULL && poly2!= NULL) {
                    PolyNode* quotient = NULL;
                    PolyNode* remainder = NULL;
                    dividePolynomial(poly1, poly2, &quotient, &remainder);
                    printf("商：");
                    printPolynomial(quotient->next);
                    printf("余式：");
                    printPolynomial(remainder->next);
                    destroyPolynomial(quotient);
                    destroyPolynomial(remainder);
                } else {
                    printf("请先创建两个多项式。\n");
                }
                break;
            case 0:
                if (poly1!= NULL) destroyPolynomial(poly1);
                if (poly2!= NULL) destroyPolynomial(poly2);
                if (result!= NULL) destroyPolynomial(result);
                printf("退出程序。\n");
                break;
            default:
                printf("无效选择，请重新输入。\n");
        }
    } while (choice!= 0);
    return 0;
}