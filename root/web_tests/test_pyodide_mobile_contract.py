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


def test_phase_shell_contains_scrolling_without_document_or_shell_overflow():
    css = _read("styles.css")
    shell_rule = re.search(r"(?m)^\.app-shell \{([^}]*)\}", css).group(1)
    battle_rule = re.search(r"(?m)^\.battle-screen \{([^}]*)\}", css).group(1)
    controls_rule = re.search(r"(?m)^\.battle-controls \{([^}]*)\}", css).group(1)

    assert "display: grid" in shell_rule
    assert "grid-template-rows: auto minmax(0, 1fr)" in shell_rule
    assert "overflow: hidden" in shell_rule
    assert "display: flex" in battle_rule
    assert "min-height: 0" in battle_rule
    assert "overflow: hidden" in battle_rule
    assert "min-height: 0" in controls_rule
    assert "overflow-y: auto" in controls_rule
    assert "overscroll-behavior: contain" in controls_rule


def test_mobile_move_and_target_phases_use_a_dedicated_surface_only_on_mobile():
    css = _read("styles.css")
    javascript = _read("js/pyd4.js")

    assert "dataset.interactionPhase = phase" in javascript
    assert "@media (max-width: 60rem)" in css
    assert '.battle-screen[data-interaction-phase="regular_moves"]' in css
    assert '.battle-screen[data-interaction-phase="targets"]' in css
    assert ".app-header" in css
    assert ".battle-status" in css
    assert ".battle-log" in css
    assert "overflow-y: hidden" in css


def test_mobile_character_surfaces_isolate_the_page_and_keep_navigation_at_the_bottom():
    css = _read("styles.css")
    javascript = _read("js/pyd4.js")
    html = _read("index.html")
    smoke = (ROOT / "web_tests" / "browser_smoke.mjs").read_text()

    assert "dataset.detailScreen = view.screen" in javascript
    assert '.overworld-screen[data-detail-screen] #route-panel' in css
    assert "detail-page-content" in html
    assert ".detail-page-content" in css
    assert "mobileDetailLayout" in smoke
    assert 'captureScreenshot(page, "mobile-character")' in smoke


def test_battle_choices_keep_touch_targets_and_wrap_authored_detail():
    css = _read("styles.css")
    choice_rule = re.search(r"(?m)^\.battle-choice \{([^}]*)\}", css).group(1)
    back_rule = re.search(r"(?m)^\.back-option \{([^}]*)\}", css).group(1)
    summary_rule = re.search(r"(?m)^\.choice-summary \{([^}]*)\}", css).group(1)

    assert "min-height: 3rem" in choice_rule
    assert "min-height: 3rem" in back_rule
    assert "white-space: normal" in summary_rule
    assert "overflow-wrap: anywhere" in summary_rule


def test_playwright_smoke_qualifies_responsive_phases_and_captures_evidence():
    smoke = (ROOT / "web_tests" / "browser_smoke.mjs").read_text()

    for required in (
        "width: 1440, height: 900",
        "width: 844, height: 390",
        "width: 390, height: 844",
        "landscape-phone Battle Actions",
        "landscape-phone Move Selection",
        "mobile Move Selection should replace Battle context only on mobile",
        "mobile move resolution did not return to Battle Actions",
        "portrait guidance",
        "controlsScrollable",
        "orientationGuidanceVisible",
        'captureScreenshot(page, "desktop-overworld")',
        'captureScreenshot(page, "desktop-battle-actions")',
        'captureScreenshot(page, "desktop-move-selection")',
        'captureScreenshot(targetPage, "desktop-target-selection")',
        'captureScreenshot(page, "landscape-battle-actions")',
        'captureScreenshot(page, "landscape-move-selection")',
    ):
        assert required in smoke


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
