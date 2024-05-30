import time
from vanuatu_alerts import config
from vanuatu_alerts.plugins.earthquake import EarthquakePlugin
from vanuatu_alerts.plugins.holiday import HolidayPlugin
from loguru import logger
import schedule
import requests

logger.add("./logs/app.log", rotation="5 MB")


def send_alert(message: str):
    url = f"https://api.telegram.org/bot{config.TG_TOKEN}/sendMessage"
    params = dict(
        chat_id=config.TG_CHAT_ID,
        text=message,
    )
    requests.get(url, params)


def run_plugin(plugin):
    logger.info(f"Plugin {plugin.name} is running")
    try:
        message = plugin.run()
        if message:
            logger.debug(f"Plugin {plugin.name} is sending a message")
            send_alert(message)
        logger.debug(f"Plugin {plugin.name} has completed")
    except Exception:
        logger.exception(f"Plugin {plugin.name} has errored")
        send_alert(f"Plugin {plugin.name} has errored")


def main(immediate: bool = False):
    plugins = [
        EarthquakePlugin(),
        HolidayPlugin(),
    ]

    if immediate:
        for plugin in plugins:
            run_plugin(plugin)

    for plugin in plugins:
        logger.info(f"Plugin {plugin.name} will run every {plugin.frequency} minutes")
        schedule.every(plugin.frequency).minutes.do(run_plugin, plugin)

    while True:
        schedule.run_pending()
        time.sleep(1)
