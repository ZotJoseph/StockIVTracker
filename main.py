import threading
import uvicorn

from controller.scheduler import start_daemon
from controller.app import app


def run_server():
    uvicorn.run(app, host = "0.0.0.0", port = 8000)

if __name__ == '__main__':

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


