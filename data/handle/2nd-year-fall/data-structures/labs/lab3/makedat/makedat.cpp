/**
 * Date: 2019-08-05 15:20:11
 * LastEditors: Aliver
 * LastEditTime: 2019-08-25 17:12:56
 */
#define _CRT_SECURE_NO_WARNINGS
#include <iostream>
#include <algorithm>
#include <fstream>
#include <time.h>
#include <cstdlib>
#include <string>
#include <cstring>
#include <set>
using namespace std;

#define OK    1
#define ERROR 0
#define TRUE  1
#define FALSE 0

typedef int Status;

Status Usage()
{
	cout << "--------------------------------------------------------------------------------------" << endl;
	cout << "makedat用法如下：" << endl;
	cout << "1、共五个参数：--help，--minkey [t]，--maxkey [l]，--output [filename]，--cmdnum [x], --order [m]" << endl;
	cout << "--------------------------------------------------------------------------------------" << endl;

	return OK;
}

Status MakeDataFile( const char *Filename, int MinKey, int MaxKey, int cmdNum, int order )
{
	srand( (unsigned int)(time( 0 )) );     //生成随机种子

	ofstream fout( Filename, ios::out );
	if ( !fout.is_open() )
		throw runtime_error( "文件打开失败!" );

	int Cur = 0;        
	int Total = 0;
    int key;
    set<decltype(key)> keys;

    unsigned int SearchNum = 0;
	unsigned int InsertNum = 0;
	unsigned int DeleteNum = 0;

    const char *Insert = "insert ";
    const char *Delete = "delete ";
    const char *Search = "find ";

    // B tree 的阶
    fout << "m " << order << endl;

    while ( Total < cmdNum ) {
        Cur = rand() % 100 + 1;
        if ( Cur > 0 && Cur <= 50 ) {
            while (1) {
                key = rand() % (MaxKey - MinKey) + MinKey;
                if (!keys.count(key)) {
                    fout << Insert << key << endl;
                    keys.insert(key);
                    break;
                } 
                else {
                    if ((rand() % 16) <= 2 ) {
                        fout << Insert << key << endl;
                        break;
                    }
                }
            }
        }
        else if (Cur > 50 && Cur <= 70) {
            while (1) {
                key = rand() % (MaxKey - MinKey) + MinKey;
                if (keys.count(key)) {
                    fout << Search << key << endl;
                    keys.insert(key);
                    break;
                }
                else {
                    if ((rand() % 16) < 1 ) {
                        fout << Search << key << endl;
                        break;
                    }
                }
            }
        }
        else if (Cur > 70 && Cur <= 95) {
            while (1) {
                key = rand() % (MaxKey - MinKey) + MinKey;
                if (keys.count(key)) {
                    fout << Delete << key << endl;
                    keys.insert(key);
                    break;
                }
                else {
                    if ((rand() % 16) < 1 ) {
                        fout << Delete << key << endl;
                        break;
                    }
                }
            }
        }
        else if (Cur > 95 && Cur <= 100) {
            fout << "error " << key << endl;
        }
        ++Total;
    }

    fout.close();
    return OK;
}

int main( int argc, char *argv[] )
{
	int cmdNum = 100;
    int order = 3;
    int MinKey = 1;
	int MaxKey = (double)(1.5 * cmdNum);
    char Filename[128] = "a.dat";

    if ( 1 == argc ) {
		cout << "正在生成数据文件......" << endl;
        cout << "共 " << cmdNum << " 条基本操作命令, B-Tree的阶为 " << order << endl;
        MakeDataFile(Filename, MinKey, MaxKey, cmdNum, order);
    }
	else {
		for ( int i = 1; i < argc; i++ ) {
			if ( !strcmp( argv[i], "--help" ) ) {
				Usage();
				return 0;
			}
			else if ( !strcmp( argv[i], "--minkey" ) ) {
				if ( !argv[i + 1] )
					break;
				int temp = atoi( argv[i + 1] );
				if ( temp > 0 ) {
					MinKey = temp;
					++i;
				}
			}
			else if ( !strcmp( argv[i], "--maxkey" ) ) {
				if ( !argv[i + 1] )
					break;
				int temp = atoi( argv[i + 1] );
				if ( temp > 0 ) {
					MaxKey = temp;
					++i;
				}
			}
			else if ( !strcmp( argv[i], "--cmdnum" ) ) {
				if ( !argv[i + 1] )
					break;
				int temp = atoi( argv[i + 1] );
				if ( temp > 0 ) {
					cmdNum = temp;
					++i;
				}
			}
			else if ( !strcmp( argv[i], "--output" ) ) {
				if ( !argv[i + 1] )
					break;
				strcpy( Filename, argv[i + 1] );
				++i;
			}
            else if ( !strcmp( argv[i], "--order") ) {
                if ( !argv[i + 1] )
					break;
                int temp = atoi( argv[i + 1] );
				if ( temp > 0 ) {
                    order = temp;
                    ++i;
				}
            }
		}
		if ( MaxKey <= MinKey ){
			MaxKey = 1024;
			MinKey = 1;
		}

		cout << "正在生成数据文件......" << endl;
		cout << "共 " << cmdNum << " 条基本操作命令, B-Tree的阶为 " << order << endl;
		MakeDataFile( Filename, MinKey, MaxKey, cmdNum, order );
	}

	return 0;
}