// The decisions panel: the run's decisions with their options, what removed or held each one, and the pick. The server
// reads them from the run's log (src/dashboard/replay.py); this script draws them as text and, while a replay is open, moves
// the replay's cursor to a decision. It shares page.js's helpers ($, make, state, getJson) and replay.js's replay and replayTo.
'use strict';

const decisionsView = { list: [] };

function replayIsOpen() {
  return typeof replay !== 'undefined' && replay.open;
}

function removedText(removedBy) {
  if (!removedBy) return '';
  return removedBy === 'shortlist' ? 'held back by the shortlist' : `removed by ${removedBy}`;
}

function weightText(weight) {
  return typeof weight === 'number' ? String(Number(weight.toPrecision(3))) : '?';
}

function optionRow(option, pick) {
  const picked = option.name !== null && option.name === pick;
  const parts = [`${option.name ?? '?'}`, `weight ${weightText(option.weight)}`];
  const removed = removedText(option.removed_by);
  if (removed) parts.push(removed);
  if (picked) parts.push('picked');
  return make('div', { class: `option-row${picked ? ' picked' : ''}` }, parts.join(' · '));
}

function decisionBlock(each) {
  const jump = make('button', { type: 'button', class: 'find-button jump' }, 'SHOW IN REPLAY');
  jump.addEventListener('click', () => replayTo(each.index + 1));
  const headline = `${each.stage ?? '?'} · ${each.row ?? '?'} · ${each.dimension ?? '?'} → ${each.pick ?? '?'} (${each.probability ?? '?'})`;
  const body = [make('div', { class: 'jev-level' }, `event ${each.index + 1} in the log`), ...each.options.map((option) => optionRow(option, each.pick))];
  if (each.missing.length) body.push(make('div', { class: 'decision-note jev-level' }, `this decision's log line lacks ${each.missing.join(', ')}`));
  return make('details', { class: 'jev-read decision-read' }, make('summary', {}, headline), ...body, jump);
}

// The jump buttons work only while a replay is open: there is no cursor to move otherwise.
function drawJumps() {
  const open = replayIsOpen();
  for (const button of document.querySelectorAll('#decisions-list .jump')) {
    button.disabled = !open;
    button.title = open ? 'Move the replay to this decision' : 'open a replay (REPLAY above the log) to move to a decision';
  }
}

function drawDecisions(list, problem) {
  decisionsView.list = list;
  $('decisions-summary').textContent = list.length ? `DECISIONS · ${list.length}` : 'DECISIONS';
  const box = $('decisions-list');
  if (problem) box.replaceChildren(make('div', { class: 'jev-level' }, `the decisions cannot be read: ${problem}`));
  else if (!list.length) box.replaceChildren(make('div', { class: 'jev-level' }, 'this run made no decisions'));
  else box.replaceChildren(...list.map(decisionBlock));
  drawJumps();
}

async function loadDecisions(id) {
  const found = await getJson(`api/runs/${id}/decisions`);
  if (state.chosen !== id) return;
  if (Array.isArray(found)) drawDecisions(found, '');
  else drawDecisions([], found?.problem ?? 'the console could not read them');
}

// A decision in the printer moves the replay's cursor to it, too.
$('paper').addEventListener('click', (event) => {
  const row = event.target.closest?.('.line.decision');
  if (row && replayIsOpen()) replayTo(Number(row.dataset.index) + 1);
});
