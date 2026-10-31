import argparse
from core_ui.grid_renderer import launch


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--game",
        choices=["akari", "tents"],
        default="akari",
    )
    launch(parser.parse_args().game)