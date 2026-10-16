import {Composition,registerRoot} from 'remotion';
import timeline from '../../content/handdraw-goji-inkred-v1/timeline.json';
import {InkredVideo} from './Video';
registerRoot(()=> <Composition id="HanddrawGojiInkredV1" component={InkredVideo} width={1920} height={1080} fps={30} durationInFrames={timeline.durationInFrames}/>);
