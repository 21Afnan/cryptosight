import sys
from pathlib import Path

# Ensure root workspace (`d:\Neurog_Internship`) is in Python path so direct execution works anywhere
root_workspace = Path(__file__).resolve().parent.parent.parent
if str(root_workspace) not in sys.path:
    sys.path.insert(0, str(root_workspace))

from cryptosight.utils.logger import get_logger
from cryptosight.utils.config import load_config

logger = get_logger("PPMain")


class PreprocessingMain:
    """
    Master initialization class for the Quantitative Preprocessing Module.
    Sets up config file paths, loads the `pconfig.yaml` dictionary, and initializes
    the 3 required output directory paths (`preprocessed_data`, `model_predicted`, `backtest_ledgers`).
    """

    def __init__(self, config_path: str | Path = None):
        if config_path is None:
            self.config_path = Path(__file__).resolve().parent / "pconfig.yaml"
        else:
            self.config_path = Path(config_path)

        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found at: {self.config_path}")

        self.config = load_config(self.config_path)
        self.model_task = str(self.config["model_task"]).lower()

        root_dir = Path(__file__).resolve().parent.parent / "csv_files" / self.model_task
        subfolders = self.config["output_dirs"]["subfolders"]

        self.output_dirs = {
            "preprocessed": root_dir / subfolders["preprocess"],
            "predicted_signals": root_dir / subfolders["predicted_signals"],
            "backtest_ledgers": root_dir / subfolders["backtest_ledgers"],
        }

        for name, path_obj in self.output_dirs.items():
            path_obj.mkdir(parents=True, exist_ok=True)

        logger.info(f"Initialized PreprocessingMain | Task: {self.model_task.upper()} | Config: {self.config_path.name}")


if __name__ == "__main__":
    app = PreprocessingMain()
    print("\n=== Preprocessing Module Ready ===")
    print(f"Config Path : {app.config_path}")
    print(f"Model Task  : {app.model_task.upper()}")
    for folder_name, folder_path in app.output_dirs.items():
        print(f"  -> {folder_name}: {folder_path.resolve()}")
