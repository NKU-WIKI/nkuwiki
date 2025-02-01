public class Main {
    public static void cmp(String A, String B){
        System.out.println("<: The operator < is undefined for the argument type(s) java.lang.String, java.lang.String");
        System.out.println(">: The operator > is undefined for the argument type(s) java.lang.String, java.lang.String");
        System.out.println("<=: The operator <= is undefined for the argument type(s) java.lang.String, java.lang.String");
        System.out.println(">=: The operator >= is undefined for the argument type(s) java.lang.String, java.lang.String");
        System.out.println("==: " + (A == B));
        System.out.println("==: " + (A == B));
        System.out.println("!=: " + (A != B));
        System.out.println("equals: " + A.equals(B));
    }
    public static void main(String[] args) {
        String A = "abc";
        String B = "abc";
        String A_ = A;
        String C = "cba";
        cmp(A,B);
        cmp(A,A_);
        cmp(A,C);
    }
}
