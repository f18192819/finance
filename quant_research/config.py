from pathlib import Path
import yaml
from .models import Instrument

ROOT = Path(__file__).resolve().parents[1]


def load_config(name):
    with (ROOT / "config" / f"{name}.yaml").open(encoding="utf-8") as f:
        return yaml.safe_load(f)


class InstrumentRegistry:
    def __init__(self, path=None):
        values = yaml.safe_load(Path(path).read_text(encoding="utf-8")) if path else load_config("instruments")
        self.instruments = {v["symbol"]: Instrument(**v) for v in values}

    def get(self, symbol):
        if symbol not in self.instruments:
            raise ValueError(f"Unknown instrument {symbol}; configure currency, exchange sessions and contract rules first")
        return self.instruments[symbol]

    def register(self, instrument):
        if instrument.symbol in self.instruments:
            raise ValueError("Instrument already registered")
        self.instruments[instrument.symbol] = instrument

    def all(self):
        return list(self.instruments.values())
