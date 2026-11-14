"""Audit installed signatures and each requested API, without pretending NAV is OHLCV."""
import inspect
import importlib.metadata
from pathlib import Path
import efinance as ef
from quant_research.data.provider import EfinanceProvider
from quant_research.data.storage import write_json


def main():
    provider = EfinanceProvider(timeout=20,retries=0)
    cases = [("stock.get_quote_history",dict(stock_codes="600519",beg="20250101",end="20251231",klt=101,fqt=0,use_id_cache=False)),
             ("stock.get_realtime_quotes",dict(fs="ETF")),
             ("fund.get_quote_history",dict(fund_code="161725",pz=10)),
             ("futures.get_quote_history",dict(quote_ids="113.rb",beg="20250101",end="20251231",klt=101,fqt=0)),
             ("futures.get_realtime_quotes",{}),("futures.get_futures_base_info",{})]
    report = dict(version=importlib.metadata.version("efinance"),apis=[])
    for method,kwargs in cases:
        mod,name = method.split(".")
        fn = getattr(getattr(ef,mod),name)
        item = dict(method=method,signature=str(inspect.signature(fn)),parameters=kwargs)
        try:
            frame,_ = provider.request(method,**kwargs)
            item.update(status="SUPPORTED",rows=len(frame),columns=list(frame.columns),sample=frame.head(2).to_dict("records"))
            if mod=="fund":
                item.update(ohlcv_compatible=False,note="NAV data cannot be converted to tradable OHLCV")
        except Exception as exc:
            item.update(status="ERROR",error=str(exc))
        report["apis"].append(item)
        write_json(Path("docs")/"efinance_api_audit.json",report)
        print(method,item["status"],flush=True)


if __name__=="__main__":
    main()

