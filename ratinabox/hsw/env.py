"""
Environment configuration loader for HSW simulations.

This module loads path configurations from a .env file and validates
that all required environment variables are set.

Usage:
    from env import config

    # Access paths
    matlab_path = config.MATLAB_FILE_PATH
    save_dir = config.get_save_directory(model_name='additive')
"""

import os
from pathlib import Path
from dotenv import load_dotenv


class MissingEnvironmentVariable(Exception):
    """Raised when a required environment variable is not set."""
    pass


class EnvConfig:
    """Configuration class that loads and validates environment variables."""

    # Required environment variables
    REQUIRED_VARS = [
        'MATLAB_FILE_PATH',
        'SAVE_DIRECTORY',
        'TRAINING_DATA_DIR',
    ]


    def __init__(self, env_file: str = None):
        """
        Initialize configuration from environment variables.

        Args:
            env_file: Optional path to .env file. If not provided, looks for
                     .env in the same directory as this module.
        """
        # Determine .env file location
        if env_file is None:
            env_file = Path(__file__).parent / '.env'

        # Load .env file
        self._load_env_file(env_file)

        # Load and validate required variables
        self._load_variables()

    def _load_env_file(self, env_file: Path) -> None:
        """Load environment variables from .env file."""
        env_path = Path(env_file)

        if not env_path.exists():
            raise FileNotFoundError(
                f"Environment file not found: {env_path}\n"
                f"Please copy .env.example to .env and configure your paths."
            )

        load_dotenv(env_path)

    def _load_variables(self) -> None:
        """Load and validate all required environment variables."""
        missing = []

        for var in self.REQUIRED_VARS:
            value = os.environ.get(var)
            if value is None:
                missing.append(var)
            else:
                setattr(self, var, value)

        if missing:
            raise MissingEnvironmentVariable(
                f"Missing required environment variables: {', '.join(missing)}\n"
                f"Please set these in your .env file."
            )

    def get_matlab_file_path(self) -> str:
        """Get the MATLAB file path from the environment configuration."""
        return self.MATLAB_FILE_PATH

    def get_save_directory(self, model_name: str = None) -> str:
        """
        Get the save directory, optionally with a model-specific subdirectory.

        Args:
            model_name: Optional model name for subdirectory (e.g., 'additive', 'dependent').

        Returns:
            Path to the save directory.
        """
        if model_name:
            return os.path.join(self.SAVE_DIRECTORY, f"{model_name}_results")
        return self.SAVE_DIRECTORY

    def get_training_data_dir(self) -> str:
        """Get the training data directory from the environment configuration."""
        return self.TRAINING_DATA_DIR

    def setup_ratinabox_figure_directory(self, save_directory: str = None) -> None:
        """
        Configure ratinabox figure directory.

        Args:
            save_directory: Directory to use. If None, uses SAVE_DIRECTORY.
        """
        import ratinabox
        directory = save_directory or self.SAVE_DIRECTORY
        ratinabox.figure_directory = directory
        os.makedirs(directory, exist_ok=True)


# Create a singleton instance for easy import
config = EnvConfig()
