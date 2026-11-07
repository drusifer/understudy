"""The console in a real Chromium: what unit tests cannot see (UND-80). Run with `bobp make test-browser`.

It needs the optional `browser` group (`bobp make install-browser`) and a Chromium (`/usr/bin/chromium`, or CHROMIUM=path);
without them every test is skipped with that reason. It is not part of `bobp make check`, which stays offline and fast.
Everything runs against invented run folders on a server started in this process: nothing private, nothing live.

The test pyramid (owner decision 17): a test is here only if a unit or integration test cannot show it, because it needs the
page's JavaScript or what is really drawn. What each class shows that nothing lower can:

* ContrastTest, ReplayBarTest and DecisionPanelTest (one look each): the colors a text is really drawn on, with the
  themes' textures and gradients behind it.
* KeyboardTest, TypedControlsTest (keyboard and limits): focus order and a visible focus mark; arrow keys on the controls.
* StatechartTest, SpendingListTest, TypedControlsTest (phone): the drawing, its overlaps and its fit at 390 px wide.
* RackAndBannerTest, LiveFollowTest, StartAndStopTest, HoldButtonsTest: the page's own scripts: what it draws for a state,
  that it follows a run that is going, that its buttons send what they should.
* ReplayBarTest, DecisionPanelTest: the replay's timer and the cursor, and a decision's panel and jump, drawn by the page.
Server answers and run files are tested without a browser, in tests/python.
"""

import json
import multiprocessing
import os
import struct
import sys
import tempfile
import threading
import unittest
import zlib
from concurrent.futures import ProcessPoolExecutor
from datetime import UTC, datetime
from pathlib import Path

from src.dashboard.runs import Launcher, _Child
from src.dashboard.server import serve

try:
    from playwright.sync_api import Error as PlaywrightError
    from playwright.sync_api import sync_playwright
except ImportError:  # the optional group is not installed
    sync_playwright = None

CHROMIUM = os.environ.get("CHROMIUM", "/usr/bin/chromium")
LOOKS = [(theme, mode) for theme in ("steampunk", "professional", "starship") for mode in ("light", "dark")]
LOOK_WORKERS = 3  # browser processes measuring looks at once (the machine has four cores; the server and the test use one)
PLAIN = ("name: plain\ndescription: a play to start\nstage:\n  data: { kind: file, path: \"{{ file }}\" }\n"
         "scene: { initial: only, beats: { only: { final: true } } }\n")

# What each piece of text is checked for: the selectors worth reading on every screen (WCAG AA: 4.5:1, 3:1 for large text).
READABLE = [
    "h1", ".subtitle", "#status-text", ".theme-label", ".theme-choice", ".mode-choice", ".plate-label", ".sketch-tab .name",
    ".rack-group", ".badge", ".printer-head span", ".paper .line", ".find-button", ".find-check", ".ended", ".summary dt", ".summary dd",
    ".box-title", ".box-card-head", ".box-zone-name", ".box-quiet", ".box-item-name", ".box-axis", ".gauge .figure", ".gauge-name", ".start-message", ".start-panel > summary", ".banner",
    ".panel-head span", ".jev > summary", ".offline", ".no-match",
    "#spending-title", ".spend-name", ".spend-amount", ".spend-more",
    ".typed-label", ".pick-option", ".toggle", ".readout", ".count-box", ".step-button",
    "#chart-title", "#chart-note", ".state-name", ".state-detail", ".row-badge", ".start-tag", ".legend", ".edge-label-text",
]

# While one element is measured its text is invisible and nothing animates, so a screenshot shows only the backdrop.
HIDE_TEXT = "*, *::before, *::after { animation: none !important; transition: none !important; }\n[data-contrast-target], [data-contrast-target] * { color: transparent !important; text-shadow: none !important; transition: none !important; animation: none !important; }\n[data-contrast-target] i, [data-contrast-target] button, [data-contrast-target] input { visibility: hidden !important; }"

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

    def start(self, launcher: Launcher | None = None, controllable=None) -> str:
        server = serve(self.runs, port=0, cache=self.root / "cache", project=self.root, launcher=launcher, controllable=controllable)
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
            {"event": "run_started", "at": stamp(0), "play": "examples/household/household.yaml", "mode": "live", **STORY},
            entered(1, "a", "start"), entered(1, "b", "ok"),  # a diagram for the readability check to measure
            {"event": "beat_started", "at": stamp(1), "beat": "read"},
            {"event": "beat_failed", "at": stamp(2), "beat": "read", "reason": "Jev needs a TypeSafe key"}],
            {"status": "failed", "failed_beat": "read", "error": "Jev needs a TypeSafe key", "beats":{}, "mode": "live"})
        spending(failed, 12)  # a long list on the run the readability check looks at
        write_run(self.runs, "run-20261101T120100-0000000b", [
            {"event": "run_started", "at": stamp(0), "play": "examples/evening/evening.yaml", "mode": "replay"},
            {"event": "beat_started", "at": stamp(1), "beat": "pick"}, {"event": "beat_completed", "at": stamp(2), "beat": "pick"},
            {"event": "run_finished", "at": stamp(3), "outcome": "booked"}],
            {"status": "complete", "beats":{"pick": "complete"}, "mode": "replay", "outcome": "booked", "outputs": {"booking.jsonl": 1}},
            {"stale": False})


class SpendingListTest(BrowserCase):
    def open_run(self, page, name):
        page.goto(self.start())
        page.wait_for_selector(".sketch-tab")
        page.locator(f".sketch-tab[title^='{name}']").click()

    def test_the_ten_largest_categories_are_listed_with_amount_and_share_and_the_rest_are_counted(self):
        run = write_run(self.runs, "run-20261101T130000-0000000c", [
            {"event": "run_started", "at": stamp(0), "play": "examples/household/household.yaml", "mode": "live"},
            {"event": "run_finished", "at": stamp(1), "outcome": "complete"}], {"status": "complete", "beats":{}, "mode": "live"})
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
            {"event": "run_started", "at": stamp(0), "play": "x/plain.yaml", "mode": "live"},
            {"event": "run_finished", "at": stamp(1), "outcome": "complete"}], {"status": "complete", "beats":{}, "mode": "live"})
        page = self.page()
        self.open_run(page, "run-20261101T130100-0000000d")
        page.wait_for_function("document.getElementById('status-text').textContent === 'DONE'")
        self.assertFalse(page.locator("#spending").is_visible())
        self.assertEqual(page.locator("#spending-title").count(), 1)  # the element exists; it is hidden, not drawn empty
        self.assertFalse(page.locator("#spending-title").is_visible())

    def test_a_spending_file_the_console_cannot_read_is_named_and_the_page_still_works(self):
        run = write_run(self.runs, "run-20261101T130200-0000000e", [
            {"event": "run_started", "at": stamp(0), "play": "x/household.yaml", "mode": "live"},
            {"event": "run_finished", "at": stamp(1), "outcome": "complete"}], {"status": "complete", "beats":{}, "mode": "live"})
        (run / "spending.jsonl").write_text('{"category": "Rent", "amount": 5, "share": 1}\nnot json\n', encoding="utf-8")
        page = self.page()
        self.open_run(page, "run-20261101T130200-0000000e")
        page.wait_for_selector("#spending")
        self.assertIn("spending.jsonl line 2 is not readable", page.locator("#spending").inner_text())
        self.assertEqual(page.locator("#status-text").inner_text(), "DONE")

    def test_the_list_fits_a_phone_without_sideways_scrolling(self):
        run = write_run(self.runs, "run-20261101T130300-0000000f", [
            {"event": "run_started", "at": stamp(0), "play": "x/household.yaml", "mode": "live"},
            {"event": "run_finished", "at": stamp(1), "outcome": "complete"}], {"status": "complete", "beats":{}, "mode": "live"})
        spending(run, 12)
        page = self.page(width=390, height=800)
        self.open_run(page, "run-20261101T130300-0000000f")
        page.wait_for_selector("#spending li")
        self.assertTrue(page.evaluate("document.documentElement.scrollWidth <= document.documentElement.clientWidth"))
        self.assertTrue(page.evaluate("(() => { const box = document.getElementById('spending').getBoundingClientRect();"
                                      " return box.left >= 0 && box.right <= window.innerWidth; })()"))


class BigPlayTest(BrowserCase):
    """UND-117: a big play is drawn as its flow, with a button for everything and back."""

    def test_a_big_plan_shows_its_flow_and_a_button_shows_all_nodes_and_back(self):
        waiting = [{**beat(f"w{number}"), "flow": False, "waits": True} for number in range(45)]
        story = plan_of([beat("a"), beat("b", True), *waiting], [("a", "b")], "a")
        story["plan"]["edges"] += [{"from": "w0", "to": "a", "kind": "reads"}]
        started = {"event": "run_started", "at": stamp(0), "play": "x/big.yaml", "mode": "live", **story}
        write_run(self.runs, "run-20261101T180000-00000001", [started, entered(1, "a", "start")], {"status": "running", "beats": {}})
        page = self.page(1600, 1000)
        page.goto(self.start())
        page.wait_for_selector(".state")
        self.assertEqual(page.locator("#chart-wrap .state").count(), 2)  # the flow only
        button = page.locator("#diagram-view")
        self.assertEqual(button.inner_text(), "SHOW ALL 47 NODES")
        button.click()
        page.wait_for_function("document.querySelectorAll('#chart-wrap .state').length === 47")
        self.assertEqual(button.inner_text(), "SHOW ONLY THE FLOW")
        button.click()
        page.wait_for_function("document.querySelectorAll('#chart-wrap .state').length === 2")

    def test_a_small_plan_has_no_such_button(self):
        started = {"event": "run_started", "at": stamp(0), "play": "x/small.yaml", "mode": "live", **STORY}
        write_run(self.runs, "run-20261101T180100-00000001", [started, entered(1, "a", "start")], {"status": "running", "beats": {}})
        page = self.page(1600, 1000)
        page.goto(self.start())
        page.wait_for_selector(".state")
        self.assertTrue(page.locator("#diagram-view").is_hidden())


WIDTHS = ((390, "one"), (1280, "two"), (1600, "three"), (1920, "three"), (2560, "three"), (3840, "three"))  # 3840: 1920 zoomed to 50%


class WidthTest(BrowserCase):
    """UND-116: the run view is three columns from 1400 px, two from 1101, one below; the page never scrolls sideways."""

    def open_at(self, width):
        name = "run-20261101T170000-00000001"
        started = {"event": "run_started", "at": stamp(0), "play": "x/chart.yaml", "mode": "live", **STORY}
        write_run(self.runs, name, [started, entered(1, "a", "start"), entered(2, "b", "ok")], {"status": "running", "beats": {}})
        page = self.page(width, 1000)
        page.goto(self.start())
        page.wait_for_selector(".state")
        return page

    def boxes(self, page):
        return {key: page.locator(selector).bounding_box() for key, selector in (
            ("printer", "#printer"), ("readouts", ".tube-panel:not(.diagram-panel)"), ("diagram", ".diagram-panel"))}

    def test_the_columns_follow_the_width_and_the_page_never_scrolls_sideways(self):
        for width, columns in WIDTHS:
            page = self.open_at(width) if width == WIDTHS[0][0] else self.reopen(width)
            self.assertTrue(page.evaluate("document.documentElement.scrollWidth <= document.documentElement.clientWidth"), width)
            box = self.boxes(page)
            if columns == "three":
                self.assertTrue(box["printer"]["x"] < box["readouts"]["x"] < box["diagram"]["x"], width)
                self.assertLess(abs(box["printer"]["y"] - box["diagram"]["y"]), 40, width)  # one row
            elif columns == "two":
                self.assertLess(box["printer"]["x"], box["readouts"]["x"], width)
                self.assertGreater(box["diagram"]["y"], box["readouts"]["y"] + box["readouts"]["height"] - 1, width)  # under both
            else:
                self.assertTrue(box["readouts"]["y"] < box["diagram"]["y"] < box["printer"]["y"], width)  # stacked, readouts first

    def reopen(self, width):
        page = self.page(width, 1000)
        page.goto(self.base)
        page.wait_for_selector(".state")
        return page

    def start(self, *args, **options):
        self.base = super().start(*args, **options)
        return self.base

    def test_the_paper_is_as_tall_as_its_lines_not_a_tall_empty_block(self):
        page = self.open_at(1600)
        window = page.locator("#paper-window").bounding_box()
        lines = page.locator("#paper").bounding_box()
        self.assertLess(window["height"], lines["height"] + 40)


class ShortRackTest(BrowserCase):
    """UND-115: the rack shows a play's newest 8 runs and the chosen one, folds the rest, and folds the unreadable runs."""

    def seed(self):
        for number in range(12):  # run-...T1000NN: the higher the number the newer
            write_run(self.runs, f"run-20261101T1000{number:02d}-000000{number:02x}",
                      [{"event": "run_started", "at": stamp(-1), "play": "x/evening.yaml", "mode": "live"},
                       {"event": "run_finished", "at": stamp(0), "outcome": "complete"}], {"status": "complete", "beats": {}})
        for number in range(3):
            write_run(self.runs, f"run-20261031T0900{number:02d}-0000010{number}", [], {})

    def test_eight_newest_tabs_and_buttons_for_the_older_and_the_unreadable_ones(self):
        self.seed()
        page = self.page()
        page.goto(self.start())
        page.wait_for_selector(".sketch-tab")
        self.assertEqual(page.locator(".sketch-tab").count(), 8)
        self.assertEqual(page.get_by_role("button", name="4 older").count(), 1)
        self.assertEqual(page.get_by_role("button", name="3 unreadable").count(), 1)
        page.get_by_role("button", name="4 older").click()
        self.assertEqual(page.locator(".sketch-tab").count(), 12)
        page.get_by_role("button", name="fewer").click()
        self.assertEqual(page.locator(".sketch-tab").count(), 8)
        page.get_by_role("button", name="3 unreadable").click()
        self.assertEqual(page.locator(".sketch-tab").count(), 11)

    def test_the_chosen_run_stays_on_the_rack_when_it_is_one_of_the_folded_ones_and_buttons_work_from_the_keyboard(self):
        self.seed()
        page = self.page()
        page.goto(self.start())
        page.wait_for_selector(".sketch-tab")
        page.get_by_role("button", name="4 older").focus()
        page.keyboard.press("Enter")
        page.locator(".sketch-tab").nth(11).click()  # the oldest of the twelve
        page.get_by_role("button", name="fewer").click()
        self.assertEqual(page.locator(".sketch-tab").count(), 9)  # the newest eight, and the chosen one
        self.assertEqual(page.locator(".sketch-tab[aria-selected='true']").count(), 1)


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
        page.add_init_script("window.understudyPollMs = 300;")  # the page asks again every 5 s; do not wait for that
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
            {"event": "run_started", "at": stamp(-1), "play": "x/live.yaml", "mode": "live"}], {"status": "running", "beats":{}})
        page = self.page()
        page.goto(self.start())
        page.wait_for_selector(".sketch-tab")
        page.locator(".sketch-tab").first.click()
        page.wait_for_function("document.getElementById('status-text').textContent === 'RUNNING'")
        before = page.locator("#paper .line").count()
        with (directory / "events.jsonl").open("a") as events:
            events.write(json.dumps({"event": "beat_started", "at": stamp(-1), "beat": "build"}) + "\n")
        page.wait_for_function(f"document.querySelectorAll('#paper .line').length > {before}", timeout=10000)
        with (directory / "events.jsonl").open("a") as events:
            events.write(json.dumps({"event": "beat_completed", "at": stamp(-1), "beat": "build"}) + "\n")
            events.write(json.dumps({"event": "run_finished", "at": stamp(-1), "outcome": "complete"}) + "\n")
        (directory / "run.json").write_text(json.dumps({"status": "complete", "beats":{"build": "complete"}}))
        page.wait_for_function("document.getElementById('status-text').textContent === 'DONE'", timeout=15000)
        self.assertEqual(page.locator("#beat-box").count(), 1)


class StartAndStopTest(BrowserCase):
    def test_play_and_stop_a_run_from_the_page_with_no_login(self):
        sketches = self.root / "sketches"
        sketches.mkdir()
        (sketches / "plain.yaml").write_text(PLAIN, encoding="utf-8")
        (self.root / "in.csv").write_text("a\n", encoding="utf-8")
        run = write_run(self.runs, "run-20261101T140000-0000000d", [{"event": "run_started", "at": stamp(-1), "play": "p.yaml", "mode": "live"}],
                        {"status": "running", "beats":{}})

        def sleeper(argv, **options):
            return _Child([sys.executable, "-c", "import time; time.sleep(60)"], **options)

        launcher = Launcher(sketches, self.runs, project=self.root, cache=self.root / "cache", spawn=sleeper, check=lambda argv: [],
                            find_run=lambda sketch, before: run.name, settle=0)
        page = self.page()
        page.goto(self.start(launcher))
        page.locator("#controls > summary").click()
        self.assertEqual(page.locator("#secret-box").count(), 0)  # there is no login
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


class HoldButtonsTest(BrowserCase):
    def held_run(self):
        return write_run(self.runs, "run-20261101T150000-0000000e", [
            {"event": "run_started", "at": stamp(-1), "play": "p.yaml", "mode": "live", **STORY},
            {"event": "paused", "at": stamp(-1), "beat": "a"}], {"status": "running", "beats":{}})

    def test_a_held_run_reads_paused_and_the_hold_buttons_work_only_where_they_apply(self):
        run = self.held_run()
        page = self.page()
        page.goto(self.start(controllable=lambda each: each == run.name))
        page.wait_for_function("document.getElementById('status-text').textContent === 'PAUSED'")
        self.assertIn("paused before a", page.locator("#ended").inner_text())
        page.locator("#controls > summary").click()
        self.assertEqual(page.locator("#controls > summary").inner_text(), "HOLD THIS RUN")
        self.assertFalse(page.locator("#sketch-pick").is_visible())  # a console that starts nothing offers no sketch
        page.wait_for_function("!document.getElementById('step').disabled")
        self.assertTrue(page.locator("#pause").is_disabled())  # it is already held
        self.assertFalse(page.locator("#resume").is_disabled())
        page.click("#step")
        page.wait_for_function("document.getElementById('start-message').textContent.includes('one beat')")
        self.assertEqual(json.loads((run / "control.json").read_text(encoding="utf-8")), {"mode": "hold", "steps": 1})
        page.click("#resume")
        page.wait_for_function("document.getElementById('start-message').textContent.includes('running on')")
        self.assertEqual(json.loads((run / "control.json").read_text(encoding="utf-8")), {"mode": "run", "steps": 1})

    def test_a_console_that_cannot_hold_runs_shows_no_hold_buttons(self):
        self.held_run()
        page = self.page()
        page.goto(self.start())
        page.wait_for_function("document.getElementById('status-text').textContent === 'PAUSED'")
        self.assertTrue(page.locator("#controls").is_hidden())


TYPED = """name: typed
description: A play with typed props and one plain value ({{ note | default('none') }}).
stage:
  mood: { kind: choice, label: Mood, options: [fun, serious, dramatic], default: fun }
  weight: { kind: range, label: Weight, min: 0, max: 1, step: 0.05, default: 0.3 }
  tickets: { kind: count, label: Party size, min: 1, max: 3, default: 2 }
  evenings: { kind: switch, label: Evenings only, default: "on" }
data: { mood: "{{ mood }}", weight: {{ weight }}, tickets: {{ tickets }}, evenings: "{{ evenings }}" }
scene: { initial: only, beats: { only: { final: true } } }
"""


FLOW = """name: flow
description: A play with a beat to hold before.
scene:
  initial: first
  beats:
    first: { do: { map: { action: rows } }, with: { rows: [ { a: 1 } ] }, to: second }
    second: { do: { map: { action: rows } }, with: { rows: [ { a: 2 } ] }, to: done }
    done: { final: true }
"""


class TypedControlsTest(BrowserCase):
    def open(self, width=1300, height=900):
        sketches = self.root / "sketches"
        sketches.mkdir()
        (sketches / "typed.yaml").write_text(TYPED, encoding="utf-8")
        (sketches / "zflow.yaml").write_text(FLOW, encoding="utf-8")
        run = write_run(self.runs, "run-20261101T150000-0000000e", [{"event": "run_started", "at": stamp(-1), "play": "typed.yaml",
                                                                    "mode": "live"}], {"status": "running", "beats":{}})
        self.started: list[list[str]] = []

        def spawn(argv, **options):
            self.started.append(argv)
            return _Child([sys.executable, "-c", "import time; time.sleep(60)"], **options)

        launcher = Launcher(sketches, self.runs, project=self.root, cache=self.root / "cache", spawn=spawn, check=lambda argv: [],
                            find_run=lambda sketch, before: run.name, settle=0)
        page = self.page(width, height)
        page.goto(self.start(launcher))
        page.locator("#controls > summary").click()
        page.wait_for_selector("#fields [data-input]")
        return page

    def unlock(self, page):
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

    def test_there_is_one_diagram_and_it_follows_the_last_choice_a_play_picked_or_a_run_chosen(self):
        page = self.open()
        self.assertEqual(page.locator(".chart-svg").count(), 0)  # the chosen run has no plan in its log
        page.click("#show-plan")
        page.wait_for_selector("#chart-wrap .state")
        self.assertEqual(page.locator(".chart-svg").count(), 1)
        self.assertEqual(page.locator("#chart-title").inner_text(), "PLAN OF typed")
        self.assertEqual(page.locator("#plan").count(), 0)  # the start panel has no diagram of its own
        page.locator(".sketch-tab").first.click()
        page.wait_for_function("document.getElementById('chart-title').textContent.startsWith('DIAGRAM OF RUN')")
        self.assertEqual(page.locator(".chart-svg").count(), 0)  # the run's own diagram (none in this log)

    def test_the_picked_play_shows_its_plan(self):
        page = self.open()
        page.click("#show-plan")
        page.wait_for_selector("#chart-wrap .state")
        self.assertEqual(page.locator("#chart-wrap .state-name").all_text_contents(), ["only"])
        self.assertIn("1 node:", page.locator("#chart-note").inner_text())

    def test_a_beat_clicked_on_the_plan_is_held_before_and_start_held_holds_at_the_first_beat(self):
        page = self.open()
        self.unlock(page)
        page.select_option("#sketch-pick", "zflow.yaml")
        page.wait_for_selector("#chart-wrap .state.pickable")
        self.assertEqual(page.locator("#chart-wrap .state.pickable").count(), 2)  # the flow's two beats; the final one is not
        page.locator("#chart-wrap .state[data-state='second']").click()
        self.assertEqual(page.locator("#chart-wrap .state.hold-here").get_attribute("data-state"), "second")
        self.assertIn("hold before second", page.locator("#chart-note").inner_text())
        page.click("#play")
        page.wait_for_function("document.getElementById('start-message').textContent.includes('started')")
        self.assertEqual(self.started[-1][self.started[-1].index("--stop-at") + 1], "second")
        self.assertEqual(page.locator("#chart-wrap .state.hold-here").count(), 0)  # spent by the start
        page.click("#play-held")
        page.wait_for_function("document.getElementById('start-message').textContent.includes('already running') || "
                               "document.getElementById('start-message').textContent.includes('started')")

    def test_a_clicked_beat_is_cleared_by_clicking_it_again_and_works_from_the_keyboard(self):
        page = self.open()
        page.select_option("#sketch-pick", "zflow.yaml")
        page.wait_for_selector("#chart-wrap .state.pickable")
        beat = page.locator("#chart-wrap .state[data-state='first']")
        beat.focus()
        page.keyboard.press("Enter")
        self.assertEqual(page.locator("#chart-wrap .state.hold-here").count(), 1)
        self.assertEqual(beat.get_attribute("aria-pressed"), "true")
        page.keyboard.press(" ")
        self.assertEqual(page.locator("#chart-wrap .state.hold-here").count(), 0)

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


def beat(name: str, final: bool = False) -> dict:
    return {"id": name, "kind": "beat", "write": False, "flow": True, "final": final, "waits": False, "action": None}


def plan_of(nodes: list, moves: list, initial: str) -> dict:
    return {"plan": {"nodes": nodes, "props": [], "initial": initial,
                     "edges": [{"from": each[0], "to": each[1], "kind": "move", **({"when": each[2]} if len(each) > 2 else {})}
                               for each in moves]}}


STORY = plan_of([beat("a"), beat("b"), beat("c", True)], [("a", "b"), ("b", "c", {"ready": {"eq": True}})], "a")


def entered(second: int, state_name: str, cause: str) -> dict:
    return {"event": "beat_entered", "at": stamp(second), "beat": state_name, "caused_by": cause}


class StatechartTest(BrowserCase):
    def run_with_story(self, name, events, manifest, story=None):
        started = {"event": "run_started", "at": stamp(0), "play": "x/chart.yaml", "mode": "live", **(STORY if story is None else story)}
        return write_run(self.runs, name, [started, *events], manifest)

    def open(self, name, width=1300, height=900):
        page = self.page(width, height)
        page.goto(self.start())
        page.wait_for_selector(".sketch-tab")
        page.locator(f".sketch-tab[title^='{name}']").click()
        return page

    def test_a_box_says_what_the_beat_does_a_completed_one_how_many_rows_and_the_first_is_marked_start(self):
        name = "run-20261101T165500-0000000b"
        story = plan_of([{**beat("a"), "action": "map.where"}, beat("b", True)], [("a", "b")], "a")
        story["plan"]["nodes"].append({"id": "f", "kind": "piece", "write": False, "flow": False, "final": False, "waits": False,
                                       "action": None, "with": None, "path": "sales.jsonl"})
        done = {"event": "beat_completed", "at": stamp(2), "beat": "a", "read": {}, "wrote": {}, "made": {"rows": 3, "keys": ["x"]}}
        self.run_with_story(name, [entered(1, "a", "start"), done], {"status": "running", "beats": {}}, story=story)
        page = self.open(name)
        page.wait_for_selector(".state-detail")
        self.assertEqual(sorted(page.locator(".state-detail").all_text_contents()), ["map.where", "sales.jsonl"])
        self.assertEqual(page.locator(".row-badge").all_text_contents(), ["3 rows"])
        self.assertEqual(page.locator(".start-tag").all_text_contents(), ["START"])
        self.assertIn("map.where", page.get_by_role("button", name="a, current beat, map.where, 3 rows").get_attribute("aria-label"))

    def test_the_beat_box_follows_the_run_and_a_clicked_beat_shows_its_inputs_and_outputs_as_charts(self):
        name = "run-20261101T165000-00000009"
        sales = {"rows": 40, "keys": ["amount", "payee"], "columns": [
            {"name": "amount", "kind": "number", "rows": 40, "min": 2, "max": 90, "mean": 31.5},
            {"name": "payee", "kind": "text", "rows": 40, "distinct": 9, "top": [["Cafe", 12], ["Bus", 9], ["Books", 5], ["Rent", 3], ["Gym", 2]]}]}
        made = {"rows": 40, "keys": ["kind"], "columns": [
            {"name": "kind", "kind": "text", "rows": 40, "distinct": 2, "top": [["food", 30], ["travel", 10]]}]}
        done = {"event": "beat_completed", "at": stamp(2), "beat": "a", "action": "map.where", "read": {"sales": sales}, "made": made, "wrote": {}}
        self.run_with_story(name, [entered(1, "a", "start"), done, entered(3, "b", "ok")], {"status": "running", "beats": {}})
        page = self.open(name)
        page.wait_for_selector(".box-title")
        self.assertIn("b", page.locator(".box-title").inner_text())  # follows the beat the run is on
        page.locator(".state[data-state='a']").click()
        self.assertTrue(page.locator(".box-title").inner_text().startswith("a"))
        self.assertIn("map.where", page.locator(".box-title").inner_text())
        self.assertEqual(page.locator(".box-zone").first.locator(".box-card-head").inner_text(), "sales · 40 rows")
        charts = page.locator(".box-chart").evaluate_all("els => els.map(e => e.getAttribute('aria-label'))")
        self.assertTrue(any(each.startswith("amount: from 2 to 90, mean 31.5") for each in charts), charts)  # a gauge
        self.assertTrue(any(each.startswith("payee: 9 different values") for each in charts), charts)  # bars
        self.assertTrue(any(each.startswith("kind: food 30, travel 10") for each in charts), charts)  # a donut
        self.assertEqual(page.locator(".state.chosen").get_attribute("data-state"), "a")
        page.locator(".state[data-state='a']").click()  # again: back to following the run
        self.assertIn("b", page.locator(".box-title").inner_text())

    def test_a_beat_that_runs_once_per_row_shows_one_pass_and_a_stepper_and_that_passs_jev_answer(self):
        name = "run-20261101T165200-0000000c"
        columns = [{"name": "score", "kind": "number", "rows": 1, "min": 0.5, "max": 0.5, "mean": 0.5}]
        passes = [{"event": "iteration", "at": stamp(2), "beat": "a", "index": number, "of": 3, "item": {"title": f"Film {number}"},
                   "made": {"rows": 1, "columns": columns}} for number in range(3)]
        jev = [{"event": "jev_read", "at": stamp(2), "source": f"a.review[{number}].audience", "top": "loved" if number else "bored",
                "probability": 0.9 if number else 0.4, "options": 2, "levels": [["loved" if number else "bored", 0.9 if number else 0.4], ["mixed", 0.1]]}
               for number in range(3)]
        started = [entered(1, "a", "start"), {"event": "beat_started", "at": stamp(1), "beat": "a"}]
        self.run_with_story(name, [*started, *passes, *jev], {"status": "running", "beats": {}})
        page = self.open(name)
        page.wait_for_selector(".box-pass")
        self.assertEqual(page.locator(".box-pass").inner_text(), "pass 3 of 3")  # the latest while the run goes
        self.assertIn("Film 2", page.locator(".box-item-value").first.inner_text())
        self.assertEqual(page.locator(".box-extras .box-chart").count(), 1)  # only this pass's answer
        page.get_by_role("button", name="previous pass").click()
        self.assertEqual(page.locator(".box-pass").inner_text(), "pass 2 of 3")
        self.assertIn("Film 1", page.locator(".box-item-value").first.inner_text())
        page.get_by_role("button", name="previous pass").click()
        page.get_by_role("button", name="previous pass").is_disabled()
        self.assertIn("UNSURE", page.locator(".box-extras .box-chart").first.get_attribute("aria-label").upper())  # 0.4 is under 0.7

    def test_a_beat_logged_without_the_lists_shows_in_the_box_without_them_and_without_error(self):
        name = "run-20261101T165100-0000000a"
        self.run_with_story(name, [entered(1, "a", "start"), {"event": "beat_completed", "at": stamp(2), "beat": "a"}],
                            {"status": "running", "beats": {}})
        page = self.open(name)
        page.wait_for_selector(".box-title")
        page.locator(".state[data-state='a']").click()
        self.assertIn("makes nothing to draw", page.locator("#beat-box").inner_text())
        self.assertEqual(page.locator(".box-chart").count(), 0)

    def test_each_state_is_a_box_with_a_name_finals_are_double_bordered_and_only_guarded_moves_have_labels(self):
        name = "run-20261101T160000-00000001"
        self.run_with_story(name, [entered(1, "a", "start"), entered(2, "b", "ok")], {"status": "running", "beats":{}})
        page = self.open(name)
        page.wait_for_selector(".state")
        self.assertEqual(page.locator(".state").count(), 3)
        self.assertEqual(page.locator(".state.final .final-ring").count(), 1)
        self.assertEqual(page.locator(".edge").count(), 2)
        self.assertEqual(page.locator(".edge-label-text").count(), 1)
        self.assertEqual(page.locator(".edge-label-text").text_content(), "ready = true")
        self.assertEqual(page.get_by_role("button", name="a", exact=True).count(), 1)
        self.assertEqual(page.get_by_role("button", name="b, current beat", exact=True).count(), 1)
        self.assertEqual(page.get_by_role("button", name="c, final beat", exact=True).count(), 1)

    def test_the_state_the_run_is_in_is_lit_and_the_move_just_taken_is_marked(self):
        name = "run-20261101T160100-00000002"
        self.run_with_story(name, [entered(-1, "a", "start")], {"status": "running", "beats":{}})
        page = self.open(name)
        page.wait_for_selector(".state.current")
        self.assertEqual(page.locator(".state.current").get_attribute("data-state"), "a")
        self.assertEqual(page.locator(".edge.taken").count(), 0)

    def test_the_light_moves_to_the_next_state_within_a_second_of_the_change(self):
        name = "run-20261101T160200-00000003"
        run = self.run_with_story(name, [entered(-1, "a", "start")], {"status": "running", "beats":{}})
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
                            {"status": "complete", "beats":{}, "outcome": "complete"})
        page = self.open(name)
        page.wait_for_selector(".state.current[data-state='c']")
        page.wait_for_function("document.getElementById('status-text').textContent === 'DONE'")
        self.assertIn("done", page.locator("#chart-note").inner_text().lower())

    def test_a_run_whose_log_has_no_plan_says_so_and_draws_nothing(self):
        name = "run-20261101T160400-00000005"
        write_run(self.runs, name, [{"event": "run_started", "at": stamp(0), "play": "x/old.yaml", "mode": "live"},
                                    {"event": "run_finished", "at": stamp(1), "outcome": "complete"}],
                  {"status": "complete", "beats":{}})
        page = self.open(name)
        page.wait_for_function("document.getElementById('status-text').textContent === 'DONE'")
        self.assertIn("no plan", page.locator("#chart-note").inner_text())
        self.assertEqual(page.locator("#chart-wrap svg").count(), 0)

    def test_names_and_guards_with_markup_are_drawn_as_text_and_run_nothing(self):
        name = "run-20261101T160500-00000006"
        hostile = "<img src=x onerror=window.pwned=1>"
        story = plan_of([beat(hostile), beat("b", True)], [(hostile, "b", {"<b>x</b>": {"eq": 1}})], hostile)
        self.run_with_story(name, [entered(1, hostile, "start")], {"status": "running", "beats":{}}, story=story)
        page = self.open(name)
        page.wait_for_selector(".state")
        self.assertEqual(page.evaluate("window.pwned"), None)
        self.assertEqual(page.locator("#chart-wrap img").count(), 0)
        self.assertIn(hostile, page.locator(".state-name").first.text_content())
        self.assertEqual(page.locator("#chart-wrap b").count(), 0)

    def test_the_diagram_fits_a_phone_without_sideways_scrolling_of_the_page(self):
        name = "run-20261101T160600-00000007"
        self.run_with_story(name, [entered(1, "a", "start")], {"status": "running", "beats":{}})
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
        page.goto(self.start(launcher))
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
              return { id: el.id || el.getAttribute('class') || el.tagName, name: label, outline: cs.outlineStyle !== 'none' && parseFloat(cs.outlineWidth) > 0 || cs.boxShadow !== 'none', tag: el.tagName }; }""")
            reached.setdefault(info["id"], info)
        for needed in ("looks-toggle", "find-text", "find-stage", "find-failures", "jump-start", "jump-failure", "jump-end",
                       "sketch-pick", "replay-pick"):
            if needed == "looks-toggle":
                continue  # shown only on a phone
            self.assertIn(needed, reached, f"{needed} cannot be reached with Tab; reached {sorted(reached)}")
        reached.pop("BODY", None)  # Tab came back round to the page itself
        unnamed = [each["id"] for each in reached.values() if not each["name"]]
        self.assertEqual(unnamed, [], "controls without an accessible name")
        unfocused = [each["id"] for each in reached.values() if not each["outline"]]
        self.assertEqual(unfocused, [], "controls that show no focus indicator")


def contrast_problems(base: str, theme: str, mode: str) -> list[str]:
    """Open the console at `base` in one look, in a browser of its own, and list every text that is not readable there.

    A function of its own, importable by name, so the six looks can be measured in separate processes at the same time:
    the time is spent in Chromium taking a picture of each text (about 0.2 s each), and a picture cannot be taken faster."""
    problems = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(executable_path=CHROMIUM, args=["--no-sandbox"])
        page = browser.new_context(viewport={"width": 1300, "height": 900}, bypass_csp=True).new_page()
        page.goto(f"{base}/?theme={theme}&mode={mode}")
        page.add_style_tag(content=HIDE_TEXT)
        page.wait_for_selector(".sketch-tab")
        page.locator(".sketch-tab").nth(1).click()
        page.wait_for_selector(".banner")
        page.locator("#controls > summary").click()
        page.select_option("#sketch-pick", "typed.yaml")  # its dial, fader, stepper and switch are read in every look
        # the picked play's plan replaces the run's diagram; wait for it (the run's own diagram is there before) and let it settle
        page.wait_for_function("document.getElementById('chart-title').textContent.startsWith('PLAN OF')")
        page.wait_for_selector("#chart-wrap .state")
        page.fill("#find-text", "zzz-nothing")
        for selector in READABLE:
            found, pixels = None, None
            for _ in range(3):  # the page may redraw (a diagram) between finding a text and taking its picture: look again
                found = page.evaluate(FIRST_VISIBLE_JS, selector)
                if found is None:
                    break
                try:
                    # the text is invisible here (see HIDE_TEXT), so this is only what is behind it
                    pixels = decode_png(page.locator("[data-contrast-target]").first.screenshot(timeout=5000))
                    break
                except PlaywrightError:
                    pixels = None
            page.evaluate("document.querySelector('[data-contrast-target]')?.removeAttribute('data-contrast-target')")
            if found is None or pixels is None:
                continue
            large = found["size"] >= 24 or (found["size"] >= 18.66 and found["weight"] >= 700)
            needed = 3.0 if large else 4.5
            worst = min((contrast(found["color"], background) for background in backdrops(pixels)), default=21.0)
            if worst < needed:
                problems.append(f"{theme}/{mode} {selector} ({found['text']!r}): {worst:.2f} < {needed}")
        browser.close()
    return problems


class ContrastTest(BrowserCase):
    def test_text_is_readable_in_every_theme_and_mode(self):
        """Only a browser shows what a text is really drawn on (the themes' textures and gradients), so this measures
        the real pixels, in all six looks, each in its own browser process at the same time."""
        self.failed_and_done_runs()
        sketches = self.root / "sketches"
        sketches.mkdir()
        (sketches / "plain.yaml").write_text(PLAIN, encoding="utf-8")
        (sketches / "typed.yaml").write_text(TYPED, encoding="utf-8")
        launcher = Launcher(sketches, self.runs, project=self.root, cache=self.root / "cache")
        base = self.start(launcher)
        with ProcessPoolExecutor(max_workers=LOOK_WORKERS, mp_context=multiprocessing.get_context("spawn")) as pool:
            results = list(pool.map(contrast_problems, [base] * len(LOOKS), [theme for theme, _ in LOOKS], [mode for _, mode in LOOKS]))
        problems = [problem for each in results for problem in each]
        self.assertEqual(problems, [], "\n" + "\n".join(problems))


class ReplayBarTest(BrowserCase):
    NAME = "run-20261101T170000-00000001"
    EVENTS = 9  # run_started, three state_entered, two stages (two events each), run_finished

    def finished(self, name=None):
        started = {"event": "run_started", "at": stamp(0), "play": "x/chart.yaml", "mode": "live", **STORY}
        return write_run(self.runs, name or self.NAME, [
            started, entered(1, "a", "start"), {"event": "beat_started", "at": stamp(2), "beat": "a"},
            {"event": "beat_completed", "at": stamp(3), "beat": "a"}, entered(4, "b", "ok"),
            {"event": "beat_started", "at": stamp(5), "beat": "b"}, {"event": "beat_completed", "at": stamp(6), "beat": "b"},
            entered(7, "c", "ok"), {"event": "run_finished", "at": stamp(8), "outcome": "complete"}],
            {"status": "complete", "beats":{"a": "complete", "b": "complete"}, "mode": "live", "outcome": "complete"})

    def open(self, width=1300, height=900):
        page = self.page(width, height)
        page.add_init_script("window.understudyReplayMs = 40;")
        page.goto(self.start())
        page.wait_for_selector(".sketch-tab")
        page.wait_for_function("document.getElementById('status-text').textContent === 'DONE'")
        return page

    def text(self, page, selector):
        return page.locator(selector).inner_text()

    def test_replay_steps_forward_and_back_and_the_page_follows_the_cursor(self):
        self.finished()
        page = self.open()
        self.assertTrue(page.locator("#replay").is_hidden())
        page.click("#replay-open")
        page.wait_for_function(f"document.getElementById('replay-at').textContent === 'event 0 of {self.EVENTS}'")
        self.assertEqual(page.locator("#paper .line").count(), 0)
        for _ in range(4):
            page.click("#replay-step")
        page.wait_for_function(f"document.getElementById('replay-at').textContent === 'event 4 of {self.EVENTS}'")
        self.assertEqual(page.locator("#paper .line").count(), 4)
        self.assertEqual(page.get_by_role("button", name="a, current beat", exact=True).count(), 1)
        self.assertEqual(self.text(page, "#status-text"), "REPLAY")
        page.click("#replay-back")
        page.wait_for_function(f"document.getElementById('replay-at').textContent === 'event 3 of {self.EVENTS}'")
        self.assertEqual(page.locator("#paper .line").count(), 3)

    def test_the_scrubber_jumps_to_any_event_and_the_last_one_shows_how_the_run_ended(self):
        self.finished()
        page = self.open()
        page.click("#replay-open")
        page.wait_for_function("!document.getElementById('replay-scrub').disabled")
        page.locator("#replay-scrub").fill(str(self.EVENTS))
        page.wait_for_function(f"document.getElementById('replay-at').textContent === 'event {self.EVENTS} of {self.EVENTS}'")
        self.assertIn("done after 2 beats", self.text(page, "#ended"))
        self.assertEqual(page.get_by_role("button", name="c, final beat, current beat", exact=False).count(), 1)
        page.locator("#replay-scrub").fill("0")
        page.wait_for_function(f"document.getElementById('replay-at').textContent === 'event 0 of {self.EVENTS}'")
        self.assertEqual(page.locator("#paper .line").count(), 0)

    def test_the_scrubber_has_a_name_a_value_and_works_from_the_keyboard(self):
        self.finished()
        page = self.open()
        page.click("#replay-open")
        page.wait_for_function("!document.getElementById('replay-scrub').disabled")
        scrub = page.locator("#replay-scrub")
        self.assertEqual(scrub.get_attribute("aria-label"), "Event position in the replay")
        scrub.focus()
        page.keyboard.press("ArrowRight")
        page.keyboard.press("ArrowRight")
        page.wait_for_function(f"document.getElementById('replay-at').textContent === 'event 2 of {self.EVENTS}'")
        self.assertEqual(scrub.get_attribute("aria-valuetext"), f"event 2 of {self.EVENTS}")
        for name in ("STEP BACK", "PLAY", "STEP", "LIVE"):
            self.assertEqual(page.get_by_role("button", name=name, exact=True).count(), 1, name)

    def test_play_runs_to_the_end_by_itself_and_pause_holds_it(self):
        self.finished()
        page = self.open()
        page.click("#replay-open")
        page.wait_for_function("!document.getElementById('replay-scrub').disabled")
        page.click("#replay-play")
        page.wait_for_function("document.getElementById('replay-play').textContent === 'PAUSE'")
        page.wait_for_function(f"document.getElementById('replay-at').textContent === 'event {self.EVENTS} of {self.EVENTS}'")
        page.wait_for_function("document.getElementById('replay-play').textContent === 'PLAY'")  # it stops at the end
        page.locator("#replay-scrub").fill("1")
        page.click("#replay-play")
        page.click("#replay-play")  # paused at once
        held = self.text(page, "#replay-at")
        page.wait_for_timeout(300)
        self.assertEqual(self.text(page, "#replay-at"), held)

    def test_live_ends_the_replay_and_shows_the_run_as_it_is(self):
        self.finished()
        page = self.open()
        page.click("#replay-open")
        page.wait_for_function("!document.getElementById('replay-scrub').disabled")
        page.click("#replay-step")
        page.click("#replay-live")
        page.wait_for_function("document.getElementById('status-text').textContent === 'DONE'")
        self.assertTrue(page.locator("#replay").is_hidden())
        self.assertEqual(page.locator("#paper .line").count(), self.EVENTS)

    def test_a_log_that_cannot_be_read_is_refused_in_one_line_and_the_bar_stays_closed(self):
        folder = self.finished()
        lines = (folder / "events.jsonl").read_text(encoding="utf-8").splitlines()
        lines[1] = "{oops"
        (folder / "events.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
        page = self.open()
        page.click("#replay-open")
        page.wait_for_function("document.getElementById('replay-message').textContent.includes('line 2 is not readable')")
        self.assertTrue(page.locator("#replay").is_hidden() or page.locator("#replay-scrub").is_disabled())

    def test_a_run_that_is_still_going_cannot_be_replayed(self):
        write_run(self.runs, self.NAME, [{"event": "run_started", "at": stamp(-1), "play": "p.yaml", "mode": "live"}],
                  {"status": "running", "beats":{}})
        page = self.page()
        page.goto(self.start())
        page.wait_for_function("document.getElementById('status-text').textContent === 'RUNNING'")
        self.assertTrue(page.locator("#replay-open").is_disabled())
        self.assertIn("still going", page.locator("#replay-open").get_attribute("title"))

    def test_the_bar_is_readable_in_every_theme_and_mode_and_fits_a_phone(self):
        self.finished()
        base = self.start()
        problems = []
        # one look, not six: the bar reuses classes (.find-button, .readout, .start-message) that ContrastTest measures in all six

        def measure(page, label, selectors):
            for selector in selectors:
                found = page.evaluate(FIRST_VISIBLE_JS, selector)
                if found is None:
                    continue
                target = page.locator("[data-contrast-target]").first
                pixels = decode_png(target.screenshot())
                page.evaluate("document.querySelector('[data-contrast-target]')?.removeAttribute('data-contrast-target')")
                worst = min((contrast(found["color"], background) for background in backdrops(pixels)), default=21.0)
                if worst < 4.5:
                    problems.append(f"{label} {selector}: {worst:.2f}")

        for theme, mode in LOOKS[1:2]:  # steampunk, dark: where the one flake and the worst margins were
            page = self.page(390, 800)
            page.goto(f"{base}/?theme={theme}&mode={mode}")
            page.add_style_tag(content=HIDE_TEXT)
            page.wait_for_function("document.getElementById('status-text').textContent === 'DONE'")
            measure(page, f"{theme}/{mode}", ["#replay-open"])  # enabled now; a disabled control is exempt
            page.click("#replay-open")
            page.wait_for_function("!document.getElementById('replay-scrub').disabled")
            page.click("#replay-step")
            page.wait_for_function("document.getElementById('replay-at').textContent.startsWith('event 1 ')")
            box = page.locator("#replay").bounding_box()
            self.assertTrue(box and box["x"] >= 0 and box["x"] + box["width"] <= 390, f"{theme}/{mode} bar fits")
            measure(page, f"{theme}/{mode}", ["#replay-at", "#replay-step", "#replay-live", "#replay-message"])
        self.assertEqual(problems, [], "\n" + "\n".join(problems))


def a_decision(second, row, pick, options):
    return {"event": "decision", "at": stamp(second), "beat": "match", "row": row, "dimension": "temp", "pick": pick,
            "probability": 0.7, "options": options}


HOT = [{"name": "hot", "weight": 0.7, "removed_by": None}, {"name": "iced", "weight": 0.3, "removed_by": None}]
FORBIDDEN = [{"name": "small", "weight": 0.0, "removed_by": "forbid rule 2"}, {"name": "large", "weight": 0.7, "removed_by": None},
             {"name": "medium", "weight": 0.3, "removed_by": "shortlist"}]


class DecisionPanelTest(BrowserCase):
    NAME = "run-20261101T180000-00000001"

    def deciding(self, decisions, name=None):
        started = {"event": "run_started", "at": stamp(0), "play": "x/chart.yaml", "mode": "live", **STORY}
        events = [started, entered(1, "a", "start"), {"event": "beat_started", "at": stamp(2), "beat": "match"}, *decisions,
                  {"event": "beat_completed", "at": stamp(8), "beat": "match"}, {"event": "run_finished", "at": stamp(9), "outcome": "complete"}]
        return write_run(self.runs, name or self.NAME, events,
                         {"status": "complete", "beats":{"match": "complete"}, "mode": "live", "outcome": "complete"})

    def open(self):
        page = self.page()
        page.add_init_script("window.understudyReplayMs = 40;")
        page.goto(self.start())
        page.wait_for_function("document.getElementById('status-text').textContent === 'DONE'")
        return page

    def test_each_decision_opens_to_its_options_the_rule_that_removed_them_and_the_pick(self):
        self.deciding([a_decision(3, "teens", "hot", HOT), a_decision(4, "adults", "large", FORBIDDEN)])
        page = self.open()
        page.wait_for_function("document.getElementById('decisions-summary').textContent === 'DECISIONS · 2'")
        page.locator("#decisions-summary").click()
        self.assertEqual(page.locator(".decision-read").count(), 2)
        page.locator(".decision-read > summary").nth(1).click()
        text = page.locator(".decision-read").nth(1).inner_text()
        for expected in ("match", "adults", "temp", "large", "small", "removed by forbid rule 2", "held back by the shortlist", "picked"):
            self.assertIn(expected, text)
        self.assertEqual(page.locator(".decision-read").nth(1).locator(".option-row").count(), 3)
        self.assertEqual(page.locator(".decision-read").nth(1).locator(".option-row.picked").count(), 1)

    def test_a_run_with_no_decisions_says_so(self):
        self.deciding([])
        page = self.open()
        page.wait_for_function("document.getElementById('decisions-summary').textContent === 'DECISIONS'")
        page.locator("#decisions-summary").click()
        self.assertIn("made no decisions", page.locator("#decisions-list").inner_text())

    def test_a_decision_with_a_missing_field_shows_what_it_has_and_names_what_is_missing(self):
        self.deciding([{"event": "decision", "at": stamp(3), "beat": "match", "dimension": "temp"}])
        page = self.open()
        page.wait_for_function("document.getElementById('decisions-summary').textContent === 'DECISIONS · 1'")
        page.locator("#decisions-summary").click()
        page.locator(".decision-read > summary").first.click()
        self.assertIn("lacks row, pick, probability, options", page.locator(".decision-read").first.inner_text())

    def test_names_from_a_log_are_drawn_as_text_and_run_nothing(self):
        self.deciding([a_decision(3, "<b id='x'>teens</b>", "<img src=x onerror=window.pwned=1>", HOT)])
        page = self.open()
        page.wait_for_function("document.getElementById('decisions-summary').textContent === 'DECISIONS · 1'")
        page.locator("#decisions-summary").click()
        self.assertEqual(page.locator("#decisions-list b, #decisions-list img").count(), 0)
        self.assertIn("<b id='x'>teens</b>", page.locator("#decisions-list").inner_text())
        self.assertFalse(page.evaluate("Boolean(window.pwned)"))

    def test_the_printer_names_each_decision(self):
        self.deciding([a_decision(3, "teens", "hot", HOT)])
        page = self.open()
        self.assertIn("decision match: teens temp = hot (0.7)", page.locator("#paper .line.decision").first.inner_text())

    def test_in_a_replay_a_decision_in_the_list_or_in_the_printer_moves_the_cursor_to_its_event(self):
        self.deciding([a_decision(3, "teens", "hot", HOT), a_decision(4, "adults", "large", FORBIDDEN)])  # events 3 and 4 (0-based)
        page = self.open()
        page.locator("#decisions-summary").click()
        self.assertTrue(page.locator(".decision-read .jump").first.is_disabled())  # no replay open: nothing to move
        page.click("#replay-open")
        page.wait_for_function("!document.getElementById('replay-scrub').disabled")
        page.locator(".decision-read > summary").nth(1).click()
        page.locator(".decision-read").nth(1).locator(".jump").click()
        page.wait_for_function("document.getElementById('replay-at').textContent.startsWith('event 5 of ')")  # index 4 + 1
        page.locator("#paper .line.decision").first.click()
        page.wait_for_function("document.getElementById('replay-at').textContent.startsWith('event 4 of ')")  # index 3 + 1

    def test_the_panel_is_readable_in_every_theme_and_mode(self):
        self.deciding([a_decision(3, "teens", "hot", HOT), a_decision(4, "adults", "large", FORBIDDEN)])
        base = self.start()
        problems = []
        # one look, not six: the panel reuses classes (.jev > summary, .jev-level, .find-button) that ContrastTest measures in all six
        for theme, mode in LOOKS[1:2]:  # steampunk, dark
            page = self.page()
            page.goto(f"{base}/?theme={theme}&mode={mode}")
            page.add_style_tag(content=HIDE_TEXT)
            page.wait_for_function("document.getElementById('decisions-summary').textContent === 'DECISIONS · 2'")
            page.locator("#decisions-summary").click()
            page.locator(".decision-read > summary").nth(1).click()
            for selector in ("#decisions-summary", ".decision-read > summary", ".option-row", ".decision-note"):
                found = page.evaluate(FIRST_VISIBLE_JS, selector)
                if found is None:
                    continue
                target = page.locator("[data-contrast-target]").first
                pixels = decode_png(target.screenshot())
                page.evaluate("document.querySelector('[data-contrast-target]')?.removeAttribute('data-contrast-target')")
                worst = min((contrast(found["color"], background) for background in backdrops(pixels)), default=21.0)
                if worst < 4.5:
                    problems.append(f"{theme}/{mode} {selector}: {worst:.2f}")
        self.assertEqual(problems, [], "\n" + "\n".join(problems))


if __name__ == "__main__":
    unittest.main()
