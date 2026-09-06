// Minimal SVG/DOM stub, enough to run the labelling chart component headlessly.
// The CTM is the identity, so viewBox units and "client" pixels coincide and a
// clientX of 300 means x=300 in the chart's own coordinates.

class El {
  constructor(tag) {
    this.tagName = tag; this.attrs = {}; this.children = []; this.handlers = {};
    this.style = {}; this._text = '';
  }
  setAttribute(k, v) { this.attrs[k] = v; }
  getAttribute(k) { return this.attrs[k]; }
  get id() { return this.attrs.id; }
  set id(v) { this.attrs.id = v; }
  set textContent(v) { this._text = String(v); }
  get textContent() { return this._text; }
  appendChild(c) { this.children.push(c); c.parent = this; return c; }
  remove() {
    if (this.parent) this.parent.children = this.parent.children.filter((c) => c !== this);
  }
  addEventListener(t, fn) { (this.handlers[t] ||= []).push(fn); }
  dispatch(t, ev) { (this.handlers[t] || []).forEach((fn) => fn(ev)); }
  querySelector(sel) {
    const want = sel.replace('#', '');
    const walk = (n) => {
      for (const c of n.children) {
        if (c.attrs.id === want) return c;
        const r = walk(c); if (r) return r;
      }
      return null;
    };
    return walk(this);
  }
  // SVG bits
  getScreenCTM() { return { inverse: () => ({ identity: true }) }; }
  createSVGPoint() {
    return { x: 0, y: 0, matrixTransform(_m) { return { x: this.x, y: this.y }; } };
  }
  setPointerCapture() {} releasePointerCapture() {}
  descendants() {
    return this.children.flatMap((c) => [c, ...c.descendants()]);
  }
}

globalThis.document = {
  createElementNS: (_ns, tag) => new El(tag),
  createElement: (tag) => new El(tag),
};

// A pointer event whose clientY EXPLODES if anything reads it. Vertical
// position is meaningless for this label, and the whole point of drawing the
// chart by hand was that no code path can touch it.
export function pointer(clientX, id = 1) {
  return {
    clientX, pointerId: id, preventDefault() {},
    get clientY() { throw new Error('read clientY — a drag must be horizontal only'); },
  };
}
export { El };
