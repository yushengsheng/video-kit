import {useEffect, useState} from 'react';
import {AbsoluteFill, Audio, Img, Sequence, cancelRender, continueRender, delayRender, staticFile, useCurrentFrame} from 'remotion';
import art from '../../content/handdraw-goji-v1/art.json';
import story from '../../content/handdraw-goji-v1/story.json';
import timeline from '../../content/handdraw-goji-v1/timeline.json';

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
  if(shape.motion==='leaves')return `rotate(${Math.sin(time*1.2)*.55} 800 700)`;
  if(shape.motion==='sieve')return `translate(${Math.sin(time*7)*1.7} ${Math.sin(time*7)*.65})`;
  if(shape.motion==='lens')return `translate(${Math.sin(time*.7)*6} ${Math.cos(time*.8)*3})`;
  if(shape.motion==='steam')return `translate(0 ${-Math.sin(time*1.4+index*.1)*7})`;
  if(shape.motion==='falling')return `translate(0 ${(time*.7+index*.2)%1*34})`;
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
        <linearGradient id="sky" x2="0" y2="1"><stop stopColor="#a9c7c3"/><stop offset=".6" stopColor="#e5dec0"/><stop offset="1" stopColor="#f1d5a3"/></linearGradient>
        <linearGradient id="wall" x2=".9" y2="1"><stop stopColor="#f5e8c6"/><stop offset="1" stopColor="#d6c69c"/></linearGradient>
        <linearGradient id="berry" x1="0" x2="1" y2=".3"><stop stopColor="#d67347"/><stop offset=".43" stopColor="#c94f36"/><stop offset="1" stopColor="#a33e32"/></linearGradient>
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
        return <g key={i} opacity={s.opacity} transform={move(s,time,i)}>
          {s.fill&&cp>0&&<path d={s.d} fill={s.fill} mask={s.draw&&cp<1?`url(#paint-${scene.id}-${i})`:undefined}/>}
          {s.strokeWidth>0&&ip>0&&<path d={s.d} fill="none" stroke={s.stroke} strokeWidth={s.strokeWidth} strokeLinecap="round" strokeLinejoin="round" strokeDasharray={ip<1?g.length:undefined} strokeDashoffset={ip<1?g.length*(1-ip):undefined}/>}
        </g>;
      })}
    </svg>
    {tip&&<Img src={staticFile('handdraw-moon-v1/drawing-hand.png')} style={{position:'absolute',width:887*.25,height:1774*.25,left:tip.x*1.2-109*.25,top:tip.y*1.2-36*.25,opacity:.9,transform:'rotate(-3deg)',transformOrigin:`${109*.25}px ${36*.25}px`}}/>}
  </>;
}

export function GojiVideo(){
  const frame=useCurrentFrame();
  const [fontHandle]=useState(()=>delayRender('Goji Chinese font'));
  useEffect(()=>{
    new FontFace('GojiSerif',`url(${staticFile('fonts/NotoSerifSC-Regular.ttf')})`).load().then(font=>{document.fonts.add(font);continueRender(fontHandle);}).catch(cancelRender);
  },[fontHandle]);
  const current=timeline.scenes.find(s=>frame>=s.from&&frame<s.from+s.durationInFrames)??timeline.scenes.at(-1)!;
  const index=timeline.scenes.indexOf(current);
  const scene=art[index];const copy=story.scenes[index];
  const time=(frame-current.from)/30;
  const cue=timeline.captions.find(c=>frame>=c.startFrame&&frame<c.endFrame);
  const ending=scene.id==='ending';
  const titleOpacity=ease(time/.5);
  const finalFade=1-ease((frame-(timeline.durationInFrames-12))/12);
  return <AbsoluteFill style={{background:'#e9ddbb',fontFamily:'GojiSerif',color:'#414e42'}}>
    <AbsoluteFill style={{opacity:finalFade}}>
      <Illustration scene={scene} time={time}/>
      <Img src={staticFile('handdraw-goji-v1/paper.jpg')} style={{position:'absolute',inset:0,width:'100%',height:'100%',mixBlendMode:'multiply',opacity:.33,pointerEvents:'none'}}/>
      <div style={{position:'absolute',inset:0,background:'linear-gradient(180deg,rgba(252,241,211,.20),transparent 32%,transparent 78%,rgba(249,237,206,.93) 100%)'}}/>
      <div style={{position:'absolute',top:53,left:94,right:94,display:'flex',alignItems:'center',justifyContent:'space-between',fontSize:20,letterSpacing:4,color:'#655e47',opacity:.85}}>
        <span>本草日常 <span style={{padding:'0 20px',opacity:.45}}>/</span> 枸杞</span>
        <span style={{fontSize:17,letterSpacing:3}}>手绘食养录 · {String(index+1).padStart(2,'0')}</span>
      </div>
      <div style={{position:'absolute',left:96,top:ending?260:116,opacity:titleOpacity,width:ending?570:1650}}>
        <div style={{fontSize:20,letterSpacing:5,color:'#96764c',marginBottom:18}}>{copy.eyebrow}</div>
        <div style={{fontSize:ending?62:scene.id==='question'?58:47,letterSpacing:3,lineHeight:1.55,fontWeight:500,color:'#3c5144',textShadow:'0 2px 12px #efdfb966'}}>{ending?<>认真挑选，<br/>自然好滋味</>:copy.headline}</div>
        {'subline' in copy&&<div style={{fontSize:ending?27:25,letterSpacing:3,lineHeight:1.7,marginTop:15,color:'#766b4f'}}>{copy.subline}</div>}
        {ending&&<><div style={{height:1,width:85,background:'#af7b51',marginTop:35}}/><div style={{fontSize:19,letterSpacing:4,color:'#8e7958',marginTop:28}}>茶里 · 汤里 · 家常里</div></>}
      </div>
      {['label','ending'].includes(scene.id)&&<div style={{position:'absolute',left:scene.id==='ending'?1090:1065,top:scene.id==='ending'?335:501,width:scene.id==='ending'?180:137,textAlign:'center',fontSize:scene.id==='ending'?34:25,letterSpacing:7,color:'#695d43'}}>枸杞</div>}
      {['orchard','label','ending'].includes(scene.id)&&<div style={{position:'absolute',right:95,bottom:139,fontSize:16,letterSpacing:2,color:'#776d51'}}>画面及包装为手绘示意</div>}
      {scene.id==='family'&&<div style={{position:'absolute',right:95,bottom:139,fontSize:16,letterSpacing:2,color:'#776d51'}}>传统中医语境 · 食品不能替代药物</div>}
      {cue&&<div style={{position:'absolute',left:100,right:100,bottom:61,textAlign:'center',fontSize:39,letterSpacing:1.3,lineHeight:1.45,color:'#443f32',textShadow:'0 1px 5px #fff1d4,0 -1px 5px #fff1d4'}}>{cue.text}</div>}
      <div style={{position:'absolute',bottom:29,left:95,right:95,height:1,background:'#9e967144'}}><div style={{height:1,width:`${frame/(timeline.durationInFrames-1)*100}%`,background:'#a4694a'}}/></div>
    </AbsoluteFill>
    <Sequence from={timeline.audioLeadFrames}><Audio src={staticFile(timeline.audio)} volume={1}/></Sequence>
    <Audio src={staticFile('handdraw-goji-v1/audio/music-foley.wav')} volume={1}/>
  </AbsoluteFill>;
}
