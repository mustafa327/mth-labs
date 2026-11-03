/* OceanBond model viewer. WebGL2 + a small glTF 2.0 reader for this asset.
   The model is loaded from the actual GLB, including textures and baked animation.
   No remote dependencies, tracking, procedural replacement model or hidden API. */
(()=>{'use strict';
const $=s=>document.querySelector(s), canvas=$('#scene');
const reduced=matchMedia('(prefers-reduced-motion: reduce)');
const query = new URLSearchParams(location.search);
const catalogue = {
 farming:{label:'Farming · The growing plot',file:'models/farming.glb',target:[0,1.0,0],az:.55,el:.58,dist:8.3,sea:false},
 combat:{label:'Combat · The training ground',file:'models/combat.glb',target:[0,1.55,0],az:2.65,el:.24,dist:8.1,sea:false},
 crafting:{label:'Crafting · The workbench',file:'models/crafting.glb',target:[0,1.4,0],az:.52,el:.42,dist:8.2,sea:false},
 settlement:{label:'Settlement · The first home',file:'models/settlement.glb',target:[0,1.65,0],az:.62,el:.31,dist:9.5,sea:false},
 sailing:{label:'Sailing · The red sail',file:'../../oceanbond-raft/assets/red-sail-raft.glb',target:[-.4,2.8,0],az:.60,el:.16,dist:15.4,sea:true}
};
const kind = Object.hasOwn(catalogue,query.get('scene')) ? query.get('scene') : 'farming';
const config = catalogue[kind];
document.title = config.label + ' | OceanBond';
$('#model-name').textContent=config.label;
$('#back').href='../../oceanbond.html#'+kind;
$('#download').href=config.file;
$('#model-file-fallback').href=config.file;
canvas.setAttribute('aria-label',config.label+'. Animated three-dimensional model. Drag or use arrow keys to rotate. Plus and minus zoom. Space pauses.');
if(!config.sea)$('#environment').hidden=true;

let gl;try{gl=canvas.getContext('webgl2',{alpha:false,antialias:true,powerPreference:'low-power'})}catch{}
function fail(s){$('#loading').hidden=true;$('#error').hidden=false;$('#error-text').textContent=s}
if(!gl){fail('This interactive model needs WebGL 2. The downloadable model remains available.');return}
const PI=Math.PI,TAU=PI*2,clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
const add=(a,b)=>a.map((v,i)=>v+b[i]),sub=(a,b)=>a.map((v,i)=>v-b[i]),dot=(a,b)=>a.reduce((s,v,i)=>s+v*b[i],0),cross=(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]],norm=a=>{let d=Math.hypot(...a)||1;return a.map(v=>v/d)};
const I=()=>new Float32Array([1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1]);
function mul(a,b){let o=new Float32Array(16);for(let c=0;c<4;c++)for(let r=0;r<4;r++)for(let k=0;k<4;k++)o[c*4+r]+=a[k*4+r]*b[c*4+k];return o}
function trs(t=[0,0,0],q=[0,0,0,1],s=[1,1,1]){const [x,y,z,w]=q,xx=x*x,yy=y*y,zz=z*z,xy=x*y,xz=x*z,yz=y*z,wx=w*x,wy=w*y,wz=w*z;return new Float32Array([(1-2*(yy+zz))*s[0],2*(xy+wz)*s[0],2*(xz-wy)*s[0],0,2*(xy-wz)*s[1],(1-2*(xx+zz))*s[1],2*(yz+wx)*s[1],0,2*(xz+wy)*s[2],2*(yz-wx)*s[2],(1-2*(xx+yy))*s[2],0,...t,1])}
function look(eye,target){const z=norm(sub(eye,target)),x=norm(cross([0,1,0],z)),y=cross(z,x);return new Float32Array([x[0],y[0],z[0],0,x[1],y[1],z[1],0,x[2],y[2],z[2],0,-dot(x,eye),-dot(y,eye),-dot(z,eye),1])}
function proj(fov,a,n,f){let t=1/Math.tan(fov/2);return new Float32Array([t/a,0,0,0,0,t,0,0,0,0,(f+n)/(n-f),-1,0,0,2*f*n/(n-f),0])}
function ortho(l,r,b,t,n,f){return new Float32Array([2/(r-l),0,0,0,0,2/(t-b),0,0,0,0,-2/(f-n),0,-(r+l)/(r-l),-(t+b)/(t-b),-(f+n)/(f-n),1])}
function program(v,f){const p=gl.createProgram();for(const [type,source]of [[gl.VERTEX_SHADER,v],[gl.FRAGMENT_SHADER,f]]){const s=gl.createShader(type);gl.shaderSource(s,source);gl.compileShader(s);if(!gl.getShaderParameter(s,gl.COMPILE_STATUS))throw Error(gl.getShaderInfoLog(s));gl.attachShader(p,s);gl.deleteShader(s)}gl.linkProgram(p);if(!gl.getProgramParameter(p,gl.LINK_STATUS))throw Error(gl.getProgramInfoLog(p));return p}
const meshVS=`#version 300 es
precision highp float;
layout(location=0)in vec3 p;layout(location=1)in vec3 n;layout(location=2)in vec2 uv;
layout(location=3)in vec3 morph0;layout(location=4)in vec3 morph1;layout(location=5)in vec3 mn0;layout(location=6)in vec3 mn1;
uniform mat4 model,vp,lightVP;uniform vec2 weights;
out vec3 world,N;out vec2 tex;out vec4 shadow;
void main(){vec3 pp=p+morph0*weights.x+morph1*weights.y;vec4 w=model*vec4(pp,1.);world=w.xyz;N=normalize(mat3(model)*(n+mn0*weights.x+mn1*weights.y));tex=uv;shadow=lightVP*w;gl_Position=vp*w;}`;
const tone=`vec3 tone(vec3 x){return clamp((x*(2.51*x+.03))/(x*(2.43*x+.59)+.14),0.,1.);}`;
const meshFS=`#version 300 es
precision highp float;in vec3 world,N;in vec2 tex;in vec4 shadow;uniform sampler2D albedoTex,normalTex,ormTex,depthTex;
uniform vec4 base;uniform vec3 eye,emissive;uniform float roughness,metalness,hasTex,normalScale,shadowSize;uniform int wire;out vec4 frag;
${tone}
float distribution(float ndh,float r){float a=r*r,a2=a*a,d=ndh*ndh*(a2-1.)+1.;return a2/(3.14159265*d*d+.0001);}
vec3 mappedNormal(){vec3 nn=normalize(N);if(!gl_FrontFacing)nn=-nn;if(hasTex<.5)return nn;vec3 q0=dFdx(world),q1=dFdy(world);vec2 st0=dFdx(tex),st1=dFdy(tex);vec3 S=normalize(q0*st1.t-q1*st0.t),T=normalize(-q0*st1.s+q1*st0.s);vec3 m=texture(normalTex,tex).xyz*2.-1.;m.xy*=normalScale;return normalize(mat3(S,T,nn)*m);}
void main(){vec3 col=base.rgb;if(hasTex>.5)col*=pow(texture(albedoTex,tex).rgb,vec3(2.2));vec3 no=mappedNormal(),V=normalize(eye-world),L=normalize(vec3(-.60,.9,.65)),H=normalize(L+V);
float r=roughness,m=metalness;if(hasTex>.5){vec3 orm=texture(ormTex,tex).rgb;r*=orm.g;m*=orm.b;}r=clamp(r,.09,1.);float nv=max(dot(no,V),.01),nl=max(dot(no,L),0.),nh=max(dot(no,H),0.),vh=max(dot(V,H),0.);
vec3 F0=mix(vec3(.04),col,m),F=F0+(1.-F0)*pow(1.-vh,5.);float k=(r+1.)*(r+1.)/8.;float G=(nv/(nv*(1.-k)+k))*(nl/(nl*(1.-k)+k));vec3 spec=distribution(nh,r)*G*F/(4.*nv*nl+.001);
float shade=1.;vec3 sp=shadow.xyz/shadow.w*.5+.5;if(sp.x>0.&&sp.x<1.&&sp.y>0.&&sp.y<1.&&sp.z<1.){float hit=0.;float bias=max(.00070*(1.-nl),.00019);for(int x=-1;x<=1;x++)for(int y=-1;y<=1;y++){float d=texture(depthTex,sp.xy+vec2(x,y)/shadowSize).r;hit+=sp.z-bias>d?1.:0.;}shade=1.-hit*.085;}
vec3 hemi=mix(vec3(.26,.20,.15),vec3(.48,.62,.77),no.y*.5+.5);vec3 ambient=col*hemi*.62;vec3 direct=((1.-F)*(1.-m)*col/3.14159+spec)*vec3(4.2,3.75,3.10)*nl*shade;
// Broad sky sheen, restrained edge lighting, soft forward scattering through cloth.
vec3 refl=reflect(-V,no);vec3 env=mix(vec3(.10,.17,.19),vec3(.64,.76,.85),smoothstep(-.3,1.,refl.y));vec3 rgb=ambient+direct+env*F0*(1.-r)*.32;
if(normalScale>.70)rgb+=col*max(0.,dot(-no,L))*.20;
rgb=tone((rgb+emissive)*1.15);float fog=smoothstep(24.,90.,length(world-eye));rgb=mix(rgb,vec3(.42,.57,.65),fog*.5);frag=vec4(pow(max(rgb,0.),vec3(1./2.2)),1.);}`;
const depthFS=`#version 300 es
precision highp float;void main(){}`;
const noise=`float hash(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}float noise(vec2 p){vec2 i=floor(p),f=fract(p);f=f*f*(3.-2.*f);return mix(mix(hash(i),hash(i+vec2(1,0)),f.x),mix(hash(i+vec2(0,1)),hash(i+vec2(1,1)),f.x),f.y);}float fbm(vec2 p){return noise(p)*.55+noise(p*2.03)*.28+noise(p*4.17)*.12+noise(p*8.03)*.05;}`;
const fullVS=`#version 300 es
precision highp float;out vec2 uv;void main(){vec2 p=vec2((gl_VertexID<<1)&2,gl_VertexID&2);uv=p;gl_Position=vec4(p*2.-1.,1.,1.);}`;
const skyFS=`#version 300 es
precision highp float;in vec2 uv;uniform float aspect,time,tanFov,studio;uniform mat3 basis;out vec4 frag;${noise}
void main(){if(studio>.5){vec3 c=mix(vec3(.045,.075,.085),vec3(.13,.19,.20),smoothstep(1.,.05,uv.y));float glow=exp(-length((uv-vec2(.63,.5))*vec2(1.,.8))*4.);c+=glow*vec3(.08,.10,.10);frag=vec4(c,1.);return;}
vec2 v=uv*2.-1.;vec3 ray=normalize(basis*vec3(v.x*aspect*tanFov,v.y*tanFov,1.));float y=max(ray.y,0.);vec3 c=mix(vec3(.71,.78,.83),vec3(.30,.52,.80),smoothstep(0.,.95,y));vec3 sun=normalize(vec3(-.46,.51,-.7));float d=length(ray-sun);c+=vec3(.25,.16,.07)*exp(-d*7.);c=mix(c,vec3(1.,.95,.82),1.-smoothstep(.024,.032,d));
vec2 q=ray.xz/(.15+max(.05,ray.y))*1.2;q.x+=time*.008;float a=fbm(q),b=fbm(q+vec2(.04,.13));float cover=smoothstep(.50,.62,a)*smoothstep(.025,.13,ray.y);vec3 cc=mix(vec3(.69,.58,.73),vec3(1.,.85,.78),smoothstep(-.025,.06,a-b));c=mix(c,cc,cover);frag=vec4(c,1.);}`;
const waves=`float wave(vec2 p){return .072*sin(p.x*.92+p.y*.64-time*.91)+.037*sin(p.x*1.92-p.y*.77+time*1.39)+.019*cos(p.y*3.4+p.x*.5-time*1.83);}`;
const waterVS=`#version 300 es
precision highp float;layout(location=0)in vec3 p;uniform mat4 vp;uniform float time,studio;out vec3 world;${waves}
void main(){world=p;world.y=studio>.5?-.07:wave(p.xz)+.22;gl_Position=vp*vec4(world,1.);}`;
const waterFS=`#version 300 es
precision highp float;in vec3 world;uniform vec3 eye;uniform float time,studio;uniform mat4 lightVP,boatInverse;uniform sampler2D depthTex;out vec4 frag;${waves}${noise}${tone}
void main(){vec2 p=world.xz;if(studio>.5){float d=length(p);vec3 c=mix(vec3(.055,.095,.10),vec3(.035,.055,.065),smoothstep(7.,25.,d));vec4 lp=lightVP*vec4(world,1.);vec3 sp=lp.xyz/lp.w*.5+.5;float sh=1.;if(sp.x>0.&&sp.x<1.&&sp.y>0.&&sp.y<1.){float s=0.;for(int x=-1;x<=1;x++)for(int y=-1;y<=1;y++)s+=sp.z-.0007>texture(depthTex,sp.xy+vec2(x,y)/1024.).r?1.:0.;sh=1.-s*.065;}c*=sh;frag=vec4(pow(c,vec3(1./2.2)),1.);return;}
// Keep seawater out of the hollow canoe interiors.
vec3 bp=(boatInverse*vec4(world,1.)).xyz;float ht=(bp.z/3.85+1.)*.5;
if(ht>0.002&&ht<.998){float halfWidth=.575*pow(max(0.,sin(ht*3.14159265)),.56)+.018;
float localRim=.64+.65*pow(abs(ht*2.-1.),3.)+.24*pow(max(0.,1.-ht*2.),7.);
float localDepth=.70*(1.-.62*pow(abs(ht*2.-1.),4.));float f=(localRim-bp.y)/localDepth;
if(f>0.&&f<1.&&abs(abs(bp.x)-1.72)<halfWidth*sqrt(max(0.,1.-f*f))-.006)discard;}
float w=wave(p),dx=(wave(p+vec2(.02,0))-w)/.02,dz=(wave(p+vec2(0,.02))-w)/.02;vec2 ripple=vec2(noise(p*9.+time*.12),noise(p*8.-time*.16))-.5;vec3 N=normalize(vec3(-dx+ripple.x*.07,1.,-dz+ripple.y*.07)),V=normalize(eye-world);float f=pow(1.-max(0.,dot(N,V)),3.);vec3 deep=mix(vec3(.012,.12,.20),vec3(.018,.38,.45),clamp((w+.11)*3.4,0.,1.));vec3 rgb=mix(deep,vec3(.36,.56,.66),f*.73);
float crest=smoothstep(.043,.100,w);float ribbons=1.-smoothstep(.025,.12,abs(sin(p.x*1.55+p.y*2.9-time*1.4+fbm(p*2.)*2.9)));float foam=ribbons*crest*.46;
float bow=exp(-pow((abs(p.x)-1.72)*7.,2.))*exp(-pow((p.y+3.65)*2.7,2.));foam=max(foam,bow*smoothstep(.3,.65,noise(p*12.-time*2.))*.8);rgb=mix(rgb,vec3(.72,.93,.94),foam);
float spec=pow(max(0.,dot(reflect(-normalize(vec3(-.6,.9,.65)),N),V)),160.);rgb+=vec3(1.,.83,.61)*spec*.47;float fog=smoothstep(35.,180.,length(world-eye));rgb=mix(rgb,vec3(.44,.59,.66),fog);frag=vec4(pow(rgb,vec3(1./2.2)),1.);}`;
const partVS=`#version 300 es
precision highp float;layout(location=0)in vec4 p;uniform mat4 vp;uniform float height;out float alpha;void main(){vec4 c=vp*vec4(p.xyz,1.);gl_Position=c;gl_PointSize=clamp(height*.018/max(.1,c.w),1.,12.);alpha=p.w;}`;
const partFS=`#version 300 es
precision highp float;in float alpha;out vec4 frag;void main(){float d=length(gl_PointCoord-.5)*2.;if(d>1.)discard;frag=vec4(.88,.98,1.,alpha*(1.-d));}`;
let mainP,depthP,skyP,waterP,partP;
try{mainP=program(meshVS,meshFS);depthP=program(meshVS,depthFS);skyP=program(fullVS,skyFS);waterP=program(waterVS,waterFS);partP=program(partVS,partFS)}catch(e){console.error(e);fail('The graphics shader did not compile: '+e.message);return}
const locations=new Map;function loc(p,n){if(!locations.has(p))locations.set(p,{});const map=locations.get(p);if(!(n in map))map[n]=gl.getUniformLocation(p,n);return map[n]}
const u1=(p,n,v)=>gl.uniform1f(loc(p,n),v),u2=(p,n,v)=>gl.uniform2fv(loc(p,n),v),u3=(p,n,v)=>gl.uniform3fv(loc(p,n),v),um=(p,n,v)=>gl.uniformMatrix4fv(loc(p,n),false,v);
function bindTex(p,n,tex,unit){gl.activeTexture(gl.TEXTURE0+unit);gl.bindTexture(gl.TEXTURE_2D,tex);gl.uniform1i(loc(p,n),unit)}
function mkTex(data,w=1,h=1){const tex=gl.createTexture();gl.bindTexture(gl.TEXTURE_2D,tex);gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,w,h,0,gl.RGBA,gl.UNSIGNED_BYTE,new Uint8Array(data));gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.LINEAR);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.LINEAR);return tex}
const white=mkTex([255,255,255,255]),flatNormal=mkTex([128,128,255,255]);
const shadowSize=1024,depthTex=gl.createTexture(),fb=gl.createFramebuffer();gl.bindTexture(gl.TEXTURE_2D,depthTex);gl.texImage2D(gl.TEXTURE_2D,0,gl.DEPTH_COMPONENT24,shadowSize,shadowSize,0,gl.DEPTH_COMPONENT,gl.UNSIGNED_INT,null);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.NEAREST);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.NEAREST);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,gl.CLAMP_TO_EDGE);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE);gl.bindFramebuffer(gl.FRAMEBUFFER,fb);gl.framebufferTexture2D(gl.FRAMEBUFFER,gl.DEPTH_ATTACHMENT,gl.TEXTURE_2D,depthTex,0);gl.drawBuffers([gl.NONE]);gl.readBuffer(gl.NONE);if(gl.checkFramebufferStatus(gl.FRAMEBUFFER)!==gl.FRAMEBUFFER_COMPLETE){fail('Shadow framebuffer not supported.');return}gl.bindFramebuffer(gl.FRAMEBUFFER,null);
const lightVP=mul(ortho(-7,7,-6,8,.2,30),look([-10,15,11],[0,2,0]));
const waterVao=gl.createVertexArray();gl.bindVertexArray(waterVao);let waters=[];const N=config.sea?100:2;function coord(i){let u=i/N*2-1;return u*16+Math.sign(u)*Math.pow(Math.abs(u),6)*130;}
for(let j=0;j<N;j++)for(let i=0;i<N;i++){let x=coord(i),xx=coord(i+1),z=coord(j),zz=coord(j+1);waters.push(x,0,z,x,0,zz,xx,0,zz,x,0,z,xx,0,zz,xx,0,z)}let wb=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,wb);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array(waters),gl.STATIC_DRAW);gl.enableVertexAttribArray(0);gl.vertexAttribPointer(0,3,gl.FLOAT,false,0,0);const waterCount=waters.length/3;waters=null;
const particleVao=gl.createVertexArray(),particleBuf=gl.createBuffer();gl.bindVertexArray(particleVao);gl.bindBuffer(gl.ARRAY_BUFFER,particleBuf);gl.bufferData(gl.ARRAY_BUFFER,72*4*4,gl.DYNAMIC_DRAW);gl.enableVertexAttribArray(0);gl.vertexAttribPointer(0,4,gl.FLOAT,false,0,0);
const skyVao=gl.createVertexArray();gl.bindVertexArray(null);
let doc,nodes,items=[],textures=[],channels=[],ready=false;
const dim={SCALAR:1,VEC2:2,VEC3:3,VEC4:4,MAT4:16};
async function loadGLB(ab){const v=new DataView(ab);if(v.getUint32(0,true)!==0x46546c67||v.getUint32(4,true)!==2)throw Error('Not a glTF 2.0 binary');let cursor=12,bin;while(cursor<ab.byteLength){let len=v.getUint32(cursor,true),tag=v.getUint32(cursor+4,true);cursor+=8;if(tag===0x4e4f534a)doc=JSON.parse(new TextDecoder().decode(new Uint8Array(ab,cursor,len)));if(tag===0x004e4942)bin=ab.slice(cursor,cursor+len);cursor+=len}if(!doc||!bin)throw Error('Missing glTF chunks');
 const cache=new Map;function acc(i){if(cache.has(i))return cache.get(i);let a=doc.accessors[i],b=doc.bufferViews[a.bufferView],T={5126:Float32Array,5125:Uint32Array,5123:Uint16Array,5121:Uint8Array}[a.componentType];if(!T)throw Error('Unsupported accessor');let x=new T(bin,(b.byteOffset||0)+(a.byteOffset||0),a.count*dim[a.type]);cache.set(i,x);return x;}
 const aniso=gl.getExtension('EXT_texture_filter_anisotropic');
 const ims=await Promise.all(doc.images.map(async(im)=>{const b=doc.bufferViews[im.bufferView],blob=new Blob([new Uint8Array(bin,b.byteOffset||0,b.byteLength)],{type:im.mimeType});const image=await createImageBitmap(blob,{premultiplyAlpha:'none',colorSpaceConversion:'none'});let tex=gl.createTexture();gl.bindTexture(gl.TEXTURE_2D,tex);gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL,false);gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,gl.RGBA,gl.UNSIGNED_BYTE,image);gl.generateMipmap(gl.TEXTURE_2D);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.LINEAR_MIPMAP_LINEAR);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.LINEAR);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,gl.REPEAT);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_T,gl.REPEAT);if(aniso)gl.texParameterf(gl.TEXTURE_2D,aniso.TEXTURE_MAX_ANISOTROPY_EXT,Math.min(8,gl.getParameter(aniso.MAX_TEXTURE_MAX_ANISOTROPY_EXT)));image.close();return tex;}));
 textures=doc.textures.map(t=>ims[t.source]);
 nodes=doc.nodes.map(n=>({name:n.name,t:[...(n.translation||[0,0,0])],r:[...(n.rotation||[0,0,0,1])],s:[...(n.scale||[1,1,1])],weights:[...(n.weights||[0,0])],children:n.children||[],matrix:I()}));
 const geometry=new Map;for(let ni=0;ni<doc.nodes.length;ni++){const n=doc.nodes[ni];if(n.mesh===undefined)continue;for(const prim of doc.meshes[n.mesh].primitives){let vao=gl.createVertexArray();gl.bindVertexArray(vao);function attribute(ix,ai,count){if(ai===undefined){gl.disableVertexAttribArray(ix);gl.vertexAttrib3f(ix,0,0,0);return}let b=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,b);gl.bufferData(gl.ARRAY_BUFFER,acc(ai),gl.STATIC_DRAW);gl.enableVertexAttribArray(ix);gl.vertexAttribPointer(ix,count,gl.FLOAT,false,0,0)}attribute(0,prim.attributes.POSITION,3);attribute(1,prim.attributes.NORMAL,3);attribute(2,prim.attributes.TEXCOORD_0,2);attribute(3,prim.targets?.[0]?.POSITION,3);attribute(4,prim.targets?.[1]?.POSITION,3);attribute(5,prim.targets?.[0]?.NORMAL,3);attribute(6,prim.targets?.[1]?.NORMAL,3);const indices=acc(prim.indices);let ib=gl.createBuffer();gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER,ib);gl.bufferData(gl.ELEMENT_ARRAY_BUFFER,indices,gl.STATIC_DRAW);items.push({vao,node:ni,count:indices.length,type:indices instanceof Uint32Array?gl.UNSIGNED_INT:gl.UNSIGNED_SHORT,material:doc.materials[prim.material]});}}
 for(const a of doc.animations||[])for(const c of a.channels){const s=a.samplers[c.sampler];channels.push({node:c.target.node,path:c.target.path,times:acc(s.input),values:acc(s.output),stride:c.target.path==='rotation'?4:c.target.path==='weights'?doc.meshes[doc.nodes[c.target.node].mesh].weights.length:3});}
 // The visible mesh is the imported model, not a procedural surrogate.
 const url=URL.createObjectURL(new Blob([ab],{type:'model/gltf-binary'}));$('#download').href=url;$('#download').download='OceanBond-'+kind+'.glb';window.__asset={nodes:nodes.length,meshes:items.length,triangles:items.reduce((s,i)=>s+i.count/3,0),images:ims.length,clips:(doc.animations||[]).map(a=>a.name),bytes:ab.byteLength};
 ready=true;$('#loading').hidden=true;if(parent!==window&&location.origin!=='null')parent.postMessage({type:'ob-model-ready',scene:kind},location.origin);$('#status').textContent='MODEL LOADED · LIVE MOTION';window.__ready=true;resize();request();}
function animate(time){let t=time%8;for(const c of channels){let i=0;while(i<c.times.length-2&&c.times[i+1]<=t)i++;let f=(t-c.times[i])/(c.times[i+1]-c.times[i]);f=clamp(f,0,1);let val=[];for(let k=0;k<c.stride;k++)val.push(c.values[i*c.stride+k]*(1-f)+c.values[(i+1)*c.stride+k]*f);if(c.path==='rotation')val=norm(val);const n=nodes[c.node];if(c.path==='translation')n.t=val;else if(c.path==='rotation')n.r=val;else if(c.path==='weights')n.weights=val;else if(c.path==='scale')n.s=val;}
 function walk(i,parent){const n=nodes[i];n.matrix=mul(parent,trs(n.t,n.r,n.s));n.children.forEach(c=>walk(c,n.matrix));}doc.scenes[doc.scene||0].nodes.forEach(i=>walk(i,I()));}
function drawModel(p,depth=false){gl.useProgram(p);for(const item of items){um(p,'model',nodes[item.node].matrix);u2(p,'weights',nodes[item.node].weights);if(!depth){const m=item.material,b=m.pbrMetallicRoughness;u3(p,'emissive',m.emissiveFactor||[0,0,0]);gl.uniform4fv(loc(p,'base'),b.baseColorFactor||[1,1,1,1]);u1(p,'roughness',b.roughnessFactor??1);u1(p,'metalness',b.metallicFactor??1);u1(p,'hasTex',b.baseColorTexture?1:0);u1(p,'normalScale',m.normalTexture?.scale??.62);bindTex(p,'albedoTex',textures[b.baseColorTexture?.index]||white,0);bindTex(p,'normalTex',textures[m.normalTexture?.index]||flatNormal,1);bindTex(p,'ormTex',textures[b.metallicRoughnessTexture?.index]||white,2);}gl.bindVertexArray(item.vao);gl.drawElements(gl.TRIANGLES,item.count,item.type,0);}}
const basePreset={target:config.target,az:config.az,el:config.el,dist:config.dist};
const presets={full:basePreset,detail:{...basePreset,dist:config.dist*.77},sail:basePreset};
let current='full',az=config.az,el=config.el,dist=config.dist,target=[...config.target],want={...basePreset,target:[...basePreset.target]},mode=config.sea?'sea':'studio',paused=reduced.matches,clock=0,last=0,raf=0,visible=true,externalVisible=true,dragging=false,changed=true,quality='high',timeScale=1;
function setView(name){current=name;want={...presets[name],target:[...presets[name].target]};
 const aspect=canvas.clientWidth/Math.max(1,canvas.clientHeight);
 if(aspect<1.05)want.dist*=Math.min(1.4,1.05/aspect);
 document.querySelectorAll('[data-view]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.view===name)));changed=true;request()}
function pause(v){paused=v;$('#play').textContent=v?'Play motion':'Pause motion';$('#play').setAttribute('aria-pressed',String(!v));$('#status').textContent=v?'MODEL LOADED · MOTION PAUSED':'MODEL LOADED · LIVE MOTION';last=0;request()}
function resize(){const r=canvas.getBoundingClientRect();const cap=quality==='low'?1:(r.width<700?1.3:1.6),dpr=Math.min(devicePixelRatio||1,cap);canvas.width=Math.max(1,Math.round(r.width*dpr));canvas.height=Math.max(1,Math.round(r.height*dpr));changed=true;}
function request(){if(!raf&&ready&&visible&&externalVisible&&!document.hidden)raf=requestAnimationFrame(render)}
let frames=0;
window.addEventListener('message',e=>{if(e.origin!==location.origin||e.source!==parent||e.data?.type!=='ob-visibility')return;externalVisible=Boolean(e.data.visible);last=0;if(externalVisible)request();else{cancelAnimationFrame(raf);raf=0}});
function render(now){raf=0;if(!visible||!externalVisible||document.hidden||!ready)return;const dt=last?Math.min(.06,(now-last)/1000):1/60;last=now;if(!paused)clock+=dt*timeScale;
 const ease=reduced.matches?1:1-Math.exp(-dt*6);az+=(want.az-az)*ease;el+=(want.el-el)*ease;dist+=(want.dist-dist)*ease;for(let i=0;i<3;i++)target[i]+=(want.target[i]-target[i])*ease;
 const drift=paused||dragging?0:Math.sin(clock*.15)*.008,eye=add(target,[Math.sin(az+drift)*Math.cos(el)*dist,Math.sin(el)*dist,Math.cos(az+drift)*Math.cos(el)*dist]);const aspect=canvas.width/canvas.height,fov=.72,view=look(eye,target);let projection=proj(fov,aspect,.1,240);
 // Reserve clean negative space for the compact editorial text on wide screens.
 // Center the model in its chapter panel.
 const vp=mul(projection,view);animate(clock);
 const bm=nodes[0].matrix;const bi=new Float32Array([bm[0],bm[4],bm[8],0,bm[1],bm[5],bm[9],0,bm[2],bm[6],bm[10],0,0,0,0,1]);
 bi[12]=-(bi[0]*bm[12]+bi[4]*bm[13]+bi[8]*bm[14]);bi[13]=-(bi[1]*bm[12]+bi[5]*bm[13]+bi[9]*bm[14]);bi[14]=-(bi[2]*bm[12]+bi[6]*bm[13]+bi[10]*bm[14]);
 gl.bindFramebuffer(gl.FRAMEBUFFER,fb);gl.viewport(0,0,shadowSize,shadowSize);gl.enable(gl.DEPTH_TEST);gl.disable(gl.CULL_FACE);gl.depthMask(true);gl.clear(gl.DEPTH_BUFFER_BIT);gl.useProgram(depthP);um(depthP,'vp',lightVP);um(depthP,'lightVP',lightVP);drawModel(depthP,true);
 gl.bindFramebuffer(gl.FRAMEBUFFER,null);gl.viewport(0,0,canvas.width,canvas.height);gl.clearColor(.1,.2,.3,1);gl.clear(gl.COLOR_BUFFER_BIT|gl.DEPTH_BUFFER_BIT);gl.disable(gl.DEPTH_TEST);gl.depthMask(false);gl.useProgram(skyP);gl.bindVertexArray(skyVao);u1(skyP,'aspect',aspect);u1(skyP,'tanFov',Math.tan(fov/2));u1(skyP,'time',clock);u1(skyP,'studio',mode==='studio'?1:0);const F=norm(sub(target,eye)),R=norm(cross(F,[0,1,0])),U=cross(R,F);gl.uniformMatrix3fv(loc(skyP,'basis'),false,new Float32Array([...R,...U,...F]));gl.drawArrays(gl.TRIANGLES,0,3);
 gl.enable(gl.DEPTH_TEST);gl.depthMask(true);gl.useProgram(waterP);um(waterP,'vp',vp);um(waterP,'boatInverse',bi);um(waterP,'lightVP',lightVP);u1(waterP,'time',clock);u1(waterP,'studio',mode==='studio'?1:0);u3(waterP,'eye',eye);bindTex(waterP,'depthTex',depthTex,3);gl.bindVertexArray(waterVao);gl.drawArrays(gl.TRIANGLES,0,waterCount);
 gl.useProgram(mainP);um(mainP,'vp',vp);um(mainP,'lightVP',lightVP);u3(mainP,'eye',eye);u1(mainP,'shadowSize',shadowSize);bindTex(mainP,'depthTex',depthTex,3);drawModel(mainP);
 if(mode==='sea'){let data=[];for(let i=0;i<72;i++){const u=(clock*.62+i*.137)%1,s=i%2?1:-1,a=i*2.39;data.push(s*1.72+Math.sin(a)*u*.23,.04+Math.sin(u*PI)*(.12+.19*Math.sin(i)**2),-3.5+u*.65,(1-u)*.65);}gl.useProgram(partP);um(partP,'vp',vp);u1(partP,'height',canvas.height);gl.bindVertexArray(particleVao);gl.bindBuffer(gl.ARRAY_BUFFER,particleBuf);gl.bufferSubData(gl.ARRAY_BUFFER,0,new Float32Array(data));gl.enable(gl.BLEND);gl.blendFunc(gl.SRC_ALPHA,gl.ONE_MINUS_SRC_ALPHA);gl.depthMask(false);gl.drawArrays(gl.POINTS,0,72);gl.depthMask(true);gl.disable(gl.BLEND);}
 frames++;window.__frame={time:clock,frames,glError:gl.getError(),paused,mode,view:current,scene:kind,visible:visible&&externalVisible};const moving=Math.abs(az-want.az)+Math.abs(el-want.el)+Math.abs(dist-want.dist)+target.reduce((s,v,i)=>s+Math.abs(v-want.target[i]),0)>.002;
 if(!paused||moving||changed){changed=false;request()}else last=0;
}
const pointers=new Map;let start=null,pinch=0;
canvas.addEventListener('pointerdown',e=>{pointers.set(e.pointerId,[e.clientX,e.clientY]);canvas.setPointerCapture(e.pointerId);dragging=true;start=[e.clientX,e.clientY];if(pointers.size===2){let p=[...pointers.values()];pinch=Math.hypot(p[0][0]-p[1][0],p[0][1]-p[1][1]);}canvas.focus({preventScroll:true})});
canvas.addEventListener('pointermove',e=>{if(!pointers.has(e.pointerId))return;pointers.set(e.pointerId,[e.clientX,e.clientY]);if(pointers.size===2){let p=[...pointers.values()],d=Math.hypot(p[0][0]-p[1][0],p[0][1]-p[1][1]);if(pinch>0)want.dist=clamp(want.dist*pinch/Math.max(20,d),3.5,28);pinch=d;}else if(start){want.az-=(e.clientX-start[0])*.006;want.el=clamp(want.el+(e.clientY-start[1])*.004,-.03,1.3);start=[e.clientX,e.clientY];}changed=true;request()});
function release(e){pointers.delete(e.pointerId);start=null;dragging=pointers.size>0;pinch=0;request()}
canvas.addEventListener('pointerup',release);canvas.addEventListener('pointercancel',release);
canvas.addEventListener('wheel',e=>{if(document.activeElement!==canvas&&!e.ctrlKey)return;e.preventDefault();want.dist=clamp(want.dist*Math.exp(e.deltaY*.001),3.5,28);changed=true;request()},{passive:false});
canvas.addEventListener('keydown',e=>{if(!['ArrowLeft','ArrowRight','ArrowUp','ArrowDown','+','=','-','Home',' '].includes(e.key))return;e.preventDefault();if(e.key==='ArrowLeft')want.az+=.13;if(e.key==='ArrowRight')want.az-=.13;if(e.key==='ArrowUp')want.el=clamp(want.el+.09,-.03,1.3);if(e.key==='ArrowDown')want.el=clamp(want.el-.09,-.03,1.3);if(e.key==='+'||e.key==='=')want.dist=Math.max(3.5,want.dist-.5);if(e.key==='-')want.dist=Math.min(28,want.dist+.5);if(e.key==='Home')setView('full');if(e.key===' ')pause(!paused);request()});
$('#play').addEventListener('click',()=>pause(!paused));$('#reset').addEventListener('click',()=>setView('full'));
document.querySelectorAll('[data-view]').forEach(b=>b.addEventListener('click',()=>setView(b.dataset.view)));
$('#environment').addEventListener('click',()=>{mode=config.sea?(mode==='sea'?'studio':'sea'):'studio';$('#environment').textContent=mode==='sea'?'Studio lighting':'Ocean setting';$('#environment').setAttribute('aria-pressed',String(mode==='studio'));request()});
$('#quality').addEventListener('click',()=>{quality=quality==='high'?'low':'high';$('#quality').textContent=quality==='low'?'Detail: light':'Detail: full';resize();request()});
$('#focus').addEventListener('click',()=>{document.body.classList.toggle('focus');$('#focus').textContent=document.body.classList.contains('focus')?'Show interface':'Focus model';request()});
$('#speed').addEventListener('input',e=>{timeScale=Number(e.target.value);$('#speed-value').textContent=timeScale.toFixed(1)+'×';request()});
$('#fullscreen').addEventListener('click',async()=>{try{if(document.fullscreenElement)await document.exitFullscreen();else await document.documentElement.requestFullscreen()}catch{$('#status').textContent='Fullscreen is not available in this browser.'}});
document.addEventListener('keydown',e=>{if(e.key==='Escape'){document.body.classList.remove('focus');$('#focus').textContent='Focus model';request()}});
new ResizeObserver(()=>{resize();request()}).observe(canvas);
new IntersectionObserver(es=>{visible=es[0].isIntersecting;last=0;if(visible)request();else{cancelAnimationFrame(raf);raf=0}},{threshold:.01}).observe(canvas);
document.addEventListener('visibilitychange',()=>{last=0;if(document.hidden){cancelAnimationFrame(raf);raf=0}else request()});reduced.addEventListener('change',()=>pause(reduced.matches));
canvas.addEventListener('webglcontextlost',e=>{e.preventDefault();cancelAnimationFrame(raf);ready=false;fail('The graphics context was interrupted. Reload the page to restart.');});
window.__test={get scene(){return kind},setView,pause,setTime:t=>{clock=t;changed=true;request()},setEnvironment:m=>{mode=m;request()},nodeMatrices:()=>nodes?.map(n=>[n.name,...n.matrix]),state:()=>nodes?.map(n=>({name:n.name,weights:n.weights,t:n.t,r:n.r})),get doc(){return doc}};
(async()=>{try{let data;if(window.RAFT_GLB){let raw=atob(window.RAFT_GLB);data=new Uint8Array(raw.length);for(let i=0;i<raw.length;i++)data[i]=raw.charCodeAt(i);data=data.buffer;}else{const r=await fetch(config.file);if(!r.ok)throw Error('Model request failed ('+r.status+').');data=await r.arrayBuffer()}await loadGLB(data);setView('full');dist=want.dist;pause(reduced.matches);}catch(e){console.error(e);fail('The model could not load. '+e.message+' Please reload the page or use the downloadable GLB.');}})();
})();
