// Sprint 2 UND-7 (ARCH §4, ADR-0007): a page as a person meets it.
//
// Playwright's `ariaSnapshot()` prints the accessibility tree as indented
// lines - `- button "Free"`, `- paragraph: Which plan?`, `- option "Large"`
// under a `- combobox "Size":`. Hidden elements are not in it; disabled
// ones say `[disabled]`. This reads those lines into the page's title, the
// text a person reads, and the controls a person could choose.

/**
 * The roles a person chooses with a click (or a pick from a list).
 * Text boxes need text to type, which is out of scope (sprint 2).
 */
const CHOOSABLE = new Set(['button', 'link', 'checkbox', 'radio', 'option']);
const LISTS = new Set(['combobox', 'listbox']);
const LINE = /^(\s*)- ([a-z]+)(?: "((?:[^"\\]|\\.)*)")?((?: \[[^\]]+\])*)(?::(?: (.*))?)?$/;

const unescape = (text) => text.replaceAll(/\\(.)/g, '$1');
const unquote = (text) => (text.startsWith('"') && text.endsWith('"') ? unescape(text.slice(1, -1)) : text);

/**
 * The control a line describes, or `null` when there is nothing to choose
 * (not a choosable role, no name, or disabled).
 */
function controlOf({ role, name, attributes, list }) {
  if (!name || !CHOOSABLE.has(role) || attributes.includes('[disabled]')) return null;
  return {
    role, name,
    ...(role === 'option' && list !== undefined && { list }),
    ...(attributes.includes('[checked]') && { checked: true }),
    ...(attributes.includes('[selected]') && { selected: true }),
  };
}

/**
 * The text a line shows a reader: a heading's name, or the inline text
 * after the colon (`- paragraph: Which plan?`).
 */
function textOf({ role, name, inline }) {
  if (role === 'heading') return name;
  return inline ? unquote(inline) : null;
}

/**
 * @param {string} snapshot `ariaSnapshot()` output
 * @returns {{ title: string|null, text: string[], controls: Array<{ role: string, name: string,
 *   list?: string, checked?: true, selected?: true }> }}
 */
export function parseSnapshot(snapshot) {
  const view = { title: null, text: [], controls: [] };
  const lists = []; // [indent, name] of the lists we are inside
  const lines = snapshot.split('\n').map((line) => readLine(line)).filter(Boolean);
  for (const line of lines) {
    const list = insideList(lists, line);
    const text = textOf(line);
    if (text) view.text.push(text);
    if (line.role === 'heading' && line.name) view.title ??= line.name;
    const control = controlOf({ ...line, list });
    if (control) view.controls.push(control);
  }
  return view;
}

/**
 * One snapshot line as `{ indent, role, name, attributes, inline }`, or `null`.
 */
function readLine(line) {
  const match = LINE.exec(line);
  if (!match) return null;
  const [, indent, role, quotedName, attributes, inline] = match;
  return { indent: indent.length, role, name: quotedName === undefined ? null : unescape(quotedName), attributes, inline };
}

/**
 * Keeps `lists` to the lists that enclose `line` (by indentation), adds
 * `line` when it is one, and names the innermost list `line` is inside.
 */
function insideList(lists, line) {
  while (lists.length > 0 && lists.at(-1)[0] >= line.indent) lists.pop();
  const enclosing = lists.at(-1)?.[1];
  if (LISTS.has(line.role)) lists.push([line.indent, line.name]);
  return enclosing;
}
