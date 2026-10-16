"""Original black-ink / selective-red drawings and procedural foley for this episode."""
import json
import math
import random
import shutil
import wave
from pathlib import Path

import numpy as np
from create_goji_art import Painting

ROOT=Path(__file__).resolve().parents[1]
CONTENT=ROOT/'content/handdraw-goji-inkred-v1'
ASSETS=ROOT/'public/handdraw-goji-inkred-v1'
INK='#4b4846'
PAPER='#f9f6ec'
R=random.Random(151052)


class Ink(Painting):
    def __init__(self):
        super().__init__()
        self.pen=True

    def path(self,data,fill=None,width=2.1,ink=INK,opacity=1,draw=None):
        super().path(data,fill,width,ink,opacity,draw)


def berry(a,x,y,s=1,angle=0):
    with a.scope(x,y,s,angle):
        a.path('M0 -44 C17 -44 30 -24 27 2 C24 25 13 51 -3 53 C-23 50 -32 26 -27 0 C-24 -23 -18 -43 0 -44 Z','url(#redwash)',1.6)
        a.path('M-12 -29 Q-23 -9 -15 20 Q-9 34 -6 40 Q-11 13 -4 -18 Z','#f4ae8d',0,opacity=.64)
        a.path('M14 -23 Q18 0 7 30 M2 8 Q-3 32 -5 42',None,1.0,'#ad473c',opacity=.72)
        a.oval(0,-43,4.3,3.1,PAPER,.8)


def leaf(a,x,y,s=1,angle=0):
    with a.scope(x,y,s,angle):
        a.path('M0 0 Q-49 -9 -58 -54 Q-10 -58 0 0 Z',None,1.4)
        a.path('M-2 -3 Q-26 -29 -53 -49',None,.8,opacity=.6)


def laptop(a,x,y,s=1,closed=False):
    with a.scope(x,y,s):
        if not closed:
            a.path('M-185 -221 L153 -221 Q166 -223 168 -206 L165 -21 L-179 -21 Z','#e4e3df',2.5)
            a.path('M-167 -204 L150 -204 L148 -38 L-160 -38 Z',None,1.3)
            for i in range(6):
                yy=-178+i*22
                a.line(f'M-140 {yy} L{-58 if i%2 else 12} {yy} M28 {yy} L125 {yy}',1.4,'#a5a39e')
            a.path('M-179 -21 L165 -21 L214 13 L-224 13 Z','#ecebe6',2.4)
            for yy in [-8,0]:
                for xx in range(-148,135,33):a.line(f'M{xx} {yy} L{xx+20} {yy}',1,'#a9a7a1')
            a.oval(-3,-29,2.7,2.7,INK,0)
        else:
            a.path('M-192 -14 L155 -14 L204 15 L-219 15 Z','#e2e1dc',2.4)
            a.line('M-192 -14 L-180 -23 L163 -23 L204 15',1.8)


def person(a,x,y,s=1,tired=True):
    with a.scope(x,y,s):
        # Same original adult office worker in both the night and break scenes.
        a.part='person'
        a.path('M-76 -200 Q-90 -251 -67 -290 Q-38 -319 30 -305 Q85 -287 88 -238 L72 -70 Q0 -52 -77 -72 Z','#eeece6',2.4)
        a.path('M-57 -288 Q-50 -218 -56 -83 M24 -294 Q38 -204 29 -75',None,1.2,'#98958f')
        a.path('M-32 -318 L-30 -295 L-3 -269 L27 -299 L27 -322 Z','#f0eeea',1.8)
        a.path('M-32 -295 L-3 -270 L-41 -258 L-61 -289 M27 -299 L-3 -270 L39 -259 L55 -285',None,1.7)
        a.path('M-64 -383 Q-71 -440 -23 -457 Q42 -475 66 -426 L61 -335 Q48 -306 14 -308 L-22 -312 Q-59 -334 -64 -383 Z','#dddcd8',2.1)
        a.path('M-51 -403 Q-39 -436 0 -433 Q47 -430 48 -390 L42 -348 Q32 -319 2 -317 Q-36 -322 -45 -354 Z','#f4f2ee',2.0)
        a.path('M-59 -390 Q-83 -441 -44 -464 Q0 -488 46 -458 Q73 -436 58 -386 Q19 -393 -13 -431 Q-32 -405 -59 -390 Z','#bbb9b4',2.2)
        a.oval(37,-465,24,21,'#bbb9b4',2)
        a.path('M24 -481 Q42 -474 56 -465',None,2.5)
        a.path('M-46 -369 Q-62 -377 -57 -358 L-47 -351 M46 -371 Q61 -379 56 -360 L46 -351',None,1.4)
        a.path('M-31 -382 Q-20 -390 -9 -383 M14 -383 Q26 -389 37 -379',None,1.7)
        if tired:
            a.path('M-34 -369 Q-21 -363 -8 -370 M13 -370 Q26 -363 37 -369',None,2.4)
            a.path('M-33 -357 Q-21 -350 -9 -358 M15 -358 Q28 -351 37 -357',None,1.0,'#aaa7a1')
            a.path('M-12 -334 Q0 -342 14 -333',None,1.7)
        else:
            a.path('M-34 -370 Q-22 -379 -9 -369 M12 -370 Q24 -380 37 -369',None,1.7)
            a.oval(-22,-369,3,4.5,INK,0);a.oval(24,-369,3,4.5,INK,0)
            a.oval(-23,-370,1.1,1.4,PAPER,0);a.oval(23,-370,1.1,1.4,PAPER,0)
            a.path('M-12 -336 Q1 -326 16 -337',None,1.6)
            with a.scope(motion='cheek'):
                a.oval(-32,-347,12,5,'#d98677',0,opacity=.31)
                a.oval(34,-347,12,5,'#d98677',0,opacity=.31)
        a.line('M3 -366 L-3 -347 L4 -345',1.0,'#a39e97')
        if tired:
            a.path('M-68 -285 Q-105 -268 -109 -219 Q-76 -195 -34 -208 L-31 -235 L-77 -238 Z','#eeece6',2.0)
            a.path('M-34 -225 Q6 -215 28 -219 L30 -203 Q4 -196 -35 -207 Z','#f2f0ec',1.7)
            a.path('M66 -285 Q115 -275 126 -238 Q144 -282 109 -328 L88 -314 Q110 -275 88 -255 Z','#eeece6',2.0)
            # Fingers actually reach the outer corner of the right eye.
            a.path('M89 -321 Q83 -339 61 -354 L33 -368 Q29 -372 35 -375 L66 -363 L54 -379 Q55 -386 63 -381 L85 -365 Q105 -344 109 -330 Z','#f2f0ec',1.7)
        else:
            for side in [-1,1]:
                with a.scope(flip=side):
                    a.path('M72 -284 Q108 -263 104 -215 L49 -195 L42 -222 L79 -238 Z','#eeece6',2)
                    a.path('M45 -218 Q19 -227 -5 -216 L-1 -198 L50 -200 Z','#f2f0ec',1.5)
        a.part='environment'


def desk(a,y=684):
    a.path(f'M248 {y} Q795 {y-8} 1395 {y} L1411 {y+22} Q808 {y+15} 233 {y+22} Z',None,2.1)
    a.line(f'M302 {y+23} L290 773 M1345 {y+23} L1354 773',2.1)


def tea_glass(a,x,y,s=1,small=False):
    with a.scope(x,y,s):
        a.part='glass'
        a.path('M-115 -278 L116 -278 L99 -3 Q0 25 -98 -3 Z',None,2.4)
        a.oval(0,-278,116,20,None,2.1)
        with a.scope(motion='water'):
            a.path('M-107 -209 Q0 -191 108 -209 L93 -11 Q0 10 -92 -11 Z','url(#amberwash)',0,opacity=.65)
            a.oval(0,-209,107,16,'#e8cd87',1.0,'#a7946a',opacity=.55)
        for i,(xx,yy,angle) in enumerate([(-46,-202,-65),(17,-196,60),(64,-200,32),(-36,-52,14),(38,-27,-40)]):
            with a.scope(motion=f'bob-{i}'):
                berry(a,xx,yy,.44,angle)
        a.path('M-85 -252 L-76 -65 M86 -235 L75 -44',None,3.5,'#b9b6ac',opacity=.45)
        a.path('M-93 -4 Q0 17 94 -4',None,1.1)
        with a.scope(motion='steam'):
            a.path('M-45 -319 Q-65 -351 -44 -372 Q-18 -400 -37 -423 M24 -317 Q5 -350 25 -377',None,1.6,'#a9a59d',opacity=.45)
        a.part='environment'


def build():
    out=[]
    def save(id,a,ink=2.9,paint=1.6,paint_at=None):
        out.append({'id':id,'shapes':a.shapes,'inkSeconds':ink,'paintSeconds':paint,'paintAt':ink+.13 if paint_at is None else paint_at})

    a=Ink()
    person(a,990,765,1.1,True)
    laptop(a,650,681,.83)
    desk(a)
    a.line('M994 754 L993 781 M950 780 L1037 780',2.0)
    a.path('M1109 470 Q1131 421 1108 398 M1098 398 Q1130 368 1153 394',None,1.4,'#9e9a93')
    # Tangled ink is an actual editable path, not a raster overlay.
    points=[]
    for i in range(160):
        t=i*.51;points.append((988+math.cos(t)*math.sin(t*.39)*105,207+math.sin(t)*math.cos(t*.61)*36))
    a.path('M'+' L'.join(f'{x:.2f} {y:.2f}' for x,y in points),None,1.2,opacity=.7)
    a.oval(1340,326,47,47,None,1.5)
    a.line('M1340 293 L1340 326 L1365 336',2)
    a.path('M259 412 Q276 407 288 421 M279 442 Q299 451 308 438',None,1.3,'#a39e95')
    save('night',a,3.7,.65)

    a=Ink()
    a.path('M203 723 Q448 721 650 718 Q865 694 980 629 Q1160 549 1369 505',None,2.4)
    a.path('M227 619 L370 506 L466 564 L581 456 L698 573 L779 543 L927 616 M294 642 Q512 597 738 637',None,1.3,'#aaa69e')
    a.path('M530 724 Q666 642 771 490 Q855 374 1070 310 M766 500 Q1033 474 1351 369',None,3.0)
    for i,(x,y,angle) in enumerate([(747,519,-20),(823,422,20),(929,363,-10),(1043,489,38),(1162,436,-15),(1289,390,22)]):
        a.path(f'M{x} {y-34} Q{x-13} {y-50} {x-30} {y-46}',None,1.8)
        leaf(a,x-30,y-46,.85,-35+i*18)
        leaf(a,x+29,y-28,.65,90-i*21)
        berry(a,x,y+19, .93 if i%2 else 1.15,angle)
    a.path('M332 673 Q413 649 492 673 M1098 673 Q1203 647 1342 662',None,1.2,'#aaa69e')
    save('red-twig',a,2.45,3.0,3.1)

    a=Ink()
    berry(a,717,559,3.25,-8)
    a.path('M713 410 Q726 377 747 365 M736 372 Q757 347 780 360',None,2.2)
    for x,y,s,angle in [(450,671,.8,-46),(1135,641,.82,40),(1267,578,.58,-18)]:berry(a,x,y,s,angle)
    # Circle appears late, synchronized with the white-point narration.
    with a.scope(motion='ring'):
        a.path('M667 427 C633 387 663 345 705 344 C758 342 788 393 753 429 C724 460 670 455 654 419',None,2.3)
        a.path('M770 385 Q861 337 941 361 M934 352 L945 363 L931 371',None,1.6)
    save('detail',a,1.65,1.15)

    a=Ink()
    # Open palm and visible fingers, with no colored skin fill.
    a.path('M213 565 L438 514 Q471 469 534 440 Q563 420 616 428 L731 449 Q752 456 746 469 Q739 479 714 473 L627 458 Q596 457 579 469 L701 489 Q726 494 724 507 Q720 520 694 513 L581 497 L694 526 Q716 531 711 544 Q706 555 682 547 L570 522 L658 553 Q676 563 665 574 Q651 579 632 572 L544 544 Q501 584 448 600 L249 667 Z',None,2.4)
    a.path('M207 564 L301 543 L335 636 L249 669',None,2)
    a.path('M439 514 Q457 536 451 565 M514 490 Q537 478 560 484 M528 521 Q548 503 564 505',None,1.1,'#9c978f')
    a.oval(947,720,263,45,None,1.4,'#b5afa3')
    a.path('M702 710 Q733 779 947 784 Q1162 775 1194 710 M711 710 Q941 769 1190 710',None,2)
    for i in range(12):
        x=629+(i%4)*48;y=472+(i//4)*24
        with a.scope(motion=f'fall-{i}'):
            berry(a,x,y,.38+(i%3)*.04,-20+i*17)
    a.path('M1191 371 L1348 371 L1348 541 L1191 541 Z',None,1.8)
    for yy in [401,424,448,475]:a.line(f'M1211 {yy} L1327 {yy}',1.2,'#a39f96')
    a.line('M1234 505 L1246 518 L1273 493',2.3)
    save('handfall',a,1.9,1.0)

    a=Ink()
    tea_glass(a,793,740,1.2)
    # Spout and stream occupy their own light ink region.
    a.path('M1120 297 Q1139 272 1173 287 L1256 354 Q1272 370 1255 389 L1209 440 Q1190 455 1170 441 L1091 373 L1029 403 L1007 386 L1085 337 Z',None,1.9)
    a.path('M1171 290 Q1207 243 1246 274 Q1272 300 1247 340',None,2.1)
    with a.scope(motion='pour'):
        a.path('M1014 393 Q925 390 868 468 M1024 404 Q944 404 881 469',None,1.7,'#aaa395',opacity=.75)
    a.path('M406 742 Q782 755 1167 741',None,1.3,'#b3ada1')
    save('tea',a,1.6,2.1,1.9)

    a=Ink()
    person(a,1004,751,1.06,False)
    desk(a)
    laptop(a,561,677,.68,True)
    tea_glass(a,1010,518,.32,True)
    with a.scope(motion='warmflow'):
        a.path('M1149 663 C1241 554 1123 503 1021 432 Q982 417 977 386',None,4,'#d4b772',opacity=.5)
    a.oval(1356,337,43,43,None,1.2,'#a39f95')
    a.path('M1356 306 L1356 337 L1378 325',None,1.7)
    save('pause',a,2.3,1.8,2.65)

    a=Ink()
    # Generic transparent pouch: only the red fruit is colored.
    a.path('M668 278 Q793 267 928 278 L922 320 L946 729 Q800 754 649 729 L674 320 Z',None,2.7)
    a.path('M674 296 Q793 284 920 295 M674 310 L921 309 M675 322 Q793 313 920 321',None,1.2)
    a.path('M691 358 Q795 350 902 358 L907 471 Q795 487 685 471 Z',PAPER,1.4)
    for i in range(32):
        y=529+(i//8)*53;x=698+(i%8)*26+R.uniform(-8,8)
        berry(a,x,y,.40,R.uniform(-70,70))
    a.path('M663 733 Q798 771 937 732',None,1.4)
    for x,y,s,angle in [(527,727,.68,-65),(1064,718,.68,45),(1122,730,.48,-50)]:berry(a,x,y,s,angle)
    with a.scope(motion='check'):
        a.path('M1060 475 L1087 507 L1166 423',None,6.0,'#bc5147')
    save('ending',a,2.1,1.8)
    return out


def sound():
    tl=json.loads((CONTENT/'timeline.json').read_text(encoding='utf-8'));art=json.loads((CONTENT/'art.json').read_text(encoding='utf-8'))
    sr=24000;n=math.ceil(tl['durationSeconds']*sr);mix=np.zeros(n);rng=np.random.default_rng(52105);events=[]
    def add(at,signal,gain,label):
        start=max(0,round(at*sr));end=min(n,start+len(signal))
        if end>start:mix[start:end]+=signal[:end-start]*gain
        events.append({'seconds':round(at,3),'type':label})
    def hiss(length,rough=False):
        t=np.arange(round(sr*length))/sr;noise=rng.normal(0,1,len(t))
        low=np.convolve(noise,np.ones(11 if rough else 33)/(11 if rough else 33),'same')
        return (noise-low if rough else low)*np.minimum(t/.05,1)*np.minimum((length-t)/.1,1)*(.5+.5*np.sin(2*np.pi*11*t)**2)
    def bell(f,length=.8):
        t=np.arange(round(sr*length))/sr
        return (np.sin(2*np.pi*f*t)+.21*np.sin(2*np.pi*f*2.76*t))*np.exp(-t*5)*(1-np.exp(-t*160))
    for scene,visual in zip(tl['scenes'],art):
        start=scene['from']/30;dur=scene['durationInFrames']/30
        add(start+.1,hiss(visual['inkSeconds'],True),.008,'dip-pen-paper')
        if scene['id']!='night':add(start+visual['paintAt'],hiss(min(visual['paintSeconds'],dur-visual['paintAt'])),.019,'soft-brush-wash')
        if scene['id']=='night':
            t=np.arange(round(sr*.72))/sr
            breath=np.convolve(rng.normal(0,1,len(t)),np.ones(45)/45,'same')*np.sin(np.pi*t/.72)**2
            add(start+4.8,breath,.048,'synthetic-breath-texture-not-human-recording')
        if scene['id']=='red-twig':add(start+visual['paintAt'],bell(1270,.65),.034,'red-ink-drop')
        if scene['id']=='detail':add(start+3.7,hiss(.52,True),.018,'circle-mark')
        if scene['id']=='handfall':
            for i in range(12):add(start+2.65+i*.055,bell(600+i*31,.095),.027,'dry-fruit-tick')
        if scene['id']=='tea':add(start+1.8,hiss(2.4),.09,'water-pour')
        if scene['id']=='pause':
            for i,f in enumerate([1046.5,1318.5,1568]):add(start+2.7+i*.14,bell(f,1.2),.022,'soft-chime')
        if scene['id']=='ending':
            t=np.arange(round(sr*.22))/sr
            add(start+4.8,np.sin(2*np.pi*(110*t-130*t*t))*np.exp(-t*28)+rng.normal(0,.1,len(t))*np.exp(-t*45),.063,'pen-finish-stamp')
    fade=np.minimum(np.arange(n)/sr/.1,1)*np.minimum((n-np.arange(n))/sr/.45,1);mix*=fade
    with wave.open(str(ASSETS/'audio/foley.wav'),'wb') as f:
        f.setnchannels(2);f.setsampwidth(2);f.setframerate(sr)
        f.writeframes((np.column_stack((mix,mix*.97))*32767).clip(-32767,32767).astype('<i2').tobytes())
    (CONTENT/'foley-events.json').write_text(json.dumps({'source':'original procedural synthesis; no background music','peak':float(np.max(np.abs(mix))),'events':events},ensure_ascii=False,indent=2), encoding='utf-8')


if __name__=='__main__':
    CONTENT.mkdir(exist_ok=True);ASSETS.mkdir(exist_ok=True);(ASSETS/'audio').mkdir(exist_ok=True)
    art=build();(CONTENT/'art.json').write_text(json.dumps(art,ensure_ascii=False,separators=(',',':')), encoding='utf-8')
    shutil.copy2(ROOT/'public/handdraw-moon-v1/paper.jpg',ASSETS/'paper.jpg')
    sound()
    print(json.dumps({'scenes':len(art),'paths':[len(x['shapes']) for x in art]}))
