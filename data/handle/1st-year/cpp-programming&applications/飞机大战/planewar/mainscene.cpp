#include "mainscene.h"
#include "config.h"
#include "map.h"
#include <QPainter>
#include <QMouseEvent>
#include <ctime>
#include <QtMultimedia/QAudio>
#include <QtMultimedia/QMediaPlayer>

MainScene::MainScene(QWidget *parent)
    : QWidget(parent)
{
    initScene();
}

MainScene::~MainScene()
{}

void MainScene::initScene()
{
    setFixedSize(GAME_WIDTH,GAME_HEIGHT);

    setWindowTitle(GAME_TITLE);

    setWindowIcon(QIcon(GAME_ICON));

    m_Timer.setInterval(GAME_RATE);

    m_recorder=0;

    srand((unsigned int)time(NULL));

    playGame();

}

void MainScene::playGame()
{
    m_Timer.start();


    connect(&m_Timer,&QTimer::timeout,[=](){
        enemyToScene();
        updatePosition();
        update();
        collisionDetection();
    });
}

void MainScene::updatePosition()
{
    m_map.mapPosition();

    m_hero.shoot();

    for(int i = 0 ;i < BULLET_NUM;i++)
    {
        if(!m_hero.m_bullets[i].m_Free)
        {
            m_hero.m_bullets[i].updatePosition();
        }
    }
    for(int i = 0 ; i< ENEMY_NUM;i++)
    {
        //非空闲敌机 更新坐标
       if(m_enemys[i].m_Free == false)
       {
          m_enemys[i].updatePosition();
       }
    }
    for(int i = 0 ; i < BOMB_NUM;i++)
    {
        if(m_bombs[i].m_Free == false)
        {
           m_bombs[i].updateInfo();
        }
    }
}

void MainScene::paintEvent(QPaintEvent *event)
{
    QPainter painter(this);

    painter.drawPixmap(0,m_map.m_map1_posY,m_map.m_map1);
    painter.drawPixmap(0,m_map.m_map2_posY,m_map.m_map2);

    painter.drawPixmap(m_hero.m_X,m_hero.m_Y,m_hero.m_Plane);

    for(int i = 0 ;i < BULLET_NUM;i++)
    {
        if(!m_hero.m_bullets[i].m_Free)
        {
            painter.drawPixmap(m_hero.m_bullets[i].m_X,m_hero.m_bullets[i].m_Y,m_hero.m_bullets[i].m_Bullet);
        }
    }
    for(int i = 0 ; i< ENEMY_NUM;i++)
    {
        if(m_enemys[i].m_Free == false)
        {
            painter.drawPixmap(m_enemys[i].m_X,m_enemys[i].m_Y,m_enemys[i].m_enemy);
        }
    }
    for(int i = 0 ; i < BOMB_NUM;i++)
    {
        if(m_bombs[i].m_Free == false)
        {
            painter.drawPixmap(m_bombs[i].m_X,m_bombs[i].m_Y,m_bombs[i].m_pixArr[m_bombs[i].m_index]);
        }
    }
}

void MainScene::mouseMoveEvent(QMouseEvent *event)
{
    int x = event->x() - m_hero.m_Rect.width()*0.5; //鼠标位置 - 飞机矩形的一半
    int y = event->y() - m_hero.m_Rect.height()*0.5;

    //边界检测
    if(x <= 0 )
    {
        x = 0;
    }
    if(x >= GAME_WIDTH - m_hero.m_Rect.width())
    {
        x = GAME_WIDTH - m_hero.m_Rect.width();
    }
    if(y <= 0)
    {
        y = 0;
    }
    if(y >= GAME_HEIGHT - m_hero.m_Rect.height())
    {
        y = GAME_HEIGHT - m_hero.m_Rect.height();
    }
    m_hero.setPosition(x,y);
}

void MainScene::enemyToScene()
{
    m_recorder++;
    if(m_recorder < ENEMY_INTERVAL)
    {
        return;
    }

    m_recorder = 0;

    for(int i = 0 ; i< ENEMY_NUM;i++)
    {
        if(m_enemys[i].m_Free)
        {
            //敌机空闲状态改为false
            m_enemys[i].m_Free = false;
            //设置坐标
            m_enemys[i].m_X = rand() % (GAME_WIDTH - m_enemys[i].m_Rect.width());
            m_enemys[i].m_Y = -m_enemys[i].m_Rect.height();
            break;
        }
    }
}

void MainScene::collisionDetection()
{
    for(int i = 0 ;i < ENEMY_NUM;i++)
    {
        if(m_enemys[i].m_Free)
        {
            continue;
        }

        for(int j = 0 ; j < BULLET_NUM;j++)
        {
            if(m_hero.m_bullets[j].m_Free)
            {
                continue;
            }
            if(m_enemys[i].m_Rect.intersects(m_hero.m_bullets[j].m_Rect))
            {
                m_enemys[i].m_Free = true;
                m_hero.m_bullets[j].m_Free = true;
                for(int k = 0 ; k < BOMB_NUM;k++)
                {
                    if(m_bombs[k].m_Free)
                    {
                        //爆炸状态设置为非空闲
                        m_bombs[k].m_Free = false;
                        //更新坐标

                        m_bombs[k].m_X = m_enemys[i].m_X;
                        m_bombs[k].m_Y = m_enemys[i].m_Y;
                        break;
                    }
                }
            }
        }
    }

}
