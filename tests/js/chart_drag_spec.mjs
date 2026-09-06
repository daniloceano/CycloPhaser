import { El, pointer } from './dom.mjs';
// chart.mjs is written next to this file by tests/test_manual_labels.py,
// straight from label_tab._CHART_JS, so the spec always runs the JS that
// actually ships rather than a copy that can drift.
import chart from './chart.mjs';

const W = 1000, ML = 74, MR = 22, MT = 26, MB = 44;
const N = 101;                       // steps 0..100
const PW = W - ML - MR;              // 904
const sx = (i) => ML + (i / (N - 1)) * PW;      // 9.04 viewBox units per step
const ix = (x) => Math.round(((x - ML) / PW) * (N - 1));

function mount(phases) {
  const parent = new El('div');
  let emitted = null;
  chart({
    parentElement: parent,
    setTriggerValue: (k, v) => { emitted = { k, v: JSON.parse(v) }; },
    data: {
      sid: 'T1', n: N,
      y: Array.from({ length: N }, (_, i) => -1e-5 - 1e-7 * i * (N - i)),
      phases, colors: { incipient: '#65a1e6', intensification: '#f7b538',
                        mature: '#d62828', decay: '#9aa981', residual: 'gray' },
      w: W, h: 520, ml: ML, mr: MR, mt: MT, mb: MB,
    },
  });
  const svg = parent.querySelector('#cp-label-chart').children[0];
  return { parent, svg, emit: () => emitted };
}

const PHASES = [
  { phase: 'incipient', start_idx: 0, tolerance_idx: 0 },
  { phase: 'intensification', start_idx: 20, tolerance_idx: 3 },
  { phase: 'mature', start_idx: 50, tolerance_idx: 5 },
  { phase: 'decay', start_idx: 75, tolerance_idx: 4 },
];
const clone = () => PHASES.map((p) => ({ ...p }));

let pass = 0, fail = 0;
const ok = (name, cond, extra = '') => {
  if (cond) { pass++; console.log('  ok   ' + name); }
  else { fail++; console.log('  FAIL ' + name + ' ' + extra); }
};

// grips are the 'move' hit areas: transparent rects with cursor ew-resize
const grips = (svg) => svg.children.filter(
  (c) => c.tagName === 'rect' && c.attrs.cursor === 'ew-resize');
const edges = (svg) => svg.children.filter(
  (c) => c.tagName === 'rect' && c.attrs.cursor === 'col-resize');
const bands = (svg) => svg.children.filter(
  (c) => c.tagName === 'rect' && c.attrs['fill-opacity'] === 0.30);
const bars = (svg) => svg.children.filter(
  (c) => c.tagName === 'rect' && c.attrs['fill-opacity'] === 0.38);
const tags = (svg) => svg.children.filter((c) => c.tagName === 'text' && c.attrs['font-weight'] === '600');

console.log('\n1. it renders');
{
  const { svg } = mount(clone());
  ok('one path for the raw series', svg.children.filter((c) => c.tagName === 'path').length === 1);
  ok('one shaded band per phase', bands(svg).length === 4, `got ${bands(svg).length}`);
  ok('one bar per boundary (not the first phase)', bars(svg).length === 3, `got ${bars(svg).length}`);
  ok('one move-grip per boundary', grips(svg).length === 3);
  ok('two edge grips per boundary', edges(svg).length === 6);
}

console.log('\n2. bar thickness IS the tolerance');
{
  const { svg } = mount(clone());
  const b = bars(svg);
  const step = PW / (N - 1);
  ok('±3 bar is 6 steps wide', Math.abs(b[0].attrs.width - 6 * step) < 1e-6,
     `${b[0].attrs.width} vs ${6 * step}`);
  ok('±5 bar is 10 steps wide', Math.abs(b[1].attrs.width - 10 * step) < 1e-6);
  ok('bar is centred on the boundary', Math.abs(b[0].attrs.x - (sx(20) - 3 * step)) < 1e-6);
  ok('label shows index and margin', tags(svg)[0].textContent === '20 ±3',
     JSON.stringify(tags(svg)[0].textContent));
}

console.log('\n3. dragging a bar moves the boundary, and the shading follows');
{
  const { svg, emit } = mount(clone());
  grips(svg)[1].dispatch('pointerdown', pointer(sx(50)));   // grab the mature bar
  svg.dispatch('pointermove', pointer(sx(40)));
  const bandsNow = bands(svg);
  ok('boundary moved to 40', Math.abs(bars(svg)[1].attrs.x - (sx(40) - 5 * (PW / (N - 1)))) < 1e-6);
  ok('preceding band now ends at 40', Math.abs(bandsNow[1].attrs.x + bandsNow[1].attrs.width - sx(40)) < 1e-6);
  ok('following band now starts at 40', Math.abs(bandsNow[2].attrs.x - sx(40)) < 1e-6);
  ok('label updated', tags(svg)[1].textContent === '40 ±5');
  ok('nothing emitted mid-drag', emit() === null);
  svg.dispatch('pointerup', pointer(sx(40)));
  const e = emit();
  ok('emits on release', e && e.k === 'edit');
  ok('payload carries the new index', e.v.phases[2].start_idx === 40, JSON.stringify(e.v.phases));
  ok('other boundaries untouched', e.v.phases[1].start_idx === 20 && e.v.phases[3].start_idx === 75);
  ok('tolerances untouched', e.v.phases.map((p) => p.tolerance_idx).join() === '0,3,5,4');
}

console.log('\n4. a bar cannot cross its neighbours');
{
  const { svg, emit } = mount(clone());
  grips(svg)[1].dispatch('pointerdown', pointer(sx(50)));
  svg.dispatch('pointermove', pointer(sx(5)));      // way past the one at 20
  svg.dispatch('pointerup', pointer(sx(5)));
  ok('clamped to one past the previous boundary', emit().v.phases[2].start_idx === 21,
     String(emit().v.phases[2].start_idx));
}
{
  const { svg, emit } = mount(clone());
  grips(svg)[1].dispatch('pointerdown', pointer(sx(50)));
  svg.dispatch('pointermove', pointer(sx(95)));     // past the one at 75
  svg.dispatch('pointerup', pointer(sx(95)));
  ok('clamped to one before the next boundary', emit().v.phases[2].start_idx === 74,
     String(emit().v.phases[2].start_idx));
}

console.log('\n5. dragging an edge changes only the margin');
{
  const { svg, emit } = mount(clone());
  edges(svg)[2].dispatch('pointerdown', pointer(sx(50)));   // an edge of the mature bar
  svg.dispatch('pointermove', pointer(sx(62)));
  svg.dispatch('pointerup', pointer(sx(62)));
  const e = emit();
  ok('margin became |62-50| = 12', e.v.phases[2].tolerance_idx === 12, String(e.v.phases[2].tolerance_idx));
  ok('the boundary itself did not move', e.v.phases[2].start_idx === 50);
}
{
  const { svg, emit } = mount(clone());
  edges(svg)[2].dispatch('pointerdown', pointer(sx(50)));
  svg.dispatch('pointermove', pointer(sx(38)));              // dragged to the other side
  svg.dispatch('pointerup', pointer(sx(38)));
  ok('margin is symmetric, |38-50| = 12', emit().v.phases[2].tolerance_idx === 12);
}
{
  const { svg, emit } = mount(clone());
  edges(svg)[2].dispatch('pointerdown', pointer(sx(50)));
  svg.dispatch('pointermove', pointer(sx(50)));
  svg.dispatch('pointerup', pointer(sx(50)));
  ok('margin can reach 0, never negative', emit().v.phases[2].tolerance_idx === 0);
}

console.log('\n6. the vertical axis is untouchable');
{
  const { svg, emit } = mount(clone());
  // pointer() throws if clientY is read, so merely completing this is the proof
  grips(svg)[0].dispatch('pointerdown', pointer(sx(20)));
  svg.dispatch('pointermove', pointer(sx(30)));
  svg.dispatch('pointerup', pointer(sx(30)));
  ok('a whole drag never reads clientY', emit().v.phases[1].start_idx === 30);
  const before = bands(svg).map((b) => `${b.attrs.y}/${b.attrs.height}`).join();
  svg.dispatch('pointermove', pointer(sx(70)));
  ok('bands keep their full height, always', before === bands(svg).map((b) => `${b.attrs.y}/${b.attrs.height}`).join());
}

console.log('\n7. a pointermove with no bar grabbed does nothing');
{
  const { svg, emit } = mount(clone());
  svg.dispatch('pointermove', pointer(sx(10)));
  svg.dispatch('pointerup', pointer(sx(10)));
  ok('no stray edit emitted', emit() === null);
}

console.log('\n8. re-rendering replaces the chart instead of stacking one');
{
  const parent = new El('div');
  const data = { sid: 'T1', n: N, y: Array.from({ length: N }, () => -1e-5),
                 phases: clone(), colors: {}, w: W, h: 520, ml: ML, mr: MR, mt: MT, mb: MB };
  chart({ parentElement: parent, setTriggerValue: () => {}, data });
  chart({ parentElement: parent, setTriggerValue: () => {}, data });
  chart({ parentElement: parent, setTriggerValue: () => {}, data });
  ok('exactly one chart in the DOM', parent.children.length === 1, `got ${parent.children.length}`);
}

console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
