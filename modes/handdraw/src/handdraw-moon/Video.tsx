import {useEffect, useState} from 'react';
import {AbsoluteFill, Audio, Img, Sequence, cancelRender, continueRender, delayRender, staticFile, useCurrentFrame} from 'remotion';
import artData from '../../content/handdraw-moon-v1/art.json';
import defaultTimeline from '../../content/handdraw-moon-v1/timeline.json';

type Shape = {
  d: string; fill: string | null; stroke: string; strokeWidth: number; opacity: number;
  part: string; draw: boolean; bounds: number[];
};
type ShapeInfo = {shape: Shape; path: SVGPathElement; length: number; fillPath: SVGPathElement; fillLength: number; fillD: string};
type Segment = {kind: 'ink' | 'colour'; index: number; start: number; end: number; info: ShapeInfo};
const scenes = artData as {id: string; shapes: Shape[]}[];
export type HanddrawArt = typeof scenes;
export type MovieTimeline = typeof defaultTimeline;
export type HanddrawProps = {
  art?: HanddrawArt; timing?: MovieTimeline; title?: string;
  assets?: {paper: string; hand: string; font: string};
};
const defaultAssets = {paper:'handdraw-moon-v1/paper.jpg', hand:'handdraw-moon-v1/drawing-hand.png', font:'fonts/NotoSerifSC-Regular.ttf'};
const geometryCache = new WeakMap<typeof scenes[number], ShapeInfo[]>();
const clamp = (x: number) => Math.max(0, Math.min(1, x));
const smooth = (x: number) => {const t = clamp(x); return t*t*(3-2*t);};
const layer = {x: 48, y: 83, scale: 1.14};

function fillPath(shape: Shape) {
  const [left, top, right, bottom] = shape.bounds;
  const step = Math.max(12, Math.min(24, (bottom-top)/3));
  let d = '';
  let reverse = false;
  for (let y = top-14; y <= bottom+30; y += step) {
    const x1 = reverse ? right+16 : left-16;
    const x2 = reverse ? left-16 : right+16;
    d += `${d ? ' L' : 'M'}${x1},${y} L${x2},${y+step*.14}`;
    reverse = !reverse;
  }
  return d;
}

function geometry(scene: typeof scenes[number]): ShapeInfo[] {
  const saved = geometryCache.get(scene);
  if (saved) return saved;
  const info = scene.shapes.map(shape => {
    const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    path.setAttribute('d', shape.d);
    const brush = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    const fillD = fillPath(shape);
    brush.setAttribute('d', fillD);
    return {shape, path, length: path.getTotalLength(), fillPath: brush, fillLength: brush.getTotalLength(), fillD};
  });
  geometryCache.set(scene, info);
  return info;
}

function makeSchedule(info: ShapeInfo[], seconds: number, sceneId: string): Segment[] {
  const drawingSeconds = Math.max(3.1, Math.min(7.1, seconds-1.0));
  const priority = [...(sceneId === 'look-up' ? ['moon'] : []), 'monkey-head', 'monkey-body', 'monkey-arms', 'monkey-legs', 'monkey-tail', 'well-stones', 'wooden-bucket', 'rope', 'moon', 'moon-reflection', 'water', 'gesture', 'splashes', 'tree-branch', 'ground'];
  const ordered = info.map((item, index) => ({item, index})).sort((a,b) => {
    const rank = (part: string) => {const index = priority.indexOf(part); return index < 0 ? priority.length : index;};
    return rank(a.item.shape.part)-rank(b.item.shape.part);
  });
  const ink = ordered.filter(({item}) => item.shape.draw && item.shape.strokeWidth > 0);
  const colour = ordered.filter(({item}) => item.shape.draw && item.shape.fill);
  const inkWeight = ink.reduce((sum, {item}) => sum+Math.pow(item.length, .66), 0);
  const colourWeight = colour.reduce((sum, {item}) => sum+Math.sqrt((item.shape.bounds[2]-item.shape.bounds[0])*(item.shape.bounds[3]-item.shape.bounds[1])), 0);
  const segments: Segment[] = [];
  let cursor = .10;
  for (const {item, index} of ink) {
    const duration = drawingSeconds*.62*Math.pow(item.length, .66)/inkWeight;
    segments.push({kind:'ink', index, start:cursor, end:cursor+duration, info:item});
    cursor += duration;
  }
  cursor += .06;
  for (const {item, index} of colour) {
    const weight = Math.sqrt((item.shape.bounds[2]-item.shape.bounds[0])*(item.shape.bounds[3]-item.shape.bounds[1]));
    const duration = drawingSeconds*.34*weight/colourWeight;
    segments.push({kind:'colour', index, start:cursor, end:cursor+duration, info:item});
    cursor += duration;
  }
  return segments;
}

function Drawing({scene, seconds, time, hand}: {scene: typeof scenes[number]; seconds: number; time: number; hand: string}) {
  const info = geometry(scene);
  const schedule = makeSchedule(info, seconds, scene.id);
  const active = schedule.find(segment => time >= segment.start && time < segment.end);
  const inkSegments = new Map(schedule.filter(s => s.kind === 'ink').map(s => [s.index, s]));
  const colourSegments = new Map(schedule.filter(s => s.kind === 'colour').map(s => [s.index, s]));
  const phase = (segment: Segment | undefined) => segment ? clamp((time-segment.start)/(segment.end-segment.start)) : 1;
  let tip: {x: number; y: number} | undefined;
  if (active) {
    const p = phase(active);
    const path = active.kind === 'ink' ? active.info.path : active.info.fillPath;
    const length = active.kind === 'ink' ? active.info.length : active.info.fillLength;
    tip = path.getPointAtLength(p*length);
  }
  const appearance = smooth(time/.13);
  const handOpacity = active ? appearance * smooth((seconds-time)/.2) : 0;
  return <>
    <svg width="1920" height="1080" style={{position:'absolute', inset:0, opacity:appearance}}>
      <defs>
        {info.map((item, i) => item.shape.fill && <clipPath key={i} id={`clip-${scene.id}-${i}`}><path d={item.shape.d}/></clipPath>)}
        {info.map((item, i) => item.shape.fill && item.shape.draw && <mask key={i} id={`paint-${scene.id}-${i}`} maskUnits="userSpaceOnUse" x="-200" y="-200" width="2200" height="1500">
          <path d={item.fillD} fill="none" stroke="white" strokeWidth="51" strokeLinecap="round" strokeLinejoin="round" strokeDasharray={item.fillLength} strokeDashoffset={item.fillLength*(1-phase(colourSegments.get(i)))}/>
        </mask>)}
      </defs>
      <g transform={`translate(${layer.x},${layer.y}) scale(${layer.scale})`}>
        {info.map((item, i) => {
          const shape = item.shape;
          const inkProgress = phase(inkSegments.get(i));
          const colourProgress = phase(colourSegments.get(i));
          return <g key={i} opacity={shape.opacity}>
            {shape.fill && <path d={shape.d} fill={shape.fill} opacity={shape.draw ? (colourProgress > 0 ? .93 : 0) : smooth(time/.8)*.7}
              mask={shape.draw && colourProgress < 1 ? `url(#paint-${scene.id}-${i})` : undefined}/ >}
            {shape.strokeWidth > 0 && inkProgress > 0 && <path d={shape.d} fill="none" stroke={shape.stroke} strokeWidth={shape.strokeWidth} strokeLinecap="round" strokeLinejoin="round"
              strokeDasharray={inkProgress < 1 ? item.length : undefined} strokeDashoffset={inkProgress < 1 ? item.length*(1-inkProgress) : undefined}/ >}
          </g>;
        })}
      </g>
    </svg>
    {tip && <Img src={staticFile(hand)} style={{position:'absolute', width:887*.31, height:1774*.31,
      left:layer.x+tip.x*layer.scale-109*.31, top:layer.y+tip.y*layer.scale-36*.31, opacity:handOpacity,
      transform:`rotate(${Math.sin(time*1.1)*1.2}deg)`, transformOrigin:`${109*.31}px ${36*.31}px`}}/>}
  </>;
}

export function MoonVideo({art=scenes, timing=defaultTimeline, title='井里的月亮', assets=defaultAssets}: HanddrawProps) {
  const timeline = timing;
  const frame = useCurrentFrame();
  const [fontHandle] = useState(() => delayRender('Load Chinese story font'));
  useEffect(() => {
    const font = new FontFace('MoonSerif', `url(${staticFile(assets.font)})`);
    font.load().then(loaded => {document.fonts.add(loaded); continueRender(fontHandle);}).catch(cancelRender);
  }, [fontHandle, assets.font]);
  const current = timeline.scenes.find(scene => frame >= scene.from && frame < scene.from+scene.durationInFrames) ?? timeline.scenes[timeline.scenes.length-1];
  const scene = art.find(item => item.id === current.id)!;
  const local = (frame-current.from)/timeline.fps;
  const caption = timeline.captions.find(cue => frame >= cue.startFrame && frame < cue.endFrame);
  const finalFade = 1-smooth((frame-(timeline.durationInFrames-13))/13);
  return <AbsoluteFill style={{background:'#f9f6ec', fontFamily:'MoonSerif', color:'#493f35'}}>
    <Img src={staticFile(assets.paper)} style={{position:'absolute', inset:0, width:'100%', height:'100%'}}/>
    <AbsoluteFill style={{opacity:finalFade}}>
      <Drawing scene={scene} seconds={current.durationInFrames/timeline.fps} time={local} hand={assets.hand}/>
      {frame < 85 && <div style={{position:'absolute', left:153, top:90, fontSize:57, letterSpacing:9, opacity:smooth(frame/12)*(1-smooth((frame-64)/21))}}>{title}</div>}
      {caption && <div style={{position:'absolute', left:110, right:110, bottom:67, textAlign:'center', fontSize:40, letterSpacing:2,
        lineHeight:1.55, color:'#463e35', textShadow:'0 1px 5px #f9f6ec, 0 -1px 5px #f9f6ec'}}>{caption.text}</div>}
    </AbsoluteFill>
    <Sequence from={timeline.audioLeadFrames}><Audio src={staticFile(timeline.audio)} volume={1}/></Sequence>
  </AbsoluteFill>;
}
