// A decision line in the printer moves the open replay's cursor to it. (A blend's decisions are drawn as weight bars in the
// beat box, src/dashboard/box.js.) It shares page.js's helper ($) and replay.js's replay and replayTo.
'use strict';

$('paper').addEventListener('click', (event) => {
  const row = event.target.closest?.('.line.decision');
  if (row && typeof replay !== 'undefined' && replay.open) replayTo(Number(row.dataset.index) + 1);
});
