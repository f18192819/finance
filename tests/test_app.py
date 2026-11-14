from streamlit.testing.v1 import AppTest


def test_dashboard_pages_without_data():
    app=AppTest.from_file("app.py",default_timeout=30).run()
    assert not app.exception
    for name in ("鏁版嵁涓績","甯傚満鎵弿","绛栫暐瀹為獙瀹?,"鍘嗗彶鍥炴祴","缁勫悎鍒嗘瀽","浜ゆ槗璁板綍涓庤鍒?,"绯荤粺璁剧疆"):
        app.sidebar.radio[0].set_value(name).run()
        assert not app.exception


def test_dashboard_runs_loaded_data_backtest(dataset,tmp_path,monkeypatch):
    from quant_research.app import dashboard
    from quant_research.research.experiments import ExperimentManager
    manager=ExperimentManager(tmp_path/"ui_experiments")
    monkeypatch.setattr(dashboard,"ExperimentManager",lambda:manager)
    dataset.bars["symbol"]="510300"
    app=AppTest.from_file("app.py",default_timeout=30).run()
    app.session_state["datasets"]={"510300":dataset}
    app.sidebar.radio[0].set_value("鍘嗗彶鍥炴祴").run()
    next(b for b in app.button if b.label=="杩愯骞朵繚瀛樺洖娴?).click().run()
    assert not app.exception and not app.error
    assert len(manager.list())==1
    assert len(app.metric)>=4

