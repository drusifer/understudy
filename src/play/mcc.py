"""The names a new category may take: the ISO 18245 merchant category list (UND-55).

The list is the MIT `iso18245` package (ISO 18245:2003 codes with network descriptions). Only the
ISO descriptions and the code ranges' group names are offered, and codes reserved for private use
are left out. Jev chooses a group and then a name from here; it never writes a name.
"""

from collections.abc import Callable

import iso18245


class MccError(Exception):
    """The MCC list is not available; the run stops before any naming."""


def load_mcc(get_all: Callable[[], list] = iso18245.get_all_mccs) -> dict[str, list[str]]:
    """{group name: sorted distinct ISO descriptions} for the codes in use."""
    try:
        codes = list(get_all())
    except Exception as error:  # the package's own data failing to load, whatever the cause
        raise MccError(f"the MCC list cannot be read: {error}") from error
    groups: dict[str, set[str]] = {}
    for code in codes:
        if code.range.reserved or not code.iso_description:
            continue
        groups.setdefault(code.range.description, set()).add(code.iso_description.strip())
    if not groups:
        raise MccError("the MCC list cannot be read: it holds no codes in use")
    return {group: sorted(names) for group, names in sorted(groups.items())}
