"""Original layered gouache-style goji illustrations, sound bed, and editable SVG paths."""
import json
import math
import random
import wave
from contextlib import contextmanager
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

from create_moon_art import Art

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / 'content/handdraw-goji-v1'
ASSETS = ROOT / 'public/handdraw-goji-v1'
INK = '#585644'
R = random.Random(10715)


class Painting(Art):
    def __init__(self):
        super().__init__()
        self.pen = False
        self.motion = ''

    @contextmanager
    def scope(self, x=0, y=0, scale=1, angle=0, flip=1, pen=None, motion=None):
        previous = self.matrix, self.pen, self.motion
        a, b, c, d, e, f = self.matrix
        t = math.radians(angle)
        p, q, r, s = math.cos(t)*scale*flip, math.sin(t)*scale*flip, -math.sin(t)*scale, math.cos(t)*scale
        self.matrix = a*p+c*q, b*p+d*q, a*r+c*s, b*r+d*s, a*x+c*y+e, b*x+d*y+f
        if pen is not None:
            self.pen = pen
        if motion is not None:
            self.motion = motion
        try:
            yield
        finally:
            self.matrix, self.pen, self.motion = previous

    def path(self, data, fill=None, width=1.8, ink=INK, opacity=1, draw=None):
        scale = math.hypot(self.matrix[0], self.matrix[1])
        super().path(data, fill, width*scale, ink, opacity, self.pen if draw is None else draw)
        self.shapes[-1]['motion'] = self.motion

    def rect(self, x, y, w, h, fill, width=0, **kw):
        self.path(f'M{x} {y} L{x+w} {y} L{x+w} {y+h} L{x} {y+h} Z', fill, width, **kw)


def leaf(a, x, y, scale=1, angle=0, color='#78955a'):
    with a.scope(x, y, scale, angle):
        a.path('M0 0 C-27 -11 -38 -42 -16 -65 C14 -62 24 -22 0 0 Z', color, 1, '#63784d')
        a.line('M0 -2 Q-9 -29 -16 -58', .9, '#bac38b', opacity=.8)


def berry(a, x, y, scale=1, angle=0, ripe=True):
    with a.scope(x, y, scale, angle):
        a.path('M0 -26 C12 -25 20 -12 17 6 C15 22 7 33 -2 34 C-15 32 -20 19 -18 2 C-17 -16 -11 -26 0 -26 Z',
               'url(#berry)' if ripe else '#a8b46d', 1.1, '#a74937' if ripe else '#7f8954')
        a.path('M-7 -17 C-14 -3 -12 14 -7 23 C-8 7 -6 -3 -3 -14 Z', '#f4b278', 0, opacity=.65)
        a.line('M7 -17 Q11 -1 7 15 M1 5 Q-1 20 -3 26', .9, '#a73d32', opacity=.56)
        a.oval(0, -25, 3.1, 2.4, '#eee0b1', .4, '#b29c72')


def twig(a, x, y, scale=1, angle=0, count=7, motion='leaves'):
    with a.scope(x, y, scale, angle, motion=motion):
        a.path('M-4 135 Q-3 -36 32 -154 Q10 -19 5 135 Z', '#9b8659', .8, '#77684c')
        for i in range(count):
            yy = 105-i*37
            xx = 5+(105-yy)*.08
            side = -1 if i%2 else 1
            a.line(f'M{xx} {yy} Q{xx+side*29} {yy-18} {xx+side*45} {yy-28}', 1.5, '#827451')
            leaf(a, xx+side*20, yy-18, .62, -side*48, R.choice(['#759353','#92a65d','#587e55']))
            berry(a, xx+side*42, yy+3, .48, side*18)
            if i%2:
                berry(a, xx+side*63, yy-6, .38, -side*21)


def cloud(a, x, y, scale=1):
    with a.scope(x, y, scale):
        a.path('M-130 20 C-144 0 -112 -22 -80 -17 C-67 -55 -4 -64 16 -21 C65 -46 111 -13 108 9 C143 13 154 29 139 38 L-117 38 Z', '#fff4d9', 0, opacity=.78)


def landscape(a, theme='field'):
    a.part = 'background'
    a.rect(0, 0, 1600, 900, 'url(#sky)')
    a.oval(1290, 145, 100, 100, '#fff1c6', 0, opacity=.5)
    cloud(a, 370, 120, 1.4)
    cloud(a, 1090, 200, .8)
    for d, fill in [
        ('M0 435 Q160 310 330 408 Q470 277 640 400 Q850 245 1050 375 Q1290 274 1600 387 L1600 900 L0 900 Z','#a7b6a0'),
        ('M0 511 Q180 402 376 472 Q567 366 741 488 Q1039 365 1251 471 Q1450 397 1600 453 L1600 900 L0 900 Z','#91a789'),
        ('M0 576 Q241 478 480 548 Q742 453 1000 545 Q1290 466 1600 547 L1600 900 L0 900 Z','#b6b97b')]:
        a.path(d, fill, 0)
    a.path('M0 690 Q380 544 710 617 Q1200 520 1600 620 L1600 900 L0 900 Z', '#cfbd80', 0)
    a.path('M650 900 Q828 748 851 615 Q883 550 1000 531 Q920 577 927 638 Q932 770 1100 900 Z', '#dfcba1', 0)
    for i in range(13):
        yy = 532+i*20
        a.line(f'M0 {yy+70} Q330 {yy-18} 615 {yy+5} M1030 {yy+4} Q1310 {yy-52} 1600 {yy-12}', 2.5, '#96975c', opacity=.38)
    # Small settlement and distant poplars establish depth without dominating the scene.
    for i in range(7):
        x = 1060+i*65
        a.rect(x, 452, 45, 47, '#e6d5ad')
        a.path(f'M{x-8} 454 L{x+21} 429 L{x+54} 454 Z', '#7f8a76', 1.2)
        a.rect(x+17, 474, 10, 24, '#9d9171')
    for i in range(23):
        x=R.randint(40,1570); y=R.randint(430,500)
        a.line(f'M{x} {y} L{x} {y-45}', 2, '#869674')
        a.oval(x, y-45, 11, 40, '#8da17f', 0, opacity=.7)
    if theme == 'field':
        for row in range(3):
            for col in range(7):
                bush(a, 80+col*247+row*35, 590+row*87, .47+row*.12)


def bush(a, x, y, scale=1):
    with a.scope(x, y, scale):
        a.path('M-8 40 Q-25 -35 -78 -75 M-2 40 Q10 -46 51 -92 M5 40 Q39 3 100 -44', None, 5, '#8e8056')
        for i in range(22):
            xx=R.uniform(-110,115); yy=R.uniform(-105,8)
            leaf(a,xx,yy,.47,R.uniform(-160,160),R.choice(['#678555','#839957','#a1ac65']))
            if i%2==0:
                berry(a,xx+R.uniform(-5,7),yy+15,.35,R.uniform(-35,35))


def room(a, kitchen=False):
    a.part = 'background'
    a.rect(0,0,1600,900,'url(#wall)')
    a.rect(0,596,1600,304,'#d7bd92')
    for yy in range(635,900,52):
        a.line(f'M0 {yy} L1600 {yy}',1,'#bca27f',opacity=.5)
    a.rect(85,91,540,430,'#b3c8ba',4,ink='#907b5c')
    a.rect(105,111,500,390,'url(#sky)')
    a.path('M105 395 Q275 266 435 366 Q541 286 605 345 L605 501 L105 501 Z','#9cae8d',0)
    a.path('M105 461 Q340 343 605 408 L605 501 L105 501 Z','#b7b77e',0)
    for xx in [105,272,438,605]:
        a.rect(xx-5,111,10,390,'#a88e68')
    a.rect(105,303,500,9,'#a88e68')
    a.path('M66 63 Q207 29 352 67 Q451 28 646 64 L625 135 Q516 96 351 136 Q213 92 83 136 Z','#b99160',1,'#9e805d')
    a.rect(934,106,588,15,'#a68c63',2)
    a.rect(934,338,588,16,'#9a835e',2)
    for i in range(5):
        jar(a,994+i*105,303, .64, ['#a7b49a','#c9b18a','#bcc6b0','#c1a881','#acb6a3'][i])
    a.line('M966 124 L966 335 M1494 124 L1494 335', 5, '#a68d67')
    # Shadow on plaster, warm window light, a pot of leaves.
    a.path('M105 500 L605 500 L925 858 L283 858 Z','#fff0be',0,opacity=.19)
    a.path('M1281 624 L1395 624 L1375 726 L1304 726 Z','#a7775c',2)
    for i in range(8):
        leaf(a,1335,639,.95,-75+i*21,R.choice(['#758e5d','#94a06b','#537958']))
    if kitchen:
        a.rect(1050,541,480,130,'#a5b2a0',2)
        a.rect(1029,527,525,25,'#897b63',1.5)
        a.rect(1090,570,171,80,'#b9c0a7',1)
        a.oval(1382,572,25,20,'#e4d3ae',2)


def jar(a,x,y,scale=1,color='#bdc5ab'):
    with a.scope(x,y,scale):
        a.path('M-37 -130 L38 -130 L36 -111 Q56 -84 54 -34 L49 0 Q0 15 -48 0 L-52 -34 Q-55 -86 -36 -110 Z', color,2)
        a.path('M-42 -141 Q0 -150 44 -141 L45 -128 Q0 -119 -43 -128 Z','#907650',2)
        a.path('M-29 -95 Q-42 -56 -32 -20',None,5,'#e9e6cb',opacity=.55)
        a.path('M-20 -76 Q0 -84 23 -76 L24 -39 Q0 -30 -23 -39 Z','#e1d2af',1)


def table(a,y=665):
    a.part='table'
    a.path(f'M-40 {y} Q798 {y-29} 1640 {y} L1620 {y+75} Q800 {y+42} -20 {y+75} Z','url(#wood)',2.5,'#a08762')
    a.rect(0,y+65,1600,190,'#c2a278')
    for i in range(7):
        yy=y+87+i*21
        a.line(f'M0 {yy} Q420 {yy-10} 830 {yy+2} Q1210 {yy-9} 1600 {yy}',1,'#9f805d',opacity=.33)


def bowl(a,x,y,scale=1,count=28,paint=False):
    with a.scope(x,y,scale,pen=paint):
        a.oval(0,50,137,24,'#9e8060',0,opacity=.15,draw=False)
        a.path('M-129 -4 Q-115 97 -2 105 Q105 99 129 -4 Z','url(#ceramic)',2.4,'#6a8178')
        a.path('M-112 21 Q-93 76 -40 83',None,5,'#f4f1d9',opacity=.7,draw=False)
        a.oval(0,-5,133,46,'#d4caa8',2.2,'#768c7f')
        a.oval(0,-7,117,35,'#af6850',0,draw=False)
        for i in range(count):
            yy=R.uniform(-27,18); xx=R.uniform(-100,100)*math.sqrt(max(.1,1-(yy/45)**2))
            berry(a,xx,yy,.34,R.uniform(-95,95))
        a.path('M-124 12 Q0 55 123 11',None,3,'#f3e6be',draw=False)


def arm(a,d, width=15, skin='#e6b491'):
    a.line(d,width+3,'#8c725c')
    a.line(d,width,skin)


def person(a,x,y,scale=1,kind='elder',pose='inspect',flip=1):
    with a.scope(x,y,scale,flip=flip):
        elder=kind=='elder'; woman=kind=='woman'
        coat='#76978a' if elder else '#bc6e53' if woman else '#8193a2'
        # Grounded body and legs, shaped cloth, and small visible folds.
        a.path('M-53 -113 L-58 8 L-19 11 L-4 -95 L17 10 L57 8 L49 -118 Z','#77735d',2)
        a.path('M-59 0 Q-82 2 -80 20 L-17 21 L-19 6 M18 5 L17 21 L81 21 Q78 0 53 0', '#565a4e',2)
        a.path('M-54 -328 Q-106 -305 -105 -241 L-86 -111 Q-5 -91 85 -114 L99 -242 Q97 -309 47 -327 Z',coat,2.6)
        a.path('M-71 -283 Q-74 -195 -58 -120 L-34 -117 Q-55 -196 -46 -292 Z','#405e59' if elder else '#985341' if woman else '#627484',0,opacity=.24)
        a.path('M-34 -331 L0 -287 L35 -329 M0 -285 Q-4 -188 5 -114',None,2,'#d8caa4')
        for yy in [-251,-218,-186]:
            a.oval(4,yy,3,3,'#eadab5',0)
        a.path('M-22 -353 L-21 -325 Q0 -302 24 -327 L24 -355 Z','#dda788',1.5)
        if woman:
            a.path('M-51 -449 Q-83 -393 -64 -345 L-39 -323 Q-67 -393 -42 -435 Z','#504941',2)
            a.path('M36 -441 Q83 -422 64 -352 L44 -322 Q66 -405 36 -441 Z','#504941',2)
        a.path('M-56 -425 Q-56 -478 -2 -480 Q58 -475 58 -425 L50 -379 Q36 -341 0 -344 Q-34 -345 -51 -380 Z','#efc09a',2.3,'#7f6955')
        a.oval(-57,-402,8,13,'#e5ad88',1.3)
        a.oval(57,-402,8,13,'#e5ad88',1.3)
        hair='#d7d1b7' if elder else '#514b43'
        a.path('M-58 -415 Q-78 -470 -37 -488 Q9 -514 50 -477 Q75 -459 57 -412 L42 -439 Q7 -429 -17 -457 Q-28 -432 -48 -428 Z',hair,2)
        if woman:
            a.oval(34,-487,29,25,'#514b43',2)
            a.path('M24 -510 Q44 -495 61 -492',None,4,'#bb7b59')
        if elder:
            a.path('M-44 -459 Q-15 -482 31 -457',None,2,'#eee4c9')
            a.path('M-45 -410 Q-29 -417 -18 -411 M20 -411 Q36 -416 46 -408',None,3,'#b0ae99')
        else:
            a.path('M-42 -411 Q-29 -419 -18 -413 M18 -413 Q31 -419 43 -410',None,2.5,'#594d41')
        a.path('M-39 -400 Q-30 -406 -21 -398 M20 -398 Q30 -406 40 -400',None,2.3,'#574d42')
        a.oval(-29,-399,2.8,4,'#51483d',0)
        a.oval(30,-399,2.8,4,'#51483d',0)
        a.line('M2 -400 Q-8 -380 5 -379',1.4,'#b48065')
        a.path('M-16 -366 Q1 -358 20 -367',None,1.9,'#9e6754')
        a.oval(-37,-381,10,5,'#d68e77',0,opacity=.24)
        a.oval(37,-381,10,5,'#d68e77',0,opacity=.24)
        if elder:
            a.path('M-18 -374 Q-3 -381 1 -373 Q9 -380 24 -373 L14 -365 Q3 -368 -6 -363 Z','#ded9c0',1)
            a.path('M-27 -356 Q0 -323 30 -356 Q23 -323 1 -309 Q-22 -329 -27 -356 Z','#e1dbc3',1.2)
            a.line('M-42 -385 L-49 -381 M43 -384 L49 -380',1,'#a98b70')
        if pose=='inspect':
            a.path('M-82 -296 Q-128 -280 -111 -218 L-45 -199 L-33 -230 L-79 -248 Z',coat,2)
            arm(a,'M-48 -218 Q-19 -203 10 -218',18)
            a.path('M79 -293 Q126 -291 140 -246 L101 -214 L66 -245 Z',coat,2)
            arm(a,'M114 -237 Q146 -244 154 -283',18)
            a.oval(153,-291,13,17,'#e8b48e',1.6)
        elif pose=='smell':
            a.path('M-78 -292 Q-107 -283 -110 -248 Q-55 -224 -9 -251 L-20 -283 L-77 -277 Z',coat,2)
            arm(a,'M-16 -266 Q16 -290 24 -336',16)
            a.path('M7 -335 Q22 -346 44 -334 Q32 -323 13 -324 Z','#e9ba92',1.4)
            for i in range(3):
                berry(a,15+i*7,-338,.13,30)
            a.path('M74 -294 Q122 -276 110 -203 L49 -220 L53 -250 Z',coat,2)
            arm(a,'M60 -234 Q31 -245 7 -264',16)
        elif pose=='tea':
            a.path('M-76 -292 Q-132 -260 -103 -203 L-36 -231 L-48 -261 Z',coat,2)
            a.path('M77 -291 Q117 -277 104 -220 L41 -229 L49 -261 Z',coat,2)
            arm(a,'M-45 -247 L-14 -251 M53 -247 L22 -251',17)
            cup(a,2,-236,.33)
        elif pose=='pick':
            a.path('M74 -294 Q118 -301 137 -340 L164 -320 Q150 -264 109 -245 Z',coat,2)
            arm(a,'M148 -332 Q175 -357 180 -388',15)
            a.path('M172 -389 Q173 -410 185 -416 Q201 -413 195 -401 L188 -384 Z','#e9b993',1.5)
            a.path('M-78 -291 Q-117 -272 -106 -211 L-58 -184 L-42 -214 L-80 -241 Z',coat,2)
            arm(a,'M-52 -204 Q-15 -190 12 -202',16)
        elif pose=='cook':
            a.path('M-74 -295 Q-126 -260 -104 -219 L-44 -222 L-43 -252 L-83 -254 Z',coat,2)
            arm(a,'M-48 -238 L15 -222',17)
            a.path('M74 -291 Q115 -281 130 -233 L104 -213 L66 -254 Z',coat,2)
            arm(a,'M118 -228 Q157 -232 187 -204',17)
            a.line('M181 -211 L216 -161',6,'#8f7350')
        else:
            a.path('M-80 -291 Q-132 -248 -91 -205 L-29 -245 L-45 -269 Z',coat,2)
            arm(a,'M-38 -257 Q-9 -284 8 -306',17)
            berry(a,11,-312,.2,25)
            a.path('M78 -293 Q124 -264 110 -215 L46 -203 L42 -234 L81 -246 Z',coat,2)
            arm(a,'M50 -220 L-1 -221',17)
        if woman:
            # Apron is tied around an adult torso; no childlike body proportions.
            a.path('M-35 -279 Q0 -265 36 -279 L63 -114 Q3 -99 -60 -115 Z','#dfc592',1.4)
            a.line('M-30 -270 L-41 -323 M29 -270 L39 -321',5,'#d7b77d')
            a.path('M-22 -204 L25 -204 L23 -163 Q0 -150 -21 -164 Z','#ceae76',1.2)


def cup(a,x,y,scale=1, water=True):
    with a.scope(x,y,scale):
        a.path('M-68 -127 L67 -127 L58 0 Q0 18 -59 0 Z','url(#glass)',2.4,'#8c9f92')
        if water:
            a.path('M-61 -93 L61 -93 L53 -5 Q0 8 -53 -5 Z','#dec477',0,opacity=.42)
            a.oval(0,-93,60,12,'#eee1a2',1.1,'#b7aa7c',opacity=.75)
            for xx,yy,ang in [(-26,-87,-40),(13,-83,40),(33,-70,15),(-12,-24,-20)]:
                berry(a,xx,yy,.25,ang)
        a.path('M-47 -109 L-40 -20',None,5,'#fffbe8',opacity=.8)
        a.oval(0,-128,69,13,None,2,'#a7b5a3')
        a.path('M70 -105 Q121 -117 111 -62 Q102 -36 64 -36',None,7,'#a9b5a5')


def magnifier(a,x,y,scale=1):
    with a.scope(x,y,scale,angle=-18,pen=True,motion='lens'):
        a.line('M-4 55 L-8 174',23,'#846a49')
        a.line('M-8 75 L-10 167',13,'#bb9262')
        a.oval(0,0,83,83,'#d6e3d0',8,'#8e7854',opacity=.72)
        a.oval(0,0,74,74,None,2,'#eedcb0')
        a.path('M-51 -34 Q-31 -65 10 -61',None,7,'#fff9df',opacity=.8)


def hands(a, sieve=False):
    # Two forearms enter from the edges, with distinct thumb and finger contours.
    a.path('M-20 580 L209 528 Q248 490 292 493 L344 516 Q365 525 352 542 L299 529 Q280 538 269 563 L225 585 L-20 685 Z','#e5b38d',2)
    a.path('M1620 577 L1406 530 Q1375 491 1333 492 L1279 514 Q1252 529 1271 544 L1326 529 Q1348 542 1365 565 L1402 592 L1620 686 Z','#e5b38d',2)
    a.line('M274 523 Q302 510 327 526 M1346 522 Q1320 510 1296 528',1.5,'#b78664')
    a.path('M0 570 L138 547 L181 647 L0 704 Z','#80998c',2)
    a.path('M1600 568 L1480 548 L1439 647 L1600 710 Z','#80998c',2)


def tray(a,x,y,scale=1,angle=0,count=75):
    with a.scope(x,y,scale,angle,motion='sieve'):
        a.oval(0,0,390,127,'#a98754',4,'#8e704a')
        a.oval(0,-13,379,117,'#ceb179',3,'#ead3a0')
        for yy in range(-100,101,14):
            w=math.sqrt(max(0,1-(yy/115)**2))*367
            a.line(f'M{-w} {yy-12} L{w} {yy-12}',1,'#957d50',opacity=.48)
        for xx in range(-340,341,24):
            h=math.sqrt(max(0,1-(xx/375)**2))*106
            a.line(f'M{xx} {-h-12} L{xx} {h-12}',1,'#9d8150',opacity=.45)
        for i in range(count):
            yy=R.uniform(-90,80); xx=R.uniform(-345,345)*math.sqrt(max(.1,1-(yy/110)**2))
            berry(a,xx,yy,.4,R.uniform(-90,90))
        a.path('M-384 5 Q-2 160 385 4',None,8,'#c4a16b')


def packet(a,x,y,scale=1,pen=False):
    with a.scope(x,y,scale,pen=pen):
        a.path('M-107 -341 Q-1 -349 107 -341 L102 -304 L123 1 Q0 26 -123 1 L-102 -304 Z','url(#pack)',3,'#8d8061')
        a.rect(-102,-334,204,18,'#708b71',1)
        a.line('M-98 -307 Q1 -315 99 -307',2,'#b6a581')
        a.path('M-97 -114 Q0 -162 99 -118 L107 -9 Q0 8 -106 -9 Z','#98a37a',0)
        a.path('M-100 -66 Q-37 -111 12 -75 Q63 -118 105 -65 L106 -8 Q0 8 -106 -8 Z','#748e6c',0)
        a.path('M-67 -257 L66 -257 L66 -133 Q0 -115 -67 -133 Z','#f3e5c5',1.3,'#bcaa82')
        a.oval(0,-189,49,49,'#d9b582',1.2,'#b99b6f')
        for xx,yy,ss,ang in [(-28,-171,.8,-18),(16,-169,.85,24),(5,-218,.64,-36)]:
            berry(a,xx,yy,ss,ang)
        a.path('M-87 -294 Q-102 -148 -91 -33',None,4,'#f5ebce',opacity=.65)


def build():
    scenes=[]
    def save(id,a):
        scenes.append({'id':id,'shapes':a.shapes})

    a=Painting(); room(a); person(a,410,733,1.08,pose='inspect'); table(a,654)
    bowl(a,837,636,1,25); bowl(a,1261,647,.94,29); magnifier(a,535,259,.95)
    twig(a,1510,650,.95,-22); save('question',a)

    a=Painting(); room(a); table(a,579)
    bowl(a,569,574,1.65,42); bowl(a,1195,584,1.37,35)
    magnifier(a,852,358,1.7); berry(a,851,353,1.65,-18); twig(a,1480,508,1.1,18)
    save('inspect',a)

    a=Painting(); landscape(a,'quiet')
    a.path('M0 735 Q450 616 865 724 Q1250 644 1600 742 L1600 900 L0 900 Z','#e6d5ab',0)
    with a.scope(1020,438,2.2,18,pen=True):
        a.line('M-95 118 Q-41 55 18 -77',4,'#8d7654')
        for xx,yy,ang in [(-65,49,-50),(13,-65,25),(45,-25,58)]:
            leaf(a,xx,yy,.8,ang)
        berry(a,-22,57,1.8,10)
        berry(a,56,20,1.18,-12)
    bowl(a,461,681,.85,25); save('look',a)

    a=Painting(); room(a); person(a,1030,765,1.18,pose='smell'); table(a,695)
    bowl(a,635,692,1,23); twig(a,1490,601,1,15)
    a.part='scent'
    with a.scope(motion='steam'):
        a.path('M1112 354 Q1080 325 1109 306 Q1132 284 1107 261 M1143 357 Q1162 332 1140 318',None,3,'#a99f7d',opacity=.5)
    save('smell',a)

    a=Painting(); room(a); table(a,586)
    a.path('M456 758 L578 574 Q600 507 645 503 L740 526 L950 484 Q995 479 998 500 Q993 516 964 529 L810 581 L1018 550 Q1054 554 1041 576 L831 635 L1016 616 Q1045 626 1024 643 L817 693 L965 685 Q992 692 967 714 L761 768 L586 822 Z','#e7b48d',2.6)
    a.path('M1499 512 L1250 467 Q1214 437 1166 431 L1006 439 Q967 444 985 467 L1120 485 L1033 512 Q1013 531 1035 544 L1152 521 Q1201 550 1250 537 L1489 621 Z','#e9bc96',2.6)
    a.path('M1188 436 Q1213 461 1239 467 M1120 485 L1156 483',None,2,'#bd8966')
    for xx,yy,s,ang in [(712,564,.9,-35),(786,552,.84,18),(858,536,.9,26),(780,621,.8,-28),(704,633,.75,22),(858,608,.7,36)]:
        with a.scope(pen=True): berry(a,xx,yy,s,ang)
    twig(a,1455,460,.9,37); save('touch',a)

    a=Painting(); room(a); table(a,657)
    with a.scope(pen=True):
        cup(a,651,692,2)
        cup(a,1192,692,2)
    # The right-hand glass visibly contains both suspended and submerged berries.
    for xx,yy in [(1181,654),(1239,644),(1158,620)]: berry(a,xx,yy,.5,23)
    berry(a,368,638,1.1,-24); berry(a,386,696,1.05,18)
    twig(a,1507,601,.9,17); save('water',a)

    a=Painting(); landscape(a)
    person(a,640,750,.75,kind='woman',pose='pick')
    person(a,1178,685,.51,pose='pick',flip=-1)
    twig(a,788,531,.56,-5)
    bush(a,868,724,1.2); bowl(a,602,800,.48,20)
    twig(a,94,744,1.25,-12); twig(a,1502,700,1.1,24)
    save('orchard',a)

    a=Painting(); landscape(a,'quiet')
    a.path('M0 470 L480 470 L480 711 L0 711 Z','#e7d4ab',2)
    a.path('M-40 470 L146 327 L466 338 L554 472 Z','#89937b',2)
    for i in range(9): a.line(f'M{40+i*49} 462 L{160+i*36} 349',2,'#6b7b6c',opacity=.6)
    a.rect(75,532,89,179,'#9b8965',2)
    a.rect(276,530,121,104,'#9fae91',3)
    a.path('M0 706 L1600 644 L1600 900 L0 900 Z','#dac59b',0)
    person(a,1090,748,.88,pose='inspect');
    for xx,yy,ss in [(439,710,1.05),(836,810,.78),(265,846,.63)]:
        a.line(f'M{xx-180*ss} {yy} L{xx-205*ss} {yy+90*ss} M{xx+181*ss} {yy} L{xx+200*ss} {yy+90*ss}',10,'#947b54')
        tray(a,xx,yy,ss,0,60)
    twig(a,1455,737,1.3,21); save('drying',a)

    a=Painting(); landscape(a,'quiet'); table(a,624)
    tray(a,808,551,1.48,-3,113); hands(a,True)
    with a.scope(motion='falling'):
        for xx,yy,ss in [(751,745,.3),(1023,715,.28),(520,740,.24),(930,788,.29)]: berry(a,xx,yy,ss,44)
    save('sieve',a)

    a=Painting(); room(a); person(a,472,743,1.02,kind='woman',pose='inspect'); table(a,650)
    packet(a,944,732,1.15,True)
    a.path('M1150 570 L1395 590 L1377 749 L1135 725 Z','#eee8d0',2,'#afab91')
    for i in range(5):
        a.line(f'M1178 {611+i*19} L1353 {623+i*19}',2,'#a3ab91',opacity=.65)
    a.oval(1318,691,27,27,None,3,'#a3876a')
    twig(a,1511,684,1.1,24); save('label',a)

    a=Painting(); room(a,True)
    person(a,355,787,.9,pose='tea')
    person(a,1050,740,.9,kind='woman',pose='cook')
    person(a,1410,776,.83,kind='young',pose='eat',flip=-1)
    table(a,717)
    bowl(a,578,710,.68,21); cup(a,290,753,.8)
    a.path('M902 681 Q916 785 1018 785 Q1118 776 1125 682 Z','#897f68',3)
    a.oval(1014,681,114,38,'#d7ba83',3,'#8d7d5f')
    for i in range(11): berry(a,R.uniform(947,1070),R.uniform(663,689),.25,R.uniform(-75,75))
    a.path('M910 694 Q864 671 863 716 Q874 742 923 735 M1120 695 Q1160 677 1165 715 Q1154 739 1114 736',None,8,'#82745a')
    with a.scope(motion='steam'):
        for xx in [969,1012,1053]:
            a.path(f'M{xx} 645 Q{xx-22} 609 {xx+6} 582 Q{xx+22} 558 {xx} 530',None,4,'#f4edcf',opacity=.8)
    save('family',a)

    a=Painting(); landscape(a,'quiet')
    a.path('M0 686 Q365 601 800 684 Q1200 591 1600 685 L1600 900 L0 900 Z','#e7d8af',0)
    a.oval(1006,772,347,46,'#b5a67a',0,opacity=.25)
    a.path('M664 738 Q1010 676 1364 739 L1363 779 Q1007 832 665 777 Z','#c8ab7a',2,'#a88b5c')
    a.oval(1014,738,351,57,'#e8d4aa',2,'#ba9e6e')
    packet(a,983,710,1.55,True)
    bowl(a,1258,729,.75,28); cup(a,701,746,1.1)
    twig(a,1441,601,1.62,18); twig(a,575,787,1.18,-59)
    for xx,yy,s,ang in [(814,792,.65,-18),(864,801,.55,63),(1195,808,.59,25),(1162,804,.6,-35)]: berry(a,xx,yy,s,ang)
    save('ending',a)
    return scenes


def create_texture():
    rng=np.random.default_rng(20261015)
    fine=rng.normal(0,1.3,(1080,1920,1))
    coarse=Image.fromarray(rng.integers(0,255,(54,96),dtype=np.uint8)).resize((1920,1080)).filter(ImageFilter.GaussianBlur(16))
    pixels=np.array([247,239,216])[None,None,:]+fine+(np.array(coarse)[:,:,None]-128)*.055
    Image.fromarray(np.clip(pixels,0,255).astype('uint8')).save(ASSETS/'paper.jpg',quality=94)


def create_sound():
    """Original synthesized warm plucks and soft foley, tied to the actual narration cuts."""
    timeline=json.loads((CONTENT/'timeline.json').read_text(encoding='utf-8'))
    sr=24000; duration=timeline['durationSeconds']; n=math.ceil(duration*sr)
    mix=np.zeros(n,dtype=np.float64); rng=np.random.default_rng(1023)

    def add(t,signal,gain=1):
        start=round(t*sr); end=min(n,start+len(signal))
        if end>start: mix[start:end]+=signal[:end-start]*gain

    def pluck(freq,length=2.4):
        t=np.arange(int(length*sr))/sr
        env=(1-np.exp(-t*70))*np.exp(-t*2.8)
        return (np.sin(2*np.pi*freq*t)+.26*np.sin(2*np.pi*freq*2*t)+.07*np.sin(2*np.pi*freq*3*t))*env

    # Pentatonic motif, sparse notes below the narration; final bars grow gently.
    notes=[261.626,329.628,391.995,440.0,523.251,440.0,391.995,329.628]
    for i,t in enumerate(np.arange(.6,duration-1,1.55)):
        gain=.016 if t<duration-12 else .023
        add(t,pluck(notes[i%8]),gain)
        if i%4==0: add(t,pluck(notes[(i+2)%8]/2,4.0),.013)
    t=np.arange(sr*3)/sr
    gong=(np.sin(2*np.pi*138*t)+.35*np.sin(2*np.pi*223.4*t)+.16*np.sin(2*np.pi*379.5*t))*np.exp(-t*2.7)*(1-np.exp(-t*65))
    add(.05,gong,.053)
    for i,sc in enumerate(timeline['scenes']):
        start=sc['from']/30
        if sc['id'] in ['inspect','look','smell','touch']:
            add(start+.1,pluck(880 if i%2 else 1046.5,.7),.029)
        if sc['id']=='inspect':
            tt=np.arange(int(sr*.45))/sr; noise=rng.normal(0,1,len(tt))
            signal=np.convolve(noise,np.ones(8)/8,'same')*np.sin(np.pi*tt/.45)**2
            add(start+.12,signal,.025)
        if sc['id'] in ['drying','sieve']:
            tt=np.arange(int(sr*1.8))/sr; noise=rng.normal(0,1,len(tt))
            signal=np.convolve(noise,np.ones(5)/5,'same')*(.5+.5*np.sin(tt*2*np.pi*5))*np.sin(np.pi*tt/1.8)**2
            add(start+.15,signal,.037)
        if sc['id']=='orchard':
            tt=np.arange(int(sr*3))/sr; noise=rng.normal(0,1,len(tt))
            signal=np.convolve(noise,np.ones(110)/110,'same')*np.sin(np.pi*tt/3)**2
            add(start,signal,.07)
    fade=np.minimum(np.arange(n)/sr/1.3,1)*np.minimum((n-np.arange(n))/sr/1.5,1)
    mix*=fade
    stereo=np.column_stack((mix,mix*.96))
    with wave.open(str(ASSETS/'audio/music-foley.wav'),'wb') as f:
        f.setnchannels(2);f.setsampwidth(2);f.setframerate(sr)
        f.writeframes((np.clip(stereo,-.9,.9)*32767).astype('<i2').tobytes())


if __name__=='__main__':
    CONTENT.mkdir(parents=True,exist_ok=True); ASSETS.mkdir(parents=True,exist_ok=True)
    scenes=build()
    (CONTENT/'art.json').write_text(json.dumps(scenes,ensure_ascii=False,separators=(',',':')), encoding='utf-8')
    create_texture();create_sound()
    (CONTENT/'asset-sources.json').write_text(json.dumps({
        'art':'Original code illustration: scripts/create_goji_art.py. Not AI image generation.',
        'music':'Original synthesized pentatonic plucks and foley: scripts/create_goji_art.py. No third-party music.',
        'hand':json.loads((ROOT/'content/handdraw-moon-v1/asset-sources.json').read_text(encoding='utf-8'))['hand'],
        'font':'Noto Serif SC, SIL Open Font License; public/fonts/OFL.txt',
        'product':'Illustrated generic packaging. No real product photo, brand, laboratory certificate or farm ownership represented.'
    },ensure_ascii=False,indent=2), encoding='utf-8')
    print(json.dumps({'scenes':len(scenes),'shapes':[len(s['shapes']) for s in scenes]}))
