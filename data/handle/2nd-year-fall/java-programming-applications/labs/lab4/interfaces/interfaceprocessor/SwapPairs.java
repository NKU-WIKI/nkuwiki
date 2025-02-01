package interfaces.interfaceprocessor;
public class SwapPairs implements Processor {
    @Override
    public String name() {
        return "Swap Pairs Processor";
    }
    @Override
    public Object process(Object input) {
        String str = (String) input;
        return swapPairs(str);
    }
    private String swapPairs(String str) {
        StringBuilder result = new StringBuilder(str);
        for (int i = 0; i < result.length() - 1; i += 2) {
            char temp = result.charAt(i);
            result.setCharAt(i, result.charAt(i + 1));
            result.setCharAt(i + 1, temp);
        }
        return result.toString();
    }
    public static void main(String[] args) {
        SwapPairs swapPairsProcessor = new SwapPairs();
        // 使用 Apply 来处理字符串 "abcdefg"
        Apply.process(swapPairsProcessor, "abcdefg");
    }
}
