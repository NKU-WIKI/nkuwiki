cmake_minimum_required(VERSION 3.10)   # 指定最低 CMake 版本

project(LAB2)          # 定义项目名称和版本

# 设置 C++ 标准为 C++11
set(CMAKE_CXX_STANDARD 11)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# set(CMAKE_C_COMPILER "C:/MinGW/bin/gcc.exe")   # 修改为你的 gcc 路径
# set(CMAKE_CXX_COMPILER "C:/MinGW/bin/g++.exe")  # 修改为你的 g++ 路径

# 添加头文件搜索路径
include_directories(${PROJECT_SOURCE_DIR}/include)

# 添加源文件
# add_library(MyLib src/printhello.cpp)        # 创建一个库目标 MyLib
add_executable(main src/main.cpp)  # 创建一个可执行文件目标 Main

# 链接库到可执行文件
# target_link_libraries(main MyLib)