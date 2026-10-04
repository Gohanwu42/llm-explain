import assert from 'node:assert/strict';
import { existsSync, readFileSync } from 'node:fs';
import test from 'node:test';
import vm from 'node:vm';

// Exercise the exact model shipped in the offline HTML, without a browser or DOM.
const htmlPath = new URL('../assets/explainer.html', import.meta.url);
const html = existsSync(htmlPath) ? readFileSync(htmlPath, 'utf8') : '';
const source = html.match(/<script id="water-model">([\s\S]*?)<\/script>/)?.[1];
const context = vm.createContext({ module: { exports: {} } });
if (source) vm.runInContext(source, context, { filename: 'explainer.html:model' });

function calculate(overrides = {}) {
  assert.equal(
    typeof context.module.exports.calculateTank,
    'function',
    'The HTML must expose its real water-tank model without requiring the DOM.',
  );
  return context.module.exports.calculateTank({
    capacityL: 40,
    initialL: 20,
    inflowLpm: 3,
    outflowLpm: 2,
    minutes: 10,
    ...overrides,
  });
}

test('accumulates the difference between flows in liters, not their sum', () => {
  const result = calculate();
  assert.equal(result.netLpm, 1);
  assert.equal(result.volumeL, 30);
  assert.equal(result.elapsedMinutes, 10);
  assert.equal(result.boundaryMinutes, 20);
  assert.equal(result.boundary, 'full');
  assert.equal(result.atBoundary, false);
  assert.equal(result.beyondBoundary, false);
});

test('equal flows leave the initial volume unchanged and have no future boundary', () => {
  const result = calculate({ inflowLpm: 2, outflowLpm: 2, minutes: 500 });
  assert.equal(result.volumeL, 20);
  assert.equal(result.netLpm, 0);
  assert.equal(result.boundaryMinutes, null);
  assert.equal(result.boundary, null);
  assert.equal(result.beyondBoundary, false);
});

test('draining subtracts net outflow and predicts when the tank is empty', () => {
  const result = calculate({ inflowLpm: 1, outflowLpm: 3, minutes: 5 });
  assert.equal(result.volumeL, 10);
  assert.equal(result.netLpm, -2);
  assert.equal(result.boundaryMinutes, 10);
  assert.equal(result.boundary, 'empty');
  assert.equal(result.atBoundary, false);
});

test('zero elapsed time preserves the initial condition', () => {
  const result = calculate({ minutes: 0 });
  assert.equal(result.volumeL, 20);
  assert.equal(result.elapsedMinutes, 0);
  assert.equal(result.atBoundary, false);
});

test('the exact full boundary is valid but a later request stops at the boundary', () => {
  const exact = calculate({ minutes: 20 });
  assert.equal(exact.volumeL, 40);
  assert.equal(exact.atBoundary, true);
  assert.equal(exact.beyondBoundary, false);

  const later = calculate({ minutes: 30 });
  assert.equal(later.volumeL, 40);
  assert.equal(later.elapsedMinutes, 20);
  assert.equal(later.requestedMinutes, 30);
  assert.equal(later.beyondBoundary, true);
});

test('a request after emptying returns the last valid state, never negative water', () => {
  const result = calculate({ inflowLpm: 1, outflowLpm: 3, minutes: 30 });
  assert.equal(result.volumeL, 0);
  assert.equal(result.elapsedMinutes, 10);
  assert.equal(result.boundary, 'empty');
  assert.equal(result.beyondBoundary, true);
});

test('a tank starting at its outgoing boundary has no valid positive interval', () => {
  const full = calculate({ initialL: 40, minutes: 0 });
  assert.equal(full.atBoundary, true);
  assert.equal(full.beyondBoundary, false);
  const later = calculate({ initialL: 40, minutes: 1 });
  assert.equal(later.elapsedMinutes, 0);
  assert.equal(later.beyondBoundary, true);
  const empty = calculate({ initialL: 0, inflowLpm: 1, outflowLpm: 3, minutes: 1 });
  assert.equal(empty.volumeL, 0);
  assert.equal(empty.elapsedMinutes, 0);
  assert.equal(empty.beyondBoundary, true);
});

test('decimal arithmetic does not mislabel a mathematically exact boundary', () => {
  const result = calculate({ capacityL: 0.3, initialL: 0.1, inflowLpm: 0.3, outflowLpm: 0.2, minutes: 2 });
  assert.equal(result.volumeL, 0.3);
  assert.equal(result.atBoundary, true);
  assert.equal(result.beyondBoundary, false);
});

test('doubling both flows doubles the net rate, so five minutes reaches thirty liters', () => {
  const result = calculate({ inflowLpm: 6, outflowLpm: 4, minutes: 5 });
  assert.equal(result.netLpm, 2);
  assert.equal(result.volumeL, 30);
});

test('invalid physical inputs are rejected instead of being coerced or clamped', () => {
  for (const [field, value] of [
    ['capacityL', 0], ['capacityL', -1], ['initialL', -1], ['initialL', 41],
    ['inflowLpm', -1], ['outflowLpm', -1], ['minutes', -1],
    ['capacityL', Infinity], ['initialL', NaN], ['inflowLpm', '3'],
    ['outflowLpm', null], ['minutes', undefined], ['minutes', ''],
  ]) {
    assert.throws(() => calculate({ [field]: value }), { name: /TypeError|RangeError/ }, `${field}=${String(value)}`);
  }
});

test('large finite flows cannot overflow the volume calculation beyond capacity', () => {
  const result = calculate({ inflowLpm: Number.MAX_VALUE, outflowLpm: 0, minutes: 2 });
  assert.equal(result.volumeL, 40);
  assert.equal(result.beyondBoundary, true);
  assert.ok(Number.isFinite(result.elapsedMinutes));
});

test('unrepresentable boundary times produce a clear numerical error', () => {
  assert.throws(
    () => calculate({ inflowLpm: Number.MIN_VALUE, outflowLpm: 0 }),
    { name: 'RangeError' },
  );
});

// A small DOM boundary double runs the shipped interface script itself. It
// records values and event handlers; it does not replace model or UI behavior.
// Native range/keyboard mechanics and visual layout still need a real browser.
function interfaceFixture() {
  function element(attributes = {}) {
    const attrs = new Map(Object.entries(attributes));
    const listeners = new Map();
    return {
      value: attributes.value ?? '', max: attributes.max ?? '',
      dataset: { preset: attributes['data-preset'] }, textContent: '',
      get valueAsNumber() { return this.value === '' ? NaN : Number(this.value); },
      setAttribute(key, value) { attrs.set(key, String(value)); },
      getAttribute(key) { return attrs.get(key) ?? null; },
      hasAttribute(key) { return attrs.has(key); },
      removeAttribute(key) { attrs.delete(key); },
      addEventListener(type, listener) { listeners.set(type, listener); },
      dispatch(type) { listeners.get(type)?.({ target: this, currentTarget: this, preventDefault() {} }); },
      reset() {},
    };
  }
  const nodes = new Map();
  const presets = [];
  for (const tag of html.matchAll(/<[a-z][^>]*>/gi)) {
    const attrs = Object.fromEntries([...tag[0].matchAll(/([a-z-]+)="([^"]*)"/gi)].map((match) => [match[1], match[2]]));
    if (attrs.id || attrs['data-preset']) {
      const node = element(attrs);
      if (attrs.id) nodes.set(attrs.id, node);
      if (attrs['data-preset']) presets.push(node);
    }
  }
  const document = {
    getElementById(id) {
      assert.ok(nodes.has(id), `The fixture must resolve the real HTML element ${id}.`);
      return nodes.get(id);
    },
    querySelectorAll(selector) {
      assert.equal(selector, '[data-preset]');
      return presets;
    },
  };
  const browser = vm.createContext({ document });
  for (const match of html.matchAll(/<script\b[^>]*>([\s\S]*?)<\/script>/g)) {
    vm.runInContext(match[1], browser, { filename: 'explainer.html:interface' });
  }
  return {
    node: (id) => nodes.get(id),
    input(id, value) { const node = nodes.get(id); node.value = String(value); node.dispatch('input'); },
    clickPreset(name) { presets.find((node) => node.dataset.preset === name).dispatch('click'); },
  };
}

test('expanded slider bounds remain stable while lowering and restoring the value', () => {
  for (const id of ['inflow', 'outflow', 'minutes']) {
    const page = interfaceFixture();
    page.input(id, 100);
    assert.equal(Number(page.node(id + '-range').max), 100);
    page.input(id + '-range', 90);
    assert.equal(Number(page.node(id + '-range').max), 100, `${id} must keep its expanded maximum`);
    page.input(id + '-range', 100);
    assert.equal(page.node(id).valueAsNumber, 100);
  }
});

test('reset and presets deliberately restore the standard slider bounds', () => {
  for (const reset of ['reset', 'balanced']) {
    const page = interfaceFixture();
    page.input('inflow', 100);
    page.input('outflow', 100);
    page.input('minutes', 100);
    if (reset === 'reset') page.node('reset').dispatch('click');
    else page.clickPreset(reset);
    assert.equal(Number(page.node('inflow-range').max), 10);
    assert.equal(Number(page.node('outflow-range').max), 10);
    assert.equal(Number(page.node('minutes-range').max), 40);
  }
});

function displayedEquation(page) {
  const rendered = page.node('equation-value').textContent;
  const parts = rendered.match(/^(.+) L \+ \((.+) − (.+)\) L\/min × (.+) min ([=≈]) (.+) L$/);
  assert.ok(parts, `Expected a readable equation with explicit units, received: ${rendered}`);
  const number = (value) => Number(value.replaceAll(',', ''));
  return {
    initial: number(parts[1]), inflow: number(parts[2]), outflow: number(parts[3]),
    minutes: number(parts[4]), operator: parts[5], result: number(parts[6]), rendered,
  };
}

test('the visible equation preserves near-equal flows instead of making their difference zero', () => {
  const page = interfaceFixture();
  page.input('inflow', 3.1234);
  page.input('outflow', 3.1233);
  page.input('minutes', 100000);
  const equation = displayedEquation(page);
  assert.equal(equation.inflow, 3.1234);
  assert.equal(equation.outflow, 3.1233);
  const left = equation.initial + (equation.inflow - equation.outflow) * equation.minutes;
  assert.ok(Math.abs(left - 30) < 1e-9, equation.rendered);
  assert.equal(equation.result, 30);
  assert.equal(equation.operator, '≈', 'A rounded computed result must be marked as approximate.');
});

test('small decimal operands keep enough precision for the displayed relationship to hold', () => {
  const page = interfaceFixture();
  page.input('inflow', 0.00000031234);
  page.input('outflow', 0.00000031233);
  page.input('minutes', 1000000000);
  const equation = displayedEquation(page);
  assert.equal(equation.inflow, 0.00000031234);
  assert.equal(equation.outflow, 0.00000031233);
  const left = equation.initial + (equation.inflow - equation.outflow) * equation.minutes;
  assert.ok(Math.abs(left - 20.01) < 1e-9, equation.rendered);
  assert.equal(equation.result, 20.01);
});

test('a rounded result is distinguished from the exact time operand', () => {
  const page = interfaceFixture();
  page.input('inflow', 1);
  page.input('outflow', 0);
  page.input('minutes', 0.12345);
  const equation = displayedEquation(page);
  assert.equal(equation.minutes, 0.12345);
  assert.equal(equation.result, 20.123);
  assert.equal(equation.operator, '≈');
  assert.ok(page.node('volume-output').textContent.startsWith('≈'));
});

test('boundary equations preserve the calculated boundary time rather than rounding an operand', () => {
  const page = interfaceFixture();
  page.input('inflow', 5);
  page.input('outflow', 2);
  page.input('minutes', 10);
  const equation = displayedEquation(page);
  assert.equal(equation.minutes, 20 / 3);
  const left = equation.initial + (equation.inflow - equation.outflow) * equation.minutes;
  assert.ok(Math.abs(left - 40) < 1e-12, equation.rendered);
  assert.equal(equation.result, 40);
});
