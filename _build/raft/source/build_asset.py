"""OceanBond red-sail outrigger: original textured glTF 2.0 mesh + baked clips.
No game assets, remote downloads, or external model dependencies.
"""
from pathlib import Path
import io, json, struct, math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy.ndimage import gaussian_filter
from scipy.spatial import cKDTree
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'site/assets'; OUT.mkdir(parents=True, exist_ok=True)
TEX=ROOT/'source/textures'; TEX.mkdir(exist_ok=True)
rng=np.random.default_rng(83)
PI=np.pi

def noise(w,h,gx,gy):
 a=(rng.random((gy,gx))*255).astype('uint8')
 return np.array(Image.fromarray(a).resize((w,h),Image.Resampling.BICUBIC),dtype=np.float32)/255

def normal_map(height,amount=3):
 dy,dx=np.gradient(height)
 n=np.stack((-dx*amount,-dy*amount,np.ones_like(dx)),axis=-1)
 n/=np.linalg.norm(n,axis=-1,keepdims=True)
 return Image.fromarray(np.uint8(np.clip(n*.5+.5,0,1)*255))

def png(im):
 f=io.BytesIO();im.save(f,format='PNG',optimize=True);return f.getvalue()

def texset(name,base,height,roughness,amount):
 base.save(TEX/(name+'-color.png'))
 normal=normal_map(height,amount);normal.save(TEX/(name+'-normal.png'))
 r=np.uint8(np.clip(roughness,0,1)*255)
 orm=Image.fromarray(np.dstack([np.full_like(r,255),r,np.zeros_like(r)]))
 orm.save(TEX/(name+'-roughness.png'))
 f=io.BytesIO();base.save(f,format='JPEG',quality=93,subsampling=0)
 return f.getvalue(),png(normal.resize((512,512),Image.Resampling.LANCZOS)),png(orm.resize((512,512),Image.Resampling.LANCZOS))

# Worn longitudinal wood grain, knots and fibers, all authored here.
w=h=1024;yy,xx=np.mgrid[0:h,0:w].astype(np.float32);u=xx/w;v=yy/h
large=noise(w,h,8,12);grain=noise(w,h,18,340);fine=noise(w,h,100,1024)
warp=.008*np.sin(u*19+v*7)+.012*np.sin(u*5+v*17)
for ku,kv in [(0.23,.31),(.74,.73),(.52,.91)]:
 d=((u-ku)/.13)**2+((v-kv)/.032)**2
 warp+=.023*np.exp(-d)*np.sin((u-ku)*9)
fibers=np.sin((v+warp)*PI*420 + 2.6*large)*.5+.5
height=.40*grain+.1*fine+.30*fibers+.2*large
value=.52+.22*large+.13*grain+.035*fine-.07*(fibers>.9)
color=np.dstack([146*value+44,91*value+22,48*value+14])
for ku,kv in [(0.23,.31),(.74,.73),(.52,.91)]:
 d=np.sqrt(((u-ku)/.055)**2+((v-kv)/.023)**2)
 knot=(1-np.clip(d/2,0,1))*.19+(np.sin(d*12)**2)*np.exp(-d)*.09
 color*=1-knot[:,:,None]
# Fine weathering at tiny split lines
for i in range(45):
 y=rng.integers(0,h);x=rng.integers(0,w-250);length=rng.integers(40,260)
 color[y:y+1,x:x+length]*=.70
wood=texset('weathered-teak',Image.fromarray(np.uint8(np.clip(color,0,255))),height,.65+.18*grain,15)
# Sail canvas with visibly stitched panels, subtle warp/weft, and a small original seam emblem.
large=noise(w,h,10,10);f=noise(w,h,900,900)
warp=np.sin(xx*PI*.8)*.5+.5;weft=np.sin(yy*PI*.8)*.5+.5
canvas=.35*warp+.35*weft+.3*f
panel=(np.floor(v*6)%2)*.025
val=.80+.13*large+.04*f+panel
arr=np.dstack([188*val+24,34*val+14,22*val+8]);img=Image.fromarray(np.uint8(np.clip(arr,0,255)))
d=ImageDraw.Draw(img)
for y in [16,180,360,540,720,900,1006]:
 d.line([(0,y),(1024,y)],fill=(113,35,26),width=8)
 d.line([(0,y+7),(1024,y+7)],fill=(219,94,57),width=3)
 for x in range(5,1024,14):d.line([(x,y+3),(x+6,y+4)],fill=(227,164,106),width=1)
# Reinforced mast-side hem and perimeter stitches.
d.rectangle((990,0,1023,1023),fill=(137,40,27));d.line([(984,0),(984,1024)],fill=(218,120,70),width=3)
for y in range(0,1024,14):d.line([(987,y),(987,y+7)],fill=(240,181,106),width=2)
# Small original nautical spiral embroidery, never an external game's logo.
cx,cy=500,485
pts=[]
for a in np.linspace(0,PI*3.8,240):
 r=9+8*a;pts.append((cx+r*np.cos(a),cy+r*np.sin(a)*.86))
d.line(pts,fill=(229,173,105),width=7,joint='curve')
d.arc((cx-105,cy-85,cx+125,cy+100),0,130,fill=(237,192,133),width=5)
sail=texset('crimson-canvas',img,canvas,.89+.04*f,7)
# Rope with tightly wound visible strands.
w2=h2=512;Y,X=np.mgrid[0:h2,0:w2].astype('f');R=.5+.5*np.sin((X/512*8+Y/512*34)*PI*2)
rr=noise(512,512,256,256);RV=.62+.2*R+.12*rr
rope=texset('hemp',Image.fromarray(np.uint8(np.dstack([185*RV+35,147*RV+24,96*RV+15]))),R*.65+rr*.35,.95+rr*.04,7)

class GLB:
 def __init__(self):
  self.doc={'asset':{'version':'2.0','generator':'MTH Labs / original Red Sail asset builder','copyright':'Original OceanBond concept asset created for Mustafa Thaeer'},'scene':0,'scenes':[{'name':'OceanBond_Red_Sail','nodes':[0]}],'nodes':[{'name':'OceanBond_Red_Sail','children':[],'translation':[0,0,0],'rotation':[0,0,0,1]}],'meshes':[],'materials':[],'textures':[],'images':[],'samplers':[{'magFilter':9729,'minFilter':9987,'wrapS':10497,'wrapT':10497}],'accessors':[],'bufferViews':[],'animations':[]}
  self.bin=bytearray();self.batches={};self.tris=0
 def buf(self,b,target=None):
  while len(self.bin)%4:self.bin.append(0)
  i=len(self.doc['bufferViews']);view={'buffer':0,'byteOffset':len(self.bin),'byteLength':len(b)}
  if target:view['target']=target
  self.doc['bufferViews'].append(view);self.bin.extend(b);return i
 def acc(self,a,typ,target=None):
  a=np.asarray(a);component=5126
  if a.dtype==np.uint32:component=5125
  else:a=a.astype('<f4')
  i=len(self.doc['accessors']);flat=a.reshape(-1, {'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[typ])
  d={'bufferView':self.buf(a.tobytes(),target),'componentType':component,'count':len(flat),'type':typ}
  if len(flat):d.update({'min':flat.min(axis=0).astype(float).tolist(),'max':flat.max(axis=0).astype(float).tolist()})
  self.doc['accessors'].append(d);return i
 def textures(self,imgs,name):
  ids=[]
  for i,b in enumerate(imgs):
   ix=len(self.doc['images']);self.doc['images'].append({'bufferView':self.buf(b),'mimeType':('image/jpeg' if b[:2]==b'\xff\xd8' else 'image/png'),'name':name+str(i)})
   ids.append(len(self.doc['textures']));self.doc['textures'].append({'sampler':0,'source':ix})
  return ids
 def mat(self,name,col,tex=None,rough=.65,metal=0):
  p={'baseColorFactor':[*col,1],'metallicFactor':metal,'roughnessFactor':rough};d={'name':name,'pbrMetallicRoughness':p,'doubleSided':True}
  if tex:
   p['baseColorTexture']={'index':tex[0]};p['metallicRoughnessTexture']={'index':tex[2]};p['roughnessFactor']=1
   d['normalTexture']={'index':tex[1],'scale':(.12 if 'canvas' in name else .22)}
  i=len(self.doc['materials']);self.doc['materials'].append(d);return i
 def node(self,name,parent=0,**kw):
  i=len(self.doc['nodes']);self.doc['nodes'].append({'name':name,**kw});self.doc['nodes'][parent].setdefault('children',[]).append(i);return i
 def mesh(self,name,pos,uv,idx,mat,parent=0,morph=None):
  pos=np.array(pos,dtype='f4');uv=np.array(uv,dtype='f4');idx=np.array(idx,dtype='uint32').reshape(-1,3)
  n=normals(pos,idx)
  prim={'attributes':{'POSITION':self.acc(pos,'VEC3',34962),'NORMAL':self.acc(n,'VEC3',34962),'TEXCOORD_0':self.acc(uv,'VEC2',34962)},'indices':self.acc(idx.flatten(),'SCALAR',34963),'material':mat}
  mesh={'name':name,'primitives':[prim]}
  if morph:
   prim['targets']=[]
   for target in morph:
    target=np.array(target,dtype='f4');mn=normals(pos+target,idx)-n
    prim['targets'].append({'POSITION':self.acc(target,'VEC3',34962),'NORMAL':self.acc(mn,'VEC3',34962)})
   mesh['weights']=[0]*len(morph);mesh['extras']={'targetNames':['Gust_A','Gust_B'][:len(morph)]}
  mi=len(self.doc['meshes']);self.doc['meshes'].append(mesh);self.tris+=len(idx)
  ni=self.node(name,parent,mesh=mi)
  if morph:self.doc['nodes'][ni]['weights']=[0]*len(morph)
  return ni
 def batch(self,name,p,uv,idx,mat):
  if mat not in self.batches:self.batches[mat]={'name':name,'p':[],'uv':[],'idx':[]}
  b=self.batches[mat];off=len(b['p']);b['p'].extend(p);b['uv'].extend(uv);b['idx'].extend(np.array(idx)+off)
 def finish(self):
  for mat,b in self.batches.items():self.mesh(b['name'],b['p'],b['uv'],b['idx'],mat)
  while len(self.bin)%4:self.bin.append(0)
  self.doc['buffers']=[{'byteLength':len(self.bin)}]
  j=json.dumps(self.doc,separators=(',',':')).encode();j+=b' '*((-len(j))%4)
  b=bytes(self.bin);out=struct.pack('<III',0x46546c67,2,12+8+len(j)+8+len(b))+struct.pack('<II',len(j),0x4e4f534a)+j+struct.pack('<II',len(b),0x004e4942)+b
  (OUT/'red-sail-raft.glb').write_bytes(out)
  stats={'meshPrimitives':len(self.doc['meshes']),'triangles':self.tris,'textureImages':len(self.doc['images']),'materials':len(self.doc['materials']),'bytes':len(out),'animations':[{'name':a['name'],'channels':len(a['channels'])} for a in self.doc['animations']]}
  (ROOT/'tests/asset-stats.json').write_text(json.dumps(stats,indent=2));print(json.dumps(stats,indent=2))

def unit(x):
 x=np.array(x,dtype=float);l=np.linalg.norm(x,axis=-1,keepdims=True);return x/np.maximum(l,1e-10)
def normals(p,tri):
 face=np.cross(p[tri[:,1]]-p[tri[:,0]],p[tri[:,2]]-p[tri[:,0]])
 n=np.zeros_like(p)
 for i in range(3):np.add.at(n,tri[:,i],face)
 bad=np.linalg.norm(n,axis=1)<1e-9
 if bad.any() and (~bad).any():
  near=cKDTree(p[~bad]).query(p[bad])[1];n[bad]=n[~bad][near]
 return unit(n).astype('f4')
def gridmesh(func,nu,nv):
 p=[];uv=[];tri=[]
 for j in range(nv+1):
  for i in range(nu+1):
   p.append(func(i/nu,j/nv));uv.append([i/nu,j/nv])
 for j in range(nv):
  for i in range(nu):
   a=j*(nu+1)+i;tri.extend([[a,a+1,a+nu+2],[a,a+nu+2,a+nu+1]])
 return np.array(p),np.array(uv),np.array(tri)
def tube(points,rad=.02,n=8,repeat=2):
 pts=np.array(points,dtype=float);tang=unit(np.gradient(pts,axis=0));ref=np.array([0,1,0]);x=[]
 for t in tang:
  r=ref if abs(t[1])<.93 else [0,0,1];x.append(unit(np.cross(t,r)))
 x=np.array(x);z=unit(np.cross(tang,x));p=[];uv=[];tri=[]
 lens=np.concatenate([[0],np.cumsum(np.linalg.norm(np.diff(pts,axis=0),axis=1))]);total=max(lens[-1],.01)
 for j,pt in enumerate(pts):
  rr=rad[j] if np.ndim(rad) else rad
  for i in range(n+1):
   a=i/n*PI*2;p.append(pt+rr*(np.cos(a)*x[j]+np.sin(a)*z[j]));uv.append([lens[j]*repeat,i/n])
 for j in range(len(pts)-1):
  for i in range(n):
   a=j*(n+1)+i;tri.extend([[a,a+1,a+n+2],[a,a+n+2,a+n+1]])
 return np.array(p),np.array(uv),np.array(tri)
def batchtube(points,rad,mat,n=8,name='Details',repeat=2):
 p,uv,idx=tube(points,rad,n,repeat);G.batch(name,p,uv,idx,mat)
def beam(a,b,r,mat,n=12):
 a=np.array(a);b=np.array(b);ts=np.linspace(0,1,10);pts=[a+(b-a)*t+np.array([0,.007*np.sin(t*PI),0]) for t in ts];batchtube(pts,r,mat,n,repeat=1.3,name='Timber_Structure')
def orb(c,s,mat,nu=12,nv=8):
 p,uv,idx=gridmesh(lambda u,v:np.array(c)+np.array(s)*[np.sin(v*PI)*np.cos(u*PI*2),np.cos(v*PI),np.sin(v*PI)*np.sin(u*PI*2)],nu,nv)
 G.batch('Metal_Fittings',p,uv,idx,mat)
def rounded_plank(c,sz,mat,ang=0):
 # Capsule-shaped flattened beam with variable oval end caps.
 a=np.linspace(-1,1,24);p=[]
 # Elongated capsule oriented x, fine contour variation; y/z scaled oval.
 for t in a:
  for j in range(17):
   r=math.sqrt(max(.001,1-max(0,(abs(t)-.9)/.1)**2));th=j/16*PI*2
   q=np.array([t*sz[0]/2,sz[1]/2*np.cos(th)*r,sz[2]/2*np.sin(th)*r])
   xx=q[0]*np.cos(ang)-q[2]*np.sin(ang);zz=q[0]*np.sin(ang)+q[2]*np.cos(ang)
   p.append(np.array(c)+[xx,q[1],zz])
 uv=[[i/23*2,j/16] for i in range(24) for j in range(17)];ids=[]
 for i in range(23):
  for j in range(16):
   k=i*17+j;ids.extend([[k,k+17,k+18],[k,k+18,k+1]])
 G.batch('Deck_Planks',p,uv,ids,mat)

G=GLB();W=G.textures(wood,'teak');S=G.textures(sail,'canvas');R=G.textures(rope,'hemp')
MAT={
 'hull':G.mat('Warm worn teak / hull',(.90,.80,.65),W),
 'deck':G.mat('Sun-bleached teak / deck',(.98,.94,.84),W),
 'rim':G.mat('Carved walnut / gunwale',(.55,.42,.28),W),
 'spar':G.mat('Oiled bamboo / spars',(.82,.64,.38),W),
 'rope':G.mat('Twisted natural hemp',(.91,.87,.73),R),
 'sail':G.mat('Stitched crimson woven canvas',(1,1,1),S),
 'bronze':G.mat('Weathered bronze pins',(.49,.29,.11),rough=.33,metal=.76),
 'inlay':G.mat('Faded turquoise inlay',(.065,.37,.39),rough=.78),
 'dark':G.mat('Dark lashings',(.10,.075,.048),R),
 'red':G.mat('Sail binding',(.42,.035,.02),rough=.86)
}
# Hollow hand-shaped canoe hulls: distinct inner and outer skins, upward-curving tips.
for cx in [-1.72,1.72]:
 def hull(t,theta,inside=False):
  a=2*t-1;z=a*3.85;tip=abs(a)
  width=.575*(max(0,np.sin(PI*t))**.56)+.018
  top=.64+.65*tip**3+.24*max(0,-a)**7
  dep=.70*(1-.62*tip**4)
  if inside:width=max(.015,width-.073);dep=max(.04,dep-.115)
  return np.array([cx+width*np.cos(theta),top-dep*np.sin(theta),z])
 for inside,mat in [(False,MAT['hull']),(True,MAT['deck'])]:
  p,uv,idx=gridmesh(lambda u,v:hull(u,v*PI,inside),96,24)
  if inside:idx=idx[:,::-1]
  uv[:,0]*=2.5;uv[:,1]*=1.0
  G.batch('Hollow_Carved_Hulls',p,uv,idx,mat)
 # Carved rims follow the real canoe contour.
 for theta in [0,PI]:
  pts=[hull(t,theta)+[0,.012,0] for t in np.linspace(.005,.995,100)]
  batchtube(pts,.06,MAT['rim'],12,'Carved_Gunwales')
  # Thin turquoise line and bronze stitch accent run around both sides.
  pts2=[hull(t,theta+.10 if theta==0 else theta-.10)+[0,-.075,0] for t in np.linspace(.015,.985,90)]
  batchtube(pts2,.015,MAT['inlay'],6,'Turquoise_Inlay')
 # Five interior ribs and wooden seats, slim real curved lengths.
 for t in [.18,.31,.46,.62,.79]:
  pts=[hull(t,a,True)+[0,.015,0] for a in np.linspace(0,PI,30)]
  batchtube(pts,.028,MAT['rim'],8,'Canoe_Ribs')
 for z in [-2.55,2.4]:
  rounded_plank([cx,.68,z],[.83,.10,.24],MAT['deck'])
 # Gunwale pin heads and visible lashing holes.
 for z in np.linspace(-2.95,2.95,15):
  for s in [-1,1]:
   pos=hull((z/3.85+1)/2,0 if s>0 else PI)
   orb(pos+[0,.042,0],[.028,.016,.028],MAT['bronze'],8,6)
# Curved cross beams, four with longitudinal grain.
for z in [-1.65,1.65]:
 pts=[[x,.88+.12*(1-(x/2.55)**2),z+.04*np.sin(x)] for x in np.linspace(-2.6,2.6,70)]
 batchtube(pts,.105,MAT['spar'],16,'Curved_Cross_Beams',.9)
# Walking deck: individually worn, rounded slats.
for j,z in enumerate(np.linspace(-1.68,1.68,21)):
 rounded_plank([-.02,.985+float(rng.uniform(-.012,.012)),z],[2.8+float(rng.uniform(-.08,.08)),.11,.137],MAT['deck'],float(rng.uniform(-.008,.008)))
# Real twisted lashings round each beam joint.
for x in [-1.72,1.72]:
 for z in [-1.65,1.65]:
  for strand in range(3):
   pts=[]
   for t in np.linspace(0,1,340):
    a=t*PI*2*8;f=t*PI*2*48+strand*PI*2/3
    pts.append([x+(t-.5)*.42,.90+(.127+.012*np.cos(f))*np.cos(a),z+(.127+.012*np.cos(f))*np.sin(a)+.012*np.sin(f)])
   batchtube(pts,.0105,MAT['rope'],5,'Twisted_Lashings')
# Two deck toe rails and small fixtures.
for x in [-1.36,1.36]:beam([x,1.08,-1.7],[x,1.08,1.7],.047,MAT['rim'])
# Coiled spare mooring rope on the deck.
pts=[]
for t in np.linspace(0,1,650):
 a=t*PI*2*6;rad=.13+t*.38;pts.append([.73+rad*np.cos(a),1.08+.015*np.sin(a*2),.83+rad*np.sin(a)])
batchtube(pts,.028,MAT['rope'],8,'Spare_Rope_Coil')
# Rope tail to cleat.
batchtube([[1.16,1.08,.88],[1.29,1.05,1.1],[1.2,1.07,1.3],[1.36,1.07,1.55],[1.61,.97,1.69]],.025,MAT['rope'],8,'Spare_Rope_Coil')
# Mast foot socket, bronze bands and tapered spar.
beam([.25,.97,-.17],[.25,1.27,-.17],.17,MAT['rim'],16)
pts=[[.25-.16*t,1.08+5.58*t,-.17+.10*t] for t in np.linspace(0,1,64)]
batchtube(pts,np.linspace(.095,.046,64),MAT['spar'],18,'Main_Mast',1.1)
for y in [1.23,1.40,2.0,3.0,4.0,5.0,6.3]:
 cx=.25-.16*((y-1.08)/5.58);cz=-.17+.1*((y-1.08)/5.58)
 batchtube([[cx+.101*np.cos(a),y,cz+.101*np.sin(a)] for a in np.linspace(0,PI*2,33)],.018,MAT['rope'],8,'Mast_Bindings')
# Standing rigging with sag, correctly attached to mast and structure.
def cable(a,b,sag=.05):
 a=np.array(a);b=np.array(b)
 return [a+(b-a)*t+[0,-sag*np.sin(PI*t),0] for t in np.linspace(0,1,55)]
for dest in [[1.7,1.02,-1.65],[1.7,1.02,1.65]]:
 batchtube(cable([.095,6.48,-.07],dest,.08),.017,MAT['rope'],7,'Standing_Rigging')
# Main sail, with actual continuous shape and multiple morph deformations.
rig=G.node('Sail_Rig',translation=[0,0,0],rotation=[0,0,0,1])
def sailpoint(u,v):
 width=2.82+.62*np.sin(PI*v)-1.46*v**3
 x=.28-.16*v-width*(1-u)
 y=1.65+4.83*v+.24*(1-u)*(1-v)-.08*(1-u)*v
 z=-.13+.1*v+.42*np.sin(PI*u)*np.sin(PI*v)+.060*np.sin(PI*u)*np.sin(PI*6*v)
 return np.array([x,y,z])
def displace(p,uv,which):
 u,v=uv;free=(1-u)**.72
 z=.105*free*np.sin(PI*v)*np.sin(PI*2*v+PI*u+which*PI/2)
 x=.024*free*np.sin(PI*v)*np.cos(PI*3*v+which)
 return np.array([x,.015*free*np.sin(PI*v+u*3+which),z])
p,uv,idx=gridmesh(sailpoint,38,70)
morph=[[displace(pt,tc,k) for pt,tc in zip(p,uv)] for k in range(2)]
sailnode=G.mesh('Crimson_Sail_Cloth',p,uv,idx,MAT['sail'],rig,morph)
# Rope hem and battens deform with sail; can export normals too.
def sailtrim(name,uvpath,r,mat):
 pp=np.array([sailpoint(u,v)+[0,0,.015] for u,v in uvpath]);p,uv,ids=tube(pp,r,8,1.5)
 morph=[]
 for k in range(2):
  changes=np.array([displace(pt,tc,k) for pt,tc in zip(pp,uvpath)])
  morph.append(np.repeat(changes,9,axis=0))
 return G.mesh(name,p,uv,ids,mat,rig,morph)
trimnodes=[]
for j,v in enumerate([0,.18,.36,.54,.72,.90,1]):
 trimnodes.append(sailtrim(f'Bent_Bamboo_Batten_{j}',[(u,v) for u in np.linspace(0,1,70)],.025 if j<6 else .018,MAT['spar']))
for j,path in enumerate([[(0,v) for v in np.linspace(0,1,100)],[(1,v) for v in np.linspace(0,1,100)]]):
 trimnodes.append(sailtrim('Sail_Edge_Rope_'+str(j),path,.021,MAT['rope']))
# Decorative small pennant on the mast, actual fluttering geometry.
def flagpoint(u,v):return np.array([.09-1.05*u,6.62+.12*np.sin(u*3)-.26*v*(1-u*.7),-.07+.08*np.sin(u*4)])
p,uv,idx=gridmesh(flagpoint,28,5)
fm=[]
for k in range(2):fm.append([[0,.07*u*np.sin(u*6+k),.15*u*np.sin(u*7+k*PI/2)] for u,v in uv])
flagnode=G.mesh('Wind_Pennant',p,uv,idx,MAT['sail'],rig,fm)
# An actual paddle with broad, smooth carved blade and leather grip; animated pivot.
oar=G.node('Steering_Paddle',translation=[1.50,1.52,2.25],rotation=[0,0,0,1])
p,uv,idx=tube([[0,t,0] for t in np.linspace(-2.0,1.0,50)],.040,12,2)
G.mesh('Paddle_Shaft',p,uv,idx,MAT['spar'],oar)
def blade(u,v):
 y=-1.8-1.02*v;wid=.22*(np.sin(PI*v)**.45)+.035; a=u*PI*2
 return np.array([wid*np.cos(a),y,.04*np.sin(a)*(np.sin(PI*v)*.7+.3)])
p,uv,idx=gridmesh(blade,20,32);G.mesh('Carved_Paddle_Blade',p,uv,idx,MAT['hull'],oar)
# Curved bronze edge on paddle grip.
p,uv,idx=tube([[.03*np.cos(a),.65+(a/(16*PI))*.32,.03*np.sin(a)] for a in np.linspace(0,PI*2*8,200)],.014,6,2);G.mesh('Paddle_Grip',p,uv,idx,MAT['rope'],oar)
# Functional mast base braces.
beam([.25,1.14,-.17],[.25,1.58,-.17],.13,MAT['rim'],12)
# Animation sampled as standards-compliant glTF TRS and morph channels.
def quat_euler(x,y,z):
 cx,sx=np.cos(x/2),np.sin(x/2);cy,sy=np.cos(y/2),np.sin(y/2);cz,sz=np.cos(z/2),np.sin(z/2)
 return [sx*cy*cz+cx*sy*sz,cx*sy*cz-sx*cy*sz,cx*cy*sz+sx*sy*cz,cx*cy*cz-sx*sy*sz]
times=np.linspace(0,8,97).astype('f4');tin=G.acc(times,'SCALAR');samplers=[];channels=[]
def ch(node,path,values,typ):
 ix=len(samplers);samplers.append({'input':tin,'output':G.acc(values,typ),'interpolation':'LINEAR'});channels.append({'sampler':ix,'target':{'node':node,'path':path}})
ch(0,'translation',[[.035*np.sin(t*PI/4),.075*np.sin(t*PI/2),0] for t in times],'VEC3')
ch(0,'rotation',[quat_euler(.018*np.sin(t*PI/4),.014*np.sin(t*PI/4),.025*np.sin(t*PI/2)) for t in times],'VEC4')
ch(rig,'rotation',[quat_euler(0,.018*np.sin(t*PI/2),0) for t in times],'VEC4')
for ni in [sailnode,*trimnodes,flagnode]:
 ch(ni,'weights',[[np.sin(t*PI),np.cos(t*PI*.5)] for t in times],'SCALAR')
# Paddle rests through water with a shallow rowing gesture.
ch(oar,'rotation',[quat_euler(-.18+.075*np.sin(t*PI/2),-.1,.53+.065*np.cos(t*PI/2)) for t in times],'VEC4')
G.doc['animations']=[{'name':'Wind_and_Waves_8s','samplers':samplers,'channels':channels,'extras':{'description':'Baked root drift, canvas morphs, flexing sail spars, pennant and steering paddle. Continuous loop.'}}]
G.finish()
