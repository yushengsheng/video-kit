import {Composition, registerRoot} from 'remotion';
import story from '../../content/handdraw-moon-v1/story.json';
import timeline from '../../content/handdraw-moon-v1/timeline.json';
import {MoonVideo} from './Video';

registerRoot(() => <Composition id={story.id} component={MoonVideo} width={story.width} height={story.height} fps={story.fps} durationInFrames={timeline.durationInFrames}/>);
