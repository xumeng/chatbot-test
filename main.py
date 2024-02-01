import uvicorn
from loguru import logger
import os

if __name__ == "__main__":
    dir_log = "logs"
    path_log = os.path.join(dir_log, "log.log")
    logger.add(
        path_log,
        rotation="0:00",
        enqueue=True,
        serialize=False,
        encoding="utf-8",
        retention="10 days",
    )
    logger.debug("service restarted")

    uvicorn.run("app:app", host="0.0.0.0", port=8080, reload=True)
