from .config import CROSSLIST_PROFILE_DIR
from .mobile_server import start_mobile_server
from .services.audit_service import AuditService
from .services.progress_store import ProgressStore
from .ui.main_window import MainWindow


def run() -> None:
    store = ProgressStore()
    service = AuditService(store=store, profile_dir=CROSSLIST_PROFILE_DIR)
    mobile_url = start_mobile_server(service)
    app = MainWindow(progress_store=store, audit_service=service, mobile_url=mobile_url)
    app.mainloop()
