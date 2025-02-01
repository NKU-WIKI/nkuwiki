#include <iostream>
#include <fstream>
#include <queue>
#include <unordered_map>
#include <vector>
#include <bitset>
#include <string>
using namespace std;

// 定义Huffman树的节点
struct HuffmanNode {
    char ch;  // 字符
    int freq;  // 字符出现频率
    HuffmanNode *left, *right;

    HuffmanNode(char c, int f) : ch(c), freq(f), left(nullptr), right(nullptr) {}
};

// 自定义比较函数，用于优先队列
struct Compare {
    bool operator()(HuffmanNode* a, HuffmanNode* b) {
        return a->freq > b->freq;
    }
};

// 优先队列的手动实现（最小堆）
class PriorityQueue {
private:
    vector<HuffmanNode*> heap; // 使用 vector 实现堆

    // 获取父节点、左子节点和右子节点的索引
    int parent(int i) { return (i - 1) / 2; }
    int left(int i) { return 2 * i + 1; }
    int right(int i) { return 2 * i + 2; }

    // 上移操作（heapify-up）：插入元素时调整堆
    void heapifyUp(int index) {
        while (index > 0 && heap[parent(index)]->freq > heap[index]->freq) {
            swap(heap[index], heap[parent(index)]);
            index = parent(index);
        }
    }

    // 下移操作（heapify-down）：删除元素时调整堆
    void heapifyDown(int index) {
        int size = heap.size();
        int smallest = index;
        int l = left(index);
        int r = right(index);

        if (l < size && heap[l]->freq < heap[smallest]->freq)
            smallest = l;
        if (r < size && heap[r]->freq < heap[smallest]->freq)
            smallest = r;

        if (smallest != index) {
            swap(heap[index], heap[smallest]);
            heapifyDown(smallest);
        }
    }

public:
    // 插入节点到优先队列
    void push(HuffmanNode* node) {
        heap.push_back(node);  // 在末尾插入新节点
        heapifyUp(heap.size() - 1);  // 上移调整堆
    }

    // 返回优先队列的最小元素（最小频率的节点）
    HuffmanNode* top() {
        if (!heap.empty()) {
            return heap[0];
        } else {
            throw out_of_range("Heap is empty!");
        }
    }

    // 删除优先队列的最小元素
    void pop() {
        if (heap.empty()) {
            throw out_of_range("Heap is empty!");
        }

        // 将堆顶元素与最后一个元素交换，然后删除最后一个元素
        heap[0] = heap.back();
        heap.pop_back();
        heapifyDown(0);  // 下移调整堆
    }

    // 检查队列是否为空
    bool empty() {
        return heap.empty();
    }

    // 获取优先队列的大小
    int size() {
        return heap.size();
    }
};

// 生成字符频率表
unordered_map<char, int> calculateFrequency(const string &text) {
    unordered_map<char, int> frequency;
    for (char ch : text) {
        frequency[ch]++;
    }
    return frequency;
}

// 构建Huffman树
HuffmanNode* buildHuffmanTree(const unordered_map<char, int> &frequency) {
    PriorityQueue pq;
    for (auto pair : frequency) {
        pq.push(new HuffmanNode(pair.first, pair.second));
    }

    while (pq.size() > 1) {
        HuffmanNode* left = pq.top(); pq.pop();
        HuffmanNode* right = pq.top(); pq.pop();

        HuffmanNode* merged = new HuffmanNode('\0', left->freq + right->freq);
        merged->left = left;
        merged->right = right;

        pq.push(merged);
    }

    return pq.top();
}

// 生成Huffman编码
void generateCodes(HuffmanNode* node, const string &prefix, unordered_map<char, string> &codebook) {
    if (node == nullptr) return;
    if (node->left == nullptr && node->right == nullptr) {
        codebook[node->ch] = prefix;
    }

    generateCodes(node->left, prefix + "0", codebook);
    generateCodes(node->right, prefix + "1", codebook);
}

// 编码文本
string encodeText(const string &text, const unordered_map<char, string> &codebook) {
    string encoded = "";
    for (char ch : text) {
		if(codebook.find(ch)==codebook.end()) cout<<ch<<endl;
        else encoded += codebook.at(ch);
    }
    return encoded;
}

// 保存二进制文件
void saveBinaryFile(const string &filepath, const string &binaryData) {
    ofstream out(filepath, ios::binary);

    // 保存二进制数据的长度，以便译码时能恢复正确的位数
    size_t dataLength = binaryData.size();
    out.write(reinterpret_cast<const char*>(&dataLength), sizeof(dataLength));

    // 逐个字节（8位）将二进制字符串写入文件
    bitset<8> bits;
    for (size_t i = 0; i < binaryData.size(); i += 8) {
        // 取8位，如果不足8位补齐
        string byteString = binaryData.substr(i, 8);
        if (byteString.size() < 8) {
            byteString.append(8 - byteString.size(), '0');
        }
        bits = bitset<8>(byteString);
        out.put(static_cast<unsigned char>(bits.to_ulong()));
    }

    out.close();
}


// 加载二进制文件
string loadBinaryFile(const string &filepath) {
    ifstream in(filepath, ios::binary);
    // 读取保存的二进制数据的长度
    size_t dataLength;
    in.read(reinterpret_cast<char*>(&dataLength), sizeof(dataLength));

    // 读取实际的二进制数据
    string binaryData = "";
    unsigned char byte;
    while (in.get((char&)byte)) {
        bitset<8> bits(byte);
        binaryData += bits.to_string();
    }
    in.close();
    // 根据保存的长度截取需要的位（去掉多余的填充位）
    return binaryData.substr(0, dataLength);
}


// 解码文本
string decodeText(const string &binaryData, HuffmanNode* root) {
    string decoded = "";
    HuffmanNode* current = root;
    for (char bit : binaryData) {
        if (bit == '0') {
            current = current->left;
        } else {
            current = current->right;
        }

        if (!current->left && !current->right) {
            decoded += current->ch;
            current = root;
        }
    }
    return decoded;
}

// 删除Huffman树，释放内存
void deleteHuffmanTree(HuffmanNode* node) {
    if (!node) return;
    deleteHuffmanTree(node->left);
    deleteHuffmanTree(node->right);
    delete node;
}

void readFile(const string& fileName) {
    ifstream file(fileName);
    if (file.is_open()) {
        string line;
        while (getline(file, line)) {
            cout << line << endl;
        }
        file.close();
    } else {
        cerr << "Unable to open file: " << fileName << endl;
    }
}

// 主程序
int main() {
    // 1. 读取inputfile1_ascii.txt文件
    ifstream inputFile1("inputfile1_ascii.txt");
    string inputText1((istreambuf_iterator<char>(inputFile1)), istreambuf_iterator<char>());
    inputFile1.close();

    // 2. 统计字符频率
    unordered_map<char, int> frequency = calculateFrequency(inputText1);
	
	for(int i = 0; i < 128; ++ i)if(frequency.find((char)(i))==frequency.end()){
		frequency.insert({char(i),0});
	}
    // 3. 构建Huffman树
    HuffmanNode* huffmanTree = buildHuffmanTree(frequency);

    // 4. 生成字符编码
    unordered_map<char, string> codebook;
    generateCodes(huffmanTree, "", codebook);

	// 5. 将字符的频率和对应编码保存到outputfile1.txt
	ofstream outputFile1("outputfile1.txt");
	for (auto pair : codebook) {
		outputFile1 << pair.first << ": " << frequency[pair.first] << " " << pair.second << endl;
	}
	outputFile1.close();

    // 6. 读取inputfile2_ascii.txt文件
    ifstream inputFile2("inputfile2_ascii.txt");
    string inputText2((istreambuf_iterator<char>(inputFile2)), istreambuf_iterator<char>());
    inputFile2.close();
	
    // 7. 对inputfile2.txt中的文本进行编码
    string encodedText = encodeText(inputText2, codebook);

    // 8. 将编码结果保存到二进制文件outputfile.dat
    saveBinaryFile("outputfile.dat", encodedText);
    double compressionRatio = (encodedText.size() / 8.0) / inputText2.size();
    cout<<"compressionRatio = "<<compressionRatio<<endl;

    // 9. 读取二进制文件并进行译码
    string binaryData = loadBinaryFile("outputfile.dat");
    string decodedText = decodeText(binaryData, huffmanTree);

    // 10. 将译码结果保存到outputfile2.txt
    ofstream outputFile2("outputfile2.txt");
    outputFile2 << decodedText;
    outputFile2.close();

    // 11. 比较inputfile2_ascii.txt和outputfile2.txt是否相同
    string file1 = "inputfile2_ascii.txt";
    string file2 = "outputfile2.txt";
    string diffFile = "differences.txt";  // 保存差异输出的文件

    // 构造命令行并将输出重定向到 diffFile
#ifdef _WIN32
    string command = "fc " + file1 + " " + file2 + " > " + diffFile;
#else
    string command = "diff " + file1 + " " + file2 + " > " + diffFile;
#endif

    // 执行系统命令并将不同之处写入文件
    int result = system(command.c_str());

    // 检查文件是否相同
    if (result == 0) {
        cout << "The files are identical." << endl;
    } else {
        cout << "The files have differences. Showing differences:" << endl;
        readFile(diffFile);  // 读取并输出差异
    }
    // 清理内存
    deleteHuffmanTree(huffmanTree);

    return 0;
}
