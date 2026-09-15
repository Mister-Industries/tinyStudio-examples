// visual.js — Serial Plotter (tinyStudio theme)
// Graphs the latest number printed over Serial (serialValue()) as a scrolling
// line, auto-scaling to the data. Try Serial.println(analogRead(A0)) on the
// board. Switch to Code to edit this sketch; Visual to run it.

const MAX = 240; // points kept on screen
let data = [];
let shown = 0;   // eased readout

function setup() {
  createCanvas(720, 720);
}

function draw() {
  background(theme.bg);
  const pad = 42;

  // pull the most recent serial value each frame
  if (serialAvailable()) {
    data.push(serialValue());
    if (data.length > MAX) data.shift();
  }

  // label
  noStroke();
  fill(theme.muted);
  textFont(theme.font);
  textStyle(BOLD);
  textSize(20);
  textAlign(LEFT, TOP);
  text('SERIAL PLOTTER', pad, pad);

  // big readout
  shown = lerp(shown, serialValue(), 0.15);
  fill(theme.text);
  textFont(theme.mono);
  textStyle(NORMAL);
  textSize(96);
  text(serialAvailable() ? shown.toFixed(2) : '—', pad, pad + 42);
  fill(theme.muted);
  textFont(theme.font);
  textSize(20);
  text(serialAvailable() ? 'latest value' : 'waiting for serial…', pad, pad + 156);

  // auto-scale to the data range (with a little headroom)
  let lo = Math.min(...data, 0);
  let hi = Math.max(...data, 1);
  if (hi === lo) hi = lo + 1;

  // chart card
  const top = 255;
  const w = width - pad * 2;
  const h = height - top - pad;
  fill(theme.panel);
  stroke(theme.border);
  strokeWeight(1.5);
  rect(pad, top, w, h, 15);

  // grid
  stroke(theme.grid);
  strokeWeight(1);
  for (let i = 1; i < 4; i++) {
    const y = top + (h * i) / 4;
    line(pad + 21, y, pad + w - 21, y);
  }

  // plotted line
  noFill();
  stroke(theme.accent);
  strokeWeight(3);
  beginShape();
  for (let i = 0; i < data.length; i++) {
    const x = map(i, 0, MAX - 1, pad + 21, pad + w - 21);
    const y = map(data[i], lo, hi, top + h - 21, top + 21, true);
    vertex(x, y);
  }
  endShape();

  // axis range labels
  noStroke();
  fill(theme.muted);
  textFont(theme.mono);
  textAlign(RIGHT, TOP);
  textSize(16);
  text(hi.toFixed(0), pad + w - 21, top + 9);
  textAlign(RIGHT, BOTTOM);
  text(lo.toFixed(0), pad + w - 21, top + h - 9);
}
