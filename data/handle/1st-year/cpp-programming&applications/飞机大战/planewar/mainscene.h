#ifndef MAINSCENE_H
#define MAINSCENE_H

#include <QWidget>
#include "map.h"
#include <QTimer>
#include "heroplane.h"
#include "enemyplane.h"
#include "bomb.h"

class MainScene : public QWidget
{
    Q_OBJECT

public:
    MainScene(QWidget *parent = nullptr);
    ~MainScene();

    void initScene();
    //启动游戏  用于启动定时器对象
    void playGame();
    //更新坐标
    void updatePosition();
    //绘图事件
    void paintEvent(QPaintEvent *event);

    void mouseMoveEvent(QMouseEvent *event);

    //敌机出场
    void enemyToScene();

    void collisionDetection();



    Map m_map;

    QTimer m_Timer;

    HeroPlane m_hero;

    //敌机数组
    EnemyPlane m_enemys[ENEMY_NUM];

    //敌机出场间隔记录
    int m_recorder;

    Bomb m_bombs[BOMB_NUM];
};
#endif // MAINSCENE_H
