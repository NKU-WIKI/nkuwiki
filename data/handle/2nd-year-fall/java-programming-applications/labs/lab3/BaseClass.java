abstract class BaseClass {
    void firstMethod() {
        secondMethod();
    }

    abstract void secondMethod();
}

class SubClass extends BaseClass {
    @Override
    void secondMethod() {
        System.out.println("Overridden method in SubClass");
    }

    public static void main(String[] args) {
        BaseClass obj = new SubClass();
        obj.firstMethod();
    }
}
