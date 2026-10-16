import {Composition, registerRoot} from 'remotion';
import timeline from '../../content/handdraw-goji-v1/timeline.json';
import {GojiVideo} from './Video';

registerRoot(()=> <Composition id="HanddrawGojiV1" component={GojiVideo} width={1920} height={1080} fps={30} durationInFrames={timeline.durationInFrames}/>);
