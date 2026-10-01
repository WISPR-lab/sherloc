from htmlclean import clean_description


def test_script_is_removed_with_its_content():
    assert clean_description("a<script>alert(1)</script>b") == "ab"


def test_style_is_removed_with_its_content():
    assert clean_description("a<style>body{x:y}</style>b") == "ab"


def test_attributes_are_stripped_from_allowed_tags():
    assert clean_description('<b onclick="x()" class="c">t</b>') == "<b>t</b>"


def test_disallowed_tags_are_dropped_but_their_text_is_kept():
    assert clean_description('<a href="javascript:x()">go</a>') == "go"
    assert clean_description("<iframe src=x></iframe>text") == "text"
    assert clean_description("<img src=x onerror=y>") == ""


def test_text_is_escaped():
    assert clean_description("1 < 2 & 3 > 2") == "1 &lt; 2 &amp; 3 &gt; 2"
    assert clean_description("&lt;script&gt;") == "&lt;script&gt;"


def test_allowed_formatting_survives():
    html = "<p>One<br>Two</p><ul><li>a</li><li><i>b</i></li></ul>"
    assert clean_description(html) == html


def test_unclosed_tags_are_closed():
    assert clean_description("<b>bold") == "<b>bold</b>"


def test_stray_closing_tags_are_ignored():
    assert clean_description("a</b>b</script>c") == "abc"


def test_none_and_non_strings_become_empty():
    assert clean_description(None) == ""
    assert clean_description(float("nan")) == ""
