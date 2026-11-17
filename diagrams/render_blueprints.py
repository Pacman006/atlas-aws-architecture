#!/usr/bin/env python3
"""Render source-controlled, vector-first Atlas architecture diagrams.

Requires: svgwrite, cairosvg. Outputs editable SVGs and readable PNGs.
No AWS account or third-party image generation services are used.
"""
from pathlib import Path
import svgwrite
import cairosvg

OUT = Path(__file__).resolve().parent
C = {
    'ink': '#17263D', 'muted': '#526781', 'navy': '#162B4A', 'line':'#A5B7CC',
    'blue': '#2D6DAD', 'blue_bg': '#EAF3FE', 'green':'#197658','green_bg':'#E6F6ED',
    'amber':'#9A650E','amber_bg':'#FFF4DE','purple':'#6D48A6','purple_bg':'#F0EBFA',
    'cloud':'#F6F9FD', 'white':'#FFFFFF', 'teal':'#097D92', 'teal_bg':'#E1F5F7',
    'red':'#AC5751', 'red_bg':'#FBEDEB', 'bg':'#FFFFFF', 'soft':'#EEF3F9'
}
FONT='DejaVu Sans, Arial, sans-serif'


def txt(d,x,y,s,size=25,fill=None,weight=400,anchor='start',tracking=None):
    kw = dict(insert=(x,y), fill=fill or C['ink'], font_size=size,
              font_family=FONT, font_weight=weight, text_anchor=anchor)
    if tracking:kw['letter_spacing']=tracking
    return d.add(d.text(s, **kw))


def multiline(d,x,y,lines,size=22,color=None,weight=400,line_gap=36,anchor='start'):
    for i,line in enumerate(lines):
        txt(d,x,y+i*line_gap,line,size,color,weight,anchor)


def rect(d,x,y,w,h,fill='white',border=None,rad=20,stroke=2):
    d.add(d.rect(insert=(x,y),size=(w,h),rx=rad,ry=rad,fill=C.get(fill,fill),
                 stroke=C.get(border,border) if border else 'none',stroke_width=stroke))


def label(d,x,y,text,color='muted'):
    txt(d,x,y,text,23,C.get(color,color),700)


def card(d,x,y,w,h,tag,lines,accent='blue',detail=None,small=False):
    accents={'blue':('blue_bg','blue'),'green':('green_bg','green'),
             'amber':('amber_bg','amber'),'purple':('purple_bg','purple'),
             'teal':('teal_bg','teal'),'red':('red_bg','red')}
    bg,st=accents[accent]
    rect(d,x,y,w,h,bg,st,18,2.5)
    rect(d,x,y,12,h,st,None,6)
    txt(d,x+29,y+38,tag.upper(),19,C[st],700,tracking='1')
    multiline(d,x+29,y+86,lines,26 if not small else 22,C['ink'],700,39 if not small else 33)
    if detail:
        txt(d,x+29,y+h-26,detail,19,C['muted'])


def line(d,pts,color='blue',width=5,dashed=False,arrow=True):
    coords=' '.join(f'{x},{y}' for x,y in pts)
    style={'fill':'none','stroke':C.get(color,color),'stroke_width':width,
            'stroke_linecap':'round','stroke_linejoin':'round'}
    if dashed:style['stroke_dasharray']='13,12'
    if arrow:
        marker_name = color if color in ('blue','green','amber','purple','teal') else 'blue'
        style['marker_end']=f'url(#arrow_{marker_name})'
    d.add(d.polyline(points=pts,**style))


def doc(w,h,title,subtitle):
    d=svgwrite.Drawing(size=(f'{w}px',f'{h}px'),viewBox=f'0 0 {w} {h}')
    defs=d.defs
    for key in ('blue','green','amber','purple','teal'):
        marker=d.marker(id=f'arrow_{key}',insert=(9,5),size=(10,10),orient='auto',markerUnits='strokeWidth')
        marker.add(d.path(d='M 0 0 L 10 5 L 0 10 z',fill=C[key]))
        defs.add(marker)
    rect(d,0,0,w,h,'bg',rad=0)
    rect(d,0,0,w,142,'navy',rad=0)
    txt(d,78,67,title,43,'#FFFFFF',700)
    txt(d,78,112,subtitle,23,'#D5E5F8')
    return d


def pill(d,x,y,w,s,bg='#E5EFFB',fg='#274D73'):
    rect(d,x,y,w,43,bg,rad=20)
    txt(d,x+w/2,y+29,s,18,fg,700,anchor='middle')


def write(d,svg_name,png_name):
    svg_path=OUT/svg_name
    png_path=OUT/png_name
    d.saveas(str(svg_path),pretty=True)
    cairosvg.svg2png(url=str(svg_path),write_to=str(png_path),output_width=int(d['width'].replace('px','')))
    print(f'{svg_path.name}: {svg_path.stat().st_size:,} bytes | {png_path.name}: {png_path.stat().st_size:,} bytes')

# --------- 1: SYSTEM OVERVIEW ---------
d=doc(2400,1650,'PROJECT ATLAS  /  AWS SYSTEM ARCHITECTURE',
      'React + Flask API  •  Elastic Beanstalk  •  private RDS  •  CloudFront  •  GitHub delivery')
rect(d,875,188,1450,560,'cloud','line',24,2)
label(d,920,232,'AWS VPC    10.42.0.0/16','navy')
rect(d,895,264,430,375,'blue_bg','line',18,1.5)
rect(d,1345,264,485,375,'green_bg','line',18,1.5)
rect(d,1850,264,455,375,'amber_bg','line',18,1.5)
label(d,920,302,'PUBLIC  /  AZ-A + AZ-B','blue')
label(d,1372,302,'PRIVATE APP  /  AZ-A + AZ-B','green')
label(d,1876,302,'PRIVATE DB  /  AZ-A + AZ-B','amber')
# arrows first (they pass through box edges only)
line(d,[(360,420),(430,420)])
line(d,[(812,420),(928,420)])
line(d,[(1275,420),(1375,420)])
line(d,[(1802,420),(1878,420)],'green')
line(d,[(615,494),(615,568)],'amber',width=4)
# architecture actors
card(d,55,346,305,148,'Internet client',['Browser / users'],'blue',detail='Public HTTPS viewer')
card(d,430,346,382,148,'Global CDN',['Amazon CloudFront'],'blue',detail='TLS 443 · edge cache policies')
card(d,928,346,347,148,'Traffic entry',['Load Balancer (ALB)'],'blue',detail='Health: GET /health')
card(d,1375,346,427,148,'Private compute',['Elastic Beanstalk EC2'],'green',detail='Auto Scaling: min 2 · max 4')
card(d,1878,346,400,148,'Private data',['RDS PostgreSQL'],'amber',detail='TCP 5432 · TLS · backups')
# connections/labels
pill(d,358,303,132,'HTTPS 443')
pill(d,788,303,152,'443 / 80')
pill(d,1271,303,133,'HTTP 80')
pill(d,1770,303,148,'TLS 5432','#E7F5E9','#187653')
card(d,426,568,385,158,'Image origin',['Private S3 images'],'amber',detail='CloudFront OAC /images/*',small=True)
pill(d,65,553,292,'No direct EC2 / DB access', '#E9F1FA', C['blue'])
txt(d,919,571,'ALB SG: CloudFront-only origin ranges',19,C['muted'])
txt(d,1370,571,'EC2 SG: allow ALB only',19,C['muted'])
txt(d,1870,571,'RDS: non-public DB subnets',19,C['muted'])
txt(d,1370,610,'NAT egress → AWS APIs (HTTPS 443)',19,C['muted'])
txt(d,1870,610,'Secrets Manager credentials',19,C['muted'])
# delivery lane
rect(d,57,800,2270,345,'#F8F5FE','#D7C9EF',24,2)
label(d,90,847,'CONTINUOUS DELIVERY   /   master branch → deploy','purple')
line(d,[(520,968),(632,968)],'purple')
line(d,[(1055,968),(1168,968)],'purple')
line(d,[(1602,968),(1710,968)],'purple')
card(d,93,893,427,159,'Source control',['GitHub / master'],'purple',detail='Push initiates workflow')
card(d,632,893,423,159,'Identity',['GitHub OIDC → STS'],'purple',detail='No saved AWS access keys')
card(d,1168,893,434,159,'Release artifact',['Versioned S3 ZIP'],'purple',detail='Build React / package Flask')
card(d,1710,893,573,159,'Application update',['Elastic Beanstalk release'],'purple',detail='Update version + CDN invalidation')
# telemetry
rect(d,57,1195,2270,366,'#F1FAF7','#C5E8DA',24,2)
label(d,90,1242,'ACTIVITY LOGGING   /   streaming → CSV → reporting','green')
coords=[(92,1300,350,'Flask request logs',['JSON events']),(493,1300,354,'CloudWatch Logs',['30-day retention']),(890,1300,354,'Kinesis Stream',['Streaming input']),(1288,1300,380,'Firehose + Lambda',['CSV transformation']),(1714,1300,569,'S3 CSV → Athena',['CloudWatch dashboard'])]
for i,(x,y,w,tag,lines) in enumerate(coords):
    card(d,x,y,w,155,tag,lines,'green',small=True)
    if i<len(coords)-1:
        next_x=coords[i+1][0]
        line(d,[(x+w,1375),(next_x,1375)],'green',width=4)
txt(d,78,1617,'Security boundary: browser → CloudFront; origin access filtered; application and database remain privately addressed.',20,C['muted'])
write(d,'architecture.svg','architecture.png')

# --------- 2: NETWORK AND SECURITY ---------
d=doc(2200,1620,'PROJECT ATLAS  /  NETWORK & SECURITY BLUEPRINT',
      'Two Availability Zones  •  six subnets  •  tier-specific security groups  •  restricted route tables')
rect(d,76,392,2048,948,'cloud','line',25,2)
label(d,116,1310,'VPC 10.42.0.0/16  ·  regional AWS boundary','navy')
card(d,802,239,595,138,'Global origin access',['CloudFront edge locations'],'blue',detail='ALB ingress restricted to CloudFront IP ranges')
# AZ columns
rect(d,111,430,945,830,'#F0F6FE','#B8CFE6',22,2)
rect(d,1143,430,945,830,'#F0F6FE','#B8CFE6',22,2)
label(d,148,482,'AVAILABILITY ZONE A','blue')
label(d,1180,482,'AVAILABILITY ZONE B','blue')
line(d,[(970,377),(590,412),(590,521)],'blue')
line(d,[(1230,377),(1610,412),(1610,521)],'blue')
# internal routing arrows (before cards)
for x in (590,1610):
    line(d,[(x,719),(x,803)],'blue')
    line(d,[(x,997),(x,1083)],'green')
# public cards
card(d,162,528,844,191,'Public subnet A  ·  10.42.0.0/24',
     ['ALB network node  +  NAT gateway A'],'blue',detail='Internet Gateway route · NAT available in demo and production')
card(d,1194,528,844,191,'Public subnet B  ·  10.42.1.0/24',
     ['ALB network node  +  NAT-B (production)'],'blue',detail='No NAT-B in single-NAT demonstration configuration')
# private app cards
card(d,162,803,844,194,'Private app subnet A  ·  10.42.10.0/24',
     ['Elastic Beanstalk / EC2  (Auto Scaling)'],'green',detail='ALB SG → EC2 TCP 80 · NAT HTTPS egress')
card(d,1194,803,844,194,'Private app subnet B  ·  10.42.11.0/24',
     ['Elastic Beanstalk / EC2  (Auto Scaling)'],'green',detail='ALB SG → EC2 TCP 80 · NAT HTTPS egress')
# db cards
card(d,162,1083,844,150,'Isolated DB subnet A  ·  10.42.20.0/24',
     ['RDS PostgreSQL (non-public)'],'amber',detail='App SG only → TCP 5432 / TLS',small=True)
card(d,1194,1083,844,150,'Isolated DB subnet B  ·  10.42.21.0/24',
     ['RDS standby path / Multi-AZ'],'amber',detail='No internet default route / database subnet group',small=True)
# notes bottom
rect(d,78,1380,2044,175,'#F7FAFC','#D1DFED',22,2)
label(d,118,1430,'TRAFFIC RULES','navy')
multiline(d,118,1480,[
    'CloudFront → ALB: TCP 443 (production) / 80 (demo)  •  ALB → EC2: TCP 80  •  EC2 → RDS: TCP 5432 (TLS)',
    'EC2 → AWS APIs: TCP 443 via NAT  •  S3 image origin is outside VPC and uses CloudFront OAC  •  no public DB endpoint'
],21,C['muted'],400,41)
write(d,'network.svg','network.png')

# --------- 3: TELEMETRY ---------
d=doc(2350,1160,'PROJECT ATLAS  /  LOG STREAMING & CSV ANALYTICS',
      'Request events are collected in CloudWatch, streamed to Kinesis, transformed to CSV, and queried from S3')
rect(d,65,183,2220,510,'#F7FBFD','#C3D7E9',26,2)
label(d,110,232,'END-TO-END ACTIVITY LOG DELIVERY','navy')
items=[
(103,309,350,'01  APPLICATION',['Flask JSON logs'],'green','Request metadata only'),
(543,309,350,'02  LOG COLLECTION',['CloudWatch Logs'],'blue','30-day log retention'),
(983,309,350,'03  DATA STREAM',['Kinesis Streams'],'teal','Near-real-time events'),
(1423,309,350,'04  TRANSFORMATION',['Firehose + Lambda'],'purple','gzip → normalized CSV'),
(1863,309,350,'05  STORAGE',['S3 CSV objects'],'amber','activity/ prefix')]
for i,(x,y,w,tag,lines,color,detail) in enumerate(items):
    card(d,x,y,w,222,tag,lines,color,detail)
    if i<len(items)-1:
        line(d,[(x+w,414),(items[i+1][0],414)],'blue',width=5)
# insights down
line(d,[(2038,531),(2038,762),(1610,762),(1610,798)],'green',width=5)
line(d,[(713,531),(713,798)],'green',width=5)
rect(d,130,787,940,211,'#EAF7F0','#8FC9AC',22,2)
rect(d,1280,787,940,211,'#EAF7F0','#8FC9AC',22,2)
label(d,172,843,'OPERATIONS DASHBOARD','green')
multiline(d,172,895,['CloudWatch metrics: request count, 5xx, latency','Designed for operations; does not query CSV directly'],24,C['ink'],400,46)
label(d,1322,843,'ANALYTICS / QUERY','green')
multiline(d,1322,895,['Athena reads the delivered CSV files in S3','Create table using analytics/athena.sql'],24,C['ink'],400,46)
txt(d,92,1073,'Data safety: do not include authentication tokens, secrets, passwords, request bodies or unnecessary personal information in request logs.',22,C['muted'])
write(d,'telemetry.svg','telemetry.png')
