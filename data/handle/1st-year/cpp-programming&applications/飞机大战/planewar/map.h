#ifndef MAP_H
#define MAP_H
#include<QPixmap>

class Map
{
public:
    Map();

    void mapPosition();

public:

    QPixmap m_map1;
    QPixmap m_map2;

    int m_map1_posY;
    int m_map2_posY;

    int m_scroll_speed;
};

#endif // MAP_H
