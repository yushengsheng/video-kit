import {Composition, registerRoot} from 'remotion';
import timeline from '../../content/handdraw-moon-v1/timeline.json';
import {MoonVideo, type HanddrawProps} from './Video';

registerRoot(() => <Composition id="HanddrawWorkflow" component={MoonVideo}
  width={1920} height={1080} fps={30} durationInFrames={timeline.durationInFrames}
  defaultProps={{} as HanddrawProps} calculateMetadata={({props}) => ({durationInFrames:(props as HanddrawProps).timing?.durationInFrames ?? timeline.durationInFrames})}/>);
