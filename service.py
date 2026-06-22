from __future__ import annotations

from datetime import datetime, timedelta
from time import sleep

from app_data import collect_due_notifications
from notifications import send_notification
from storage import DataStore, NotificationState


def run() -> None:
    store = DataStore()
    state = NotificationState()

    while True:
        now = datetime.now()
        data = store.load()

        # Check the current minute and the previous five minutes. Android can
        # briefly pause background work under battery-saving modes.
        for minute_offset in range(6):
            check_time = now - timedelta(minutes=minute_offset)
            due_items = collect_due_notifications(data, check_time)

            for item in due_items:
                key = f"{check_time.date().isoformat()}|{item['id']}|{item['time']}"
                if state.mark_if_new(key):
                    send_notification(item["title"], item["message"])

        sleep(20)


if __name__ == "__main__":
    run()
