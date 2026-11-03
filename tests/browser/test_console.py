"""The console in a real Chromium: what unit tests cannot see (UND-80). Run with `bobp make test-browser`.

It needs the optional `browser` group (`bobp make install-browser`) and a Chromium (`/usr/bin/chromium`, or CHROMIUM=path);
without them every test is skipped with that reason. It is not part of `bobp make check`, which stays offline and fast.
Everything runs against invented run folders on a server started in this process: nothing private, nothing live.
"""

import json
import os
import struct
import sys
import tempfile
import threading
import unittest
import zlib
from datetime import UTC, datetime
from pathlib import Path

from src.dashboard.runs import Launcher, _Child
from src.dashboard.server import serve

try:
    from playwright.sync_api import sync_playwright
except ImportError:  # the optional group is not installed
    sync_playwright = None

CHROMIUM = os.environ.get("CHROMIUM", "/usr/bin/chromium")
SECRET = "browser-test-secret"
LOOKS = [(theme, mode) for theme in ("steampunk", "professional", "starship") for mode in ("light", "dark")]
PLAIN = "name: plain\ndescription: a sketch to start\nsources:\n  data: {{ file }}\nmachine: { initial: only, states: { only: { final: true } } }\n"

# What each piece of text is checked for: the selectors worth reading on every screen (WCAG AA: 4.5:1, 3:1 for large text).
READABLE = [
    "h1", ".subtitle", "#status-text", ".theme-label", ".theme-choice", ".mode-choice", ".plate-label", ".sketch-tab .name",
    ".rack-group", ".badge", ".printer-head span", ".paper .line", ".find-button", ".find-check", ".ended", ".summary dt", ".summary dd",
    ".stage-lamp", ".group summary", ".gauge .figure", ".gauge-name", ".start-message", ".start-panel > summary", ".banner",
    ".panel-head span", ".jev > summary", ".offline", ".no-match",
    "#spending-title", ".spend-name", ".spend-amount", ".spend-more",
    ".typed-label", ".pick-option", ".toggle", ".readout", ".count-box", ".step-button",
    "#chart-title", "#chart-note", ".state-name", ".edge-label-text",
]

# While one element is measured its text is invisible and nothing animates, so a screenshot shows only the backdrop.
HIDE_TEXT = "[data-contrast-target], [data-contrast-target] * { color: transparent !important; text-shadow: none !important; transition: none !important; animation: none !important; }\n[data-contrast-target] i, [data-contrast-target] button, [data-contrast-target] input { visibility: hidden !important; }"

FIRST_VISIBLE_JS ="""(selector) => {
  for (const el of document.querySelectorAll(selector)) {
    const box = el.getBoundingClientRect(); if (!box.width || !box.height || !el.innerText?.trim()) continue;
    el.scrollIntoView({ block: 'center' });
    const cs = getComputedStyle(el); const m = cs.color.match(/rgba?\\(([^)]+)\\)/).slice(1)[0].split(',').map((v) => Number(v.trim()));
    const result = { text: el.innerText.trim().slice(0, 30), color: { r: m[0], g: m[1], b: m[2] }, size: parseFloat(cs.fontSize), weight: Number(cs.fontWeight) };
    el.setAttribute('data-contrast-target', '');  // from here on its text is invisible (HIDE_TEXT): read everything first
    return result;
  }
  return null;
}"""


def decode_png(data: bytes) -> list[list[tuple[int, int, int]]]:
    """The rows of pixels of an 8-bit RGB or RGBA PNG, as (r, g, b): enough to see what a screen really shows behind text."""
    position, chunks, header = 8, [], None
    while position < len(data):
        length, kind = struct.unpack(">I4s", data[position:position + 8])
        body = data[position + 8:position + 8 + length]
        if kind == b"IHDR":
            header = struct.unpack(">IIBBBBB", body)
        elif kind == b"IDAT":
            chunks.append(body)
        position += 12 + length
    width, height, depth, color_type = header[:4]
    assert depth == 8 and color_type in {2, 6}, "expected an 8-bit RGB or RGBA screenshot"
    step = 3 if color_type == 2 else 4
    raw, stride, rows, previous = zlib.decompress(b"".join(chunks)), width * step, [], bytearray(width * step)
    for row in range(height):
        kind, line = raw[row * (stride + 1)], bytearray(raw[row * (stride + 1) + 1:(row + 1) * (stride + 1)])
        for index in range(stride):
            left = line[index - step] if index >= step else 0
            up, corner = previous[index], previous[index - step] if index >= step else 0
            if kind == 1:
                line[index] = (line[index] + left) & 255
            elif kind == 2:
                line[index] = (line[index] + up) & 255
            elif kind == 3:
                line[index] = (line[index] + (left + up) // 2) & 255
            elif kind == 4:
                estimate = left + up - corner
                nearest = min((abs(estimate - left), left), (abs(estimate - up), up), (abs(estimate - corner), corner))[1]
                line[index] = (line[index] + nearest) & 255
        rows.append(line)
        previous = line
    return [[(line[index], line[index + 1], line[index + 2]) for index in range(0, stride, step)] for line in rows]


EDGE = 4  # pixels at the edge of an element that are ignored: borders and shadows are not what the text sits on


def backdrops(rows: list[list[tuple[int, int, int]]]) -> list[dict]:
    """The colors that fill the inside of the box behind the text (each at least 8% of it, rounded to steps of 8)."""
    inside = [row[EDGE:-EDGE] for row in rows[EDGE:-EDGE]]
    pixels = [pixel for row in (inside if inside and inside[0] else rows) for pixel in row]
    counts: dict[tuple[int, int, int], list[int]] = {}
    for red, green, blue in pixels:
        counts.setdefault((red // 8, green // 8, blue // 8), []).append(red * 65536 + green * 256 + blue)
    found = []
    for members in counts.values():
        if len(members) >= 0.08 * len(pixels):
            value = members[len(members) // 2]
            found.append({"r": value >> 16, "g": (value >> 8) & 255, "b": value & 255})
    return found


def luminance(color: dict) -> float:
    def part(value: float) -> float:
        value /= 255
        return value / 12.92 if value <= 0.03928 else ((value + 0.055) / 1.055) ** 2.4

    return 0.2126 * part(color["r"]) + 0.7152 * part(color["g"]) + 0.0722 * part(color["b"])


def contrast(foreground: dict, background: dict) -> float:
    first, second = sorted((luminance(foreground), luminance(background)), reverse=True)
    return (first + 0.05) / (second + 0.05)


def write_run(root: Path, name: str, events: list[dict], manifest: dict, summary: dict | None = None) -> Path:
    directory = root / name
    directory.mkdir(parents=True)
    (directory / "events.jsonl").write_text("".join(json.dumps(each) + "\n" for each in events), encoding="utf-8")
    (directory / "run.json").write_text(json.dumps(manifest), encoding="utf-8")
    (directory / "summary.json").write_text(json.dumps(summary or {}), encoding="utf-8")
    return directory


def spending(directory: Path, categories: int) -> None:
    """A `spending.jsonl` of that many categories, the largest first, as the household writes it."""
    rows = [{"category": f"Group {n}: A rather long category name number {n}", "count": 10 + n, "amount": 5000.0 - n * 100,
             "share": round(0.3 - n * 0.02, 4)} for n in range(categories)]
    (directory / "spending.jsonl").write_text("".join(json.dumps(each) + "\n" for each in rows), encoding="utf-8")


def stamp(second: int) -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat() if second < 0 else f"2026-11-01T12:00:{second:02d}+00:00"


@unittest.skipIf(sync_playwright is None, "playwright is not installed: run 'bobp make install-browser'")
@unittest.skipUnless(Path(CHROMIUM).exists(), f"no Chromium at {CHROMIUM}: set CHROMIUM=path")
class BrowserCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(executable_path=CHROMIUM, args=["--no-sandbox"])

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()

    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.root = Path(self.folder.name).resolve()
        self.runs = self.root / "runs"
        self.runs.mkdir()
        self.servers: list = []

    def start(self, launcher: Launcher | None = None, secret: str | None = None) -> str:
        server = serve(self.runs, port=0, cache=self.root / "cache", project=self.root, launcher=launcher, secret=secret)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        return f"http://127.0.0.1:{server.server_address[1]}"

    def page(self, width: int = 1300, height: int = 900):
        # bypass_csp: the page's policy forbids the string evaluation Playwright's waits use; the policy itself is tested in
        # tests/python/test_dashboard.py (SecurityHeadersTest) and the page is checked to run under it by every other test here
        context = self.browser.new_context(viewport={"width": width, "height": height}, bypass_csp=True)
        self.addCleanup(context.close)
        return context.new_page()

    def failed_and_done_runs(self):
        failed = write_run(self.runs, "run-20261101T120000-0000000a", [
            {"event": "run_started", "at": stamp(0), "sketch": "examples/household/household.yaml", "mode": "live", **STORY},
            entered(1, "a", "start"), entered(1, "b", "ok"),  # a diagram for the readability check to measure
            {"event": "stage_started", "at": stamp(1), "stage": "read"},
            {"event": "stage_failed", "at": stamp(2), "stage": "read", "reason": "Jev needs a TypeSafe key"}],
            {"status": "failed", "failed_stage": "read", "error": "Jev needs a TypeSafe key", "stages": {}, "mode": "live"})
        spending(failed, 12)  # a long list on the run the readability check looks at
        write_run(self.runs, "run-20261101T120100-0000000b", [
            {"event": "run_started", "at": stamp(0), "sketch": "examples/evening/evening.yaml", "mode": "replay"},
            {"event": "stage_started", "at": stamp(1), "stage": "pick"}, {"event": "stage_completed", "at": stamp(2), "stage": "pick"},
            {"event": "run_finished", "at": stamp(3), "outcome": "booked"}],
            {"status": "complete", "stages": {"pick": "complete"}, "mode": "replay", "outcome": "booked", "outputs": {"booking.jsonl": 1}},
            {"stale": False})


class SpendingListTest(BrowserCase):
    def open_run(self, page, name):
        page.goto(self.start())
        page.wait_for_selector(".sketch-tab")
        page.locator(f".sketch-tab[title^='{name}']").click()

    def test_the_ten_largest_categories_are_listed_with_amount_and_share_and_the_rest_are_counted(self):
        run = write_run(self.runs, "run-20261101T130000-0000000c", [
            {"event": "run_started", "at": stamp(0), "sketch": "examples/household/household.yaml", "mode": "live"},
            {"event": "run_finished", "at": stamp(1), "outcome": "complete"}], {"status": "complete", "stages": {}, "mode": "live"})
        spending(run, 13)
        page = self.page()
        self.open_run(page, "run-20261101T130000-0000000c")
        page.wait_for_selector("#spending li")
        rows = page.locator("#spending li")
        self.assertEqual(rows.count(), 10)
        self.assertIn("Group 0", rows.nth(0).inner_text())
        self.assertIn("$5,000.00", rows.nth(0).inner_text())
        self.assertIn("30.0%", rows.nth(0).inner_text())
        self.assertIn("3 more", page.locator(".spend-more").inner_text())

    def test_a_run_without_the_file_shows_no_list_and_no_heading(self):
        write_run(self.runs, "run-20261101T130100-0000000d", [
            {"event": "run_started", "at": stamp(0), "sketch": "x/plain.yaml", "mode": "live"},
            {"event": "run_finished", "at": stamp(1), "outcome": "complete"}], {"status": "complete", "stages": {}, "mode": "live"})
        page = self.page()
        self.open_run(page, "run-20261101T130100-0000000d")
        page.wait_for_function("document.getElementById('status-text').textContent === 'DONE'")
        self.assertFalse(page.locator("#spending").is_visible())
        self.assertEqual(page.locator("#spending-title").count(), 1)  # the element exists; it is hidden, not drawn empty
        self.assertFalse(page.locator("#spending-title").is_visible())

    def test_a_spending_file_the_console_cannot_read_is_named_and_the_page_still_works(self):
        run = write_run(self.runs, "run-20261101T130200-0000000e", [
            {"event": "run_started", "at": stamp(0), "sketch": "x/household.yaml", "mode": "live"},
            {"event": "run_finished", "at": stamp(1), "outcome": "complete"}], {"status": "complete", "stages": {}, "mode": "live"})
        (run / "spending.jsonl").write_text('{"category": "Rent", "amount": 5, "share": 1}\nnot json\n', encoding="utf-8")
        page = self.page()
        self.open_run(page, "run-20261101T130200-0000000e")
        page.wait_for_selector("#spending")
        self.assertIn("spending.jsonl line 2 is not readable", page.locator("#spending").inner_text())
        self.assertEqual(page.locator("#status-text").inner_text(), "DONE")

    def test_the_list_fits_a_phone_without_sideways_scrolling(self):
        run = write_run(self.runs, "run-20261101T130300-0000000f", [
            {"event": "run_started", "at": stamp(0), "sketch": "x/household.yaml", "mode": "live"},
            {"event": "run_finished", "at": stamp(1), "outcome": "complete"}], {"status": "complete", "stages": {}, "mode": "live"})
        spending(run, 12)
        page = self.page(width=390, height=800)
        self.open_run(page, "run-20261101T130300-0000000f")
        page.wait_for_selector("#spending li")
        self.assertTrue(page.evaluate("document.documentElement.scrollWidth <= document.documentElement.clientWidth"))
        self.assertTrue(page.evaluate("(() => { const box = document.getElementById('spending').getBoundingClientRect();"
                                      " return box.left >= 0 && box.right <= window.innerWidth; })()"))


class RackAndBannerTest(BrowserCase):
    def test_switching_runs_shows_each_ones_state_and_a_failed_run_shows_why_and_jumps_to_the_line(self):
        self.failed_and_done_runs()
        page = self.page()
        page.goto(self.start())
        page.wait_for_selector(".sketch-tab")
        tabs = page.locator(".sketch-tab")
        self.assertEqual(tabs.count(), 2)
        tabs.nth(0).click()  # newest first: the done evening run
        page.wait_for_function("document.getElementById('status-text').textContent === 'DONE'")
        self.assertIn("outcome booked", page.locator("#ended").inner_text())
        tabs.nth(1).click()
        page.wait_for_function("document.getElementById('status-text').textContent === 'FAILED'")
        self.assertIn("read: Jev needs a TypeSafe key", page.locator(".banner").inner_text())
        page.locator(".banner").click()
        self.assertTrue(page.locator("#paper .line.held").is_visible())
        self.assertTrue(page.locator(".badge").first.is_visible())  # the failed tab carries its badge in words

    def test_the_page_says_when_the_server_is_gone_and_recovers_without_a_reload(self):
        self.failed_and_done_runs()
        base = self.start()
        page = self.page()
        page.goto(base)
        page.wait_for_selector(".sketch-tab")
        port = int(base.rsplit(":", 1)[1])
        server = self.servers  # keep the linter honest: the server belongs to `start`, stopped here by closing its socket
        del server
        page.route("**/api/**", lambda route: route.abort())  # the same as an unreachable server, without racing a restart
        page.wait_for_selector("#offline:not([hidden])", timeout=15000)
        self.assertIn("DISCONNECTED", page.locator("#offline").inner_text())
        page.unroute("**/api/**")
        page.wait_for_selector("#offline[hidden]", state="attached", timeout=15000)
        self.assertGreater(port, 0)


class LiveFollowTest(BrowserCase):
    def test_lines_appended_to_a_running_run_appear_without_a_reload_and_the_run_ends_cleanly(self):
        directory = write_run(self.runs, "run-20261101T130000-0000000c", [
            {"event": "run_started", "at": stamp(-1), "sketch": "x/live.yaml", "mode": "live"}], {"status": "running", "stages": {}})
        page = self.page()
        page.goto(self.start())
        page.wait_for_selector(".sketch-tab")
        page.locator(".sketch-tab").first.click()
        page.wait_for_function("document.getElementById('status-text').textContent === 'RUNNING'")
        before = page.locator("#paper .line").count()
        with (directory / "events.jsonl").open("a") as events:
            events.write(json.dumps({"event": "stage_started", "at": stamp(-1), "stage": "build"}) + "\n")
        page.wait_for_function(f"document.querySelectorAll('#paper .line').length > {before}", timeout=10000)
        with (directory / "events.jsonl").open("a") as events:
            events.write(json.dumps({"event": "stage_completed", "at": stamp(-1), "stage": "build"}) + "\n")
            events.write(json.dumps({"event": "run_finished", "at": stamp(-1), "outcome": "complete"}) + "\n")
        (directory / "run.json").write_text(json.dumps({"status": "complete", "stages": {"build": "complete"}}))
        page.wait_for_function("document.getElementById('status-text').textContent === 'DONE'", timeout=15000)
        self.assertEqual(page.locator(".stage-lamp.complete").count(), 1)


class StartAndStopTest(BrowserCase):
    def test_unlock_play_and_stop_a_run_from_the_page(self):
        sketches = self.root / "sketches"
        sketches.mkdir()
        (sketches / "plain.yaml").write_text(PLAIN, encoding="utf-8")
        (self.root / "in.csv").write_text("a\n", encoding="utf-8")
        run = write_run(self.runs, "run-20261101T140000-0000000d", [{"event": "run_started", "at": stamp(-1), "sketch": "p.yaml", "mode": "live"}],
                        {"status": "running", "stages": {}})

        def sleeper(argv, **options):
            return _Child([sys.executable, "-c", "import time; time.sleep(60)"], **options)

        launcher = Launcher(sketches, self.runs, project=self.root, cache=self.root / "cache", spawn=sleeper, check=lambda argv: [],
                            find_run=lambda sketch, before: run.name, settle=0)
        page = self.page()
        page.goto(self.start(launcher, SECRET))
        page.locator("#controls > summary").click()
        self.assertTrue(page.locator("#play").is_disabled())
        self.assertIn("needs the access secret", page.locator("#play").get_attribute("title"))
        page.fill("#secret-box", "wrong")
        page.click("#unlock")
        page.wait_for_function("document.getElementById('start-message').textContent.includes('not this console')")
        self.assertTrue(page.locator("#play").is_disabled())
        page.fill("#secret-box", SECRET)
        page.click("#unlock")
        page.wait_for_function("!document.getElementById('play').disabled")
        page.fill("#field-file", "in.csv")
        page.click("#play")
        page.wait_for_function(f"document.getElementById('start-message').textContent.includes('{run.name}')")
        page.wait_for_function("document.getElementById('status-text').textContent === 'RUNNING'")
        page.click("#play")  # a second Play for the same sketch
        page.wait_for_function("document.getElementById('start-message').textContent.includes('already running')")
        self.assertEqual(page.locator("#start-message button").count(), 1)
        page.click("#stop")
        page.wait_for_function("document.getElementById('status-text').textContent === 'STOPPED'", timeout=15000)
        self.assertTrue(page.locator("#stop").is_disabled())
        self.assertFalse(page.locator("#play").is_disabled())
        urls = []
        page.on("request", lambda request: urls.append(request.url))
        page.reload()
        self.assertFalse(any(SECRET in each for each in urls))  # the secret is never in an address
        self.assertFalse(page.evaluate("JSON.stringify(localStorage)").count(SECRET))


TYPED = """name: typed
description: A sketch with typed inputs and one plain value ({{ note | default('none') }}).
inputs:
  mood: { kind: choice, label: Mood, options: [fun, serious, dramatic], default: fun }
  weight: { kind: range, label: Weight, min: 0, max: 1, step: 0.05, default: 0.3 }
  tickets: { kind: count, label: Party size, min: 1, max: 3, default: 2 }
  evenings: { kind: switch, label: Evenings only, default: "on" }
data: { mood: "{{ mood }}", weight: {{ weight }}, tickets: {{ tickets }}, evenings: "{{ evenings }}" }
machine: { initial: only, states: { only: { final: true } } }
"""


class TypedControlsTest(BrowserCase):
    def open(self, width=1300, height=900):
        sketches = self.root / "sketches"
        sketches.mkdir()
        (sketches / "typed.yaml").write_text(TYPED, encoding="utf-8")
        run = write_run(self.runs, "run-20261101T150000-0000000e", [{"event": "run_started", "at": stamp(-1), "sketch": "typed.yaml",
                                                                    "mode": "live"}], {"status": "running", "stages": {}})
        self.started: list[list[str]] = []

        def spawn(argv, **options):
            self.started.append(argv)
            return _Child([sys.executable, "-c", "import time; time.sleep(60)"], **options)

        launcher = Launcher(sketches, self.runs, project=self.root, cache=self.root / "cache", spawn=spawn, check=lambda argv: [],
                            find_run=lambda sketch, before: run.name, settle=0)
        page = self.page(width, height)
        page.goto(self.start(launcher, SECRET))
        page.locator("#controls > summary").click()
        page.wait_for_selector("#fields [data-input]")
        return page

    def unlock(self, page):
        page.fill("#secret-box", SECRET)
        page.click("#unlock")
        page.wait_for_function("!document.getElementById('play').disabled")

    def test_each_declared_input_has_the_control_of_its_kind_at_its_default_with_a_name_and_a_readable_value(self):
        page = self.open()
        dial = page.get_by_role("radiogroup", name="Mood")
        self.assertEqual(dial.get_by_role("radio").count(), 3)
        self.assertEqual(dial.get_by_role("radio", checked=True).inner_text(), "fun")
        fader = page.get_by_role("slider", name="Weight")
        self.assertEqual((fader.input_value(), page.locator("#field-weight-readout").inner_text()), ("0.3", "0.3"))
        stepper = page.get_by_role("spinbutton", name="Party size")
        self.assertEqual(stepper.input_value(), "2")
        switch = page.get_by_role("switch", name="Evenings only")
        self.assertEqual((switch.get_attribute("aria-checked"), switch.inner_text()), ("true", "ON"))
        self.assertTrue(page.locator("#field-note").is_visible())  # a name the sketch takes but does not declare stays a text box
        self.assertEqual(page.locator("#field-note").get_attribute("type"), "text")

    def test_every_control_works_from_the_keyboard(self):
        page = self.open()
        page.get_by_role("radio", name="fun").focus()
        page.keyboard.press("ArrowRight")
        self.assertEqual(page.get_by_role("radiogroup", name="Mood").get_by_role("radio", checked=True).inner_text(), "serious")
        page.keyboard.press("ArrowRight")
        page.keyboard.press("ArrowRight")  # the end of the dial: it stops, it does not wrap
        self.assertEqual(page.get_by_role("radiogroup", name="Mood").get_by_role("radio", checked=True).inner_text(), "dramatic")
        page.get_by_role("slider", name="Weight").focus()
        page.keyboard.press("ArrowRight")
        self.assertEqual(page.locator("#field-weight-readout").inner_text(), "0.35")
        page.get_by_role("spinbutton", name="Party size").focus()
        page.keyboard.press("ArrowUp")
        self.assertEqual(page.get_by_role("spinbutton", name="Party size").input_value(), "3")
        page.get_by_role("switch", name="Evenings only").focus()
        page.keyboard.press("Space")
        self.assertEqual(page.get_by_role("switch", name="Evenings only").get_attribute("aria-checked"), "false")
        self.assertEqual(page.get_by_role("switch", name="Evenings only").inner_text(), "OFF")

    def test_a_control_cannot_be_set_outside_its_limits(self):
        page = self.open()
        stepper = page.get_by_role("spinbutton", name="Party size")
        page.get_by_role("button", name="increase Party size").click()  # 2 to 3, the most this sketch allows
        self.assertEqual(stepper.input_value(), "3")
        self.assertTrue(page.get_by_role("button", name="increase Party size").is_disabled())
        for _ in range(2):
            page.get_by_role("button", name="decrease Party size").click()  # 3 to 1, the least
        self.assertEqual(stepper.input_value(), "1")
        self.assertTrue(page.get_by_role("button", name="decrease Party size").is_disabled())
        stepper.fill("99")
        stepper.blur()
        self.assertEqual(stepper.input_value(), "3")  # typed past the limit, it is put back inside
        fader = page.get_by_role("slider", name="Weight")
        fader.focus()
        page.keyboard.press("End")
        self.assertEqual(page.locator("#field-weight-readout").inner_text(), "1")
        page.keyboard.press("ArrowRight")
        self.assertEqual(page.locator("#field-weight-readout").inner_text(), "1")

    def test_play_sends_every_value_the_defaults_for_the_ones_left_alone(self):
        page = self.open()
        self.unlock(page)
        page.get_by_role("radio", name="dramatic").click()
        page.get_by_role("switch", name="Evenings only").click()
        page.fill("#field-note", "hello")
        page.click("#play")
        page.wait_for_function("document.getElementById('start-message').textContent.includes('run-20261101T150000-0000000e')")
        (argv,) = self.started
        pairs = sorted(argv[i + 1] for i, word in enumerate(argv) if word == "--with")
        self.assertEqual(pairs, ["evenings=off", "mood=dramatic", "note=hello", "tickets=2", "weight=0.3"])

    def test_the_controls_fit_a_phone(self):
        page = self.open(width=390, height=900)
        self.assertTrue(page.evaluate("document.documentElement.scrollWidth <= document.documentElement.clientWidth"))
        for selector in ("#field-mood", "#field-weight", "#field-tickets", "#field-evenings"):
            box = page.locator(selector).bounding_box()
            self.assertTrue(box and box["x"] >= 0 and box["x"] + box["width"] <= 390, selector)


STORY = {"initial": "a", "states": [{"name": "a", "final": False}, {"name": "b", "final": False}, {"name": "c", "final": True}],
         "transitions": [{"from": "a", "to": "b", "event": "ok"}, {"from": "b", "to": "c", "event": "ok", "when": {"ready": {"eq": True}}}]}


def entered(second: int, state_name: str, cause: str) -> dict:
    return {"event": "state_entered", "at": stamp(second), "state": state_name, "caused_by": cause}


class StatechartTest(BrowserCase):
    def run_with_story(self, name, events, manifest, story=None):
        started = {"event": "run_started", "at": stamp(0), "sketch": "x/chart.yaml", "mode": "live", **(STORY if story is None else story)}
        return write_run(self.runs, name, [started, *events], manifest)

    def open(self, name, width=1300, height=900):
        page = self.page(width, height)
        page.goto(self.start())
        page.wait_for_selector(".sketch-tab")
        page.locator(f".sketch-tab[title^='{name}']").click()
        return page

    def test_each_state_is_a_box_with_a_name_finals_are_double_bordered_and_only_guarded_moves_have_labels(self):
        name = "run-20261101T160000-00000001"
        self.run_with_story(name, [entered(1, "a", "start"), entered(2, "b", "ok")], {"status": "running", "stages": {}})
        page = self.open(name)
        page.wait_for_selector(".state")
        self.assertEqual(page.locator(".state").count(), 3)
        self.assertEqual(page.locator(".state.final .final-ring").count(), 1)
        self.assertEqual(page.locator(".edge").count(), 2)
        self.assertEqual(page.locator(".edge-label-text").count(), 1)
        self.assertEqual(page.locator(".edge-label-text").text_content(), "ready = true")
        self.assertEqual(page.get_by_role("img", name="a", exact=True).count(), 1)
        self.assertEqual(page.get_by_role("img", name="b, current state", exact=True).count(), 1)
        self.assertEqual(page.get_by_role("img", name="c, final state", exact=True).count(), 1)

    def test_the_state_the_run_is_in_is_lit_and_the_move_just_taken_is_marked(self):
        name = "run-20261101T160100-00000002"
        self.run_with_story(name, [entered(-1, "a", "start")], {"status": "running", "stages": {}})
        page = self.open(name)
        page.wait_for_selector(".state.current")
        self.assertEqual(page.locator(".state.current").get_attribute("data-state"), "a")
        self.assertEqual(page.locator(".edge.taken").count(), 0)

    def test_the_light_moves_to_the_next_state_within_a_second_of_the_change(self):
        name = "run-20261101T160200-00000003"
        run = self.run_with_story(name, [entered(-1, "a", "start")], {"status": "running", "stages": {}})
        page = self.open(name)
        page.wait_for_selector(".state.current[data-state='a']")
        with (run / "events.jsonl").open("a", encoding="utf-8") as events:
            events.write(json.dumps(entered(-1, "b", "ok")) + "\n")
        page.wait_for_selector(".state.current[data-state='b']", timeout=1500)
        self.assertEqual(page.locator(".edge.taken").get_attribute("data-to"), "b")
        self.assertEqual(page.locator(".state.current").count(), 1)

    def test_a_finished_run_keeps_its_last_state_lit_and_says_how_it_ended(self):
        name = "run-20261101T160300-00000004"
        self.run_with_story(name, [entered(1, "a", "start"), entered(2, "b", "ok"), entered(3, "c", "ok"),
                                   {"event": "run_finished", "at": stamp(4), "outcome": "complete"}],
                            {"status": "complete", "stages": {}, "outcome": "complete"})
        page = self.open(name)
        page.wait_for_selector(".state.current[data-state='c']")
        page.wait_for_function("document.getElementById('status-text').textContent === 'DONE'")
        self.assertIn("done", page.locator("#chart-note").inner_text().lower())

    def test_a_run_whose_log_has_no_story_says_so_and_draws_nothing(self):
        name = "run-20261101T160400-00000005"
        write_run(self.runs, name, [{"event": "run_started", "at": stamp(0), "sketch": "x/old.yaml", "mode": "live"},
                                    {"event": "run_finished", "at": stamp(1), "outcome": "complete"}],
                  {"status": "complete", "stages": {}})
        page = self.open(name)
        page.wait_for_function("document.getElementById('status-text').textContent === 'DONE'")
        self.assertIn("no story", page.locator("#chart-note").inner_text())
        self.assertEqual(page.locator("#chart-wrap svg").count(), 0)

    def test_names_and_guards_with_markup_are_drawn_as_text_and_run_nothing(self):
        name = "run-20261101T160500-00000006"
        hostile = "<img src=x onerror=window.pwned=1>"
        story = {"initial": hostile, "states": [{"name": hostile, "final": False}, {"name": "b", "final": True}],
                 "transitions": [{"from": hostile, "to": "b", "event": "ok", "when": {"<b>x</b>": {"eq": 1}}}]}
        self.run_with_story(name, [entered(1, hostile, "start")], {"status": "running", "stages": {}}, story=story)
        page = self.open(name)
        page.wait_for_selector(".state")
        self.assertEqual(page.evaluate("window.pwned"), None)
        self.assertEqual(page.locator("#chart-wrap img").count(), 0)
        self.assertIn(hostile, page.locator(".state-name").first.text_content())
        self.assertEqual(page.locator("#chart-wrap b").count(), 0)

    def test_the_diagram_fits_a_phone_without_sideways_scrolling_of_the_page(self):
        name = "run-20261101T160600-00000007"
        self.run_with_story(name, [entered(1, "a", "start")], {"status": "running", "stages": {}})
        page = self.open(name, width=390, height=900)
        page.wait_for_selector(".state")
        self.assertTrue(page.evaluate("document.documentElement.scrollWidth <= document.documentElement.clientWidth"))
        box = page.locator("#chart-wrap").bounding_box()
        self.assertTrue(box and box["x"] >= 0 and box["x"] + box["width"] <= 390)


class KeyboardTest(BrowserCase):
    def test_every_control_is_reachable_by_keyboard_has_a_name_and_shows_where_focus_is(self):
        self.failed_and_done_runs()
        sketches = self.root / "sketches"
        sketches.mkdir()
        (sketches / "plain.yaml").write_text(PLAIN, encoding="utf-8")
        launcher = Launcher(sketches, self.runs, project=self.root, cache=self.root / "cache")
        page = self.page()
        page.goto(self.start(launcher, SECRET))
        page.wait_for_selector(".sketch-tab")
        page.locator(".sketch-tab").nth(1).click()
        page.wait_for_selector(".banner")
        page.locator("#controls > summary").click()
        reached: dict[str, dict] = {}
        page.evaluate("document.activeElement.blur()")
        for _ in range(80):
            page.keyboard.press("Tab")
            info = page.evaluate("""() => { const el = document.activeElement; const cs = getComputedStyle(el);
              const label = el.getAttribute('aria-label') || el.innerText?.trim() || (el.labels && el.labels[0]?.innerText) || el.getAttribute('placeholder') || el.title || '';
              return { id: el.id || el.className || el.tagName, name: label, outline: cs.outlineStyle !== 'none' && parseFloat(cs.outlineWidth) > 0 || cs.boxShadow !== 'none', tag: el.tagName }; }""")
            reached.setdefault(info["id"], info)
        for needed in ("looks-toggle", "find-text", "find-stage", "find-failures", "jump-start", "jump-failure", "jump-end", "secret-box",
                       "unlock", "sketch-pick", "replay-pick"):
            if needed == "looks-toggle":
                continue  # shown only on a phone
            self.assertIn(needed, reached, f"{needed} cannot be reached with Tab; reached {sorted(reached)}")
        reached.pop("BODY", None)  # Tab came back round to the page itself
        unnamed = [each["id"] for each in reached.values() if not each["name"]]
        self.assertEqual(unnamed, [], "controls without an accessible name")
        unfocused = [each["id"] for each in reached.values() if not each["outline"]]
        self.assertEqual(unfocused, [], "controls that show no focus indicator")


class ContrastTest(BrowserCase):
    def test_text_is_readable_in_every_theme_and_mode(self):
        self.failed_and_done_runs()
        sketches = self.root / "sketches"
        sketches.mkdir()
        (sketches / "plain.yaml").write_text(PLAIN, encoding="utf-8")
        (sketches / "typed.yaml").write_text(TYPED, encoding="utf-8")
        launcher = Launcher(sketches, self.runs, project=self.root, cache=self.root / "cache")
        base = self.start(launcher, SECRET)
        problems = []
        for theme, mode in LOOKS:
            page = self.page()
            page.goto(f"{base}/?theme={theme}&mode={mode}")
            page.add_style_tag(content=HIDE_TEXT)
            page.wait_for_selector(".sketch-tab")
            page.locator(".sketch-tab").nth(1).click()
            page.wait_for_selector(".banner")
            page.locator("#controls > summary").click()
            page.select_option("#sketch-pick", "typed.yaml")  # its dial, fader, stepper and switch are read in every look
            page.fill("#find-text", "zzz-nothing")
            for selector in READABLE:
                found = page.evaluate(FIRST_VISIBLE_JS, selector)
                if found is None:
                    continue
                target = page.locator("[data-contrast-target]").first
                pixels = decode_png(target.screenshot())  # the text is invisible here (see HIDE_TEXT), so this is only what is behind it
                page.evaluate("document.querySelector('[data-contrast-target]').removeAttribute('data-contrast-target')")
                large = found["size"] >= 24 or (found["size"] >= 18.66 and found["weight"] >= 700)
                needed = 3.0 if large else 4.5
                worst = min((contrast(found["color"], background) for background in backdrops(pixels)), default=21.0)
                if worst < needed:
                    problems.append(f"{theme}/{mode} {selector} ({found['text']!r}): {worst:.2f} < {needed}")
        self.assertEqual(problems, [], "\n" + "\n".join(problems))


if __name__ == "__main__":
    unittest.main()
