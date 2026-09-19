from pathlib import Path
import re


ROOT = Path(__file__).parents[1]
SHELL = ROOT / "web" / "pyd4"


def _read(relative):
    return (SHELL / relative).read_text()


def test_mobile_shell_exposes_explicit_immersive_and_rotation_controls():
    html = _read("index.html")

    assert 'id="immersive"' in html
    assert 'id="orientation-guidance"' in html
    assert 'id="orientation-detail"' in html
    assert "manual rotation" in html.lower()


def test_mobile_css_uses_viewport_safe_area_and_touch_constraints():
    css = _read("styles.css")

    assert "100dvh" in css
    assert "--app-height" in css
    assert "env(safe-area-inset-top)" in css
    assert "env(safe-area-inset-bottom)" in css
    assert "touch-action: manipulation" in css
    assert "min-height: 3rem" in css
    body_rule = re.search(r"(?m)^body \{([^}]*)\}", css).group(1)
    assert "overflow: hidden" in body_rule
    assert "orientation: portrait" in css


def test_mobile_javascript_handles_orientation_and_progressive_enhancement():
    javascript = _read("js/pyd4.js")

    assert 'matchMedia("(orientation: portrait)")' in javascript
    assert "addEventListener(\"change\"" in javascript
    assert "window.addEventListener(\"resize\"" in javascript
    assert "window.innerHeight" in javascript
    assert "requestFullscreen" in javascript
    assert 'screen.orientation.lock("landscape")' in javascript
    assert "manual rotation" in javascript.lower()
    assert "catch" in javascript
