from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class InterfaceSystemTests(unittest.TestCase):
    def test_component_lab_is_packaged_as_static_web_assets(self) -> None:
        html = (ROOT / "web" / "components.html").read_text(encoding="utf-8")
        css = (ROOT / "web" / "components.css").read_text(encoding="utf-8")
        script = (ROOT / "web" / "components.js").read_text(encoding="utf-8")

        for component in ("Button", "Field", "Tabs", "Evidence claim", "Timeline cue", "Trace session"):
            self.assertIn(component, html)
        for state in ('data-state="empty"', 'data-state="loading"', 'data-state="error"', 'data-state="success"'):
            self.assertIn(state, html)
        self.assertIn("prefers-reduced-motion", css)
        self.assertIn("aria-selected", script)

    def test_workbench_links_to_interface_system(self) -> None:
        html = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
        self.assertIn('href="./components.html"', html)
        self.assertIn('src="./static-demo.js', html)

    def test_static_assets_use_subpath_safe_relative_urls(self) -> None:
        workbench = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
        components = (ROOT / "web" / "components.html").read_text(encoding="utf-8")
        self.assertIn('href="./styles.css', workbench)
        self.assertIn('src="./app.js', workbench)
        self.assertIn('href="./styles.css', components)
        self.assertIn('href="./components.css', components)
        self.assertNotIn('href="/components.html"', workbench)
        self.assertNotIn('href="/"', components)


if __name__ == "__main__":
    unittest.main()
