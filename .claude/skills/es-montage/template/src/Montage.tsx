import React from 'react';
import {
  AbsoluteFill,
  Audio,
  interpolate,
  OffthreadVideo,
  Sequence,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import {loadFont as loadCairo} from '@remotion/google-fonts/Cairo';
import {loadFont as loadTajawal} from '@remotion/google-fonts/Tajawal';
import {loadFont as loadAlmarai} from '@remotion/google-fonts/Almarai';
import {loadFont as loadNotoKufi} from '@remotion/google-fonts/NotoKufiArabic';

type Word = {text: string; start: number; end: number};
type Caption = {start: number; end: number; words: Word[]};
// zoomOrigin: the face center in this part, so the punch-in keeps it in place
type Segment = {from: number; to: number; outStart: number; zoomOrigin?: [number, number] | null};
type Brand = {
  accent: string;
  textColor: string;
  font: string;
  captionSize: number;
  captionY: number;
  hook: string;
  hookAccentWord: string;
  hookSeconds: number;
  musicVolume: number;
  zoomOnCuts: boolean;
  progressBar: boolean;
};
export type MontageProps = {
  fps: number;
  width: number;
  height: number;
  durationInFrames: number;
  video: string;
  segments: Segment[];
  captions: Caption[];
  music: string | null;
  // the head on the 1080x1920 canvas: during the hook, and its usual spot (null = unknown)
  face: {hook: Box; typical: Box} | null;
  brand: Brand;
};
type Box = {x0: number; y0: number; x1: number; y1: number};
type Layout = {captionCenter: number; hookTop: number; hookSize: number};

const ZOOM = 1.09;
const TOP_SAFE = 110; // under the platform's top icons
const CAPTION_MAX = 0.8; // lower than this hides behind the like/comment UI

// Put the hook and captions where they never cover the face
const planLayout = (face: MontageProps['face'], brand: Brand, W: number, H: number): Layout => {
  const chars = Math.max(1, brand.hook.trim().length);
  const textW = W - 120;
  // rough width of a heavy Arabic/Latin glyph ≈ 0.58em; prefer one line
  let lines = 1;
  let hookSize = Math.min(96, textW / (chars * 0.58));
  if (hookSize < 64) {
    lines = 2;
    hookSize = Math.min(96, (textW * 2) / (chars * 0.58));
  }
  hookSize = Math.max(52, hookSize);
  const hookH = () => lines * hookSize * 1.3;
  const capHalf = brand.captionSize * 1.35; // up to two caption lines
  let captionCenter = brand.captionY * H;

  if (!face) {
    return {captionCenter, hookTop: TOP_SAFE + 20, hookSize};
  }

  // the punch-in grows the face around its own center
  const grow = (b: Box) => {
    const cy = (b.y0 + b.y1) / 2;
    return {top: cy - (cy - b.y0) * ZOOM, bottom: cy + (b.y1 - cy) * ZOOM};
  };
  // captions sit under the chin of the usual framing
  captionCenter = Math.min(Math.max(captionCenter, grow(face.typical).bottom + 30 + capHalf), CAPTION_MAX * H);

  const {top, bottom} = grow(face.hook);

  // 1) above the head, shrinking a little if needed
  const room = top - 30 - TOP_SAFE;
  if (room >= hookH()) {
    return {captionCenter, hookTop: TOP_SAFE + (room - hookH()) * 0.35, hookSize};
  }
  const fit = room / (lines * 1.3);
  if (fit >= 52) {
    hookSize = fit;
    return {captionCenter, hookTop: TOP_SAFE, hookSize};
  }
  // 2) no room above (close-up): between the chin and the captions
  const hookTop = Math.max(bottom + 24, captionCenter - capHalf - 44 - hookH());
  return {captionCenter, hookTop, hookSize};
};

const FONTS: Record<string, () => {fontFamily: string}> = {
  Cairo: () => loadCairo('normal', {weights: ['700', '800'], subsets: ['arabic', 'latin']}),
  Tajawal: () => loadTajawal('normal', {weights: ['700', '800'], subsets: ['arabic', 'latin']}),
  Almarai: () => loadAlmarai('normal', {weights: ['700', '800'], subsets: ['arabic']}),
  'Noto Kufi Arabic': () => loadNotoKufi('normal', {weights: ['700', '800'], subsets: ['arabic']}),
};

// load only the chosen font, once
const loaded: Record<string, string> = {};
const fontFor = (name: string) => {
  const key = FONTS[name] ? name : 'Cairo';
  if (!loaded[key]) loaded[key] = FONTS[key]().fontFamily;
  return loaded[key];
};

const hasArabic =(s: string) => /[؀-ۿ]/.test(s);

// one kept part of the source; every other cut gets a slight punch-in
const Part: React.FC<{seg: Segment; index: number; video: string; zoom: boolean}> = ({
  seg,
  index,
  video,
  zoom,
}) => {
  const {fps} = useVideoConfig();
  const len = Math.round((seg.to - seg.from) * fps);
  const scale = zoom && index % 2 === 1 ? ZOOM : 1;
  const origin = seg.zoomOrigin ? `${seg.zoomOrigin[0]}px ${seg.zoomOrigin[1]}px` : '50% 35%';
  return (
    // zoom around the face so it stays where the layout expects it
    <AbsoluteFill style={{transform: `scale(${scale})`, transformOrigin: origin}}>
      <OffthreadVideo
        src={staticFile(video)}
        trimBefore={Math.round(seg.from * fps)}
        trimAfter={Math.round(seg.to * fps)}
        // 2-frame fades remove clicks at the cut points
        volume={(f) => Math.max(0, Math.min(1, (f + 1) / 2, (len - f) / 2))}
        style={{width: '100%', height: '100%', objectFit: 'cover'}}
      />
    </AbsoluteFill>
  );
};

const Captions: React.FC<{captions: Caption[]; brand: Brand; fontFamily: string; centerY: number}> = ({
  captions,
  brand,
  fontFamily,
  centerY,
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = frame / fps;
  const cap = captions.find((c) => t >= c.start && t < c.end);
  if (!cap) return null;

  const enter = spring({frame: frame - Math.round(cap.start * fps), fps, config: {damping: 14, stiffness: 180}});
  const rtl = cap.words.some((w) => hasArabic(w.text));
  // exactly one highlighted word: the last one that has started
  let activeIndex = -1;
  cap.words.forEach((w, i) => {
    if (t >= w.start) activeIndex = i;
  });

  return (
    <AbsoluteFill>
      <div
        style={{
          position: 'absolute',
          left: 70,
          right: 70,
          top: centerY,
          transform: `translateY(-50%) scale(${interpolate(enter, [0, 1], [0.85, 1])})`,
          opacity: enter,
          display: 'flex',
          flexWrap: 'wrap',
          justifyContent: 'center',
          direction: rtl ? 'rtl' : 'ltr',
          columnGap: brand.captionSize * 0.28,
          rowGap: 0,
        }}
      >
        {cap.words.map((w, i) => {
          const active = i === activeIndex;
          const spoken = i <= activeIndex;
          const pop = spring({frame: frame - Math.round(w.start * fps), fps, config: {damping: 12, stiffness: 220}});
          return (
            <span
              key={i}
              style={{
                fontFamily,
                fontWeight: 800,
                fontSize: brand.captionSize,
                lineHeight: 1.35,
                color: active ? brand.accent : brand.textColor,
                opacity: spoken ? 1 : 0.55,
                transform: `scale(${active ? interpolate(pop, [0, 1], [1.12, 1.04]) : 1})`,
                textShadow: '0 4px 18px rgba(0,0,0,0.75), 0 0 2px rgba(0,0,0,0.9)',
                WebkitTextStroke: '1.5px rgba(0,0,0,0.35)',
                unicodeBidi: 'isolate',
              }}
            >
              {w.text}
            </span>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

const Hook: React.FC<{brand: Brand; fontFamily: string; top: number; size: number}> = ({
  brand,
  fontFamily,
  top,
  size,
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const words = brand.hook.split(/\s+/).filter(Boolean);
  const outStart = Math.round(brand.hookSeconds * fps) - 8;
  const out = interpolate(frame, [outStart, outStart + 8], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const accentWord = brand.hookAccentWord.trim();

  return (
    <AbsoluteFill style={{opacity: out}}>
      <div
        style={{
          position: 'absolute',
          left: 60,
          right: 60,
          top,
          display: 'flex',
          flexWrap: 'wrap',
          justifyContent: 'center',
          direction: hasArabic(brand.hook) ? 'rtl' : 'ltr',
          gap: size * 0.23,
        }}
      >
        {words.map((w, i) => {
          const s = spring({frame: frame - i * 3, fps, config: {damping: 15, stiffness: 160}});
          const isAccent = accentWord !== '' && w.includes(accentWord);
          return (
            <span
              key={i}
              style={{
                fontFamily,
                fontWeight: 800,
                fontSize: size,
                lineHeight: 1.3,
                color: isAccent ? '#111' : '#fff',
                background: isAccent ? brand.accent : 'transparent',
                padding: isAccent ? `0 ${size * 0.23}px` : 0,
                borderRadius: size * 0.19,
                opacity: s,
                transform: `translateY(${interpolate(s, [0, 1], [40, 0])}px)`,
                textShadow: isAccent ? 'none' : '0 6px 24px rgba(0,0,0,0.8)',
                unicodeBidi: 'isolate',
              }}
            >
              {w}
            </span>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

const ProgressBar: React.FC<{color: string}> = ({color}) => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();
  return (
    <div
      style={{
        position: 'absolute',
        top: 0,
        right: 0,
        height: 10,
        width: `${(frame / Math.max(1, durationInFrames - 1)) * 100}%`,
        background: color,
        borderRadius: '0 0 0 10px',
      }}
    />
  );
};

export const Montage: React.FC<MontageProps> = ({video, segments, captions, music, face, brand}) => {
  const {fps, durationInFrames, width, height} = useVideoConfig();
  const fontFamily = fontFor(brand.font);
  const layout = planLayout(face, brand, width, height);

  return (
    <AbsoluteFill style={{backgroundColor: '#000', overflow: 'hidden'}}>
      {segments.map((seg, i) => (
        <Sequence
          key={i}
          from={Math.round(seg.outStart * fps)}
          durationInFrames={Math.round((seg.to - seg.from) * fps)}
          layout="none"
        >
          <Part seg={seg} index={i} video={video} zoom={brand.zoomOnCuts} />
        </Sequence>
      ))}

      {music ? (
        <Audio
          src={staticFile(music)}
          loop
          volume={(f) =>
            brand.musicVolume *
            interpolate(f, [0, 15, durationInFrames - 30, durationInFrames], [0, 1, 1, 0], {
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
            })
          }
        />
      ) : null}

      <Captions captions={captions} brand={brand} fontFamily={fontFamily} centerY={layout.captionCenter} />

      {brand.hook.trim() ? (
        <Sequence durationInFrames={Math.round(brand.hookSeconds * fps)} layout="none">
          <Hook brand={brand} fontFamily={fontFamily} top={layout.hookTop} size={layout.hookSize} />
        </Sequence>
      ) : null}

      {brand.progressBar ? <ProgressBar color={brand.accent} /> : null}
    </AbsoluteFill>
  );
};
