"""
Startup and navigation test for AtmosCast Streamlit application.
Uses Streamlit's official AppTest framework to verify layout, widgets, and navigation.
"""

import unittest
from pathlib import Path
from streamlit.testing.v1 import AppTest


class TestStreamlitApp(unittest.TestCase):
    """Verifies that the Streamlit application shell loads and renders all pages cleanly."""

    def setUp(self):
        self.app_path = str(Path(__file__).resolve().parent.parent / "app.py")

    def test_app_initial_load(self):
        """Test that the application loads with zero unhandled exceptions."""
        at = AppTest.from_file(self.app_path).run(timeout=30)
        self.assertEqual(
            len(at.exception),
            0,
            f"App crashed on initial load with exception: {at.exception}",
        )
        # Check that title/hero is present
        self.assertTrue(len(at.markdown) > 0, "No markdown elements rendered")

    def test_sidebar_elements(self):
        """Test that the sidebar contains navigation radio and station selectbox."""
        at = AppTest.from_file(self.app_path).run(timeout=30)
        self.assertGreaterEqual(len(at.sidebar.radio), 1, "Sidebar missing navigation radio")
        self.assertGreaterEqual(len(at.sidebar.selectbox), 1, "Sidebar missing station selectbox")

        # Verify all 8 pages exist in navigation
        nav_options = at.sidebar.radio[0].options
        self.assertEqual(len(nav_options), 8, f"Expected 8 navigation pages, got {len(nav_options)}")

    def test_navigation_across_all_pages(self):
        """Verify that every view renders without runtime exceptions."""
        at = AppTest.from_file(self.app_path).run(timeout=30)
        radio = at.sidebar.radio[0]
        for option in radio.options:
            at = radio.set_value(option).run(timeout=30)
            self.assertEqual(
                len(at.exception),
                0,
                f"Exception raised while navigating to page '{option}': {at.exception}",
            )

    def test_station_selection(self):
        """Verify that station selector can change stations without exception."""
        at = AppTest.from_file(self.app_path).run(timeout=30)
        station_select = at.sidebar.selectbox[0]
        options = station_select.options
        self.assertGreaterEqual(len(options), 4, "Expected at least 4 station options")
        for st_name in options:
            at = station_select.set_value(st_name).run(timeout=30)
            self.assertEqual(
                len(at.exception),
                0,
                f"Exception raised when selecting station '{st_name}': {at.exception}",
            )


if __name__ == "__main__":
    unittest.main()
