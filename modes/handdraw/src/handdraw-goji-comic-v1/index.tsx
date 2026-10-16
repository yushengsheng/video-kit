import {Composition,registerRoot} from 'remotion';
import timeline from '../../content/handdraw-goji-comic-v1/timeline.json';
import {ComicVideo} from './Video';
registerRoot(()=> <Composition id="HanddrawGojiComicV1" component={ComicVideo} width={1920} height={1080} fps={30} durationInFrames={timeline.durationInFrames}/>);
