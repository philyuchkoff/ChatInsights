"""
ChatInsights - AI Chat Export Analysis Tool
Copyright (C) 2025 Eden_Eldith (P.C. O'Brien) c:

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.
"""

import argparse
import sys


def main():
    """Launch the app: GUI by default, CLI with --cli."""
    parser = argparse.ArgumentParser(description="ChatInsights - AI Chat Export Analysis Tool")
    parser.add_argument("--cli", action="store_true", help="Run in command-line mode (no GUI)")
    parser.add_argument("rest", nargs=argparse.REMAINDER)
    args = parser.parse_args()

    if args.cli:
        from chatinsights.cli import main as cli_main

        sys.exit(cli_main(args.rest))

    from chatinsights.gui import main as gui_main

    gui_main()


if __name__ == "__main__":
    main()
