"""Sentences the app shows about a loaded configuration — one wording, two pages.

The Calibrate page (YAML import) and the Compare page (a configuration column)
both report the keys a file does not carry and the keys the package does not
read. They must say it in the same words, so the sentences live here and both
pages call these functions rather than each typing its own. The Validate page
(benchmark review, I2) shows the same cards, so it calls them too, and the
card's list of differences is formatted here for the same reason.

Narrow cards
------------
A card is a few hundred pixels wide, and a key such as
`phase_params.prominence_relative=None` has no place to break, so the browser
cut it mid-word ("prominence_rel / ative", I1 checkpoint). `warning_html` and
`differences_html` give such names a break opportunity after each "." and "_",
and nowhere else, with `<wbr>`: an HTML break point that adds no character, so a
key copied from the card is the key itself. (An invisible U+200B did the same
job in I2 round 1 and was removed: copied into a YAML it made the key unknown,
listed as ignored while looking identical to the right one.)
"""

from __future__ import annotations

import html
import re

# A "." or "_" between two identifier characters: the only places a card may
# break a key name.
_JOINT = re.compile(r"(?<=[A-Za-z0-9])([._])(?=[A-Za-z])")
# A warning block in the app's own colours: the text keeps the theme's colour
# and the tint is translucent, so it reads on the light and the dark theme alike.
_WARNING_STYLE = ("background:rgba(255,189,69,0.18);border-left:4px solid "
                  "rgba(255,189,69,0.9);border-radius:6px;padding:10px 14px;"
                  "margin:0 0 12px 0;font-size:0.92rem;line-height:1.45;"
                  "overflow-wrap:break-word")


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


def _with_breaks(text: str) -> str:
    """HTML-escaped `text` with a <wbr> after every "." or "_" that joins two
    parts of a name; a number such as 0.3 is untouched."""
    return _JOINT.sub(lambda m: m.group(1) + "<wbr>", html.escape(text, quote=False))


def warning_html(sentence: str) -> str:
    """A card's warning (`filled_keys_sentence` or `ignored_keys_sentence`) as a
    warning-looking block for `st.markdown(..., unsafe_allow_html=True)`.

    The words are the sentence's; names may break only after "." or "_". Its text
    without the tags is the sentence itself, so whatever is copied from it is
    what the sentence says.
    """
    return (f"<div class='cp-config-warning' style='{_WARNING_STYLE}'>"
            f"{_with_breaks(sentence)}</div>")


def differences_html(diffs) -> str:
    """A card's list of differences, one line per parameter:
    "`section.key`: <this> (reference: <reference>)".

    The reference value is named as such, so the line cannot be read as "changed
    from → to" (I1 checkpoint, pending item 1). Names break only after a "." or
    "_" (see the module docstring); a value too long for the card still wraps
    rather than overflowing it.

    Args:
        diffs: {"section.key": (this value, reference value)}, as
            `compare_core.config_differences` returns it.

    Returns:
        The HTML for `st.markdown(..., unsafe_allow_html=True)`.
    """
    style = ("margin:0 0 4px 0;font-size:0.85rem;line-height:1.35;"
             "overflow-wrap:break-word")
    code = "white-space:normal;overflow-wrap:break-word"

    lines = "".join(
        f"<div style='{style}'><code style='{code}'>{_with_breaks(k)}</code>: "
        f"{html.escape(repr(a))} (reference: {html.escape(repr(b))})</div>"
        for k, (a, b) in diffs.items())
    return f"<div>{lines}</div>"
