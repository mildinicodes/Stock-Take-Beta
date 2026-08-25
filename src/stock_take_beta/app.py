from .services.progress_store import ProgressStore
from .ui.main_window import MainWindow


def run() -> None:
    store = ProgressStore()
    app = MainWindow(progress_store=store)
    app.mainloop()
