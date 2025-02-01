#ifndef BTREE_H
#define BTREE_H

#include <fstream>
#include <iostream>
#include <queue>
#include <list>

using namespace std;

template <typename KeyType>
class BTree
{
private:
    // 由于结构体中需要类型实例化，这里加一个无名模板定义
    template <typename>
    struct BTNode
    {
    public:
        int keyNum = 0;                  // 关键字数量
        struct BTNode<KeyType>* parent = nullptr; // 双亲结点
        KeyType* key = nullptr;          // 关键字向量
        struct BTNode<KeyType>** child = nullptr; // 孩子结点指针向量
        // Record **records;                // 记录指针向量
        // key的 0 号单元不使用，并且剩余单元需要等于树阶(满结点分裂)
        // child 单元数比树阶大1(最后一个用于满结点分裂)
        BTNode() : keyNum(0), parent(nullptr), key(new KeyType[maxKeyNum + 2]),
            child(new BTNode<KeyType>* [maxKeyNum + 2]{ nullptr })
        {}
        ~BTNode()
        {
            delete[] key;
            delete[] child;
            key = nullptr;
            child = nullptr;
        }
    };
public:
    using Index = int;
    enum Status
    {
        NOTFOUND = -1,
        EXISTED,
        OK,
        ERROR
    };
    // struct Record{
    // };
    template <typename>
    class Result
    {
    public:
        // Record getRecord() { return pr->Record[i]; }
        // bool isValid() { return tag; }
        // private:
        bool tag = false;   // 查找结果是否合法
        Index index = -1;      // 在结点中的关键字序号
        BTNode<KeyType> * pr = nullptr; // 结果指针
        Result() = default;
        Result(bool t, Index i, BTNode<KeyType>* p) : tag(t), index(i), pr(p) {}
        Result(const Result<KeyType> &s)
        {
            this->index = s.index;
            this->pr = s.pr;
            this->tag = s.tag;
        }
        Result<KeyType> operator=(const Result<KeyType> &s)
        {
            Result t;
            t.pr = s.pr;
            t.tag = s.tag;
            t.index = s.index;
            return t;
        }
    };

    BTree() = default;    // 默认构造
    ~BTree();
    // 插入关键字
    Status Insert(const KeyType& key);
    // 查找key
    Result<KeyType> Search(const KeyType& key);
    // 删除关键字
    Status Delete(const KeyType& key);
    // 设置B-Tree的阶
    static Status SetOrder(int m);
    // 格式化输出B-Tree
    void FormatPrint(const char *prompt = nullptr);
    // 输出查找路径
    void SearchPath(const char *prompt = nullptr);
    // 清空B树
    void Clear();

private:
    BTNode<KeyType>* root = nullptr; // 根结点
    static int order;          // B-Tree的阶，默认为3（2-3树
    static int maxKeyNum;
    static int minKeyNum;

    list<Result<KeyType>> searchPath{};

    // 递归销毁B-Tree(由析构函数调用)
    Status DestoryBTree(BTNode<KeyType>* r);
    // p 结点的关键字个数小于最大值，直接插入
    Status DirectlyInsert(BTNode<KeyType>* p, Index index, const KeyType& key, BTNode<KeyType>* childNode);
    // p 结点的关键字个数已满，需以mid为界分裂
    Status Split(BTNode<KeyType>* p, Index mid, BTNode<KeyType>* &newNode);
    // 若为空树或(根结点被分为 p, q 两个子结点)，则加入新根，关键字为key
    Status NewRoot(BTNode<KeyType>* p, BTNode<KeyType>* q, const KeyType& key);
    // 在 p 所指结点二分查找 key 的位置(未找到key则返回最接近key而不大于key的关键字索引)
    Index BinarySearch(BTNode<KeyType>* p, const KeyType& key);
    // 寻找被删除关键字(内部结点)的替代字 (选相邻右子树中的最小关键字)
    Result<KeyType> FindSubstitute(BTNode<KeyType> *right);
    // 叶子结点中，关键字数量大于最小值，直接删除
    Status DirectlyDelete(BTNode<KeyType> *p, Index index);
    // 向左轮换调正B树(删除关键字后当前结点数小于最小值，右兄弟(关键字数大于最小值)中的最小关键字上移到双亲，双亲结点对应关键字下移)
    Status LeftRotation(BTNode<KeyType> *parent, Index childIndex);
    // 向右轮换调正B树(删除关键字后当前结点数小于最小值，左兄弟(关键字数大于最小值)中的最大关键字上移到双亲，双亲结点对应关键字下移)
    Status RightRotation(BTNode<KeyType> *parent, Index childIndex);
    // 合并结点(默认合并到左兄弟)
    Status MergeNode(BTNode<KeyType> *parent, Index childIndex);
    // 在结点中删除指定关键字
    Status DeleteInNode(BTNode<KeyType> *node, Index keyIndex);
    // 寻找给定结点所在双亲结点的孩子索引值(有可能为 0，所以为0时对应关键字需+1)
    Index FindParentIndex(BTNode<KeyType> *parent, BTNode<KeyType> *child);
};

#include "BTree.hpp"
// #include "BTree.tpp"

#endif // BTREE_H