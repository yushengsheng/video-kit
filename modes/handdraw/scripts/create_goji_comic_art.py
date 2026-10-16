"""Original office comic: adult worker, goji superhero and food props. No image model."""
import json
import math
import random
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

from create_goji_art import Painting, berry, leaf, packet, cup, twig

ROOT=Path(__file__).resolve().parents[1]
CONTENT=ROOT/'content/handdraw-goji-comic-v1'
ASSETS=ROOT/'public/handdraw-goji-comic-v1'
INK='#4b4652'
R=random.Random(108)


def ground(a, mode='office'):
    a.rect(0,0,1600,900,'#fff0d2')
    if mode=='pop':
        a.path('M0 0 L1600 0 L1600 700 Q900 764 0 692 Z','#e8c677',0)
        for angle in range(0,360,18):
            t=math.radians(angle);c=math.cos(t);s=math.sin(t)
            a.path(f'M{900+c*230} {470+s*230} L{900+math.cos(t-.045)*1200} {470+math.sin(t-.045)*1200} L{900+math.cos(t+.045)*1200} {470+math.sin(t+.045)*1200} Z','#fff1c2',0,opacity=.68)
        for x in range(46,1600,37):
            for y in range(265,790,37):
                if (x-900)**2+(y-470)**2>200000:a.oval(x,y,2,2,'#b98a5d',0,opacity=.2)
        return
    a.path('M0 0 L1600 0 L1600 624 Q1050 598 0 651 Z','#d9e9df',0)
    a.path('M0 652 Q600 593 1600 626 L1600 900 L0 900 Z','#eccfa2',0)
    a.rect(1098,86,390,422,'#fcf5dc',3,ink='#6c8c89')
    a.rect(1115,103,355,386,'#b2d7d6')
    for i,xx in enumerate([1130,1210,1293,1385]):
        a.rect(xx,322-i%2*75,54,166+i%2*75,['#9abbaf','#9bbdbb'][i%2])
        for yy in [358,391,424,457]:a.rect(xx+9,yy,9,13,'#e6e0bd')
    a.rect(1284,103,11,386,'#e6e4c9')
    a.rect(1115,284,355,11,'#e6e4c9')
    # Pin board, an uneven plant, and warm window light make the office a place.
    a.path('M89 301 L364 298 L369 559 L91 565 Z','#c1ae86',3,INK)
    for x,y,ang,color in [(113,336,-8,'#f5d287'),(243,327,6,'#f2e6bc'),(149,447,3,'#e8ab8b')]:
        with a.scope(x,y,angle=ang):
            a.rect(0,0,89,78,color,1.2,ink='#a79373')
            for yy in [24,39,54]:a.line(f'M12 {yy} L72 {yy}',1.1,'#a99b7b')
            a.oval(43,4,3,3,'#9d6558',0)
    a.path('M1330 623 L1452 623 L1436 736 L1350 736 Z','#bd7b67',3,INK)
    for i in range(9):
        leaf(a,1391,633,.94,-79+i*20,['#5b8974','#7ea280','#a3b17a'][i%3])
    a.path('M1120 491 L1469 490 L1262 789 L886 789 Z','#fff7d6',0,opacity=.23)


def desk(a,y=652):
    a.path(f'M53 {y} Q808 {y-17} 1518 {y} L1535 {y+38} Q788 {y+25} 37 {y+39} Z','#bd8767',3,INK)
    a.path(f'M64 {y+34} L1493 {y+34} L1493 {y+163} L64 {y+163} Z','#deb78c',2,INK)
    a.line(f'M143 {y+53} L144 {y+163} M1414 {y+53} L1415 {y+163}',4,'#b18e6e')


def monitor(a,x,y,scale=1,pen=False):
    with a.scope(x,y,scale,pen=pen):
        a.path('M-209 -242 L198 -242 Q211 -243 211 -227 L209 -6 L-216 -6 L-220 -223 Q-221 -241 -209 -242 Z','#596b76',3,INK)
        a.rect(-201,-224,391,194,'url(#monitor)',2,ink='#263c52')
        for i in range(7):
            a.rect(-181,-203+i*22,97 if i%2 else 66,5,'#92bdb6',0,opacity=.7)
            a.rect(-68,-203+i*22,166 if i%3 else 111,5,'#d3bb84',0,opacity=.6)
        a.path('M-27 -3 L31 -3 L38 52 L89 65 L-88 65 L-36 51 Z','#8e9b9b',3,INK)
        a.oval(0,-16,3,3,'#d9dcb8',0)


def keyboard(a,x,y,scale=1):
    with a.scope(x,y,scale):
        a.path('M-154 -23 L136 -23 L170 13 L-173 13 Z','#7f9598',2,INK)
        for yy in [-16,-7,2]:
            for xx in range(-133,135,22):a.rect(xx,yy,14,5,'#d9dfc8')


def handline(a,d,width=18):
    a.line(d,width+4,INK)
    a.line(d,width,'#edbb99')


def worker(a,x,y,scale=1,pose='tired',grid=False):
    with a.scope(x,y,scale):
        a.path('M-50 -132 L-60 13 L-18 13 L-1 -109 L18 13 L60 13 L50 -135 Z','#638482',3,INK)
        a.path('M-61 7 Q-77 10 -78 27 L-17 27 L-18 10 M18 9 L18 27 L82 27 Q78 8 58 7','#4a5256',2.5,INK)
        a.path('M-42 -318 Q-97 -300 -104 -259 L-80 -113 Q0 -95 83 -113 L103 -260 Q98 -303 44 -318 Z','#d59059',3,INK)
        a.path('M-57 -286 Q-70 -207 -48 -123 L-26 -119 Q-44 -202 -36 -287 Z','#a86950',0,opacity=.23)
        a.path('M-22 -344 L-21 -313 L1 -284 L23 -313 L23 -344 Z','#e8b48f',2,INK)
        a.path('M-23 -317 L0 -285 L-28 -276 L-46 -310 M24 -317 L0 -285 L29 -277 L46 -310 Z','#f8e7c6',2.1,INK)
        a.path('M0 -280 L2 -112',None,1.8,'#885e4a')
        for yy in [-252,-214,-178]:a.oval(5,yy,2.4,2.4,'#f4ddb6',0)
        # Head-to-body proportion and long jaw distinguish the adult office lead.
        a.path('M-51 -423 Q-79 -465 -44 -489 Q7 -517 47 -486 Q82 -456 56 -405 L49 -371 Q33 -352 18 -355 L-17 -355 Q-35 -353 -49 -371 Z','#57505a',3,INK)
        a.path('M-48 -428 Q-43 -472 -1 -472 Q45 -469 48 -427 L44 -379 Q28 -345 0 -345 Q-32 -348 -44 -378 Z','#efc3a0',2.5,INK)
        a.path('M-50 -425 Q-66 -472 -26 -488 Q19 -510 49 -468 L51 -418 Q25 -437 -3 -465 Q-21 -437 -50 -425 Z','#57505a',2.8,INK)
        a.oval(40,-491,22,22,'#57505a',2,INK)
        a.line('M29 -506 L52 -493',4,'#d28e58')
        a.oval(-46,-392,5,7,'#edb793',1.4,INK)
        a.oval(46,-392,5,7,'#edb793',1.4,INK)
        a.oval(-49,-375,5.5,9,None,2,'#d6ad57')
        a.oval(49,-375,5.5,9,None,2,'#d6ad57')
        a.path('M-34 -413 Q-23 -420 -14 -413 M15 -413 Q27 -420 36 -412',None,2.3,INK)
        if grid:
            for xx in [-25,26]:
                a.path(f'M{xx-17} -406 Q{xx} -416 {xx+17} -406 L{xx+15} -386 Q{xx} -381 {xx-15} -387 Z','#9dbfd0',1.7,'#427486')
                for dd in [-8,0,8]:a.line(f'M{xx+dd} -407 L{xx+dd} -386 M{xx-14} {-402+dd} L{xx+14} {-402+dd}',.8,'#427486')
            a.path('M-17 -362 Q0 -374 19 -363',None,2,'#a46c61')
            a.path('M60 -431 Q76 -410 65 -396 Q54 -405 60 -431 Z','#a0c5cf',1.8,'#4f7b89')
        else:
            a.path('M-34 -400 Q-24 -409 -15 -399 M15 -399 Q25 -409 35 -400',None,2.5,INK)
            a.oval(-24,-400,2.4,3.5,INK,0);a.oval(25,-400,2.4,3.5,INK,0)
            a.path('M-15 -365 Q1 -353 18 -365',None,2,'#a4675f')
        a.line('M1 -396 L-3 -379 L4 -377',1.3,'#b5846b')
        a.oval(-33,-379,9,4,'#de927f',0,opacity=.33);a.oval(33,-379,9,4,'#de927f',0,opacity=.33)
        if pose=='tired':
            a.path('M-81 -292 Q-130 -259 -105 -198 L-45 -208 L-49 -243 L-86 -238 Z','#d59059',2.6,INK)
            handline(a,'M-47 -224 L21 -223')
            a.path('M81 -292 Q121 -267 108 -209 L69 -207 L71 -252 Z','#d59059',2.6,INK)
            handline(a,'M89 -220 Q109 -246 99 -285 L72 -341')
            a.path('M65 -335 L60 -361 Q62 -370 69 -362 L81 -346 L82 -371 Q89 -383 94 -369 L99 -342 Q94 -324 83 -325 Z','#edbb99',2,INK)
        elif pose=='thumb':
            a.path('M-82 -293 Q-116 -270 -107 -217 L-65 -207 L-54 -239 L-86 -244 Z','#d59059',2.6,INK)
            handline(a,'M-65 -224 Q-19 -215 15 -229')
            a.path('M80 -294 Q118 -286 140 -236 L115 -211 L76 -255 Z','#d59059',2.6,INK)
            handline(a,'M125 -229 Q156 -245 157 -283')
            a.path('M146 -285 L145 -317 Q154 -330 160 -316 L163 -298 L180 -303 Q190 -298 186 -286 L176 -266 L156 -266 Z','#edbb99',2,INK)
        elif pose=='eat':
            a.path('M-82 -293 Q-124 -272 -110 -214 L-55 -208 L-48 -242 L-86 -248 Z','#d59059',2.6,INK)
            handline(a,'M-51 -225 L9 -217')
            a.path('M81 -293 Q122 -274 108 -227 L72 -220 L64 -256 Z','#d59059',2.6,INK)
            handline(a,'M89 -239 Q62 -282 32 -332')
            a.path('M19 -331 Q11 -343 21 -351 L42 -344 Q50 -330 36 -324 Z','#edbb99',2,INK)
            berry(a,18,-350,.18,-20)
        elif pose=='bowl':
            for flip in [-1,1]:
                with a.scope(flip=flip):
                    a.path('M78 -293 Q120 -265 110 -216 L52 -207 L47 -239 L85 -249 Z','#d59059',2.6,INK)
                    handline(a,'M54 -226 L17 -230')
        else:
            a.path('M-81 -293 Q-124 -264 -106 -216 L-51 -214 L-45 -242 L-85 -249 Z','#d59059',2.6,INK)
            a.path('M81 -293 Q119 -264 105 -215 L50 -215 L45 -243 L85 -248 Z','#d59059',2.6,INK)
            handline(a,'M-51 -230 L-13 -223 M50 -230 L11 -221')


def hero(a,x,y,scale=1,pen=False,pose='fly'):
    with a.scope(x,y,scale,pen=pen,motion='hero'):
        a.path('M-47 -83 Q-104 -86 -193 -30 Q-149 57 -100 112 Q-117 42 -45 59 L26 77 Q73 -10 41 -85 Z','#d35d57',3,INK)
        a.path('M-51 -62 Q-98 -30 -145 8 Q-118 28 -105 67 Q-107 10 -42 -8 Z','#b24448',0,opacity=.35)
        a.line('M-49 74 L-58 123 M49 74 L67 120',14,INK)
        a.line('M-49 74 L-58 123 M49 74 L67 120',9,'#5c8796')
        a.path('M-70 111 Q-98 108 -100 129 L-44 134 L-43 112 M53 111 L49 132 L108 131 Q109 112 82 112 Z','#5b8093',3,INK)
        a.path('M-72 -23 Q-111 -49 -133 -30 M70 -24 Q108 -84 133 -90',None,17,INK)
        a.path('M-72 -23 Q-111 -49 -133 -30 M70 -24 Q108 -84 133 -90',None,11,'#657f98')
        for xx,yy,angle in [(-139,-32,-30),(141,-96,15)]:
            with a.scope(xx,yy,angle=angle):
                a.path('M-18 -13 Q-8 -27 6 -20 Q23 -23 25 -8 L21 12 Q4 26 -18 13 Z','#f6edcf',2.6,INK)
                a.path('M-12 -9 L-4 -11 M0 -10 L8 -12 M11 -8 L17 -9',None,1.5,INK)
        a.path('M0 -137 C62 -139 93 -82 85 -9 C80 57 43 101 -5 102 C-53 97 -87 63 -87 -6 C-91 -78 -58 -133 0 -137 Z','url(#berry)',3.4,INK)
        a.path('M-48 -102 Q-70 -54 -55 -14',None,10,'#efaf6a',opacity=.62)
        a.path('M-18 -137 Q-18 -160 2 -168 Q24 -158 14 -137 Z','#7f9e69',2.2,INK)
        a.path('M-53 -41 Q-35 -57 -16 -44 M18 -44 Q37 -59 55 -42',None,4,INK)
        a.oval(-34,-39,5,7,INK,0);a.oval(36,-39,5,7,INK,0)
        a.path('M-29 -8 Q1 26 33 -8 Q8 46 -17 22 Z','#fff1d2',3,INK)
        a.oval(-58,-16,12,6,'#efa17d',0);a.oval(60,-16,12,6,'#efa17d',0)
        a.path('M-79 47 Q0 69 80 46 L73 65 Q-3 87 -73 66 Z','#eec460',2,INK)
        a.path('M-12 58 L13 58 L13 78 L-12 78 Z','#f5df98',2,INK)


def burst(a,x,y,scale=1):
    with a.scope(x,y,scale,motion='spark'):
        a.path('M0 -34 L9 -10 L35 -18 L20 3 L35 23 L9 16 L-2 40 L-12 15 L-37 25 L-23 3 L-37 -17 L-11 -10 Z','#f5cf68',2,INK)


def shield(a,x,y,scale=1,color='#7596a7'):
    with a.scope(x,y,scale,pen=True,motion='shield'):
        a.path('M-134 -125 Q0 -160 134 -125 L125 25 Q111 111 0 163 Q-115 111 -126 25 Z',color,3.6,INK)
        a.path('M-115 -110 Q0 -141 115 -110 L107 23 Q90 91 0 140 Q-94 92 -109 21 Z',None,4,'#f6db86')
        a.path('M-87 -85 Q-28 -104 48 -90',None,9,'#ebf3dd',opacity=.4)
        for i in [-1,0,1]:a.oval(i*51,-10,12,12,'#e3e9ce',1.7,INK)
        a.line('M-39 -10 L-12 -10 M12 -10 L39 -10',3,'#e3e9ce')


def battery(a,x,y,full=False,scale=1):
    with a.scope(x,y,scale,motion='battery-full' if full else 'battery-low'):
        a.path('M-126 -42 L116 -42 Q125 -42 125 -32 L125 34 Q125 43 115 43 L-126 43 Z','#fff5db',3.2,INK)
        a.rect(125,-17,14,35,'#777e79',2,ink=INK)
        for i in range(5):a.rect(-116+i*46,-32,37,64,'#79a58a' if full else '#e16d5d' if i==0 else '#e5d9b8',1.5,ink='#a4987d')


def pile(a,x,y,scale=1,count=16):
    with a.scope(x,y,scale):
        a.oval(0,40,126,23,'#bd9e76',0,opacity=.18)
        for i in range(count):berry(a,R.uniform(-105,105),R.uniform(-16,29),.43,R.uniform(-75,75))


def porridge(a,x,y,scale=1):
    with a.scope(x,y,scale):
        a.path('M-139 -19 Q-121 94 -1 97 Q120 92 140 -19 Z','#729b9b',3,INK)
        a.oval(0,-20,144,45,'#eee1b2',3,INK)
        for i in range(40):a.oval(R.uniform(-119,119),R.uniform(-43,4),5,2.3,'#fff5d5',0)
        for i in range(10):berry(a,R.uniform(-100,100),R.uniform(-39,3),.31,R.uniform(-40,40))
        with a.scope(motion='steam'):
            a.path('M-56 -65 Q-79 -104 -50 -126 Q-30 -146 -49 -169 M10 -72 Q-12 -111 15 -132 Q38 -152 15 -180 M74 -64 Q53 -109 83 -134',None,4,'#fff7de',opacity=.85)


def build(representative=False):
    scenes=[]
    def save(id,a):scenes.append({'id':id,'shapes':a.shapes})
    a=Painting();ground(a);worker(a,590,767,1.12,grid=True);desk(a)
    monitor(a,1035,618,1.0,True);keyboard(a,838,687,1.1);battery(a,614,145,False,.8)
    cup(a,280,681,.48);burst(a,1334,254,.45);save('screen',a)

    a=Painting();ground(a,'pop')
    for x,y,s in [(1157,478,1),(1176,570,.8),(1234,471,.8)]:
        with a.scope(x,y,s,motion='smoke'):
            a.path('M-71 -8 Q-100 -63 -48 -83 Q-12 -120 18 -75 Q81 -83 80 -32 Q127 20 69 53 Q43 92 1 66 Q-55 99 -78 47 Q-119 33 -71 -8 Z','#7a7882',0,opacity=.28)
    hero(a,900,477,1.75,True);burst(a,1150,313,.7);burst(a,592,438,.5)
    a.path('M231 573 L473 573 L473 700 L231 700 Z','#fff0c9',3,INK)
    a.path('M279 563 Q249 502 300 472 M418 563 Q449 503 395 471',None,6,'#678b83')
    save('hero',a)
    if representative:return scenes

    a=Painting();ground(a,'pop');shield(a,466,463,1.08,'#7099aa');shield(a,1211,463,1.08,'#9fa66e')
    hero(a,856,544,1.03);burst(a,289,319,.56);burst(a,1397,641,.6);save('shields',a)

    a=Painting();ground(a);worker(a,498,759,1.03,pose='read');desk(a,647)
    a.path('M624 587 Q786 547 938 588 Q1106 549 1287 590 L1308 728 Q1093 687 937 737 Q776 691 609 733 Z','#f5e5bc',3,INK)
    a.path('M938 588 L937 737',None,3,'#b9a382')
    for yy in range(618,703,20):a.line(f'M668 {yy} Q770 {yy-20} 885 {yy} M991 {yy} Q1098 {yy-18} 1236 {yy}',1.8,'#b6a587')
    twig(a,1086,642,.55,-65,motion='leaves');hero(a,1371,551,.65);cup(a,228,679,.65);save('traditional',a)

    a=Painting();a.rect(0,0,800,900,'#e6d9d1');a.rect(800,0,800,900,'#deead8')
    a.path('M800 114 Q789 455 802 806',None,3,INK)
    for xx in [395,1195]:
        pile(a,xx,644,1.2,24);cup(a,xx,514,1.7)
    for xx,yy in [(372,484),(418,493)]:berry(a,xx,yy,.42,30)
    for xx,yy in [(1183,334),(1238,355)]:berry(a,xx,yy,.43,-20)
    # Different colors are descriptions, never a red X versus a green quality guarantee.
    a.oval(801,482,69,69,'#faedcd',3,INK);save('compare',a)

    a=Painting();ground(a);worker(a,1272,753,.87,pose='read');desk(a,657)
    a.path('M104 687 L267 553 Q308 513 364 529 L490 576 L680 536 Q720 544 699 562 L527 619 L712 592 Q749 605 720 622 L535 678 L670 661 Q697 677 667 693 L475 739 L286 767 Z','#edbd99',3,INK)
    for xx,yy,ang in [(377,586,34),(425,594,-28),(475,575,21),(463,648,22),(372,652,-21)]:
        with a.scope(pen=True):berry(a,xx,yy,.65,ang)
    packet(a,875,744,.93,True)
    a.path('M1021 631 L1167 646 L1152 749 L1005 734 Z','#f5e8c9',2,INK)
    for yy in [660,679,698]:a.line(f'M1037 {yy} L1136 {yy+8}',2,'#9ba48b')
    burst(a,701,465,.45);save('quality',a)

    a=Painting();ground(a);worker(a,646,768,1.16,pose='eat');desk(a,681)
    packet(a,1037,718,1.14,True);hero(a,1349,550,.6)
    # A visible food-instruction document is inspected before any imagined snack.
    a.path('M306 491 L476 512 L454 654 L290 628 Z','#fff4da',2.5,INK)
    for yy in [542,563,584,605]:a.line(f'M322 {yy} L435 {yy+12}',2,'#95a69a')
    with a.scope(motion='heart'):
        a.path('M800 373 C775 341 795 322 812 344 C836 318 855 343 835 365 L813 389 Z','#d77c75',2,INK)
        a.path('M857 426 C841 408 854 393 865 407 C882 389 894 407 881 422 L868 436 Z','#e4a28c',1.5,INK)
    save('snack',a)

    a=Painting();ground(a);desk(a,669)
    # Insulated mug with an open lid and two berries falling into the liquid.
    a.path('M375 392 L584 392 L567 739 Q477 770 392 739 Z','#9cbdb9',3,INK)
    a.path('M392 413 L567 413 L553 725 Q479 744 406 725 Z','#eee0aa',0)
    a.oval(479,393,105,30,'#f5e7b7',3,INK)
    a.path('M584 450 Q690 437 665 572 Q650 620 574 610',None,15,'#71999b')
    a.oval(281,699,76,25,'#67858a',3,INK)
    with a.scope(pen=True,motion='berrydrop'):
        berry(a,469,334,.73,10);berry(a,516,279,.58,-28)
    a.path('M996 410 L1255 410 L1231 641 L1020 641 Z','#d7e0c7',3,INK)
    a.path('M1014 455 L1235 455 L1219 621 L1031 621 Z','#f3e6b5',0)
    a.path('M979 651 L1266 651 L1283 747 L962 747 Z','#8aaeb1',3,INK)
    a.oval(1120,697,22,22,'#f5dfac',2,INK)
    a.path('M1256 456 Q1367 421 1354 531 Q1349 580 1238 587',None,13,'#83a4a6')
    a.path('M1003 389 L1249 389 L1264 411 L988 411 Z','#63888c',3,INK)
    for xx,yy in [(1073,562),(1184,593),(1149,482)]:berry(a,xx,yy,.48,25)
    hero(a,854,571,.55);save('tea',a)

    a=Painting();ground(a);worker(a,705,760,1.04,pose='bowl');desk(a,676)
    porridge(a,705,554,1.02);hero(a,1070,615,.45);cup(a,293,707,.8)
    berry(a,1274,702,.8,-29);berry(a,1334,723,.65,39);save('porridge',a)

    a=Painting();ground(a);worker(a,710,759,1.04,pose='thumb');desk(a,699)
    packet(a,1064,739,1.18,True);hero(a,1354,581,.63);pile(a,334,704,.68,13)
    save('choice',a)

    a=Painting();ground(a,'pop');worker(a,655,762,1.07,pose='thumb');battery(a,662,159,True,.98)
    packet(a,616,629,.5);hero(a,1105,544,1.13);burst(a,1353,370,.7);burst(a,322,516,.58)
    # A closed laptop and an outdoor leaf motif explicitly include taking a break.
    a.path('M183 692 L401 692 L439 730 L156 730 Z','#8ba5a2',3,INK)
    leaf(a,1416,739,1.6,23,'#8caa7a');leaf(a,1407,748,1.2,-57,'#5e8c75')
    save('ending',a)
    return scenes


def texture():
    rng=np.random.default_rng(106)
    n=rng.normal(0,1.1,(1080,1920,1))
    img=np.clip(np.array([252,243,218])[None,None,:]+n,0,255).astype('uint8')
    Image.fromarray(img).save(ASSETS/'paper.jpg',quality=92)


def sound():
    tl=json.loads((CONTENT/'timeline.json').read_text());sr=24000;n=round(tl['durationSeconds']*sr)
    mix=np.zeros(n);rng=np.random.default_rng(109)
    def add(start,signal,gain=1):
        i=round(start*sr);end=min(n,i+len(signal))
        if end>i:mix[i:end]+=signal[:end-i]*gain
    def note(freq,length=.5):
        t=np.arange(int(sr*length))/sr
        return (np.sin(2*np.pi*freq*t)+.2*np.sin(2*np.pi*freq*2*t))*(1-np.exp(-90*t))*np.exp(-t*8)
    notes=[329.63,392.0,440.0,523.25,440,392,293.66,329.63]
    for i,start in enumerate(np.arange(.6,tl['durationSeconds']-.5,.63)):
        add(start,note(notes[i%8],.65),.023)
        if i%2==0:add(start,note(130.81 if i%8<4 else 146.83,.5),.018)
        if i%4==0:
            t=np.arange(int(.13*sr))/sr;add(start,np.sin(2*np.pi*(85*t-210*t*t))*np.exp(-35*t),.027)
    for start in [.12,.49,.86]:add(start,note(784,.19),.056)
    for s in tl['scenes']:
        start=s['from']/30
        if s['id']=='hero':
            t=np.arange(int(.45*sr))/sr
            whoosh=np.convolve(rng.normal(0,1,len(t)),np.ones(7)/7,'same')*np.sin(np.pi*t/.45)**2
            add(start+.05,whoosh,.05)
            for i,f in enumerate([392,523.25,659.25]):add(start+.13+i*.10,note(f,.8),.051)
        if s['id']=='shields':
            add(start+.25,note(1318.5,.8),.037);add(start+.54,note(1568,.8),.028)
        if s['id']=='compare':
            t=np.arange(int(.18*sr))/sr;add(start+.12,np.sin(2*np.pi*196*t)*np.sin(np.pi*t/.18)**2,.035)
        if s['id']=='quality':
            add(start+.2,note(659.25,.6),.04);add(start+.36,note(880,.65),.04)
        if s['id']=='snack':
            for off in [.15,.29]:
                t=np.arange(int(.12*sr))/sr;add(start+off,rng.normal(0,1,len(t))*np.exp(-45*t),.023)
        if s['id']=='tea':add(start+.3,note(1174.66,.8),.032)
        if s['id']=='ending':
            for i,f in enumerate([523.25,659.25,783.99,1046.5]):add(start+.1+i*.1,note(f,.95),.044)
    mix*=np.minimum(np.arange(n)/sr/.4,1)*np.minimum((n-np.arange(n))/sr/1.15,1)
    with wave.open(str(ASSETS/'audio/music-foley.wav'),'wb') as f:
        f.setnchannels(2);f.setsampwidth(2);f.setframerate(sr)
        f.writeframes((np.column_stack((mix,mix*.97))*32767).clip(-32767,32767).astype('<i2').tobytes())


if __name__=='__main__':
    import sys
    ASSETS.mkdir(parents=True,exist_ok=True);(ASSETS/'audio').mkdir(exist_ok=True)
    scenes=build('--representative' in sys.argv)
    (CONTENT/'art.json').write_text(json.dumps(scenes,ensure_ascii=False,separators=(',',':')))
    texture();sound()
    print(json.dumps({'scenes':len(scenes),'shapes':[len(s['shapes']) for s in scenes]}))
