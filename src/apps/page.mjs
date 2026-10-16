// Sprint 2 UND-7 (ARCH §4, ADR-0009): the app hooks a page sketch gets when
// it gives none. The page target's view is what a person sees (`aria.mjs`);
// here the controls a person could choose become the moves on offer, named
// by kind and visible label (`button:Pro (paid monthly)`). Where the part
// ends is the part's to say, with the `showing` guard.

const VERBS = { button: 'press', link: 'follow', checkbox: 'tick', radio: 'pick' };

/**
 * One option per control. A list option names its list too, so the same
 * label in two lists stays two moves.
 */
function optionFor(control) {
  if (control.role === 'option') {
    return { id: `option:${control.list}=${control.name}`, what: `pick ${control.name} from ${control.list}`, value: control.name, control };
  }
  return { id: `${control.role}:${control.name}`, what: `${VERBS[control.role] ?? 'use'} ${control.name}`, value: control.name, control };
}

export const pageApp = {
  phase: (view) => (view.controls.length > 0 ? 'asking' : 'waiting'),
  project: (view) => ({ page: view.title, says: view.text.slice(-20), controls: view.controls }),
  options: (state) => state.controls.map((control) => optionFor(control)),
  act({ control: { role, name, list } }) {
    return { actions: [{ role, name, ...(list !== undefined && { list }) }] };
  },
};
