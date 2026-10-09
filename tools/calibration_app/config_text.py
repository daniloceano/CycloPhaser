"""Sentences the app shows about a loaded configuration — one wording, two pages.

The Calibrate page (YAML import) and the Compare page (a configuration column)
both report the keys a file does not carry and the keys the package does not
read. They must say it in the same words, so the sentences live here and both
pages call these functions rather than each typing its own.
"""

from __future__ import annotations


def filled_keys_that_matter(filled) -> list[tuple[str, object, object]]:
    """The filled keys whose value differs from the package's default today.

    A key filled with the same value the package would use anyway changes
    nothing a reader needs to know (the rule still filled it, and the full
    configuration still shows it). Compared after the app's `use_filter`
    translation and with `compare_core._same`'s float tolerance; a key the
    package signature does not know is left out (it is not applied).

    Args:
        filled: [("section.key", value used), ...], as `fill_missing` returns it.

    Returns:
        [("section.key", value used, package default), ...], in the given order.
    """
    import benchmark_core as bc               # sibling module; lazy, keeps this light
    from compare_core import _same
    from package_args import package_use_filter

    current = bc.current_defaults()
    out = []
    for key, value in filled:
        section, name = key.split(".", 1)
        if name not in current.get(section, {}):
            continue
        default = current[section][name]
        a, b = value, default
        if name == "use_filter":
            a, b = package_use_filter(a), package_use_filter(b)
        if not _same(a, b):
            out.append((key, value, default))
    return out


def filled_keys_sentence(filled) -> str:
    """The warning for keys absent from a file and filled by the rule of
    `research/labels/config_defaults.fill_missing` — only those whose filled
    value differs from the package's default today (`filled_keys_that_matter`).

    Args:
        filled: [("section.key", value used), ...], as `fill_missing` returns it.

    Returns:
        The sentence, or "" when no filled key differs.
    """
    keys = filled_keys_that_matter(filled)
    if not keys:
        return ""
    return (f"{len(keys)} key(s) absent from this file were filled with the "
            "earlier defaults older configuration files were written against, "
            "which differ from the package's defaults: "
            + ", ".join(f"{k}={v!r} (package default {d!r})" for k, v, d in keys))


def ignored_keys_sentence(ignored) -> str:
    """The warning for keys a file carries that are not applied.

    Args:
        ignored: the key names (\"section.key\", possibly with a reason).

    Returns:
        The sentence, or "" when nothing was ignored.
    """
    if not ignored:
        return ""
    return f"Ignored keys: {', '.join(ignored)}"
