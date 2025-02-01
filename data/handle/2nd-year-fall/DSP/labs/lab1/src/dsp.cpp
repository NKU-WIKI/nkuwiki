#include<bits/stdc++.h>
class DS {
public:
    std::vector<double> a;  // 存储实际数据
    int l, r;  // 时间范围 [l, r]
    bool is_infinite_left;  // 是否向左为无限序列
    bool is_infinite_right; // 是否向右为无限序列

public:
    // 构造函数
    DS(int l, int r, bool infinite_left = false, bool infinite_right = false)
        : l(l), r(r), is_infinite_left(infinite_left), is_infinite_right(infinite_right) {
        a.resize(r - l + 1, 0);  // 初始化数组为零
    }
    DS(int l,int r, std::vector<double>&aa):l(l),r(r),is_infinite_left(true),is_infinite_right(true){
        a.assign(aa.begin(),aa.end());
    }

    // 重载 [] 操作符访问数据
    double& operator[](int t) {
        if (t < l || t > r) {
            throw std::out_of_range("索引超出范围");
        }
        return a[t - l];
    }

    // 读入数据，向左或向右扩展
    void read_infinite(std::istream& is) {
        double value;
        char direction;

        // 提示用户选择读入的方向
        std::cout << "选择读入的方向 (l: 向左读入, r: 向右读入): ";
        std::cin >> direction;

        if (direction == 'r' || direction == 'R') {
            // 向右扩展序列
            if (is_infinite_right) {
                std::cout << "请输入向右扩展的序列数据 (Ctrl+D结束): ";
                while (is >> value) {
                    r++;
                    a.push_back(value);  // 向右插入数据
                }
            } else {
                std::cout << "当前序列不支持向右扩展。" << std::endl;
            }
        }
        else if (direction == 'l' || direction == 'L') {
            // 向左扩展序列
            if (is_infinite_left) {
                std::cout << "请输入向左扩展的序列数据 (Ctrl+D结束): ";
                while (is >> value) {
                    l--;
                    a.insert(a.begin(), value);  // 向左插入数据
                }
            } else {
                std::cout << "当前序列不支持向左扩展。" << std::endl;
            }
        } else {
            std::cout << "无效的选择!" << std::endl;
        }
    }

    // 输出序列，以 a[l:r]=[1,2,3] 格式
    friend std::ostream& operator<<(std::ostream& os, const DS& ds) {
        os << "a[" << ds.l << ":" << ds.r << "] = [";
        for (size_t i = 0; i < ds.a.size(); ++i) {
            os << ds.a[i];
            if (i < ds.a.size() - 1) os << ", ";
        }
        os << "]";
        return os;
    }

    // 获取序列的长度
    int length() const {
        return r - l + 1;
    }

    // 用零填充序列
    void pad_zero(int left, int right) {
        l -= left;
        r += right;
        a.insert(a.begin(), left, 0);
        a.insert(a.end(), right, 0);
    }

    // 延迟操作（更新时间范围 l 和 r，右移）
    void delay(int n) {
        if (n < 0) throw std::invalid_argument("延迟不能为负数");
        
        l += n;  // 增加左边界
        r += n;  // 增加右边界
    }

    // 提前操作（更新时间范围 l 和 r，左移）
    void advance(int n) {
        if (n < 0) throw std::invalid_argument("提前不能为负数");
        
        l -= n;  // 减少左边界
        r -= n;  // 减少右边界
    }

    // 反转序列
    void reverse() {
        std::reverse(a.begin(), a.end());
        int _l = l;
        l = -r;  // 更新时间范围
        r = -_l;
        std::swap(is_infinite_left, is_infinite_right);
    }

    // 拉伸序列（按因子拉伸）
    // 实时读取数据并计算拉伸结果
    void stretch(int factor, char direction = 'n') {
        if (factor <= 0) throw std::invalid_argument("拉伸因子必须是正数");
        // 打印当前序列
        std::cout << "当前序列: ";
        std::cout<<*this<<std::endl;
       
        std::vector<double> new_a;
        for(int i = l ; i <= r; ++ i){
            if(i < 0){
                new_a.push_back((*this)[i]);
                new_a.insert(new_a.end(), factor - 1, 0);
            }else if(i > 0){
                new_a.insert(new_a.end(), factor - 1, 0);
                new_a.push_back((*this)[i]);
            }else if(i == 0){
                new_a.push_back((*this)[i]);
            }
        }
        l = l * factor;
        r = r * factor;
        a.assign(new_a.begin(),new_a.end());
        std::cout << "以"<<factor<<"为因子拉伸后的序列" << *this << std::endl;
        if(direction == 'n') ;
        else if (direction == 'r' || direction == 'R') {
            // 向右拉伸序列
            if (is_infinite_right) {
                std::cout << "请输入向右拉伸的序列数据 (Ctrl+D结束): ";
                int value;
                while (std::cin >> value) {
                    r += factor;
                    if(r!=0) new_a.insert(new_a.end(),factor-1,0);
                    // 向右插入数据
                    new_a.push_back(value);
                    a.assign(new_a.begin(),new_a.end());
                    std::cout << "以"<<factor<<"为因子拉伸后的序列" << *this << std::endl;
                }
            }else {
                std::cout << "当前序列不支持向右拉伸。" << std::endl;
                return;
            }
        }else if (direction == 'l' || direction == 'L') {
            // 向左扩展序列
            if (is_infinite_left) {
                std::cout << "请输入向左拉伸的序列数据 (Ctrl+D结束): ";
                int value;
                while (std::cin >> value) {
                    l -= factor;
                    if(l!=0) new_a.insert(new_a.begin(),factor-1,0);
                    new_a.insert(new_a.begin(),value);
                    a.assign(new_a.begin(),new_a.end());
                    std::cout << "以"<<factor<<"为因子拉伸后的序列" << *this << std::endl;
                }
            } else {
                std::cout << "当前序列不支持向左拉伸。" << std::endl;
                return;
            }
        } 
        else {
            std::cout << "无效的拉伸方向!" << std::endl;
            return;
        } 
        a.assign(new_a.begin(),new_a.end());
    }
    // 压缩序列（按因子压缩）
    // 实时读取数据并计算压缩结果
    void compress(int factor, char direction = 'n') {
        if (factor <= 0) throw std::invalid_argument("压缩因子必须是正数");

        // 打印当前序列
        std::cout << "当前序列: ";
        std::cout << *this << std::endl;
        
        std::vector<double> new_a;

        for (int i = l; i <= r; ++i) {
            if (i % factor ==0 ){
                new_a.push_back((*this)[i]);
            }
        }
        l = ceil(1.0 * l / factor);
        r /= factor;
        a.assign(new_a.begin(), new_a.end());
        std::cout << "以"<<factor<<"为因子压缩后的序列: " << *this << std::endl;
        int cnt = 0;
        if (direction == 'n') {
            // 不进行任何扩展，只进行压缩
        } else if (direction == 'r' || direction == 'R') {
            // 向右压缩序列
            if (is_infinite_right) {
                std::cout << "请输入向右压缩的序列数据 (Ctrl+D结束): ";
                int value;
                cnt = 0;
                while (std::cin >> value) {
                    ++ cnt;
                    if(cnt % factor == 0 || r + 1 == 0){
                        cnt = 0;
                        ++ r;
                        new_a.push_back(value);
                        a.assign(new_a.begin(), new_a.end());
                    }
                     std::cout << "以"<<factor<<"为因子压缩后的序列: " << *this << std::endl;
                }
            } else {
                std::cout << "当前序列不支持向右压缩。" << std::endl;
                return;
            }
        } else if (direction == 'l' || direction == 'L') {
            // 向左压缩序列
            if (is_infinite_left) {
                std::cout << "请输入向左压缩的序列数据 (Ctrl+D结束): ";
                int value;
                cnt = 0;
                while (std::cin >> value) {
                    ++ cnt;
                    if(cnt % factor == 0 || l - 1 == 0){
                        cnt = 0;
                        --l;
                        new_a.insert(new_a.begin(), value);
                        a.assign(new_a.begin(), new_a.end());
                    }
                     std::cout << "以"<<factor<<"为因子压缩后的序列: " << *this << std::endl;
                }
            } else {
                std::cout << "当前序列不支持向左压缩。" << std::endl;
                return;
            }
        } else {
            std::cout << "无效的压缩方向!" << std::endl;
            return;
        }
        a.assign(new_a.begin(), new_a.end());
    }

    // 序列的差分
    void difference(char direction = 'n') {
        std::vector<double> new_a;
        for (size_t i = 1; i < a.size(); ++i) {
            new_a.push_back(a[i] - a[i - 1]);
        }
        l ++;
        a.assign(new_a.begin(), new_a.end());
        std::cout << "差分后的序列" << *this << std::endl;
        if (direction == 'n') {
        } else if (direction == 'r' || direction == 'R') {
            // 向右差分序列
            if (is_infinite_right) {
                std::cout << "请输入向右差分的序列数据 (Ctrl+D结束): ";
                int value;
                while (std::cin >> value){
                    ++ r;
                    new_a.push_back(value - *(a.end() - 1));
                    a.push_back(value);
                    std::cout << "差分后的序列: " << DS(l,r,new_a) << std::endl;
                }
            } else {
                std::cout << "当前序列不支持向右差分。" << std::endl;
                return;
            }
        } else if (direction == 'l' || direction == 'L') {
            // 向左差分序列
            if (is_infinite_left) {
                std::cout << "请输入向左差分的序列数据 (Ctrl+D结束): ";
                int value;
                while (std::cin >> value) {
                    --l;
                    new_a.insert(new_a.begin(),*a.begin() - value);
                    a.insert(a.begin(),value);
                    std::cout << "差分后的序列: " << DS(l,r,new_a) << std::endl;
                }
            } else {
                std::cout << "当前序列不支持向左压缩。" << std::endl;
                return;
            }
        } else {
            std::cout << "无效的压缩方向!" << std::endl;
            return;
        }
        a.assign(new_a.begin(), new_a.end());
    }

    // 序列的累积和// 序列的累加
    void accumulate(char direction = 'n') {
        for (size_t i = 1; i < a.size(); ++i) {
            a[i] += a[i - 1];
        }
        std::cout << "累加后的序列: " << *this << std::endl;

        if (direction == 'n') {
            // 不进行任何扩展，只进行累加操作
        } else if (direction == 'r' || direction == 'R') {
            // 向右累加序列
            if (is_infinite_right) {
                std::cout << "请输入向右累加的序列数据 (Ctrl+D结束): ";
                int value;
                while (std::cin >> value) {
                    ++r;
                    a.push_back(*(a.end()-1) + value);
                    std::cout << "累加后的序列: " << *this << std::endl;
                }
            } else {
                std::cout << "当前序列不支持向右累加。" << std::endl;
                return;
            }
        } else if (direction == 'l' || direction == 'L') {
            // 向左累加序列
            if (is_infinite_left) {
                std::cout << "请输入向左累加的序列数据 (Ctrl+D结束): ";
                int value;
                while (std::cin >> value) {
                    --l;
                    a.insert(a.begin(), *a.begin() + value);
                    std::cout << "累加后的序列: " << *this << std::endl;
                }
            } else {
                std::cout << "当前序列不支持向左累加。" << std::endl;
                return;
            }
        } else {
            std::cout << "无效的累加方向!" << std::endl;
            return;
        }
    }

    // 加法运算符重载
    DS operator+(DS& other){
        // 确保两个序列的时间范围可以对齐
        int new_l = std::min(l, other.l);
        int new_r = std::max(r, other.r);

        DS result(new_l, new_r, is_infinite_left, is_infinite_right);

        // 扩展当前序列和另一个序列，确保它们在同一时间范围内
        for (int i = new_l; i <= new_r; ++i) {
            double val_this = (i >= l && i <= r) ? (*this)[i] : 0;
            double val_other = (i >= other.l && i <= other.r) ? (other[i]) : 0;
            result[i] = val_this + val_other;
        }

        return result;
    }

    // 乘法运算符重载
    DS operator*(DS& other) {
        // 确保两个序列的时间范围可以对齐
        int new_l = std::min(l, other.l);
        int new_r = std::max(r, other.r);

        DS result(new_l, new_r, is_infinite_left, is_infinite_right);

        // 扩展当前序列和另一个序列，确保它们在同一时间范围内
        for (int i = new_l; i <= new_r; ++i) {
            double val_this = (i >= l && i <= r) ? (*this)[i] : 0;
            double val_other = (i >= other.l && i <= other.r) ? (other[i]) : 0;
            result[i] = val_this * val_other;
        }

        return result;
    }

    // 实时加法计算：每次输入新的数据进行加法并输出结果
    void add_real_time(DS& other, char direction = 'r' ) {
        double value_a, value_b;
        *this = *this + other;
        std::cout << "序列 A 和 B 之和为" << *this << std::endl; 
        while (true) {
            // 从输入流中读取当前序列的数据
            std::cout << "请输入序列 A 的新数据: "; std::cin >> value_a;
            std::cout << "请输入序列 B 的新数据: "; std::cin >> value_b;
            if(direction == 'r' || direction == 'R'){
                this->a.push_back(value_a + value_b);++r;
                other.a.push_back(value_b); ++ other.r;
            }else if(direction == 'l' || direction == 'L'){
                this->a.insert(this->a.begin(),value_a+value_b);--l;
                other.a.insert(other.a.begin(),value_b);--other.l;
            }
            std::cout << "序列 A 和 B 之和为" << *this << std::endl;  
        }
    }

    void multi_real_time(DS& other, char direction = 'r' ) {
        double value_a, value_b;
        *this = *this * other;
        std::cout << "序列 A 和 B 之积为" << *this << std::endl; 
        while (true) {
            // 从输入流中读取当前序列的数据
            std::cout << "请输入序列 A 的新数据: "; std::cin >> value_a;
            std::cout << "请输入序列 B 的新数据: "; std::cin >> value_b;
            if(direction == 'r' || direction == 'R'){
                this->a.push_back(value_a * value_b);++r;
                other.a.push_back(value_b); ++ other.r;
            }else if(direction == 'l' || direction == 'L'){
                this->a.insert(this->a.begin(),value_a*value_b);--l;
                other.a.insert(other.a.begin(),value_b);--other.l;
            }
            std::cout << "序列 A 和 B 之积为" << *this << std::endl;  
        }
    }
    friend DS convolution(DS &A, DS &B, char direction = 'n' ){
        DS C(0, A.r + B.r);
        for (int i = A.l; i <= A.r; ++i) {
            for (int j = B.l; j <= B.r; ++j) {
                C[i+j] += A[i] * B[j];
            }
        }
        if(direction == 'r' || direction == 'R'){
            double va, vb;
            while(true){
                std::cout << "请输入序列 A 的新数据: ";std::cin>>va;
                std::cout << "请输入序列 B 的新数据: ";std::cin>>vb;
                A.a.push_back(va);++A.r;
                B.a.push_back(vb);++B.r;
                C.a.resize(A.r + B.r);
                for(int i = A.l; i < A.r; ++i) C.a[i + B.r] += A.a[i] * B.a[B.r];
                for(int i = B.l; i < B.r; ++i) C.a[A.r + i] += A.a[A.r] * B.a[i];
                C.a[A.r + B.r] += A.a[A.r] * B.a[B.r];
                std::cout << "卷积后序列为: " << C << std::endl;
            }
        }
        return C;
    }
    friend DS convolution_cir(DS &A, DS &B, int k, char direction = 'n' ){
        DS C(0, k - 1);
        for (int n = 0; n < k; ++n) {
            for (int m = 0; m <= A.r && m < k; ++m) {
                int j = ((n - m) % k + k) % k;
                if(j <= B.r)
                    C.a[n] += A.a[m] * B.a[j];
            }
        }
        std::cout << k<< "-圆周卷积后序列为: " << C << std::endl;
        if(direction == 'r' || direction == 'R'){
            double va, vb;
            while(true){
                std::cout << "请输入序列 A 的新数据: ";std::cin>>va;
                std::cout << "请输入序列 B 的新数据: ";std::cin>>vb;
                A.a.push_back(va);++A.r;
                B.a.push_back(vb);++B.r;
                if(A.r < k){
                    for (int n = 0; n < k; ++n) {
                        int j = ((n - A.r) % k + k) % k;
                        if(j <= B.r)
                        C.a[n] += A.a[A.r] * B.a[j];
                    }
                }
         
                std::cout << k<< "-圆周卷积后序列为: " << C << std::endl;
            }
        }
        return C;
    }
    void normalize(){
        double sum = std::accumulate(a.begin(),a.end(),0);
        double mean = sum /= (r - l + 1);
        for(auto &i:a){
            i -= mean;
        }
        sum = 0;
        for(auto i:a){
            sum += i * i;
        }
        sum = sqrt(sum);
        for(auto &i:a){
            i /= sum;
        }
    }
    friend double similarity_nomalize(DS &A, DS &B,int l){
        double ret = 0;
        A.normalize();
        B.normalize();
        for(int i = A.l;i <= A.r ; ++ i){
            if(B.l <= i + l && i + l <= B.r)
                ret += A.a[i] * B.a[i + l];
        }
        std::cout << "归一化后序列a为" <<std::endl;
        std::cout << A << std::endl;
        std::cout << "归一化后序列b为" <<std::endl;
        std::cout << B << std::endl;
        std::cout << "l="<<l<<",归一化相似度为"<< ret << std::endl;
        return ret;
    }
    friend double similarity_window(DS &A, DS &B,int l,int k){
        double ret = 0;
        for(int i = std::max(A.l, A.r - k + 1);i <= A.r ; ++ i){
            if(B.l <= i + l && i + l <= B.r)
                ret += A.a[i] * B.a[i + l];
        }
        std::cout << "l="<<l<<",滑动窗相似度为"<< ret << std:: endl;
        while(true){
            double va,vb;
            std::cout << "请输入序列 A 的新数据: ";std::cin>>va;
            std::cout << "请输入序列 B 的新数据: ";std::cin>>vb;
            A.a.push_back(va);++A.r;
            B.a.push_back(vb);++B.r;
            if(B.l <= A.r - k + l && A.r - k + l <= B.r)
                ret -= A.a[A.r - k] * B.a[A.r - k + l];
            if(B.l <= A.r + l && A.r + l <= B.r)    
                ret += A.a[A.r] * B.a[A.r + l];
            std::cout << "l="<<l<<",滑动窗相似度为"<< ret << std:: endl;
        }
        return ret;
    }
};

// 测试代码 
int main() { 
    // 测试信号序列定义、读取写入任意位置、无限长序列的输入
    // std::vector<double> va = {1,2,3,0,5,6};
    // DS a(-3, 2, va); //定义a[-3:2]=[1,2,3,0,5,6]
    // std::cout << a << std::endl;
    // std::cout<<"写入a[-3] = 6, a[-1] = -2, a[2] = 3后"<<std::endl;
    // a[-3] = 6, a[-1] = -2, a[2] = 3;
    // std::cout << a << std::endl;
    // std::cout<<"开始无限长序列的输入："<<std::endl;
    // a.read_infinite(std::cin);//无限长序列的输入
    // std::cout<<"更新后的序列为："<<std::endl;
    // std::cout << a << std::endl;

    // 测试单序列基本操作
    // std::vector<double> va = {1,2,3,0,5,6};
    // DS a(-3, 2, va); //定义a[-3:2]=[1,2,3,0,5,6]
    // std::cout << a << std::endl;
    // // a）前、后补零操作
    // a.pad_zero(2,1);//左侧补2个0，右侧补1个0
    // std::cout<<"左侧补2个0，右侧补1个0后的序列为："<<std::endl;
    // std::cout<<a<<std::endl;
    // // b）序列延迟、提前操作
    // a.delay(3);//延迟3
    // std::cout<<"延迟3个时间单位后的序列为："<<std::endl;
    // std::cout<<a<<std::endl;
    // a.advance(2);//提前2
    // std::cout<<"提前2个时间单位后的序列为："<<std::endl;
    // std::cout<<a<<std::endl;
    // // c）序列反转操作
    // a.reverse();
    // std::cout<<"反转后的序列为："<<std::endl;
    // std::cout<<a<<std::endl;
    // // d）序列拉伸、压缩操作（上采样、下采样)
    // a.stretch(3,'r');//因子=3，向右实时输入并拉伸
    // a.compress(3,'l');//因子=3，向左实时输入并压缩
    // // e）满足序列差分、累加操作
    // a.difference('r');//向右实时输入并差分
    // a.accumulate('r');//向右实时输入并累加
    
    // 测试多序列基本操作
    std::vector<double> va = {1,2,3,0,5,6};
    std::vector<double> vb = {4,3,2,1,5,7};
    DS a(0, 5, va); //定义a[0:5]=[1,2,3,0,5,6]
    DS b(0, 5, vb); //定义b[0:5]=[4,3,2,1,5,7]
    std::cout << "序列a为" <<std::endl;
    std::cout << a << std::endl;
    std::cout << "序列b为" <<std::endl;
    std::cout << b << std::endl;
    DS c = a + b; //加法操作
    std::cout << "序列a与序列b的和为" <<std::endl;
    std::cout << c << std::endl;
    c = a * b; //乘法操作
    std::cout << "序列a与序列b的积为" <<std::endl;
    std::cout << c << std::endl;
    c = convolution(a,b); //线性卷积操作
    std::cout << "序列a与序列b的线性卷积为" <<std::endl;
    std::cout << c << std::endl;
    c = convolution_cir(a,b,8,'r'); //8点圆周卷积，向右实时读入
    std::cout << "序列a为" <<std::endl;
    std::cout << a << std::endl;
    std::cout << "序列b为" <<std::endl;
    std::cout << b << std::endl;
    double ret = similarity_window(a,b,0,3); //滑动窗相似性比对，l=0,滑动窗长度k=3
    ret = similarity_nomalize(a,b,0); //归一化相似性比对，l=0
    return 0;
}

