import logging
import threading
from pathlib import Path

import pandas as pd
from apscheduler.schedulers.background import BackgroundScheduler

from ib_ox_api.settings import settings

logger = logging.getLogger(__name__)


class DataStore:
    """Thread-safe data store for the questionnaire DataFrame."""

    def __init__(self, data_path: str, refresh_hours: int) -> None:
        self._data_path = Path(data_path)
        self._refresh_hours = refresh_hours
        self._df: pd.DataFrame = pd.DataFrame()
        self._lock = threading.Lock()
        self._scheduler = BackgroundScheduler()

    def _load(self) -> pd.DataFrame:
        path = self._data_path
        if path.suffix.lower() in {".parquet", ".pq"}:
            return pd.read_parquet(path)
        return pd.read_csv(path, dtype_backend="numpy_nullable")

    def refresh(self) -> None:
        """Reload data from disk, replacing the in-memory DataFrame."""
        logger.info("Refreshing data from %s", self._data_path)
        try:
            df = self._load()
        except FileNotFoundError:
            logger.warning("Data file not found: %s — keeping previous data", self._data_path)
            return
        except Exception:
            logger.exception("Failed to load data from %s — keeping previous data", self._data_path)
            return
        with self._lock:
            self._df = df
        logger.info("Data refreshed: %d rows, %d columns", len(df), len(df.columns))

    def get_dataframe(self) -> pd.DataFrame:
        """Return a snapshot of the current DataFrame."""
        with self._lock:
            return self._df.copy()

    def startup(self) -> None:
        """Initial load and schedule periodic refresh."""
        self.refresh()
        if self._refresh_hours > 0:
            self._scheduler.add_job(
                self.refresh,
                trigger="interval",
                hours=self._refresh_hours,
                id="data_refresh",
            )
            self._scheduler.start()
            logger.info("Data refresh scheduled every %d hour(s)", self._refresh_hours)

    def shutdown(self) -> None:
        """Stop the background scheduler."""
        if self._scheduler.running:
            self._scheduler.shutdown(wait=False)
            logger.info("Data refresh scheduler stopped")


# Module-level singleton
datastore = DataStore(
    data_path=settings.DATA_PATH,
    refresh_hours=settings.DATA_REFRESH_HOURS,
)
