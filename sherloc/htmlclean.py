"""Reduce untrusted HTML to a few formatting tags.

App descriptions come from Play Store and App Store crawls. Anyone who
publishes an app controls that text, so it is never rendered as-is.
"""

from html import escape
from html.parser import HTMLParser

ALLOWED = {"b", "strong", "i", "em", "u", "br", "p", "ul", "ol", "li"}
VOID = {"br"}
DROP_CONTENT = {"script", "style", "iframe", "object", "embed", "template", "noscript"}


class _Cleaner(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out = []
        self.open = []
        self.skip = 0  # depth inside a tag whose content is dropped

    def handle_starttag(self, tag, attrs):
        if self.skip:
            if tag in DROP_CONTENT:
                self.skip += 1
            return
        if tag in DROP_CONTENT:
            self.skip = 1
        elif tag in ALLOWED:
            # attributes are never copied
            self.out.append(f"<{tag}>")
            if tag not in VOID:
                self.open.append(tag)

    def handle_startendtag(self, tag, attrs):
        if not self.skip and tag in ALLOWED and tag in VOID:
            self.out.append(f"<{tag}>")

    def handle_endtag(self, tag):
        if self.skip:
            if tag in DROP_CONTENT:
                self.skip -= 1
            return
        if tag in ALLOWED and tag not in VOID and tag in self.open:
            while self.open:
                top = self.open.pop()
                self.out.append(f"</{top}>")
                if top == tag:
                    break

    def handle_data(self, data):
        if not self.skip:
            self.out.append(escape(data, quote=True))


def clean_description(value):
    """Return `value` as safe HTML. Non-strings (None, NaN) give ''."""
    if not isinstance(value, str):
        return ""
    cleaner = _Cleaner()
    cleaner.feed(value)
    cleaner.close()
    while cleaner.open:
        cleaner.out.append(f"</{cleaner.open.pop()}>")
    return "".join(cleaner.out)
