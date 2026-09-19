import threading
import uvicorn


from common.scheduler import start_daemon
from common.app import app
from common.logging_config import setup_logging


def run_server():
    uvicorn.run(app, host = "0.0.0.0", port = 8000)

if __name__ == '__main__':

        setup_logging()

        daemon_thread = threading.Thread(
            target = start_daemon,
            daemon = True
        )

        server_thread = threading.Thread(
            target = run_server,
            daemon = True
        )

        daemon_thread.start()
        server_thread.start()

        # if no .join() main just exits instantly
        daemon_thread.join()
        server_thread.join()


