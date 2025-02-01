/**
 * Date: 2019-07-30 11:34:28
 * LastEditors: Aliver
 * LastEditTime: 2019-08-08 14:34:15
 */
template <typename KeyType>
int BTree<KeyType>::order = 3;
template <typename KeyType>
int BTree<KeyType>::maxKeyNum = 2;
template <typename KeyType>
int BTree<KeyType>::minKeyNum = 1;

/**
 * description: 销毁B树
 * parameter: 
 * return: 
 */
template <typename KeyType>
BTree<KeyType>::~BTree()
{
    if (this->root)
        DestoryBTree(this->root);
    this->root = nullptr;
}
/**
 * description: 清空B树
 * parameter: 
 * return: 
 */
template <typename KeyType>
void BTree<KeyType>::Clear()
{
    if (this->root)
        DestoryBTree(this->root);
    this->root = nullptr;
}
/**
 * description: 递归释放B树的结点
 * parameter: 
 * return: 
 */
template <typename KeyType>
typename BTree<KeyType>::Status BTree<KeyType>::DestoryBTree(BTNode<KeyType> *r)
{
    if (r) {
        for (int i = 0; i <= r->keyNum; ++i)
            if (r->child[i])
                DestoryBTree(r->child[i]);
        delete r;
    }
    return OK;
}

/**
 * description: 插入关键字
 * parameter: key - 需被插入的关键字
 * return: 插入是否成功
 */
template <typename KeyType>
typename BTree<KeyType>::Status BTree<KeyType>::Insert(const KeyType &key)
{
    /* 由于每次搜索都会保存搜索路径，如不需要需清空路径 */
    Result<KeyType> result = this->Search(key);
    this->searchPath.clear();

    /* 如果未找到，执行插入操作，否则返回已存在 */
    if (!result.tag){
        BTNode<KeyType> *newNode = nullptr, *p = result.pr;
        Index index = result.index;
        KeyType newKey = key;
        bool over = false;
        while(p && !over) {
            /* newKey 和 newNode 直接插入到 p 结点中 index + 1 所指位置 */
            this->DirectlyInsert(p, index, newKey, newNode);
            /* 若关键字数未超过最大值 结束插入 否则需分裂结点，继续向上回溯 */
            if (p->keyNum <= this->maxKeyNum)
                over = true;
            else {
                /* 以 mid 为界，分裂 p 结点为 p 和 newNode 两个结点，mid所指关键字将被插入到p的双亲中 */
                Index mid = (this->order + 1) / 2;
                newKey = p->key[mid];
                this->Split(p, mid, newNode);
                p = p->parent;
                if (p)
                /* 查找在 p 的双亲中新关键字的插入位置 */
                    index = this->BinarySearch(p, newKey);
            }
        }
        /* 如果一直回溯到根结点插入关键字后，仍然超出最大值，需建立新根
           此时 root 被分裂为 root和newNode两个结点，p为nullptr
           注：这里的参数p可以略去 */
        if (!over)
            this->NewRoot(p, newNode, newKey);
        return OK;
    }
    else
        return EXISTED;
}
/**
 * description: 直接向指定结点的指定位置插入指定关键字和孩子结点 不管关键字数是否超出最大值
 * parameter: p - 插入结点，index - 在p中的插入位置的后一个位置，key - 被插入关键字，childNode - 被插入孩子结点
 * return: 插入状态
 */
template <typename KeyType>
typename BTree<KeyType>::Status BTree<KeyType>::DirectlyInsert(BTNode<KeyType>*p, Index index, const KeyType &key, BTNode<KeyType>*childNode)
{
    if (!p)
        return ERROR;
    /* index后所有关键字向后移动一个位置 */
    for (int i = p->keyNum; i > index; --i)
    {
        p->key[i + 1] = p->key[i];
        p->child[i + 1] = p->child[i];
    }
    /* 循环结束后 index + 1 的位置已空出，直接插入 */
    p->key[index + 1] = key;
    p->child[index + 1] = childNode;
    /* 修改双亲 */
    if (childNode)
        childNode->parent = p;
    ++p->keyNum;
    return OK;
}
/**
 * description: p的关键字已满，以mid为界分裂为p和newNode
 * parameter: p-被分裂结点，mid-界，newNode-新生结点
 * return: 分裂状态
 */
template <typename KeyType>
typename BTree<KeyType>::Status BTree<KeyType>::Split(BTNode<KeyType>*p, Index mid, BTNode<KeyType>*& newNode)
{
    newNode = new BTNode<KeyType>();
    /* 将p的mid之后的关键字和孩子移入newNode */
    newNode->keyNum = p->keyNum - mid;
    for (int i = 1; i <= newNode->keyNum; ++i){
        newNode->key[i] = p->key[i + mid];
        newNode->child[i - 1] = p->child[i + mid - 1];
        if (newNode->child[i - 1])
            newNode->child[i - 1]->parent = newNode;
    }
    /* 循环结束时最后一个孩子还未移入 */
    newNode->child[newNode->keyNum] = p->child[p->keyNum];
    if (newNode->child[newNode->keyNum])
        newNode->child[newNode->keyNum]->parent = newNode;
    /* 与p同一个双亲 */
    newNode->parent = p->parent;
    p->keyNum = mid - 1;
    return OK;
}
/**
 * description: root被分裂为root和q，需加入新的树根，其仅有一个关键字key和两个孩子：q和原来的root
 * parameter: p-nullptr 可忽略，q-root分裂产生的新结点，key-新root的关键字
 * return: 
 */
template <typename KeyType>
typename BTree<KeyType>::Status BTree<KeyType>::NewRoot(BTNode<KeyType>*p, BTNode<KeyType>*q, const KeyType &key)
{
    /* 新增root即可 */
    p = this->root;
    this->root = new BTNode<KeyType>();
    this->root->key[1] = key;
    this->root->child[0] = p;
    this->root->child[1] = q;
    ++this->root->keyNum;
    if (p)
        p->parent = this->root;
    if (q)
        q->parent = this->root;
    this->root->parent = nullptr;
    return OK;
}
/**
 * description: 查找给定关键字
 * parameter: key
 * return: 查找结果
 */
template <typename KeyType>
typename BTree<KeyType>::template Result<KeyType> BTree<KeyType>::Search(const KeyType &key)
{
    bool tag = false;
    Index index = 0;
    /* 从根开始查找 */
    BTNode<KeyType> *p = this->root, *q = nullptr;
    while (p && !tag) {
        index = this->BinarySearch(p, key);
        /* 若找到置标记并记录搜索路径 */
        if (index > 0 && p->key[index] == key) {
            tag = true;
            this->searchPath.push_back({tag, index, p});
        }
        /* 找不到搜索孩子结点并记录路径 */
        else {
            q = p;
            p = p->child[index];
            /* 这里index可能为0，指定关键字应为 1 */
            this->searchPath.push_back({tag, index + ( !index ? 1 : 0), q});
        }
    }
    if (tag)
        return Result<KeyType>{tag, index, p};
    else 
        return Result<KeyType>{tag, index, q};
}
/**
 * description: 在p中查找key的位置(未找到key则返回最接近key而不大于key的关键字索引)
 * parameter: 。。。
 * return: 关键字索引（可能返回0，不是合法关键字索引，需注意）
 */
template <typename KeyType>
typename BTree<KeyType>::Index BTree<KeyType>::BinarySearch(BTNode<KeyType> *p, const KeyType &key)
{
    if (p) {
        int left = 1, right = p->keyNum, mid = left + (right - left) / 2;

        while (left <= right) {
            mid = left + (right - left) / 2;
            if (p->key[mid] == key)
                return mid;
            else if (p->key[mid] > key)
                right = mid - 1;
            else
                left = mid + 1;
        }
        /* 这里采用二分查找
           1. 如果是 p->key[mid] > key 导致循环退出，此时right正好指向所需的索引位置(不大于而最接近)
           2. 否则，此时left正好指向满足需求的下一个位置，- 1 即可 */
        if (p->key[mid] > key)
            return right;
        else
            return left - 1;
    }
    return NOTFOUND;
}
/**
 * description: 删除指定关键字
 * parameter: 。。。
 * return: 删除状态
 */
template <typename KeyType>
typename BTree<KeyType>::Status BTree<KeyType>::Delete(const KeyType &key)
{
    /* 先搜索并清楚路径 */
    Result<KeyType> result = this->Search(key);
    this->searchPath.clear();
    /* 未找到 返回 否则如果是内部结点，寻找替代关键字(紧邻右子树的最小关键字) */
    if (!result.tag)    // 不存在要删除的关键字
        return NOTFOUND;
    if (result.pr->child[result.index]) {       // 如果是内部结点，寻找替代关键字
        Result<KeyType> coverResult = this->FindSubstitute(result.pr->child[result.index]);
        /* 如果找到替代，置换关键字并更新将被删除的关键字
           (此时被删除关键字应为右子树中最小的那个关键字) */
        if (coverResult.tag) {
            result.pr->key[result.index] = coverResult.pr->key[coverResult.index];
            result.index = coverResult.index;
            result.pr = coverResult.pr;
        }
    }
    /* 在指定结点中删除指定位置的关键字
       (注：此时调用一定是在叶子结点中删除关键字) */
    this->DeleteInNode(result.pr, result.index);
    /* 若删除过后root中无关键字，则按合并结点的约定，此时新根应为最左子树的根结点 */
    if (this->root->keyNum == 0) {
        BTNode<KeyType> *p = this->root;
        this->root = this->root->child[0];
        /* 更新双亲 */
        if (this->root)
            this->root->parent = nullptr;
        delete p;
    }
    return OK;
}
/**
 * description: 在指定结点中删除指定位置的关键字
 * parameter: 。。。
 * return: 删除状态
 */
template <typename KeyType>
typename BTree<KeyType>::Status BTree<KeyType>::DeleteInNode(BTNode<KeyType> *node, Index keyIndex)
{
    /* 若结点中关键字个数大于最小值，直接删除即可 */
    if (node && node->keyNum > this->minKeyNum)
        this->DirectlyDelete(node, keyIndex);
    else if (node) {
        /* 否则先直接删除 然后找到其双亲结点和紧邻的左右兄弟(如果有) */
        this->DirectlyDelete(node, keyIndex);
        BTNode<KeyType> *parent = node->parent;
        Index curIndex = this->FindParentIndex(parent, node);
        // 左兄弟
        BTNode<KeyType> *leftSibling = (curIndex > 0) ? parent->child[curIndex - 1] : nullptr;
        // 右兄弟
        BTNode<KeyType> *rightSibling = (curIndex >= 0 && curIndex < parent->keyNum) ? parent->child[curIndex + 1] : nullptr;
        /* 是否可向兄弟结点借关键字 */
        bool canBorrowLeft = (leftSibling && leftSibling->keyNum > this->minKeyNum);
        bool canBorrowRight = (rightSibling && rightSibling->keyNum > this->minKeyNum);
        /* 如果左兄弟可借，向右轮换 */
        if (canBorrowLeft) {
            this->RightRotation(parent, curIndex);
        }
        /* 向左轮换 */
        else if (canBorrowRight) {
            this->LeftRotation(parent, curIndex + 1);
        }
        /* 否则需合并结点，这里合并结点之后 parent中curIndex所指关键字虽已合并到紧邻左孩子，但是还没有删除，需继续递归调用以调正B树的平衡性 */
        else {
            this->MergeNode(parent, curIndex + (rightSibling ? 1 : 0));
            this->DeleteInNode(parent, curIndex + (rightSibling ? 1 : 0));
        }
    }
    return OK;
}
/**
 * description: 寻找双亲结点中孩子结点的索引
 * parameter: 。。。
 * return: 索引值
 */
template <typename KeyType>
typename BTree<KeyType>::Index BTree<KeyType>::FindParentIndex(BTNode<KeyType> *parent, BTNode<KeyType> *child)
{
    if (!parent)
        return NOTFOUND;
    Index i = 0;
    for (; i <= parent->keyNum && parent->child[i] != child; ++i)
        ;
    /* 返回0，表示该孩子没有左兄弟
       返回parent->keyNum, 表示该孩子没有右兄弟 */
    return i;
}
/**
 * description: 寻找被删除关键字(内部结点)的替代字 (选紧邻右子树中的最小关键字)
 * parameter: 传入右子树即可
 * return: Result结构的查找结果
 */
template <typename KeyType>
typename BTree<KeyType>::template Result<KeyType> BTree<KeyType>::FindSubstitute(BTNode<KeyType> *right)
{
    Result<KeyType> result;
    result.index = NOTFOUND;
    result.pr = nullptr;
    result.tag = false;
    if (!right)
        return result;
    for (; right->child[0]; right = right->child[0])
        ;
    result.index = 1;
    result.pr = right;
    result.tag = true;
    return result;
}
/**
 * description: 叶子结点中，关键字数量大于最小值，直接删除
 * parameter: 。。。
 * return: 删除状态
 */
template <typename KeyType>
typename BTree<KeyType>::Status BTree<KeyType>::DirectlyDelete(BTNode<KeyType> *p, Index index)
{
    if (!p)
        return ERROR;
    else {
        /* 直接覆盖index所指位置 */
        for (; index < p->keyNum; ++index) {
            p->key[index] = p->key[index + 1];
            p->child[index] = p->child[index + 1];
        }
        --p->keyNum;
        return OK;
    }
}
/**
 * description: 向左轮换调正B树(删除关键字后当前结点数小于最小值，右兄弟(关键字数大于最小值)中的最小关键字上移到双亲，双亲结点对应关键字下移)
 * parameter: parent - 双亲结点，childIndex - 孩子索引
 * return: 调整状态
 */
template <typename KeyType>
typename BTree<KeyType>::Status BTree<KeyType>::LeftRotation(BTNode<KeyType> *parent, Index childIndex)
{
    if (!parent)
        return ERROR;
    BTNode<KeyType> *left = parent->child[childIndex - 1];  // 即是当前结点
    BTNode<KeyType> *right = parent->child[childIndex];

    /* parent中的关键字下移到当前结点，同时移动该关键字的直接后继
       即：右兄弟的第一个孩子结点 */
    ++left->keyNum;
    left->key[left->keyNum] = parent->key[childIndex];
    left->child[left->keyNum] = right->child[0];
    if (left->child[left->keyNum])
        left->child[left->keyNum]->parent = left;

    /* 右兄弟的第一个关键字上移 */
    parent->key[childIndex] = right->key[1];

    /* 覆盖第一个 */
    --right->keyNum;
    right->child[0] = right->child[1];
    for (int i = 1; i <= right->keyNum; ++i) {
        right->key[i] = right->key[i + 1];
        right->child[i] = right->child[i + 1];
    }

    return OK;
}
/**
 * description: 向右轮换调正B树(删除关键字后当前结点数小于最小值，左兄弟(关键字数大于最小值)中的最大关键字上移到双亲，双亲结点对应关键字下移)
 * parameter: parent - 双亲结点，childIndex - 孩子索引
 * return: 调整状态
 */
template <typename KeyType>
typename BTree<KeyType>::Status BTree<KeyType>::RightRotation(BTNode<KeyType> *parent, Index childIndex)
{
    if (!parent)
        return ERROR;
    BTNode<KeyType> *left = parent->child[childIndex - 1];
    BTNode<KeyType> *right = parent->child[childIndex]; // 即是当前结点

    /* 后移关键字和结点 */
    ++right->keyNum;
    for (int i = right->keyNum; i > 1; --i) {
        right->key[i] = right->key[i - 1];
        right->child[i] = right->child[i - 1];
    }
    right->child[1] = right->child[0];

    /* 双亲结点关键字下移，并移动该关键字的直接前驱
       即：左兄弟的最后一个孩子结点 */
    right->key[1] = parent->key[childIndex];
    right->child[0] = left->child[left->keyNum];
    if (right->child[0])
        right->child[0]->parent = right;

    /* 左孩子中的最后一个关键字上移 */
    parent->key[childIndex] = left->key[left->keyNum];

    --left->keyNum;
    return OK;
}
/**
 * description: 合并结点
 * parameter: childIndex对应的左右孩子、parent的对应关键字合并到左孩子
 * return: 合并状态
 */
template <typename KeyType>
typename BTree<KeyType>::Status BTree<KeyType>::MergeNode(BTNode<KeyType> *parent, Index childIndex)
{
    if (!parent)
        return ERROR;
    // 默认向左兄弟合并
    BTNode<KeyType> *left = parent->child[childIndex - 1];
    BTNode<KeyType> *right = parent->child[childIndex]; // 即是当前结点

    /* 双亲关键字下移 */
    ++left->keyNum;
    left->key[left->keyNum] = parent->key[childIndex];
    left->child[left->keyNum] = right->child[0];
    if (left->child[left->keyNum])
        left->child[left->keyNum]->parent = left;

    /* 复制所有右兄弟信息 */
    for (int i = 1; i <= right->keyNum; ++i) {
        ++left->keyNum;
        left->key[left->keyNum] = right->key[i];
        left->child[left->keyNum] = right->child[i];
        if (left->child[left->keyNum])
            left->child[left->keyNum]->parent = left;
    }
    /* 删除右兄弟 */
    delete right;
    right = nullptr;
    return OK;
}
/**
 * description: 静态方法，修改B树的阶，默认为 2-3树
 * parameter: m - 阶
 * return: 状态
 */
template <typename KeyType>
typename BTree<KeyType>::Status BTree<KeyType>::SetOrder(int m)
{
    order = m;
    maxKeyNum = m - 1;
    minKeyNum = (m + 1) / 2 - 1;
    return OK;
}
/**
 * description: 输出Btree，其中若两个同层结点是兄弟关系，用 ‘-’ 连接
 * parameter: 提示信息
 * return: 
 */
template <typename KeyType>
void BTree<KeyType>::FormatPrint(const char *prompt)
{
    if (prompt)
        cout << prompt << endl;
    cout << "-----------------" << endl;
    queue<BTNode<KeyType> *> Q;
    if (this->root)
        Q.push(this->root);
    else {
        cout << "NULL" << endl;
        return;
    }
    int lineNum = 1, counter = 0, nextLineNum = 0;
    while (!Q.empty()) {
        BTNode<KeyType> * p = Q.front();
        Q.pop();

        if (p) {
            cout << "(" << p->keyNum << ":";
            Q.push(p->child[0]);
            for (Index i = 1; i <= p->keyNum; ++i) {
                if (i < p->keyNum)
                    cout << p->key[i] << " ";
                else
                    cout << p->key[i];
                Q.push(p->child[i]);
            }
            // cout << ") ";
            if ((!Q.empty() && Q.front()) && (p->parent == (Q.front())->parent))
                cout << ")-";
            else
                cout << ") ";

            ++counter;
            nextLineNum += p->keyNum + 1;
            if (lineNum == counter) {
                cout << endl;
                lineNum = nextLineNum;
                counter = 0;
                nextLineNum = 0;
            }
        }
    }
    cout << "-----------------" << endl << endl;
    return;
}


// 输出查找路径
template <typename KeyType>
void BTree<KeyType>::SearchPath(const char *prompt)
{
    if (this->searchPath.back().tag) {
        if (prompt)
            cout << prompt << endl;
        for (auto it : this->searchPath)
        {
            if (it.tag)
                cout << it.pr->key[it.index];
            else 
                cout << it.pr->key[it.index] << "->";
        }
        cout << endl;
    }
    this->searchPath.clear();
}