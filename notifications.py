from __future__ import annotations

from kivy.utils import platform


PACKAGE_NAME = "org.mealcare.planner"


def request_notification_permission() -> None:
    if platform != "android":
        return

    try:
        from android.permissions import request_permissions

        request_permissions(["android.permission.POST_NOTIFICATIONS"])
    except Exception:
        # Android API availability varies by OS and packaging version.
        pass


def start_reminder_service() -> bool:
    if platform != "android":
        return False

    try:
        from jnius import autoclass

        service_class = autoclass(f"{PACKAGE_NAME}.ServiceReminder")
        activity_class = autoclass("org.kivy.android.PythonActivity")
        service_class.start(activity_class.mActivity, "")
    except Exception:
        # Service startup errors should not prevent the main app from opening.
        return False

    return True


def send_notification(title: str, message: str) -> bool:
    try:
        from plyer import notification

        notification.notify(
            title=title,
            message=message,
            app_name="MealCare",
            timeout=10,
        )
    except Exception:
        # Plyer backends differ between Android and desktop environments.
        return False

    return True
