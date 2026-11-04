"""`understudy run --watch`: a console for the one run being made (ADR-0058).

It is the dashboard's server, bound to this machine only and able to hold, step and resume that one run (and no other),
started before the run so the run can begin held. The access secret is saved to the same git-ignored file the dashboard
uses and is never printed.
"""

import secrets
import threading
from pathlib import Path

from src.dashboard.server import SECRET_FILE as DASHBOARD_SECRET_FILE
from src.dashboard.server import save_secret, serve

HOST = "127.0.0.1"
SECRET_FILE = DASHBOARD_SECRET_FILE.with_name("watch.secret")  # not the dashboard's file: a watch must not lock its owner out of it


class Watch:
    """A console on `root` for the run that `started` is told about."""

    def __init__(self, root: Path, port: int, stdout):
        self.run_id: str | None = None
        self.stdout = stdout
        secret = secrets.token_urlsafe(32)
        self.server = serve(root, port, host=HOST, secret=secret, controllable=lambda run: run == self.run_id)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.address = f"http://{HOST}:{self.server.server_address[1]}"
        save_secret(SECRET_FILE, secret)
        stdout.write(f"watching: {self.address}  (this machine only)\n")
        stdout.write(f"access secret for pause, step and resume: saved in {SECRET_FILE} (read it there; it changes at every start)\n")
        stdout.flush()

    def started(self, directory: Path) -> None:
        """The run made its folder: from now on this console may hold that run."""
        self.run_id = directory.name
        self.stdout.write(f"watching run {self.run_id}\n")
        self.stdout.flush()

    def close(self) -> None:
        self.server.shutdown()
        self.server.server_close()
