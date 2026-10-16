import {useEffect, useState} from 'react';
import {AbsoluteFill, Audio, Img, Sequence, cancelRender, continueRender, delayRender, staticFile, useCurrentFrame} from 'remotion';
import art from '../../content/handdraw-goji-comic-v1/art.json';
import story from '../../content/handdraw-goji-comic-v1/story.json';
import timeline from '../../content/handdraw-goji-comic-v1/timeline.json';

type Shape = typeof art[number]['shapes'][number];
type Geometry = {path: SVGPathElement; length: number; brush: SVGPathElement; brushD: string; brushLength: number; shape: Shape};
type Stroke = {start: number; end: number; index: number; kind: 'ink'|'paint'; geometry: Geometry};
const cache = new WeakMap<typeof art[number], {geometry: Geometry[]; schedule: Stroke[]}>();
const clamp=(v:number)=>Math.max(0,Math.min(1,v));
const ease=(v:number)=>{const t=clamp(v);return t*t*(3-2*t);};

function prepare(scene: typeof art[number]) {
  const saved=cache.get(scene);
  if(saved) return saved;
  const geometry=scene.shapes.map(shape=>{
    const path=document.createElementNS('http://www.w3.org/2000/svg','path');
    path.setAttribute('d',shape.d);
    const [l,t,r,b]=shape.bounds;
    const step=Math.max(9,Math.min(22,(b-t)/4));
    let brushD='';let reverse=false;
    for(let y=t-12;y<b+25;y+=step){
      brushD+=`${brushD?' L':'M'}${reverse?r+12:l-12},${y} L${reverse?l-12:r+12},${y+step*.12}`;
      reverse=!reverse;
    }
    const brush=document.createElementNS('http://www.w3.org/2000/svg','path');
    brush.setAttribute('d',brushD);
    return {path,length:path.getTotalLength(),brush,brushD,brushLength:brush.getTotalLength(),shape};
  });
  const drawing=geometry.map((g,index)=>({g,index})).filter(({g})=>g.shape.draw);
  const ink=drawing.filter(({g})=>g.shape.strokeWidth>0);
  const paint=drawing.filter(({g})=>g.shape.fill);
  const weights=ink.map(({g})=>Math.pow(g.length,.65));
  const fills=paint.map(({g})=>Math.sqrt((g.shape.bounds[2]-g.shape.bounds[0])*(g.shape.bounds[3]-g.shape.bounds[1])));
  const inkTotal=weights.reduce((a,b)=>a+b,0);
  const fillTotal=fills.reduce((a,b)=>a+b,0);
  const schedule: Stroke[]=[];
  let cursor=.1;
  ink.forEach(({g,index},i)=>{const end=cursor+.95*weights[i]/inkTotal;schedule.push({start:cursor,end,index,kind:'ink',geometry:g});cursor=end;});
  cursor+=.03;
  paint.forEach(({g,index},i)=>{const end=cursor+.7*fills[i]/fillTotal;schedule.push({start:cursor,end,index,kind:'paint',geometry:g});cursor=end;});
  const value={geometry,schedule};cache.set(scene,value);return value;
}

function move(shape:Shape,time:number,index:number){
  if(shape.motion==='hero')return `translate(0 ${Math.sin(time*2.2)*5})`;
  if(shape.motion==='shield')return `translate(0 ${Math.sin(time*2)*3})`;
  if(shape.motion==='spark')return `translate(0 ${Math.sin(time*3.5+index)*3})`;
  if(shape.motion==='smoke')return `translate(${time*27} ${-time*12})`;
  if(shape.motion==='heart')return `translate(0 ${-Math.sin(time*1.8)*9})`;
  if(shape.motion==='berrydrop')return `translate(0 ${Math.min(80,Math.max(0,(time-1.4)*95))})`;
  if(shape.motion==='steam')return `translate(0 ${-Math.sin(time*1.4+index*.1)*7})`;
  if(shape.motion==='leaves')return `rotate(${Math.sin(time*1.3)*.5} 1100 700)`;
  return undefined;
}

function Illustration({scene,time}:{scene:typeof art[number];time:number}){
  const {geometry,schedule}=prepare(scene);
  const phase=(s:Stroke|undefined)=>s?clamp((time-s.start)/(s.end-s.start)):1;
  const ink=new Map(schedule.filter(s=>s.kind==='ink').map(s=>[s.index,s]));
  const paint=new Map(schedule.filter(s=>s.kind==='paint').map(s=>[s.index,s]));
  const active=schedule.find(s=>time>=s.start&&time<s.end);
  const activePath=active?.kind==='ink'?active.geometry.path:active?.geometry.brush;
  const tip=active&&activePath?.getPointAtLength(phase(active)*(active.kind==='ink'?active.geometry.length:active.geometry.brushLength));
  return <>
    <svg viewBox="0 0 1600 900" width="1920" height="1080" style={{position:'absolute',inset:0}}>
      <defs>
        <linearGradient id="monitor" x2="1" y2="1"><stop stopColor="#365669"/><stop offset="1" stopColor="#253a50"/></linearGradient>
        <linearGradient id="sky" x2="0" y2="1"><stop stopColor="#a9c7c3"/><stop offset=".6" stopColor="#e5dec0"/><stop offset="1" stopColor="#f1d5a3"/></linearGradient>
        <linearGradient id="wall" x2=".9" y2="1"><stop stopColor="#f5e8c6"/><stop offset="1" stopColor="#d6c69c"/></linearGradient>
        <linearGradient id="berry" x1="0" x2="1" y2=".3"><stop stopColor="#e47c4c"/><stop offset=".43" stopColor="#dd6046"/><stop offset="1" stopColor="#b84942"/></linearGradient>
        <linearGradient id="ceramic" x2=".7" y2="1"><stop stopColor="#e2e5cc"/><stop offset=".5" stopColor="#acc2b1"/><stop offset="1" stopColor="#74958a"/></linearGradient>
        <linearGradient id="glass" x2="1" y2=".1"><stop stopColor="#d7dfc4" stopOpacity=".75"/><stop offset=".45" stopColor="#f8edce" stopOpacity=".35"/><stop offset="1" stopColor="#aebba8" stopOpacity=".7"/></linearGradient>
        <linearGradient id="wood" x2=".2" y2="1"><stop stopColor="#e1c593"/><stop offset="1" stopColor="#bca072"/></linearGradient>
        <linearGradient id="pack" x2="1" y2=".1"><stop stopColor="#c5b994"/><stop offset=".12" stopColor="#e8dbb6"/><stop offset=".58" stopColor="#f1e5c7"/><stop offset="1" stopColor="#b9ae87"/></linearGradient>
        {geometry.map((g,i)=>g.shape.draw&&g.shape.fill&&<mask key={i} id={`paint-${scene.id}-${i}`} maskUnits="userSpaceOnUse" x="-400" y="-400" width="2400" height="1600">
          <path d={g.brushD} fill="none" stroke="white" strokeWidth="49" strokeLinecap="round" strokeLinejoin="round" strokeDasharray={g.brushLength} strokeDashoffset={g.brushLength*(1-phase(paint.get(i)))}/>
        </mask>)}
      </defs>
      {geometry.map((g,i)=>{
        const s=g.shape;const ip=phase(ink.get(i)), cp=phase(paint.get(i));
        return <g key={i} opacity={s.opacity*(s.motion==='smoke'?1-ease((time-.2)/1.9):s.motion==='battery-low'?.55+.45*Math.pow(Math.cos(time*5),2):1)} transform={move(s,time,i)}>
          {s.fill&&cp>0&&<path d={s.d} fill={s.fill} mask={s.draw&&cp<1?`url(#paint-${scene.id}-${i})`:undefined}/>}
          {s.strokeWidth>0&&ip>0&&<path d={s.d} fill="none" stroke={s.stroke} strokeWidth={s.strokeWidth} strokeLinecap="round" strokeLinejoin="round" strokeDasharray={ip<1?g.length:undefined} strokeDashoffset={ip<1?g.length*(1-ip):undefined}/>}
        </g>;
      })}
    </svg>
    {tip&&<Img src={staticFile('handdraw-moon-v1/drawing-hand.png')} style={{position:'absolute',width:887*.25,height:1774*.25,left:tip.x*1.2-109*.25,top:tip.y*1.2-36*.25,opacity:.9,transform:'rotate(-3deg)',transformOrigin:`${109*.25}px ${36*.25}px`}}/>}
  </>;
}

export function ComicVideo(){
  const frame=useCurrentFrame();
  const [fontHandle]=useState(()=>delayRender('Comic Chinese font'));
  useEffect(()=>{
    new FontFace('ComicSerif',`url(${staticFile('fonts/NotoSerifSC-Regular.ttf')})`).load().then(font=>{document.fonts.add(font);continueRender(fontHandle);}).catch(cancelRender);
  },[fontHandle]);
  const current=timeline.scenes.find(s=>frame>=s.from&&frame<s.from+s.durationInFrames)??timeline.scenes.at(-1)!;
  const index=timeline.scenes.indexOf(current);const scene=art[index];const copy=story.scenes[index];
  const time=(frame-current.from)/30;const cue=timeline.captions.find(c=>frame>=c.startFrame&&frame<c.endFrame);
  const ending=scene.id==='ending';const screen=scene.id==='screen';
  const fade=1-ease((frame-(timeline.durationInFrames-12))/12);
  const product=scene.id==='quality'?{x:1050,y:581,w:135}:scene.id==='snack'?{x:1244,y:482,w:165}:scene.id==='choice'?{x:1277,y:493,w:165}:null;
  return <AbsoluteFill style={{background:'#fff0d2',fontFamily:'ComicSerif',color:'#454252'}}>
    <AbsoluteFill style={{opacity:fade}}>
      <Illustration scene={scene} time={time}/>
      <Img src={staticFile('handdraw-goji-comic-v1/paper.jpg')} style={{position:'absolute',inset:0,width:'100%',height:'100%',mixBlendMode:'multiply',opacity:.24}}/>
      <div style={{position:'absolute',inset:0,background:'linear-gradient(180deg,rgba(255,246,216,.10),transparent 30%,transparent 79%,rgba(255,240,210,.95) 100%)'}}/>
      <div style={{position:'absolute',left:94,right:94,top:47,fontSize:19,letterSpacing:3,display:'flex',justifyContent:'space-between',color:'#736456'}}>
        <span>本草日常 / 打工人的枸杞小搭档</span><span>漫画篇 · {String(index+1).padStart(2,'0')}</span>
      </div>
      <div style={{position:'absolute',left:96,top:ending?285:115,width:ending||screen?520:1660,opacity:ease(time/.35)}}>
        <div style={{fontSize:20,letterSpacing:4,color:'#a4664d',marginBottom:14}}>{copy.eyebrow}</div>
        <div style={{fontSize:ending||screen?60:scene.id==='hero'?59:47,letterSpacing:2.4,lineHeight:1.55,color:'#474350',textShadow:'0 2px 3px #fff0d266'}}>{screen?<>屏幕眼，<br/>电量告急！</>:ending?<>日常轻食养，<br/>休息也跟上</>:copy.headline}</div>
        {ending&&<div style={{fontSize:24,letterSpacing:3,marginTop:24,color:'#81634f'}}>均衡饮食 · 劳逸结合</div>}
      </div>
      {screen&&<div style={{position:'absolute',left:682,top:156,width:108,textAlign:'center',fontSize:26,fontWeight:700,color:'#9b4d44',opacity:.7+.3*Math.cos(time*10)}}>10%</div>}
      {ending&&<div style={{position:'absolute',left:738,top:171,width:113,textAlign:'center',fontSize:28,color:'#f5f3d8'}}>100%</div>}
      {scene.id==='hero'&&<div style={{position:'absolute',left:280,top:746,width:286,textAlign:'center',fontSize:26,letterSpacing:2,color:'#6d6558'}}>先放下屏幕</div>}
      {scene.id==='shields'&&time>1.35&&<>
        <div style={{position:'absolute',left:396,top:640,width:325,textAlign:'center',fontSize:31,color:'#faf0cc',letterSpacing:3}}>枸杞多糖</div>
        <div style={{position:'absolute',left:1290,top:640,width:325,textAlign:'center',fontSize:31,color:'#faf0cc',letterSpacing:3}}>玉米黄质</div>
      </>}
      {scene.id==='compare'&&<>
        <div style={{position:'absolute',left:905,top:504,width:110,textAlign:'center',fontSize:75,color:'#9b6e50'}}>?</div>
        <div style={{position:'absolute',left:175,top:285,width:575,textAlign:'center',fontSize:27,letterSpacing:3,color:'#8e7066'}}>颜色深浅</div>
        <div style={{position:'absolute',right:175,top:285,width:575,textAlign:'center',fontSize:27,letterSpacing:3,color:'#697c68'}}>泡水浮沉</div>
      </>}
      {product&&time>1.35&&<div style={{position:'absolute',left:product.x-product.w/2,top:product.y,width:product.w,textAlign:'center',fontSize:24,letterSpacing:5,color:'#695d43'}}>红枸杞</div>}
      {scene.id==='snack'&&<div style={{position:'absolute',left:373,top:622,width:150,fontSize:23,letterSpacing:2,lineHeight:1.7,color:'#677b70',transform:'rotate(6deg)'}}>先看<br/>食用说明</div>}
      {scene.id==='quality'&&<div style={{position:'absolute',left:1165,top:791,width:228,textAlign:'center',fontSize:17,letterSpacing:2,color:'#6f735f'}}>标签与检测信息</div>}
      {['shields','hero','ending'].includes(scene.id)&&<div style={{position:'absolute',right:95,bottom:137,fontSize:16,letterSpacing:1.5,color:'#796c5a'}}>{scene.id==='shields'?'成分介绍 · 不代表治疗功效':'电量与角色为漫画表达，不代表食用效果'}</div>}
      {scene.id==='traditional'&&<div style={{position:'absolute',right:95,bottom:137,fontSize:16,letterSpacing:1.5,color:'#796c5a'}}>传统中医语境 · 食品不能替代药物</div>}
      {['quality','snack','choice'].includes(scene.id)&&<div style={{position:'absolute',right:95,bottom:137,fontSize:16,letterSpacing:1.5,color:'#796c5a'}}>手绘包装示意 · 以实际商品标签为准</div>}
      {cue&&<div style={{position:'absolute',left:95,right:95,bottom:60,textAlign:'center',fontSize:39,letterSpacing:1.2,lineHeight:1.45,color:'#48413b',textShadow:'0 1px 5px #fff1d5,0 -1px 5px #fff1d5'}}>{cue.text}</div>}
      <div style={{position:'absolute',left:95,right:95,bottom:28,height:2,background:'#ac8c6f33'}}><div style={{height:2,width:`${frame/(timeline.durationInFrames-1)*100}%`,background:'#bb7055'}}/></div>
    </AbsoluteFill>
    <Sequence from={timeline.audioLeadFrames}><Audio src={staticFile(timeline.audio)}/></Sequence>
    <Audio src={staticFile('handdraw-goji-comic-v1/audio/music-foley.wav')}/>
  </AbsoluteFill>;
}
