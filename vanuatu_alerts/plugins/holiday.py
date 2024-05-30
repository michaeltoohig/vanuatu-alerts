import datetime
from dataclasses import dataclass, field
from vanuatu_alerts.plugins.base import BasePlugin
import requests
from loguru import logger
from bs4 import BeautifulSoup


@dataclass
class Holiday:
    id: str = field(init=False)
    date: datetime.date
    name: str

    def __post_init__(self):
        self.id = self.date.strftime("%Y-%m-%d")


class HolidayPlugin(BasePlugin):
    def __init__(self):
        super().__init__("Holidays", 60)
        self.last_date_checked = None

    def run(self):
        today = datetime.datetime.now().date()
        if today == self.last_date_checked:
            logger.debug("Skipping - date already checked")
            return None
        try:
            html = self.fetch()
            holidays = self.parse_holidays(html)
        except Exception as e:
            raise e
        finally:
            self.last_date_checked = today
        for item in holidays:
            if item.date == today:
                logger.info(f"Today is a holiday")
                return f"Today is {item.name}"

    def parse_date(self, date_str: str) -> datetime.datetime.date:
        current_year = datetime.datetime.now().year
        date = datetime.datetime.strptime(date_str, "%d %B")
        return date.replace(year=current_year).date()

    def parse_holidays(self, html: str):
        holidays = []
        soup = BeautifulSoup(html, "html.parser")
        section = soup.find("section", id="sp-main-body")
        table = section.article.table
        tbody = table.find_all("tbody")[1]  # unusual HTML
        for row in tbody.find_all("tr"):
            tds = row.find_all("td")
            date_str = tds[1].text
            date = self.parse_date(date_str)
            name = tds[2].text.split("/", 1)[0].strip()
            holiday = Holiday(date=date, name=name)
            holidays.append(holiday)
        return holidays

    def fetch(self):
        url = "https://gov.vu/index.php/events/holidays"
        resp = requests.get(url)
        return resp.text
