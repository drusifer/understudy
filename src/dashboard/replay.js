// The replay bar: play a finished run's story back from its log. The server works out the run as it was after event N
// (src/dashboard/replay.py); this script only asks for a position, draws the answer with the page's own drawing and times PLAY.
// It shares page.js's helpers ($, state, getJson, choose, drawStatus, renderPaper, setFailures).
'use strict';

const replay = { open: false, at: 0, of: 0, timer: null, live: null, ticket: 0, busy: false };
const REPLAY_ENDED = ['done', 'failed', 'stopped', 'stalled']; // a run that is still going cannot be replayed
const replayMs = () => window.understudyReplayMs ?? 400;

function replaySay(text, kind = '') {
  const box = $('replay-message');
  box.textContent = text;
  box.className = `start-message ${kind}`;
}

function replayEnable(on) {
  for (const id of ['replay-back', 'replay-play', 'replay-step', 'replay-scrub']) $(id).disabled = !on;
}

// The REPLAY button follows the chosen run: only a run that has ended can be replayed.
function afterReplayStatus(run) {
  if (replay.open) return;
  const ended = REPLAY_ENDED.includes(run.state);
  $('replay-open').disabled = !ended;
  $('replay-open').title = ended ? 'Play this run back from its log' : 'this run is still going; replay it when it has ended';
}

async function openReplay() {
  if (!state.chosen || replay.open) return;
  const id = state.chosen;
  $('replay').hidden = false;
  replayEnable(false);
  replaySay('');
  const info = await getJson(`api/runs/${id}/replay`);
  if (!info || info.problem || !info.events) {
    replaySay(info?.problem ?? 'this run cannot be replayed', 'problem');
    return;
  }
  replay.live = await getJson(runUrl(id));
  if (!replay.live) return;
  replay.open = true;
  replay.of = info.events;
  $('replay-scrub').max = String(info.events);
  replayEnable(true);
  $('replay-open').disabled = true;
  await replayTo(0);
}

function failuresIn(lines) {
  return lines.flatMap((each, index) => (each.tone === 'held' ? [index] : []));
}

// The run as it was after `at` events, drawn the way a live run is, with the status saying REPLAY.
async function replayTo(target) {
  if (!replay.open) return;
  const at = Math.max(0, Math.min(replay.of, Number(target) || 0));
  const ticket = ++replay.ticket;
  const frame = await getJson(runUrl(state.chosen, '/replay', `at=${at}`));
  if (ticket !== replay.ticket || !replay.open) return; // a newer position was asked for, or the replay was closed
  if (!frame || frame.problem) {
    replaySay(frame?.problem ?? 'could not read the run', 'problem');
    stopReplayPlay();
    return;
  }
  replay.at = frame.at;
  $('replay-scrub').value = String(frame.at);
  const words = `event ${frame.at} of ${frame.of}`;
  $('replay-at').textContent = words;
  $('replay-scrub').setAttribute('aria-valuetext', words);
  $('replay-back').disabled = frame.at <= 0;
  $('replay-step').disabled = frame.at >= frame.of;
  const live = replay.live;
  const run = {
    ...live, ...frame, id: live.id, sketch: live.sketch, mode: live.mode, summary: live.summary,
    spending: frame.at === frame.of ? live.spending : null, failures: failuresIn(frame.lines), count: frame.at,
  };
  const chosenState = state.chosenState;
  state.lines = run.lines;
  setFailures(run.failures);
  renderPaper();
  drawStatus(run);
  state.chosenState = chosenState; // the controls keep following the real run, not the replay
  if (typeof drawButtons === 'function') drawButtons();
  $('status-text').textContent = 'REPLAY';
  $('status-lamp').className = 'lamp standby';
  $('printer-state').textContent = 'REPLAY';
}

function stopReplayPlay() {
  if (replay.timer) clearInterval(replay.timer);
  if (replay.timer) replay.ticket += 1; // a frame the timer already asked for must not land after PAUSE
  replay.timer = null;
  $('replay-play').textContent = 'PLAY';
}

function startReplayPlay() {
  if (replay.at >= replay.of) replay.at = 0; // from the end, play starts again from the beginning
  $('replay-play').textContent = 'PAUSE';
  replay.timer = setInterval(async () => {
    if (replay.busy) return;
    replay.busy = true;
    await replayTo(replay.at + 1);
    replay.busy = false;
    if (replay.at >= replay.of) stopReplayPlay();
  }, replayMs());
}

// Close the bar. `restore` draws the run as it is now (LIVE); choosing another run closes it without redrawing.
function endReplay(restore = true) {
  stopReplayPlay();
  const wasOpen = !$('replay').hidden;
  replay.open = false;
  replay.ticket += 1;
  $('replay').hidden = true;
  replaySay('');
  if (wasOpen && restore && state.chosen) choose(state.chosen);
}

$('replay-open').addEventListener('click', openReplay);
$('replay-live').addEventListener('click', () => endReplay(true));
$('replay-step').addEventListener('click', () => { stopReplayPlay(); replayTo(replay.at + 1); });
$('replay-back').addEventListener('click', () => { stopReplayPlay(); replayTo(replay.at - 1); });
$('replay-play').addEventListener('click', () => (replay.timer ? stopReplayPlay() : startReplayPlay()));
$('replay-scrub').addEventListener('input', () => { stopReplayPlay(); replayTo($('replay-scrub').value); });
