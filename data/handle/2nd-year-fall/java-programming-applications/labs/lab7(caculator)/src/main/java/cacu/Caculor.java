package cacu;

import java.util.Stack;

public class Caculor {

    //stack of numbers
    private Stack<Double> numbers = new Stack<Double>();
    //stack of operands
    private Stack<Character> operands = new Stack<Character>();


    public String caculate(String exp) {
        String tmp=cacuExpressions(exp).toString();
        numbers.clear();
        operands.clear();
        return tmp;
    }

    //get the priority of the operator
    private int getPriority(char op) {
        switch (op) {
            case '+':
            case '-':
                return 1;
            case '*':
            case '/':
                return 2;
            case '^':
                return 3;
            default:
                return -1;
        }
    }

    //calculate the number of operators in a string expression
    private int getOperatorNum(String exp) {
        int num = 0;
        for (int i = 0; i < exp.length(); i++) {
            if (exp.charAt(i) == '+' || exp.charAt(i) == '-' || exp.charAt(i) == '*' || exp.charAt(i) == '/' || exp.charAt(i) == '^') {
                num++;
            }
        }
        return num;
    }

    //calculate the top two numbers and the top operator, no input validation
    private void cacuTwoNumbers() {
        double num1 = numbers.pop();
        double num2 = numbers.pop();
        switch (operands.pop()) {
            case '+':
                numbers.push(num2 + num1);
                break;
            case '-':
                numbers.push(num2 - num1);
                break;
            case '*':
                numbers.push(num2 * num1);
                break;
            case '/':
                numbers.push(num2 / num1);
                break;
            case '^':
                numbers.push(Math.pow(num2, num1));
                break;
        }
    }

    private void numfixer(String exp,int i,int j){
        Double tmp;
        if(i-1==0&&exp.charAt(i-1) == '-'){
            numbers.push(0.0);
        }
        tmp = exp.charAt(j-1)=='%'?Double.parseDouble(exp.substring(i, j-1))/100:Double.parseDouble(exp.substring(i, j));

        numbers.push(tmp);
    }

    //caculate the result of the infix expression
    private Double cacuExpressions(String exp) {
        int num = getOperatorNum(exp);
        if (num == 0) {
            return Double.parseDouble(exp);
        }
        if(num == 1) {
            for (int i = 0; i < exp.length(); i++) {
                if (exp.charAt(i) >= '0' && exp.charAt(i) <= '9') {
                    int j = i;
                    while (j < exp.length() && ((exp.charAt(j) >= '0' && exp.charAt(j) <= '9')
                            ||exp.charAt(j) =='.'||exp.charAt(j) == '%')) {
                        j++;
                    }
                    numfixer(exp,i,j);
                    i = j - 1;
                }else{
                    operands.push(exp.charAt(i));
                }
            }
            cacuTwoNumbers();
            return numbers.pop();
        }
        for (int i = 0; i < exp.length(); i++) {
            if (exp.charAt(i) >= '0' && exp.charAt(i) <= '9') {
                int j = i;
                while (j < exp.length() && ((exp.charAt(j) >= '0' && exp.charAt(j) <= '9')
                        ||exp.charAt(j) =='.'||exp.charAt(j) == '%')) {
                    j++;
                }
                numfixer(exp,i,j);
                i = j - 1;
            } else {
                if (exp.charAt(i) == '(') {
                    operands.push(exp.charAt(i));
                } else if (exp.charAt(i) == ')') {
                    while (operands.peek() != '(') {
                        cacuTwoNumbers();
                    }
                    operands.pop();
                } else {
                    while (!operands.empty() && (getPriority(exp.charAt(i)) <= getPriority(operands.peek()))) {
                        cacuTwoNumbers();
                    }
                    operands.push(exp.charAt(i));
                }
            }
        }
        while (!operands.empty()) {
            cacuTwoNumbers();
        }
        return numbers.pop();
    }


}
