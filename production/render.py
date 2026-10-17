#!/usr/bin/env python3
"""Orion T3 Flash official launch film. Build reproducibly with Pillow, NumPy & ffmpeg.
All UI demonstrations are explicitly illustrative; no UI is claimed to be authentic.
No proprietary source/model information is included.
"""
from PIL import Image,ImageDraw,ImageFont,ImageFilter
import os,math,random,subprocess,json,concurrent.futures
import numpy as np
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
AS=ROOT/'assets'; ST=ROOT/'stills'; PART=ROOT/'segments'; QA=ROOT/'qa'
for p in (AS,ST,PART,QA):p.mkdir(parents=True,exist_ok=True)
W,H=1920,1080
FONT='/usr/share/fonts/truetype/inter/Inter-Regular.otf'
fontlist={}
for root,dirs,files in os.walk('/usr/share/fonts/truetype'):
 for name in files:
  if name in ['Inter-Regular.otf','Inter-Bold.otf','Inter-SemiBold.otf','Inter-Medium.otf','Inter-ExtraBold.otf']:
   fontlist[name]=os.path.join(root,name)
FONT=fontlist.get('Inter-Regular.otf',FONT)
BOLD=fontlist.get('Inter-Bold.otf',FONT); EXTRA=fontlist.get('Inter-ExtraBold.otf',BOLD)
SEMI=fontlist.get('Inter-SemiBold.otf',BOLD)
WHITE=(239,248,255); CYAN=(94,228,255); BLUE=(52,121,255); YELLOW=(239,246,20); MUTED=(149,176,208)

def ft(s,weight='reg'):return ImageFont.truetype({'reg':FONT,'bold':BOLD,'extra':EXTRA,'semi':SEMI}[weight],s)
def rect(d,b,fill,rad=0,outline=None,width=1):d.rounded_rectangle(b,rad,fill=fill,outline=outline,width=width)
def txt(d,xy,s,size=56,fill=WHITE,weight='reg',anchor=None,stroke=0):
 d.text(xy,s,font=ft(size,weight),fill=fill,anchor=anchor,stroke_width=stroke,stroke_fill=(3,12,27))
def multi(d,xy,lines,size=55,color=WHITE,line=1.24,weight='bold'):
 for i,s in enumerate(lines):txt(d,(xy[0],xy[1]+i*int(size*line)),s,size,color,weight)
def glow(im,cx,cy,scale=320,colour=(0,127,237),strength=0.65):
 # Additive transparent radial light bloom, intentionally subtle.
 w,h=im.size
 l=max(0,int(cx-scale*2));r=min(w,int(cx+scale*2));t=max(0,int(cy-scale*2));b=min(h,int(cy+scale*2))
 if l>=r or t>=b:return im
 ys,xs=np.ogrid[t:b,l:r]
 v=np.exp(-((xs-cx)**2+(ys-cy)**2)/(scale*scale*0.82))*strength
 area=np.asarray(im.crop((l,t,r,b)),dtype=np.float32)
 area=area+(255-area)*v[...,None]*(np.array(colour,dtype=np.float32)/255)[None,None,:]
 im.paste(Image.fromarray(np.uint8(np.clip(area,0,255))),(l,t));return im

def background(n,kind):
 y=np.linspace(0,1,H,dtype=np.float32)[:,None,None];x=np.linspace(0,1,W,dtype=np.float32)[None,:,None]
 base=np.array([3,10,27],np.float32)[None,None,:]
 X=np.broadcast_to(x,(H,W,1));Y=np.broadcast_to(y,(H,W,1))
 a=np.ones((H,W,3),dtype=np.float32)*base
 a+=np.array([5,15,35])[None,None,:]*Y
 # reflective travelling cyan highlights (vary scene)
 seed=n*37+11
 k=(n%4)
 centers=[(.81,.18),(.65,.75),(.2,.85),(.93,.55)]
 cx,cy=centers[k]
 b=np.exp(-(((X-cx)/.49)**2+((Y-cy)/.48)**2)*2.5)
 a+=b*np.array([3,25,55])[None,None,:]
 if kind in ['hero','orbit','context','signal','final']:
  cx2,cy2=(.64,.4) if kind!='final' else (.5,.46)
  bloom=np.exp(-(((X-cx2)/.3)**2+((Y-cy2)/.4)**2)*1.8)
  a+=bloom*np.array([5,33,67])[None,None,:]
 a=np.uint8(np.clip(a,0,255));im=Image.fromarray(a)
 d=ImageDraw.Draw(im,'RGBA');rng=random.Random(seed)
 # fine widescreen grid and restrained technical map elements
 for xx in range(80,W,112):d.line((xx,0,xx,H),fill=(81,152,228,10),width=1)
 for yy in range(24,H,112):d.line((0,yy,W,yy),fill=(81,152,228,9),width=1)
 for _ in range(60):
  px=rng.randint(30,W-30);py=rng.randint(40,H-40);sz=rng.choice([1,1,1,2,2,3])
  d.ellipse((px-sz,py-sz,px+sz,py+sz),fill=(97,208,255,rng.randint(25,70)))
 if kind in ['hero','orbit','final']:
  cxr,cyr=(1430,495) if kind!='final' else (980,255)
  for j in range(5):
   s=260+j*58
   d.ellipse((cxr-s,cyr-s*.55,cxr+s,cyr+s*.55),outline=(52+12*j,150+8*j,240,64-j*9),width=2)
  for j in range(3):
   d.arc((cxr-510,cyr-350,cxr+510,cyr+350),30+j*24,110+j*25,fill=(92,213,255,170-j*40),width=5)
 if kind in ['signal','speed']:
  points=[]
  for xx in range(0,W+15,15):
   yy=int(680+90*math.sin(xx/124+n)+30*math.sin(xx/41+n*.7))
   points.append((xx,yy))
  d.line(points,fill=(36,154,234,105),width=5)
 return im

def header(im,category,number,end=327.648):
 d=ImageDraw.Draw(im,'RGBA')
 d.rounded_rectangle((86,62,370,110),22,fill=(8,30,60,210),outline=(72,141,229,82),width=2)
 txt(d,(112,75),'SMILYAI  /  ORION',22,(146,207,247),'semi')
 txt(d,(1830,75),category.upper(),23,(129,177,207),'semi',anchor='ra')
 d.rectangle((0,H-8,int(W*number/end),H),fill=(29,177,242,196))
 return im

def footer(im,n,explain=False):
 d=ImageDraw.Draw(im,'RGBA');txt(d,(86,1015),'ORION T3 FLASH',18,(124,162,199),'semi')
 txt(d,(1832,1015),'orion.smilyai.org',20,(139,177,207),'semi',anchor='ra')
 if explain:txt(d,(W//2,1017),'ILLUSTRATIVE DEMONSTRATION · NOT ACTUAL PRODUCT UI',16,(137,160,184),'reg',anchor='ma')
 return im

def lo(im,box):
 f=AS/'orion_logo_clean.png'
 logo=Image.open(f).convert('RGBA');w=box[2]-box[0];h=box[3]-box[1]
 logo.thumbnail((w,h),Image.Resampling.LANCZOS)
 x=box[0]+(w-logo.width)//2;y=box[1]+(h-logo.height)//2
 im.paste(logo,(x,y),logo)

def orb(d,x,y,s=100,c=CYAN):
 d.ellipse((x-s,y-s,x+s,y+s),outline=c,width=5)
 d.ellipse((x-s*.72,y-s*.72,x+s*.72,y+s*.72),outline=(34,98,164),width=3)
 d.line((x-s*1.25,y,x+s*1.25,y),fill=(*c,210),width=4)
 d.line((x,y-s*1.25,x,y+s*1.25),fill=(*c,210),width=4)

def card(d,b,title,body,accent=CYAN):
 rect(d,b,(11,27,55),25,outline=(42,84,124),width=2)
 rect(d,(b[0]+26,b[1]+23,b[0]+38,b[1]+67),accent,5)
 txt(d,(b[0]+58,b[1]+27),title,36,WHITE,'semi')
 for i,s in enumerate(body):txt(d,(b[0]+58,b[1]+90+i*43),s,27,MUTED)

def headline(im,kicker,title,sub='',align='left',size=95):
 d=ImageDraw.Draw(im,'RGBA');x=118 if align=='left' else 960
 anchor='la' if align=='left' else 'ma'
 txt(d,(x,218),kicker.upper(),27,CYAN,'semi',anchor=anchor)
 lines=title.split('|')
 for i,s in enumerate(lines):txt(d,(x,303+i*int(size*1.08)),s,size,WHITE,'extra',anchor=anchor)
 if sub:
  for j,s in enumerate(sub.split('|')):txt(d,(x,330+len(lines)*int(size*1.08)+j*43),s,30,MUTED,'reg',anchor=anchor)

def deco_brand(im,title='',subtitle='',n=0,small=False):
 d=ImageDraw.Draw(im,'RGBA');box=(1025,175,1820,900) if not small else (1190,360,1720,890)
 lo(im,box)
 if title:headline(im,'INTRODUCING',title,subtitle,size=89)

def draw_mockup(im,mode='general',n=0):
 d=ImageDraw.Draw(im,'RGBA')
 rect(d,(500,158,1750,930),(11,23,43,250),34,outline=(70,129,183,180),width=3)
 rect(d,(500,158,1750,237),(21,39,65,255),30)
 d.rectangle((500,203,1750,237),fill=(21,39,65,255))
 for i,c in enumerate(((255,105,114),(255,191,71),(72,209,137))):d.ellipse((540+i*34,190,554+i*34,204),fill=c)
 txt(d,(687,183),'ORION T3 FLASH  ·  INTERFACE CONCEPT',20,(186,210,235),'semi')
 rect(d,(570,284,1550,394),(28,49,81,255),22)
 if mode=='general':
  txt(d,(609,307),'USER',19,CYAN,'semi');txt(d,(609,341),'Why does the Moon change shape?',31,WHITE)
  rect(d,(570,435,1666,792),(10,39,60,255),22,outline=(55,106,143,200),width=2)
  txt(d,(615,469),'ORION · ILLUSTRATIVE TEXT RESPONSE',19,CYAN,'semi')
  multi(d,(615,525),['The Moon looks different as it orbits Earth.','Sunlight illuminates different portions of','its surface from our point of view.'],29,WHITE,1.65,'reg')
  txt(d,(608,839),'Ask a question...',23,(110,150,184))
 elif mode=='writing':
  txt(d,(609,307),'USER',19,CYAN,'semi');txt(d,(609,341),'Help me write a polite thank-you.',30,WHITE)
  rect(d,(570,435,1666,792),(10,39,60,255),22,outline=(55,106,143,200),width=2)
  txt(d,(615,468),'ORION · ILLUSTRATIVE TEXT RESPONSE',19,CYAN,'semi')
  multi(d,(615,530),['Thank you so much for your help today.','I really appreciate the time you took','to explain everything so clearly.'],29,WHITE,1.65,'reg')
  txt(d,(608,839),'Ask a question...',23,(110,150,184))
 elif mode=='code':
  txt(d,(609,307),'USER',19,CYAN,'semi');txt(d,(609,341),'How do I total numbers in Python?',28,WHITE)
  rect(d,(570,435,1666,792),(10,39,60,255),22,outline=(55,106,143,200),width=2)
  txt(d,(615,466),'ORION · ILLUSTRATIVE TEXT RESPONSE',19,CYAN,'semi')
  txt(d,(626,533),'numbers = [2, 4, 6]',32,(243,231,176),'semi')
  txt(d,(626,582),'total = sum(numbers)',32,(129,222,250),'semi')
  txt(d,(626,631),'print(total)    # 12',32,(211,219,244),'semi')
  txt(d,(622,715),'Use sum() to add the items in a list.',26,WHITE)
  txt(d,(608,839),'Ask a question...',23,(110,150,184))
 elif mode=='image':
  txt(d,(609,307),'USER',19,CYAN,'semi');txt(d,(609,341),'What is in this picture?',30,WHITE)
  rect(d,(570,435,1666,792),(10,39,60,255),22,outline=(55,106,143,200),width=2)
  # miniature clearly illustrative input picture
  rect(d,(600,462,920,751),(17,90,115),14)
  d.ellipse((814,480,871,538),fill=(249,223,120))
  d.polygon([(605,706),(722,561),(814,706)],fill=(19,87,75))
  d.polygon([(730,708),(843,550),(914,708)],fill=(29,117,85))
  d.rectangle((600,705,920,750),fill=(11,69,65))
  txt(d,(964,477),'ORION · TEXT REPLY',20,CYAN,'semi')
  multi(d,(964,532),['It appears to show','mountains beneath','a bright sky.'],27,WHITE,1.7,'reg')
  txt(d,(608,839),'Ask a question...',23,(110,150,184))
 return im

def render_scene(sc,idx):
 start,end,kind,category,tag,main,sub=sc
 im=background(idx,kind); d=ImageDraw.Draw(im,'RGBA')
 # glowing accent dividers for editorial continuity
 d.rounded_rectangle((86,147,95,874),4,fill=(16,119,228,110))
 if kind=='hero':
  headline(im,tag,main,sub,size=80 if len(main)>24 else 97)
  deco_brand(im,small=(idx!=0))
 elif kind=='final':
  lo(im,(675,30,1280,660))
  txt(d,(960,673),'ORION T3 FLASH',85,WHITE,'extra',anchor='ma')
  txt(d,(960,788),main,39,CYAN,'semi',anchor='ma')
  txt(d,(960,871),'orion.smilyai.org',46,WHITE,'semi',anchor='ma')
  txt(d,(960,954),'TRY ORION NOW',25,YELLOW,'bold',anchor='ma')
 elif kind=='statement':
  headline(im,tag,main,sub,size=90 if len(main)<35 else 72)
  d.rounded_rectangle((1190,330,1730,740),32,fill=(8,30,65,170),outline=(47,113,176,140),width=2)
  for i in range(4):
   x=1280+i*105;y=530+math.sin(idx+i)*75
   d.ellipse((x-24,y-24,x+24,y+24),fill=(12,52,90),outline=CYAN,width=3)
   if i:d.line((1280+(i-1)*105,530+math.sin(idx+i-1)*75,x,y),fill=(54,158,227,160),width=3)
 elif kind in ['orbit','context']:
  headline(im,tag,main,sub,size=84 if len(main)<28 else 74)
  cx,cy=1420,535
  orb(d,cx,cy,188,BLUE)
  for j,c in enumerate((CYAN,BLUE,YELLOW)):
   phi=j*2.094+idx*.2;x=cx+math.cos(phi)*260;y=cy+math.sin(phi)*260
   d.ellipse((x-18,y-18,x+18,y+18),fill=c)
 elif kind=='question':
  headline(im,tag,main,sub,size=73)
  card(d,(1170,238,1790,430),'QUESTION',['What do I need to know?'],CYAN)
  card(d,(1240,489,1840,680),'IDEA',['What could I make?'],YELLOW)
  card(d,(1140,737,1770,927),'SOLUTION',['Where do I start?'],BLUE)
 elif kind=='code':
  headline(im,tag,main,sub,size=76)
  rect(d,(1180,268,1800,827),(11,28,52),28,outline=(47,115,178),width=3)
  txt(d,(1224,303),'example.py',29,CYAN,'semi')
  d.line((1210,373,1770,373),fill=(70,108,146),width=2)
  rows=['numbers = [2, 4, 6]','total = sum(numbers)','print(total)','', '# Output: 12']
  for i,s in enumerate(rows):txt(d,(1237,412+65*i),s,28,YELLOW if i==0 else (130,225,246) if i==1 else WHITE,'semi')
 elif kind=='mock':
  ui=Image.new('RGBA',(1920,1080),(0,0,0,0))
  draw_mockup(ui,'code' if 'code' in tag.lower() else 'image' if 'image' in tag.lower() else 'writing' if 'write' in tag.lower() else 'general')
  ui=ui.crop((495,153,1755,943)).resize((1110,695),Image.Resampling.LANCZOS)
  im.paste(ui,(778,197),ui)
  d=ImageDraw.Draw(im,'RGBA')
  txt(d,(120,288),tag.upper(),24,CYAN,'semi')
  multi(d,(120,361),main.split('|'),64,WHITE,1.16,'extra')
  for j,t in enumerate(sub.split('|')):txt(d,(120,583+j*47),t,27,MUTED)
 elif kind=='speed':
  headline(im,tag,main,sub,size=79)
  for i in range(8):
   x=1120+i*78;y=555+math.sin(i/2+idx)*46
   d.ellipse((x-10,y-10,x+10,y+10),fill=CYAN if i%3==0 else BLUE)
   if i:d.line((1120+(i-1)*78,555+math.sin((i-1)/2+idx)*46,x,y),fill=(43,175,246,130),width=4)
 elif kind=='big':
  txt(d,(960,220),tag.upper(),26,CYAN,'semi',anchor='ma')
  txt(d,(960,341),main,140 if len(main)<18 else 91,WHITE,'extra',anchor='ma')
  for i,s in enumerate(sub.split('|')):txt(d,(960,570+i*55),s,36,MUTED,'reg',anchor='ma')
  d.rounded_rectangle((345,796,1575,803),3,fill=(40,142,240,185))
 elif kind=='files':
  headline(im,tag,main,sub,size=80)
  for i in range(14):
   x=1200+(i%5)*116;y=290+(i//5)*170
   d.rounded_rectangle((x,y,x+90,y+124),12,fill=(18,50,78,230),outline=(54,139,185,135),width=2)
   d.line((x+16,y+43,x+70,y+43),fill=(72,177,222,140),width=3)
   d.line((x+16,y+64,x+70,y+64),fill=(72,177,222,140),width=3)
   d.line((x+16,y+85,x+62,y+85),fill=(72,177,222,140),width=3)
 elif kind=='upload':
  headline(im,tag,main,sub,size=78)
  rect(d,(1215,274,1750,779),(11,34,63),38,outline=(44,147,199),width=4)
  d.ellipse((1406,354,1554,502),outline=CYAN,width=6)
  d.line((1480,389,1480,468),fill=CYAN,width=10)
  d.polygon([(1440,412),(1480,362),(1520,412)],fill=CYAN)
  txt(d,(1480,584),'IMAGE INPUT',29,WHITE,'bold',anchor='ma')
  txt(d,(1480,645),'QUESTION → TEXT',26,CYAN,'semi',anchor='ma')
 elif kind=='modes':
  headline(im,tag,main,sub,size=78)
  rect(d,(1117,317,1810,752),(10,29,56),34,outline=(42,109,166),width=3)
  rect(d,(1161,378,1775,519),(15,55,84),24,outline=(58,215,246),width=3)
  txt(d,(1210,399),'INSTANT',50,WHITE,'extra')
  txt(d,(1210,472),'DEFAULT',24,CYAN,'semi')
  rect(d,(1161,555,1775,687),(17,36,59),24,outline=(65,87,121),width=2)
  txt(d,(1210,594),'LOW',50,WHITE,'extra')
 elif kind=='offer':
  txt(d,(960,235),tag,30,CYAN,'semi',anchor='ma')
  txt(d,(960,348),main,91,WHITE,'extra',anchor='ma')
  rect(d,(350,541,1570,731),(15,51,72),37,outline=(92,220,244),width=3)
  txt(d,(960,604),'JANUARY 1, 2027',76,WHITE,'bold',anchor='ma')
  txt(d,(960,786),sub,33,MUTED,anchor='ma')
 elif kind=='cta':
  headline(im,tag,main,sub,size=95 if len(main)<32 else 79)
  rect(d,(1146,477,1797,632),(10,66,95),37,outline=(103,222,247),width=3)
  txt(d,(1470,520),'TRY ORION NOW  →',43,WHITE,'bold',anchor='ma')
  txt(d,(1470,687),'orion.smilyai.org',36,CYAN,'semi',anchor='ma')
 else:headline(im,tag,main,sub)
 if kind!='final':
  footer(im,start,kind=='mock')
  header(im,category,start)
 path=ST/f'{idx:03d}.png';im.save(path,optimize=True)
 return str(path)

# Timings locked to full 327.648-second supplied track, aligned to broader musical changes.
S=[
(0,7,'orbit','I · Introduction','A NEW WAY TO BEGIN','SOMETHING NEW|IS ON THE HORIZON','A little more clarity, in every conversation.'),
(7,15,'hero','I · Introduction','SMILYAI PRESENTS','ORION|T3 FLASH','Designed for fast responses. Made for real questions.'),
(15,24,'statement','I · Introduction','EVERYDAY INTELLIGENCE','FAST. RELIABLE.|READY WHEN YOU ARE.','AI for moments when the next step matters.'),
(24,32,'hero','I · Introduction','THE NEXT CHAPTER','ASK MORE.|DO MORE.','A capable assistant for people with questions.'),
(32,40,'orbit','I · Introduction','WELCOME','YOUR NEXT STEP|STARTS HERE.','Meet Orion T3 Flash.'),
(40,48,'question','II · Everyday','EVERY QUESTION STARTS SOMEWHERE','A QUESTION.|AN IDEA.','Something you want to understand.'),
(48,56,'statement','II · Everyday','AT SCHOOL','WHEN A TOPIC|GETS TRICKY.','Start with an explanation you can explore.'),
(56,64,'question','II · Everyday','IN YOUR EVERYDAY','WHEN WORDS|MATTER.','Get help drafting a thoughtful message.'),
(64,72,'code','II · Everyday','WHEN YOU ARE BUILDING','ANOTHER LINE.|ANOTHER IDEA.','Coding assistance when you need a hand.'),
(72,80,'statement','II · Everyday','THE SIMPLEST START','JUST ASK.','You bring the question. Orion brings a text response.'),
(80,88,'hero','III · Meet Orion','INTRODUCING','ORION|T3 FLASH','Fast, reliable AI for questions, ideas and code.'),
(88,97,'mock','III · Meet Orion','ASK ANYDAY QUESTIONS','CURIOUS?|ASK ORION.','Example conversation|Clearly illustrative'),
(97,106,'statement','III · Meet Orion','UNDERSTANDING','FROM UNCERTAINTY|TO A NEXT STEP.','Follow the explanation. Ask another question.'),
(106,115,'mock','III · Meet Orion','WRITE SOMETHING','FIND THE|RIGHT WORDS.','Draft messages with AI assistance.'),
(115,123,'mock','III · Meet Orion','CODE WITH ORION','WORK THROUGH|A PROBLEM.','Understand simple code examples.'),
(123,130,'hero','III · Meet Orion','MADE TO BE USEFUL','QUESTIONS.|IDEAS. CODE.','One place to start the conversation.'),
(130,139,'speed','IV · Built for speed','DESIGNED FOR SPEED','MOVE FROM|QUESTION TO ACTION.','Responsive by design. Actual speed varies by server load.'),
(139,149,'mock','IV · Built for speed','ASK ANYDAY QUESTIONS','START WITH|A QUESTION.','Illustrative text conversation.'),
(149,160,'speed','IV · Built for speed','FOLLOW THE FLOW','KEEP YOUR|IDEAS MOVING.','Less friction between your question and next step.'),
(160,168,'statement','IV · Built for speed','A MOMENT TO THINK','FOCUS ON|WHAT MATTERS.','No invented speed claims. Just everyday usefulness.'),
(168,175,'code','IV · Built for speed','BACK TO YOUR WORK','BUILD.|TEST. IMPROVE.','Use Orion to explore code and ideas.'),
(175,184,'big','V · Context','MORE ROOM TO EXPLORE','262K TOKENS','Standard context window|For conversations with more information.'),
(184,193,'files','V · Context','STAY WITH THE DETAILS','MORE ROOM|FOR CONTEXT.','Context is the information available in a conversation.'),
(193,203,'context','V · Context','THE BIG PICTURE','KEEP MORE|IN VIEW.','A standard 262K-token context window.'),
(203,212,'big','V · Context','EXTENSION AVAILABLE ON REQUEST','UP TO 1M','Email the team to request more context.|Extension uses YaRN; not enabled by default.'),
(212,215,'statement','V · Context','UPON REQUEST','CONTACT|OUR TEAM.','Ask about the optional 1M-token extension.'),
(215,224,'upload','VI · Image input','BRING YOUR IMAGES','TEXT + IMAGE|INPUT.','Upload an image and ask a question about it.'),
(224,234,'mock','VI · Image input','IMAGE INPUT','SHOW IT.|ASK ABOUT IT.','A clearly illustrative image question.'),
(234,243,'statement','VI · Image input','RESPONSES IN TEXT','ORION REPLIES|WITH WORDS.','Text output only. No generated images, audio or video.'),
(243,250,'upload','VI · Image input','BEYOND A DESCRIPTION','BRING AN IMAGE.|ASK AWAY.','Bring visual context into the conversation.'),
(250,259,'modes','VII · Effort modes','TWO AVAILABLE MODES','YOUR WAY|TO ASK.','Instant is the default. Low is also available.'),
(259,267,'big','VII · Effort modes','DEFAULT MODE','INSTANT','The standard option when you start.'),
(267,275,'modes','VII · Effort modes','ANOTHER OPTION','INSTANT  /  LOW','Two available effort settings.'),
(275,283,'statement','VIII · Invitation','BACK TO YOUR IDEAS','MORE QUESTIONS.|MORE POSSIBILITIES.','Bring the next thing you want to figure out.'),
(283,292,'mock','VIII · Invitation','ASK ANYDAY QUESTIONS','CURIOUS?|GO AHEAD.','Ask what has been on your mind.'),
(292,300,'offer','VIII · Invitation','START EXPLORING','FREE TO USE THROUGH','Free-access offer ends January 1, 2027.'),
(300,308,'cta','VIII · Invitation','YOUR INVITATION','NO BIG SPEECH.|JUST ASK.','Free use through January 1, 2027.'),
(308,316,'hero','IX · Finale','THIS IS YOUR MOMENT','ORION|T3 FLASH','Fast, reliable AI. Ready when you are.'),
(316,322,'final','IX · Finale','TRY ORION','FAST, RELIABLE AI. READY WHEN YOU ARE.',''),
(322,327.648,'final','IX · Finale','TRY ORION','FAST, RELIABLE AI. READY WHEN YOU ARE.','')]

def run(cmd):
 p=subprocess.run(cmd,capture_output=True,text=True)
 if p.returncode:raise RuntimeError(' '.join(map(str,cmd))+'\n'+p.stderr[-3000:])

def make_segment(i,fast=True):
 start,end,*_=S[i];dur=round((end-start)*30)/30
 target=PART/f'{i:03d}.mp4'
 if target.exists() and target.stat().st_size>50000:return i
 # Deliberately restrained slow dolly on each editorial composition.
 direction=1 if i%2 else -1
 filt=f"scale=1960:1103:flags=bicubic,crop=1920:1080:x='20+{direction}*16*sin(n/130)':y='11+7*sin(n/155)',format=yuv420p"
 cmd=['ffmpeg','-nostdin','-hide_banner','-loglevel','error','-y','-loop','1','-framerate','30','-i',str(ST/f'{i:03d}.png'),'-t',f'{dur:.6f}','-vf',filt,'-an','-c:v','libx264','-preset','ultrafast' if fast else 'veryfast','-crf','21','-pix_fmt','yuv420p','-r','30','-movflags','+faststart',str(target)]
 run(cmd);return i

def main():
 import argparse,time
 p=argparse.ArgumentParser();p.add_argument('--stills-only',action='store_true');p.add_argument('--scene',type=int,default=None);p.add_argument('--workers',type=int,default=3);p.add_argument('--no-fast',action='store_true');a=p.parse_args()
 subset=[a.scene] if a.scene is not None else list(range(len(S)))
 t=time.time();print('Generating',len(subset),'scenes',flush=True)
 for i in subset:
  render_scene(S[i],i)
  if i%8==0:print('  still',i,'/',len(S),flush=True)
 # Save reproducible manifest.
 with open(ROOT/'project'/'shot_manifest.json','w') as f:
  json.dump([{'start_s':r[0],'end_s':r[1],'treatment':r[2],'act':r[3],'kicker':r[4],'title':r[5],'caption':r[6]} for r in S],f,indent=2)
 print('Generated stills in',round(time.time()-t,1),'seconds',flush=True)
 if a.stills_only:return
 print('Rendering video segments with ffmpeg...',flush=True)
 with concurrent.futures.ThreadPoolExecutor(max_workers=a.workers) as pool:
  for n in pool.map(lambda i:make_segment(i,fast=not a.no_fast),subset):
   if n%5==0:print('  segment',n,'/',len(S),flush=True)
 if a.scene is not None:return
 concat=ROOT/'project'/'concat.txt'
 concat.write_text(''.join('file '+repr(str(PART/f'{i:03d}.mp4'))+'\n' for i in range(len(S))))
 silent=ROOT/'Orion_T3_Flash_Launch_Silent.mp4'
 run(['ffmpeg','-nostdin','-hide_banner','-loglevel','error','-y','-f','concat','-safe','0','-i',str(concat),'-c','copy','-movflags','+faststart',str(silent)])
 audio=AS/'soundtrack.mp3'
 target=ROOT/'Orion_T3_Flash_Official_Launch_1080p.mp4'
 run(['ffmpeg','-nostdin','-hide_banner','-loglevel','error','-y','-i',str(silent),'-i',str(audio),'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','256k','-ar','48000','-t','327.648','-movflags','+faststart',str(target)])
 print('DONE',target,round(time.time()-t,1),'sec total',flush=True)

if __name__=='__main__':main()