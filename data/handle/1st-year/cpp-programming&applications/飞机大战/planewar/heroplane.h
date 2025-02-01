#ifndef HEROPLANE_H
#define HEROPLANE_H
#include <QPixmap>
#include "bullet.h"
class HeroPlane
{
public:
    HeroPlane();

    void shoot();

    void setPosition(int x,int y);

public:

        QPixmap m_Plane;

        int m_X;
        int m_Y;

        QRect m_Rect;

        //弹匣
        Bullet m_bullets[BULLET_NUM];

        //发射间隔记录
        int m_recorder;
};

#endif // HEROPLANE_H
