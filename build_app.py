# build_app.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from atomforge import AtomSpace
from atomforge.renderer import Renderer
from atomforge.csv_import import import_links_csv
from write_log import WriteLog
from monitor import Monitor


def create_app() -> FastAPI:
    app = FastAPI()
    app.state.monitor = Monitor(enabled=True)

    # CORS (nginx friendly)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Core engine
    mem = AtomSpace()
    render = Renderer(mem)

    # Optional seed data
    data_dir = Path(__file__).resolve().parent / "data"
    links_path = data_dir / "links.csv"

    if links_path.exists():
        report = import_links_csv(mem, str(links_path))
        print(report)

    # Store in app state
    app.state.mem = mem
    app.state.render = render
    app.state.write_log = WriteLog(max_events=500)

    return app
