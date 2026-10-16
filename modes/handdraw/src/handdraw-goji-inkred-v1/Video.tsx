import {useEffect, useState} from 'react';
import {AbsoluteFill, Audio, Img, Sequence, cancelRender, continueRender, delayRender, staticFile, useCurrentFrame} from 'remotion';
import art from '../../content/handdraw-goji-inkred-v1/art.json';
import story from '../../content/handdraw-goji-inkred-v1/story.json';
import timeline from '../../content/handdraw-goji-inkred-v1/timeline.json';

type Scene = typeof art[number];
type Shape = Scene['shapes'][number];
type Geometry = {shape: Shape; path: SVGPathElement; length: number; brush: SVGPathElement; brushD: string; brushLength: number};
type Stroke = {start: number; end: number; index: number; kind: 'ink'|'paint'; g: Geometry};
const cache = new WeakMap<Scene, {geometry: Geometry[]; schedule: Stroke[]}>();
const clamp=(v:number)=>Math.max(0,Math.min(1,v));
const ease=(v:number)=>{const t=clamp(v);return t*t*(3-2*t);};
const ROOT='handdraw-goji-inkred-v1';

function prepare(scene:Scene){
  const saved=cache.get(scene);if(saved)return saved;
  const geometry=scene.shapes.map(shape=>{
    const path=document.createElementNS('http://www.w3.org/2000/svg','path');path.setAttribute('d',shape.d);
    const [l,t,r,b]=shape.bounds;const step=Math.max(7,Math.min(18,(b-t)/4));
    let brushD='';let reverse=false;
    for(let y=t-10;y<b+24;y+=step){brushD+=`${brushD?' L':'M'}${reverse?r+10:l-10},${y} L${reverse?l-10:r+10},${y+step*.15}`;reverse=!reverse;}
    const brush=document.createElementNS('http://www.w3.org/2000/svg','path');brush.setAttribute('d',brushD);
    return {shape,path,length:path.getTotalLength(),brush,brushD,brushLength:brush.getTotalLength()};
  });
  const drawing=geometry.map((g,index)=>({g,index}));
  const special=(s:Shape)=>['ring','check'].includes(s.motion);
  const inks=drawing.filter(({g})=>g.shape.draw&&g.shape.strokeWidth>0&&!special(g.shape));
  const fills=drawing.filter(({g})=>g.shape.draw&&g.shape.fill);
  const iw=inks.map(({g})=>Math.pow(g.length,.67));const it=iw.reduce((a,b)=>a+b,0);
  const fw=fills.map(({g})=>Math.sqrt(Math.max(1,(g.shape.bounds[2]-g.shape.bounds[0])*(g.shape.bounds[3]-g.shape.bounds[1]))));const ft=fw.reduce((a,b)=>a+b,0);
  const schedule:Stroke[]=[];let cursor=.08;
  inks.forEach(({g,index},i)=>{const end=cursor+scene.inkSeconds*iw[i]/it;schedule.push({start:cursor,end,index,kind:'ink',g});cursor=end;});
  cursor=scene.paintAt;
  fills.forEach(({g,index},i)=>{const end=cursor+scene.paintSeconds*fw[i]/ft;schedule.push({start:cursor,end,index,kind:'paint',g});cursor=end;});
  drawing.filter(({g})=>special(g.shape)).forEach(({g,index},i)=>{
    const start=g.shape.motion==='check'?4.55:3.7+i*.37;
    schedule.push({start,end:start+.40,index,kind:'ink',g});
  });
  schedule.sort((a,b)=>a.start-b.start);
  const result={geometry,schedule};cache.set(scene,result);return result;
}

function motion(shape:Shape,time:number){
  if(shape.motion.startsWith('fall-')){
    const i=Number(shape.motion.split('-')[1]);const t=clamp((time-2.75-i*.048)/.9);
    const dx=(785+(i%6)*62+Math.floor(i/6)*17-(629+i%4*48))*t;
    const dy=(707+Math.floor(i/6)*25-(472+Math.floor(i/4)*24))*t*t;
    return `translate(${dx} ${dy})`;
  }
  if(shape.motion.startsWith('bob-'))return `translate(0 ${Math.sin(time*1.6+Number(shape.motion.split('-')[1]))*1.7})`;
  if(shape.motion==='steam')return `translate(0 ${-Math.sin(time*1.4)*4})`;
  return undefined;
}

function Pen({x,y,brush,color}:{x:number;y:number;brush:boolean;color:string}){
  return <g transform={`translate(${x},${y}) rotate(26)`} style={{filter:'drop-shadow(3px 6px 3px #00000020)'}}>
    {brush?<>
      <path d="M0 0 Q-21 -24 -10 -57 Q0 -73 10 -57 Q20 -24 0 0Z" fill={color} stroke="#4b4846" strokeWidth="1"/>
      <path d="M-8 -61 L-7 -212 Q0 -225 7 -212 L8 -61Z" fill="#494744" stroke="#33322f" strokeWidth="1.2"/>
      <path d="M-7 -83 L7 -83 M-7 -77 L7 -77" stroke="#a6a197" strokeWidth="2"/>
      <path d="M-3 -98 L-3 -202" stroke="#807b71" strokeWidth="1.2"/>
    </>:<>
      <path d="M0 0 L-11 -32 L-7 -58 L7 -58 L11 -32Z" fill="#d8d6cf" stroke="#4a4945" strokeWidth="1.4"/>
      <path d="M0 0 L0 -41" stroke="#55524d" strokeWidth="1.1"/>
      <circle cy="-35" r="2.3" fill="#514e48"/>
      <path d="M-7 -59 L-6 -220 Q0 -231 6 -220 L7 -59Z" fill="#4a4742" stroke="#302f2d" strokeWidth="1.3"/>
      <path d="M-3 -78 L-3 -210" stroke="#b9b3a8" strokeWidth="1.3"/>
    </>}
  </g>;
}

function Illustration({scene,time}:{scene:Scene;time:number}){
  const {geometry,schedule}=prepare(scene);
  const phase=(s:Stroke|undefined)=>s?clamp((time-s.start)/(s.end-s.start)):1;
  const ink=new Map(schedule.filter(s=>s.kind==='ink').map(s=>[s.index,s]));
  const paint=new Map(schedule.filter(s=>s.kind==='paint').map(s=>[s.index,s]));
  const active=schedule.find(s=>time>=s.start&&time<s.end);
  const activePath=active?.kind==='ink'?active.g.path:active?.g.brush;
  const tip=active&&activePath?.getPointAtLength(phase(active)*(active.kind==='ink'?active.g.length:active.g.brushLength));
  const brushColor=active?.g.shape.fill?.includes('redwash')||active?.g.shape.fill==='#f4ae8d'?'#b95045':active?.g.shape.fill?.includes('amber')||active?.g.shape.fill==='#e8cd87'?'#c9a05d':'#6c675d';
  return <svg viewBox="0 0 1600 900" width="1920" height="1080" style={{position:'absolute',inset:0}}>
    <defs>
      <linearGradient id="redwash" x1="0" x2="1" y2=".4"><stop stopColor="#c95848"/><stop offset=".48" stopColor="#e27b60"/><stop offset="1" stopColor="#ac4339"/></linearGradient>
      <linearGradient id="amberwash" x1="0" x2=".6" y2="1"><stop stopColor="#f0dfa3" stopOpacity=".35"/><stop offset="1" stopColor="#c8a15e" stopOpacity=".88"/></linearGradient>
      {geometry.map((g,i)=>g.shape.draw&&g.shape.fill&&<mask key={i} id={`paint-${scene.id}-${i}`} maskUnits="userSpaceOnUse" x="-300" y="-300" width="2300" height="1500">
        <path d={g.brushD} fill="none" stroke="white" strokeWidth="43" strokeLinecap="round" strokeLinejoin="round" strokeDasharray={g.brushLength} strokeDashoffset={g.brushLength*(1-phase(paint.get(i)))}/>
      </mask>)}
    </defs>
    {geometry.map((g,i)=>{
      const s=g.shape;const ip=phase(ink.get(i)),cp=phase(paint.get(i));
      const opacity=s.opacity*(s.motion==='pour'?ease((time-1.5)/.5)*(1-ease((time-3.5)/.6)):s.motion==='cheek'?ease((time-3)/1):s.motion==='warmflow'?ease((time-2.8)/.7):1);
      const stroke=s.stroke==='#ad473c'&&time<scene.paintAt?'#4b4846':s.stroke;
      return <g key={i} opacity={opacity} transform={motion(s,time)}>
        {s.fill&&cp>0&&<path d={s.d} fill={s.fill} mask={s.draw&&cp<1?`url(#paint-${scene.id}-${i})`:undefined}/>}
        {s.strokeWidth>0&&ip>0&&<path d={s.d} fill="none" stroke={stroke} strokeWidth={s.strokeWidth} strokeLinecap="round" strokeLinejoin="round" strokeDasharray={ip<1?g.length:undefined} strokeDashoffset={ip<1?g.length*(1-ip):undefined}/>}
      </g>;
    })}
    {tip&&<g opacity={ease(time/.15)}><Pen x={tip.x} y={tip.y} brush={active.kind==='paint'} color={brushColor}/></g>}
  </svg>;
}

export function InkredVideo(){
  const frame=useCurrentFrame();
  const [fontHandle]=useState(()=>delayRender('Load narration and handwritten Chinese fonts'));
  useEffect(()=>{
    Promise.all([
      new FontFace('InkSerif',`url(${staticFile('fonts/NotoSerifSC-Regular.ttf')})`).load(),
      new FontFace('InkHand',`url(${staticFile(`${ROOT}/fonts/MaShanZheng-Regular.ttf`)})`).load()
    ]).then(fonts=>{fonts.forEach(font=>document.fonts.add(font));continueRender(fontHandle);}).catch(cancelRender);
  },[fontHandle]);
  const current=timeline.scenes.find(s=>frame>=s.from&&frame<s.from+s.durationInFrames)??timeline.scenes.at(-1)!;
  const index=timeline.scenes.indexOf(current);const scene=art[index];const copy=story.scenes[index];
  const time=(frame-current.from)/30;const cue=timeline.captions.find(c=>frame>=c.startFrame&&frame<c.endFrame);
  const fade=1-ease((frame-(timeline.durationInFrames-13))/13);
  const headingProgress=ease((time-.15)/1.65);
  const chapter=index===0?'01':index===1?'02':index<4?'03':index<6?'04':'05';
  return <AbsoluteFill style={{background:'#f9f6ec',fontFamily:'InkSerif',color:'#4b4846'}}>
    <Img src={staticFile(`${ROOT}/paper.jpg`)} style={{position:'absolute',inset:0,width:'100%',height:'100%'}}/>
    <AbsoluteFill style={{opacity:fade}}>
      <Illustration scene={scene} time={time}/>
      <div style={{position:'absolute',left:105,right:105,top:43,display:'flex',justifyContent:'space-between',fontSize:19,letterSpacing:4,color:'#8c8578'}}>
        <span>笔下食养 / 给生活添一抹红</span><span>{chapter} · {copy.phase}</span>
      </div>
      <div style={{position:'absolute',left:112,top:112,right:100,fontFamily:'InkHand',fontSize:68,letterSpacing:3,lineHeight:1.2,whiteSpace:'nowrap',clipPath:`inset(0 ${(1-headingProgress)*100}% 0 0)`}}>{copy.headline}</div>
      <div style={{position:'absolute',left:115,top:220,fontFamily:'InkHand',fontSize:32,letterSpacing:4,color:'#7c776f',opacity:ease((time-1.2)/.6)}}>{copy.note}</div>
      {scene.id==='red-twig'&&time>7.8&&<div style={{position:'absolute',left:230,top:421,fontFamily:'InkHand',fontSize:31,letterSpacing:3,lineHeight:1.8,opacity:ease((time-7.8)/.7)}}>枸杞多糖<br/>类胡萝卜素</div>}
      {scene.id==='detail'&&time>3.8&&<div style={{position:'absolute',left:1160,top:412,fontFamily:'InkHand',fontSize:32,letterSpacing:3,lineHeight:1.8,opacity:ease((time-3.8)/.5)}}>果蒂留白<br/><span style={{fontSize:24,color:'#8b8478'}}>仅作外观观察</span></div>}
      {scene.id==='handfall'&&time>2.6&&<div style={{position:'absolute',left:1460,top:673,fontFamily:'InkHand',fontSize:27,letterSpacing:2}}>标签 · 检测</div>}
      {scene.id==='ending'&&time>2.1&&<>
        <div style={{position:'absolute',left:855,top:454,width:205,textAlign:'center',fontFamily:'InkHand',fontSize:49,letterSpacing:8,opacity:ease((time-2.1)/.6)}}>红枸杞</div>
        <div style={{position:'absolute',left:857,top:528,width:205,textAlign:'center',fontSize:15,letterSpacing:3,opacity:ease((time-2.7)/.5)}}>日常食材 / 手绘示意</div>
      </>}
      {scene.id==='pause'&&<div style={{position:'absolute',right:107,bottom:135,fontSize:17,letterSpacing:1,color:'#827a6b'}}>色彩为艺术表达，不代表食用功效</div>}
      {scene.id==='ending'&&<div style={{position:'absolute',right:107,bottom:135,fontSize:17,letterSpacing:1,color:'#827a6b'}}>通用包装手绘示意 · 以实际商品标签为准</div>}
      {cue&&<div style={{position:'absolute',left:106,right:106,bottom:62,textAlign:'center',fontSize:38,letterSpacing:1.1,lineHeight:1.45,color:'#4b4846',textShadow:'0 1px 5px #f9f6ec,0 -1px 5px #f9f6ec'}}>{cue.text}</div>}
      <div style={{position:'absolute',left:106,right:106,bottom:28,height:2,background:'#c8bca633'}}><div style={{height:2,width:`${frame/(timeline.durationInFrames-1)*100}%`,background:'#88837b'}}/></div>
    </AbsoluteFill>
    <Sequence from={timeline.audioLeadFrames}><Audio src={staticFile(timeline.audio)}/></Sequence>
    <Audio src={staticFile(`${ROOT}/audio/foley.wav`)}/>
  </AbsoluteFill>;
}
