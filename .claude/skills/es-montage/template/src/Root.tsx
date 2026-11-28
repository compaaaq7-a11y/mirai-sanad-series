import {Composition} from 'remotion';
import {Montage, MontageProps} from './Montage';
import data from './montage.json';

// montage.json is written by scripts/build_props.py — don't edit it by hand
const props = data as unknown as MontageProps;

export const RemotionRoot: React.FC = () => (
  <Composition
    id="Montage"
    component={Montage}
    durationInFrames={props.durationInFrames}
    fps={props.fps}
    width={props.width}
    height={props.height}
    defaultProps={props}
  />
);
