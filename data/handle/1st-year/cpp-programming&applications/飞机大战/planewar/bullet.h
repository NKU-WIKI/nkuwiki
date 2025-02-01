#ifndef BULLET_H
#define BULLET_H
#include "config.h"
#include <QPixmap>

class Bullet
{
public:
    Bullet();

    void updatePosition();

public:


    QPixmap m_Bullet;

    int m_X;
    int m_Y;

    int m_Speed;

    bool m_Free;

    QRect m_Rect;
};

#endif // BULLET_H
