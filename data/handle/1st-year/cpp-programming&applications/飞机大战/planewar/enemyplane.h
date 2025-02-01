#ifndef ENEMYPLANE_H
#define ENEMYPLANE_H
#include <QPixmap>

class EnemyPlane
{
public:
    EnemyPlane();

    void updatePosition();

public:

    QPixmap m_enemy;

    int m_X;
    int m_Y;

    QRect m_Rect;

    bool m_Free;

    int m_Speed;

};

#endif // ENEMYPLANE_H
