"""Original OceanBond gameplay model studies. Deterministic glTF 2.0 generation.
No downloaded models, private game files, network access, or proprietary assets.
Run from repository root: python _build/chapters/build_models.py
"""
from pathlib import Path
import io, json, struct, math
import numpy as np
from PIL import Image, ImageDraw
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'assets/oceanbond-chapters/models'
OUT.mkdir(parents=True, exist_ok=True)
PI=math.pi
rng=np.random.default_rng(3701)
def unit(v):
 v=np.array(v,dtype=float); return v/np.maximum(np.linalg.norm(v,axis=-1,keepdims=True),1e-9)
def quat(axis,angle):
 return [*(unit(axis)*math.sin(angle/2)), math.cos(angle/2)]
def tex(name):
 n=512; y,x=np.mgrid[0:n,0:n].astype(float);u=x/n;v=y/n
 local=np.random.default_rng(sum(map(ord,name))+91)
 noise=local.random((n,n));low=np.array(Image.fromarray((local.random((24,24))*255).astype('uint8')).resize((n,n),Image.Resampling.BICUBIC))/255
 if name=='wood':
  wave=np.sin(v*950+np.sin(u*12+v*6)*4+low*2);h=.5+.18*wave+.22*low+.1*noise
  c=np.array([172,116,63])[None,None,:]*(.64+.28*h[:,:,None]);rough=.68+.12*noise
 elif name=='cloth':
  h=.5+.18*np.sin(x*2.1)+.18*np.sin(y*2.1)+.1*noise;c=np.array([218,202,160])[None,None,:]*(.79+.20*h[:,:,None]);rough=.91+.08*noise
 elif name=='soil':
  h=.4*low+.6*noise;c=np.array([106,72,43])[None,None,:]*(.46+.6*h[:,:,None]);rough=.95+noise*.05
 elif name=='leaf':
  vein=np.exp(-((u-.5)*75)**2);h=.5+.15*np.sin((v*12+abs(u-.5)*9)*PI)+vein*.3
  c=np.dstack([47+27*low+24*vein,105+63*low+45*vein,25+25*low+9*vein]);rough=.6+.2*noise
 elif name=='metal':
  h=.5+noise*.15+.15*np.sin(y*5);c=np.array([174,189,191])[None,None,:]*(.72+.22*low[:,:,None]+.06*noise[:,:,None]);rough=.32+.15*noise
 else:
  h=.5+.2*low+.3*noise;c=np.array([150,145,129])[None,None,:]*(.58+.42*h[:,:,None]);rough=.87+.1*noise
 base=Image.fromarray(np.uint8(np.clip(c,0,255)));dy,dx=np.gradient(h)
 normal=unit(np.stack([-dx*2,-dy*2,np.ones_like(dx)],-1))
 normal=Image.fromarray(np.uint8(np.clip(normal*.5+.5,0,1)*255)).resize((256,256))
 orm=Image.fromarray(np.uint8(np.stack([np.ones_like(h),rough,np.ones_like(h)],-1)*255)).resize((256,256))
 result=[]
 for im,fmt in [(base,'JPEG'),(normal,'PNG'),(orm,'PNG')]:
  f=io.BytesIO();im.save(f,format=fmt,**({'quality':88} if fmt=='JPEG' else {}));result.append(f.getvalue())
 return result
TEX={k:tex(k) for k in ['wood','cloth','soil','leaf','metal','stone']}
class Model:
 def __init__(self,name):
  self.name=name;self.b=bytearray();self.d={'asset':{'version':'2.0','generator':'MTH Labs / gameplay object studies','copyright':'Original model studies for Mustafa Thaeer'},'scene':0,'scenes':[{'nodes':[0]}],'nodes':[{'name':name,'children':[]}],'meshes':[],'materials':[],'textures':[],'images':[],'samplers':[{'magFilter':9729,'minFilter':9987,'wrapS':10497,'wrapT':10497}],'accessors':[],'bufferViews':[],'animations':[]};self.groups={};self.maps={};self.anim={'name':name+'_8s','channels':[],'samplers':[]}
 def buf(self,b,target=None):
  self.b.extend(b'\0'*((-len(self.b))%4));i=len(self.d['bufferViews']);v={'buffer':0,'byteOffset':len(self.b),'byteLength':len(b)}
  if target:v['target']=target
  self.d['bufferViews'].append(v);self.b.extend(b);return i
 def acc(self,a,typ,target=None):
  a=np.asarray(a);ct=5125 if a.dtype==np.uint32 else 5126;a=a.astype('<u4' if ct==5125 else '<f4');dims={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[typ];a=a.reshape(-1,dims);i=len(self.d['accessors']);self.d['accessors'].append({'bufferView':self.buf(a.tobytes(),target),'componentType':ct,'count':len(a),'type':typ,'min':a.min(0).tolist(),'max':a.max(0).tolist()});return i
 def material(self,name,color,texture=None,metal=0,rough=.7,glow=None):
  p={'baseColorFactor':[*color,1],'metallicFactor':metal,'roughnessFactor':rough};d={'name':name,'doubleSided':True,'pbrMetallicRoughnessness':p}
  d['pbrMetallicRoughness']=d.pop('pbrMetallicRoughnessness')
  if texture:
   if texture not in self.maps:
    ids=[]
    for data in TEX[texture]:
     n=len(self.d['images']);self.d['images'].append({'name':texture+str(n),'bufferView':self.buf(data),'mimeType':'image/jpeg' if data[:2]==b'\xff\xd8' else 'image/png'});ids.append(len(self.d['textures']));self.d['textures'].append({'sampler':0,'source':n})
    self.maps[texture]=ids
   a,b,c=self.maps[texture];p.update(baseColorTexture={'index':a},metallicRoughnessTexture={'index':c});d['normalTexture']={'index':b,'scale':.23}
  if glow:d['emissiveFactor']=glow
  self.d['materials'].append(d);return len(self.d['materials'])-1
 def node(self,name,parent=0,**kw):
  i=len(self.d['nodes']);self.d['nodes'].append({'name':name,**kw});self.d['nodes'][parent].setdefault('children',[]).append(i);return i
 def add(self,geom,mat,parent=0,name='surface'):
  p,uv,idx=geom;k=(parent,mat);group=self.groups.setdefault(k,[[],[],[],name]);off=len(group[0]);group[0].extend(p);group[1].extend(uv);group[2].extend(np.array(idx)+off)
 def channel(self,node,path,values):
  values=np.asarray(values);t=np.linspace(0,8,len(values));i=len(self.anim['samplers']);self.anim['samplers'].append({'input':self.acc(t,'SCALAR'),'output':self.acc(values,'VEC4' if path=='rotation' else 'VEC3'),'interpolation':'LINEAR'});self.anim['channels'].append({'sampler':i,'target':{'node':node,'path':path}})
 def finish(self):
  triangles=0
  for (parent,mat),(p,uv,ix,name) in self.groups.items():
   p=np.array(p,dtype='f4');ix=np.array(ix,dtype='uint32');n=np.zeros_like(p);f=np.cross(p[ix[:,1]]-p[ix[:,0]],p[ix[:,2]]-p[ix[:,0]])
   for k in range(3):np.add.at(n,ix[:,k],f)
   n=unit(n);mesh={'name':name,'primitives':[{'attributes':{'POSITION':self.acc(p,'VEC3',34962),'NORMAL':self.acc(n,'VEC3',34962),'TEXCOORD_0':self.acc(uv,'VEC2',34962)},'indices':self.acc(ix.flatten(),'SCALAR',34963),'material':mat}]};self.d['meshes'].append(mesh);self.node(name,parent,mesh=len(self.d['meshes'])-1);triangles+=len(ix)
  self.d['animations']=[self.anim];self.b.extend(b'\0'*((-len(self.b))%4));self.d['buffers']=[{'byteLength':len(self.b)}];j=json.dumps(self.d,separators=(',',':')).encode();j+=b' '*((-len(j))%4);b=bytes(self.b);out=struct.pack('<III',0x46546c67,2,28+len(j)+len(b))+struct.pack('<II',len(j),0x4e4f534a)+j+struct.pack('<II',len(b),0x004e4942)+b;(OUT/(self.name+'.glb')).write_bytes(out);return {'file':self.name+'.glb','bytes':len(out),'triangles':triangles,'meshes':len(self.d['meshes']),'textureImages':len(self.d['images']),'animationChannels':len(self.anim['channels'])}
def surface(fn,nu=24,nv=12):
 p=[];uv=[];idx=[]
 for j in range(nv+1):
  for i in range(nu+1):p.append(fn(i/nu,j/nv));uv.append([i/nu,j/nv])
 for j in range(nv):
  for i in range(nu):
   a=j*(nu+1)+i;idx.extend([[a,a+1,a+nu+2],[a,a+nu+2,a+nu+1]])
 return np.array(p),np.array(uv),np.array(idx)
def sphere(c,s,nu=20,nv=12):
 return surface(lambda u,v:np.array(c)+np.array(s)*[math.sin(v*PI)*math.cos(u*PI*2),math.cos(v*PI),math.sin(v*PI)*math.sin(u*PI*2)],nu,nv)
def tube(points,r=.04,sides=10):
 pts=np.array(points);t=unit(np.gradient(pts,axis=0));a=np.array([unit(np.cross(q,[0,1,0] if abs(q[1])<.9 else [0,0,1])) for q in t]);b=unit(np.cross(t,a));p=[];uv=[];idx=[]
 for j,c in enumerate(pts):
  rr=r[j] if np.ndim(r) else r
  for i in range(sides+1):angle=i/sides*PI*2;p.append(c+rr*(math.cos(angle)*a[j]+math.sin(angle)*b[j]));uv.append([j/max(1,len(pts)-1)*2,i/sides])
 for j in range(len(pts)-1):
  for i in range(sides):n=j*(sides+1)+i;idx.extend([[n,n+1,n+sides+2],[n,n+sides+2,n+sides+1]])
 return np.array(p),np.array(uv),np.array(idx)
def beam(a,b,r=.05):return tube(np.linspace(a,b,8),r,12)
def box(c,sz,r=.025):
 c=np.array(c);half=np.array(sz)/2;p=[];uv=[];idx=[];inner=np.maximum(.001,half-r)
 for axis in range(3):
  for sign in [-1,1]:
   others=[i for i in range(3) if i!=axis]
   def fn(u,v):
    q=np.zeros(3);q[axis]=sign*half[axis];q[others[0]]=(u*2-1)*half[others[0]];q[others[1]]=(v*2-1)*half[others[1]];cl=np.clip(q,-inner,inner);return c+cl+unit(q-cl)*r
   pp,vv,ii=surface(fn,6,6)
   normal=np.cross(pp[ii[0,1]]-pp[ii[0,0]],pp[ii[0,2]]-pp[ii[0,0]])
   if normal[axis]*sign<0:ii=ii[:,::-1]
   idx.extend(ii+len(p));p.extend(pp);uv.extend(vv)
 return np.array(p),np.array(uv),np.array(idx)
def lathe(c,profile,n=48):
 pts=np.array(profile);p=[];uv=[];idx=[]
 for j,(r,y) in enumerate(pts):
  for i in range(n+1):a=i/n*PI*2;p.append(np.array(c)+[r*math.cos(a),y,r*math.sin(a)]);uv.append([i/n*2,j/(len(pts)-1)])
 for j in range(len(pts)-1):
  for i in range(n):k=j*(n+1)+i;idx.extend([[k,k+1,k+n+2],[k,k+n+2,k+n+1]])
 return np.array(p),np.array(uv),np.array(idx)
def move(g,c):return g[0]+c,g[1],g[2]
def rotate(g,axis,a):
 from math import sin,cos
 k=unit(axis);p=g[0];p=p*cos(a)+np.cross(k,p)*sin(a)+np.outer(p@k,k)*(1-cos(a));return p,g[1],g[2]
def torus(c,r,minor=.025,axis='y'):
 pts=[]
 for a in np.linspace(0,2*PI,65):pts.append(np.array(c)+([r*math.cos(a),0,r*math.sin(a)] if axis=='y' else [r*math.cos(a),r*math.sin(a),0]))
 return tube(pts,minor,8)
def materials(m):
 return {'wood':m.material('Weathered oak',(.94,.82,.64),'wood'),'dark':m.material('Dark cut wood',(.47,.36,.24),'wood'),'cloth':m.material('Woven natural fiber',(.88,.76,.51),'cloth'),'red':m.material('Crimson canvas',(.66,.10,.07),'cloth'),'blue':m.material('Ocean-blue canvas',(.06,.41,.48),'cloth'),'metal':m.material('Forged steel',(.72,.80,.81),'metal',.78,.63),'brass':m.material('Brass fittings',(.61,.36,.12),'metal',.72,.7),'leaf':m.material('Living leaves',(1,1,1),'leaf'),'soil':m.material('Rich soil',(1,1,1),'soil'),'stone':m.material('Weathered stone',(.72,.74,.71),'stone'),'orange':m.material('Warm terracotta',(.65,.25,.09),rough=.8),'gold':m.material('Golden grain',(.62,.36,.07),rough=.65),'fire':m.material('Fire glow',(1,.19,.015),glow=[1,.22,.015]),'light':m.material('Warm lantern',(1,.56,.12),glow=[.7,.25,.025])}
def pedestal(m,ma,sx=4.8,sz=3.4):
 m.add(box([0,.13,0],[sx,.26,sz],.12),ma['dark'],name='Carved wooden base');m.add(box([0,.28,0],[sx-.08,.08,sz-.08],.035),ma['wood'])
 for x in [-sx/2+.13,sx/2-.13]:
  for z in [-sz/2+.13,sz/2-.13]:m.add(sphere([x,.33,z],[.033,.014,.033],12,8),ma['brass'])
def pot(m,ma,c,r=.22):
 m.add(lathe(c,[(r*.65,0),(r,.36),(r*1.06,.4),(r*1.06,.45),(r*.9,.45),(r*.85,.38),(r*.55,.08),(0,.08)]),ma['orange'],name='Hollow terracotta pots')
def leafmesh(length=.5,width=.15,angle=0):
 def f(u,v):
  w=(v*2-1)*width*(math.sin(u*PI)**.7);h=length*.7*math.sin(u*PI*.85)-.05*u
  return [length*u*math.cos(angle)-w*math.sin(angle),h+.035*math.cos(v*PI*2)*math.sin(u*PI),length*u*math.sin(angle)+w*math.cos(angle)]
 return surface(f,14,8)
TS=np.linspace(0,8,65)
def farming():
 m=Model('farming');ma=materials(m);pedestal(m,ma,5,3.8)
 for x in [-1.42,-.42,.58]:
  m.add(box([x,.48,-.1],[.85,.23,2.65],.08),ma['soil'],name='Cultivated rows')
  for z in [-1.25,1.25]:m.add(box([x,.48,z],[.94,.20,.06]),ma['wood'])
  crop=m.node('Breeze in crop row',translation=[x,.53,0])
  for z in [-.85,-.22,.42,.99]:
   for j in range(7):m.add(move(leafmesh(.43,.13,j/7*2*PI),[0,0,z]),ma['leaf'],crop,'Sculpted leafy crops')
   m.add(sphere([0,.13,z],[.12,.12,.12],16,10),ma['leaf'],crop)
  m.channel(crop,'rotation',[quat([0,0,1],.035*math.sin(t*PI/2+x)) for t in TS])
 for z in [-1.45,1.45]:m.add(box([-.45,.52,z],[3.9,.27,.12]),ma['wood'],name='Garden timber edging')
 for x in [-2.35,1.4]:m.add(box([x,.52,0],[.13,.27,2.98]),ma['wood'])
 pivot=m.node('Hoe tilling cycle',translation=[1.6,2.2,.0])
 m.add(beam([0,-1.37,0],[0,.37,0],.042),ma['wood'],pivot,'Oak hoe handle');m.add(box([0,-1.4,.20],[.42,.075,.43],.025),ma['metal'],pivot,'Forged hoe blade');m.add(torus([0,-1.32,0],.06,.02),ma['brass'],pivot)
 m.channel(pivot,'rotation',[quat([1,0,.25],-.36+.43*math.cos(t*PI)) for t in TS])
 for k in range(9):
  n=m.node('Tilled soil',translation=[1.5,.7,.3]);m.add(sphere([0,0,0],[.034,.027,.04],8,6),ma['soil'],n)
  m.channel(n,'translation',[[1.5+(k-4)*.043,.55+.25*max(0,math.sin(t*PI+k*.11)),.15+.1*math.sin(t*PI+k)] for t in TS])
 pot(m,ma,[1.85,.33,1.25],.26);pot(m,ma,[1.95,.33,.55],.2)
 c=[1.95,.34,-1.25];m.add(lathe(c,[(.22,0),(.28,.39),(.27,.46),(.22,.46),(.22,.12),(0,.12)]),ma['blue'],name='Garden watering pail');m.add(tube([[c[0]+.25*math.cos(a),c[1]+.52+.27*math.sin(a),c[2]] for a in np.linspace(0,PI,25)],.023),ma['metal']);m.add(beam([1.76,.55,-1.25],[1.35,.87,-1.3],.045),ma['metal'])
 for z in [-1.65,1.65]:
  for x in [-2.2,2.2]:m.add(box([x,.58,z],[.14,.5,.14]),ma['wood'])
 return m.finish()
def combat():
 m=Model('combat');ma=materials(m);pedestal(m,ma,4.8,3.5)
 m.add(beam([.65,.34,-.22],[.65,3.65,-.22],.11),ma['wood']);m.add(beam([-.35,3.45,-.22],[1.65,3.45,-.22],.07),ma['wood']);m.add(beam([.65,.45,-.22],[1.6,.34,-.8],.065),ma['dark']);m.add(beam([.65,.45,-.22],[-.3,.34,-.8],.065),ma['dark'])
 target=m.node('Shield recoil',translation=[.65,2.00,.15])
 disc=rotate(lathe([0,0,0],[(0,0),(.34,.025),(.78,.05),(.88,.10),(.9,.16),(.84,.22),(.4,.27),(0,.29)]),[1,0,0],PI/2)
 m.add(disc,ma['wood'],target,'Curved round shield')
 for x in [-.64,-.32,0,.32,.64]:
  height=math.sqrt(max(0,.80**2-x*x));m.add(beam([x,-height,-.275],[x,height,-.275],.009),ma['dark'],target)
 m.add(torus([0,0,-.16],.89,.055,'z'),ma['metal'],target,'Forged shield rim');m.add(sphere([0,0,-.3],[.24,.24,.10]),ma['brass'],target)
 for a in np.linspace(0,2*PI,18,endpoint=False):m.add(sphere([.8*math.cos(a),.8*math.sin(a),-.26],[.029,.029,.025],10,6),ma['brass'],target)
 for x in [-.43,.43]:m.add(beam([x,.71,0],[x,1.45,-.35],.022),ma['cloth'],target,'Suspension rope')
 m.channel(target,'rotation',[quat([1,.15,0],.035+.15*max(0,math.sin(t*PI))*math.exp(-((t%2)-.6)**2*4)) for t in TS])
 spear=m.node('Spear thrust',translation=[-1.1,1.35,1.12])
 m.add(beam([-1.30,0,0],[1.22,0,0],.043),ma['wood'],spear,'Spear shaft')
 blade=rotate(lathe([0,0,0],[(.045,0),(.16,.14),(.115,.42),(0,.85)],n=12),[0,0,1],-PI/2);m.add(move(blade,[1.20,0,0]),ma['metal'],spear,'Leaf-shaped spear blade')
 for x in np.linspace(-.65,-.12,12):m.add(rotate(torus([0,0,0],.053,.011),[0,0,1],PI/2),ma['cloth'],m.node('Grip wrap',spear,translation=[float(x),0,0]))
 m.channel(spear,'translation',[[-1.15+.52*max(0,math.sin(t*PI))**3,1.35+.19*max(0,math.sin(t*PI))**3,1.12-.68*max(0,math.sin(t*PI))**3] for t in TS]);m.channel(spear,'rotation',[quat([0,1,0],.3+.19*math.sin(t*PI)) for t in TS])
 m.add(sphere([-1.3,.64,-.9],[.60,.28,.31],24,16),ma['cloth'],name='Bound practice bundle')
 for x in [-1.7,-.9]:m.add(torus([x,.64,-.9],.27,.021,'z'),ma['dark'])
 return m.finish()
def crafting():
 m=Model('crafting');ma=materials(m);pedestal(m,ma,4.8,3.6)
 for x in [-1.55,1.55]:
  for z in [-.7,.7]:m.add(box([x,.86,z],[.23,1.2,.25],.035),ma['dark'],name='Workbench oak frame')
 for z in [-.7,.7]:m.add(beam([-1.55,.65,z],[1.55,.65,z],.08),ma['wood'])
 for z in np.linspace(-.86,.86,7):m.add(box([0,1.53,z],[3.7,.22,.24],.035),ma['wood'],name='Individual bench planks')
 m.add(box([0,1.80,-.1],[.78,.3,.52],.09),ma['metal'],name='Forged anvil body');m.add(box([0,2.00,-.1],[1.08,.17,.65],.035),ma['metal']);m.add(move(rotate(lathe([0,0,0],[(.20,0),(.18,.25),(.10,.5),(0,.8)],24),[0,0,1],-PI/2),[.45,1.97,-.1]),ma['metal'],name='Anvil horn');m.add(box([-.15,2.12,-.08],[.54,.035,.1],.015),ma['fire'],name='Warm worked iron')
 hammer=m.node('Hammer working cycle',translation=[-.58,2.75,.04]);m.add(beam([0,-.63,0],[0,.45,0],.045),ma['wood'],hammer,'Hammer handle');m.add(box([0,-.64,0],[.43,.24,.28],.055),ma['metal'],hammer,'Hammer head')
 m.channel(hammer,'rotation',[quat([0,0,1],-.12+.65*(.5+.5*math.cos(t*PI*1.5))) for t in TS]);m.channel(hammer,'translation',[[-.58,2.78+.12*(.5+.5*math.cos(t*PI*1.5)),.04] for t in TS])
 for i in range(3):m.add(box([1.3,1.69+i*.06,-.35+i*.14],[.65,.05,.13],.018),ma['metal'],name='Iron billets')
 m.add(beam([-.95,1.70,.62],[.8,1.70,.62],.035),ma['wood']);m.add(box([.75,1.74,.60],[.16,.1,.39],.028),ma['metal'])
 for x in [-1.67,1.67]:
  for z in [-.78,.78]:m.add(sphere([x,1.65,z],[.04,.016,.04],12,8),ma['brass'])
 pot(m,ma,[-1.35,1.65,-.5],.2)
 m.add(tube([[1.2+(.13+.01*a)*math.cos(a),1.68,.45+(.13+.01*a)*math.sin(a)] for a in np.linspace(0,PI*7,150)],.019),ma['cloth'],name='Coiled binding rope');m.add(box([0,1.22,.80],[1.30,.27,.07]),ma['blue']);m.add(beam([-.2,1.22,.88],[.2,1.22,.88],.025),ma['brass'])
 return m.finish()
def settlement():
 m=Model('settlement');ma=materials(m);pedestal(m,ma,5.2,4.1)
 for x in [-1.4,1.4]:
  for z in [-.95,.95]:m.add(beam([x,.3,z],[x,2.5,z],.085),ma['dark'],name='Timber uprights')
 for x in np.linspace(-1.5,1.5,13):m.add(box([x,.72,0],[.22,.13,2.1],.018),ma['wood'],name='Stilt floorboards')
 for z in [-1.02]:
  for x in np.linspace(-1.34,1.34,17):m.add(box([x,1.55,z],[.145,1.6,.08],.015),ma['wood'],name='Wall slats')
 for x in [-1.45,1.45]:
  for z in np.linspace(-.9,.9,12):
   if -.36<z<.36:continue
   m.add(box([x,1.55,z],[.08,1.6,.145],.015),ma['wood'])
 for x in [-1.45,1.45]:m.add(box([x,1.65,0],[.1,.12,.75]),ma['dark']);m.add(box([x,1.30,0],[.1,.12,.75]),ma['dark'])
 for x in np.linspace(-1.35,1.35,18):
  if -.44<x<.44:continue
  m.add(box([x,1.53,1.00],[.14,1.56,.08],.015),ma['wood'])
 door=m.node('Door in the sea breeze',translation=[-.43,.75,1.06]);m.add(box([.39,.71,0],[.76,1.40,.07],.025),ma['blue'],door,'Woven blue door');m.add(sphere([.65,.7,.06],[.035,.035,.03],12,8),ma['brass'],door);m.channel(door,'rotation',[quat([0,1,0],-.24-.08*math.sin(t*PI/4)) for t in TS])
 for z in [-1.2,1.2]:m.add(beam([-1.6,2.43,z],[0,3.39,z],.07),ma['dark']);m.add(beam([0,3.39,z],[1.6,2.43,z],.07),ma['dark'])
 m.add(beam([0,3.39,-1.35],[0,3.39,1.35],.08),ma['dark'])
 for side in [-1,1]:
  for z in np.linspace(-1.30,1.30,54):
   pts=[[side*x,3.40-.64*x-.035*math.sin(x*4),z+.007*math.sin(x*8+z)] for x in np.linspace(0,1.72,18)]
   m.add(tube(pts,.035,7),ma['cloth'] if int(z*90)%3 else ma['gold'],name='Individual overlapping thatch')
 for x in [.55,1.05,1.55]:
  for s in [-1,1]:m.add(beam([x*s,3.41-.64*x,-1.34],[x*s,3.41-.64*x,1.34],.022),ma['dark'])
 for i in range(3):m.add(box([0,.36+i*.14,1.66-i*.18],[1.05,.12,.30]),ma['wood'],name='Porch steps')
 for j in range(8):
  n=m.node('Cloth banner',translation=[1.48,2.35,.45+j*.07]);m.add(surface(lambda u,v:[.015*math.sin(v*4),-.76*u,.075*v],3,10),ma['blue'],n,'Hanging blue canvas');m.channel(n,'rotation',[quat([0,0,1],.09*math.sin(t*PI/2+j*.3)) for t in TS])
 for a in np.linspace(0,PI*2,10,endpoint=False):m.add(sphere([-1.85+.32*math.cos(a),.40,1.36+.32*math.sin(a)],[.11,.08,.10],12,8),ma['stone'],name='Stone fire ring')
 for a in [0,PI/3,-PI/3]:m.add(move(rotate(beam([-.31,0,0],[.31,0,0],.06),[0,1,0],a),[-1.85,.40,1.36]),ma['dark'])
 for j in range(4):
  f=m.node('Fire flicker',translation=[-1.85+.06*math.cos(j),.45,1.36+.06*math.sin(j)]);m.add(sphere([0,.13,0],[.07,.20,.07],12,8),ma['light'] if j%2 else ma['fire'],f);m.channel(f,'scale',[[1,.65+.5*math.sin(t*PI*2+j)**2,1] for t in TS])
 for x,z in [(2,.3),(1.95,-.55)]:
  m.add(box([x,.62,z],[.55,.56,.55],.025),ma['wood'])
  for yy in [.43,.80]:m.add(box([x,yy,z+.29],[.58,.07,.05],.01),ma['dark'])
 return m.finish()
if __name__=='__main__':
 stats=[f() for f in [farming,combat,crafting,settlement]]
 (OUT/'manifest.json').write_text(json.dumps({'license':'Original OceanBond web concept models','note':'Animated object studies, not Unity gameplay.','models':stats},indent=2))
 print(json.dumps(stats,indent=2))
