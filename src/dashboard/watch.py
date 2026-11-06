"""`understudy run --watch`: a console for the one run being made (ADR-0058).

It is the dashboard's server, bound to this machine only and able to hold, step and resume that one run (and no other),
started before the run so the run can begin held.
"""

import threading
from pathlib import Path

from src.dashboard.server import serve

HOST = "127.0.0.1"


class Watch:
    """A console on `root` for the run that `started` is told about."""

    def __init__(self, root: Path, port: int, stdout):
        self.run_id: str | None = None
        self.stdout = stdout
        self.server = serve(root, port, host=HOST, controllable=lambda run: run == self.run_id)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.address = f"http://{HOST}:{self.server.server_address[1]}"
        stdout.write(f"watching: {self.address}  (this machine only)\n")
        stdout.flush()

    def started(self, directory: Path) -> None:
        """The run made its folder: from now on this console may hold that run."""
        self.run_id = directory.name
        self.stdout.write(f"watching run {self.run_id}\n")
        self.stdout.flush()

    def close(self) -> None:
        self.server.shutdown()
        self.server.server_close()
