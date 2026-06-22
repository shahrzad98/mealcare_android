from __future__ import annotations

from datetime import date, datetime
from typing import cast
from uuid import uuid4

from kivy.app import App
from kivy.clock import Clock
from kivy.config import Config
from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp
from kivy.properties import ListProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.checkbox import CheckBox
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import NoTransition, Screen, ScreenManager
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.uix.switch import Switch
from kivy.uix.textinput import TextInput
from kivy.uix.togglebutton import ToggleButton
from kivy.utils import get_color_from_hex
from kivy.core.window import Window

from app_data import WEEKDAYS, is_valid_time
from notifications import request_notification_permission, send_notification, start_reminder_service
from storage import DataStore


Config.set("graphics", "width", "420")
Config.set("graphics", "height", "820")
Config.set("input", "mouse", "mouse,multitouch_on_demand")

BACKGROUND = get_color_from_hex("#F4F7F2")
CARD = get_color_from_hex("#FFFFFF")
PRIMARY = get_color_from_hex("#2E7D4F")
PRIMARY_DARK = get_color_from_hex("#1F5B39")
TEXT = get_color_from_hex("#1E2B23")
MUTED = get_color_from_hex("#66756B")
DANGER = get_color_from_hex("#B42318")
BORDER = get_color_from_hex("#DDE7DF")


def label(
    text: str,
    *,
    font_size: float = 16,
    color: list[float] | None = None,
    bold: bool = False,
    height: float = 36,
    halign: str = "left",
) -> Label:
    widget = Label(
        text=text,
        font_size=font_size,
        color=color or TEXT,
        bold=bold,
        size_hint_y=None,
        height=dp(height),
        halign=halign,
        valign="middle",
    )
    widget.bind(size=lambda instance, _: setattr(instance, "text_size", (instance.width, None)))
    return widget


def action_button(text: str, callback, *, danger: bool = False, height: float = 48) -> Button:
    button = Button(
        text=text,
        size_hint_y=None,
        height=dp(height),
        background_normal="",
        background_down="",
        background_color=DANGER if danger else PRIMARY,
        color=[1, 1, 1, 1],
        bold=True,
    )
    button.bind(on_release=callback)
    return button


def outlined_button(text: str, callback, *, height: float = 42) -> Button:
    button = Button(
        text=text,
        size_hint_y=None,
        height=dp(height),
        background_normal="",
        background_down="",
        background_color=get_color_from_hex("#E9F2EC"),
        color=PRIMARY_DARK,
        bold=True,
    )
    button.bind(on_release=callback)
    return button


class CardBox(BoxLayout):
    background_color = ListProperty(CARD)

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        with self.canvas.before:
            self._color = Color(*self.background_color)
            self._rectangle = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(14)])
        self.bind(pos=self._sync_canvas, size=self._sync_canvas, background_color=self._sync_color)

    def _sync_canvas(self, *_args) -> None:
        self._rectangle.pos = self.pos
        self._rectangle.size = self.size

    def _sync_color(self, *_args) -> None:
        self._color.rgba = self.background_color


class BaseScreen(Screen):
    def get_app(self) -> "MealCareApp":
        return cast("MealCareApp", App.get_running_app())

    def show_message(self, title: str, message: str) -> None:
        content = BoxLayout(orientation="vertical", spacing=dp(12), padding=dp(16))
        content.add_widget(label(message, height=70))
        popup = Popup(title=title, content=content, size_hint=(0.88, None), height=dp(210))
        content.add_widget(action_button("OK", lambda _button: popup.dismiss()))
        popup.open()

    def refresh(self) -> None:
        pass


class TodayScreen(BaseScreen):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        root = BoxLayout(orientation="vertical", padding=[dp(14), dp(8), dp(14), dp(8)])
        self.scroll = ScrollView()
        self.content = BoxLayout(orientation="vertical", spacing=dp(12), size_hint_y=None, padding=[0, 0, 0, dp(18)])
        self.content.bind(minimum_height=self.content.setter("height"))
        self.scroll.add_widget(self.content)
        root.add_widget(self.scroll)
        self.add_widget(root)

    def refresh(self) -> None:
        self.content.clear_widgets()
        now = datetime.now()
        day_name = now.strftime("%A")
        date_key = now.date().isoformat()
        data = self.get_app().store.load()

        self.content.add_widget(label(now.strftime("%A, %d %B %Y"), font_size=22, bold=True, height=46))
        self.content.add_widget(label("Today's full meal plan", font_size=14, color=MUTED, height=28))

        meal_plans = data.get("meal_plans", {})
        meals = meal_plans.get(day_name, []) if isinstance(meal_plans, dict) else []
        completions = data.get("completions", {})
        today_completion = completions.get(date_key, {}) if isinstance(completions, dict) else {}

        completed_count = 0
        if isinstance(meals, list):
            completed_count = sum(
                1
                for meal in meals
                if isinstance(meal, dict)
                and isinstance(today_completion, dict)
                and bool(today_completion.get(str(meal.get("id", "")), False))
            )
        self.content.add_widget(
            label(
                f"{completed_count} of {len(meals) if isinstance(meals, list) else 0} meals completed",
                color=PRIMARY_DARK,
                bold=True,
                height=32,
            )
        )

        if isinstance(meals, list):
            for raw_meal in meals:
                if not isinstance(raw_meal, dict):
                    continue
                meal_id = str(raw_meal.get("id", "meal"))
                done = isinstance(today_completion, dict) and bool(today_completion.get(meal_id, False))
                self.content.add_widget(self._meal_card(raw_meal, date_key, meal_id, done))

        self.content.add_widget(label("Daily essentials and vitamins", font_size=20, bold=True, height=44))
        reminders = data.get("reminders", [])
        if isinstance(reminders, list):
            for raw_reminder in reminders:
                if not isinstance(raw_reminder, dict) or not bool(raw_reminder.get("enabled", True)):
                    continue
                category = "Vitamin" if raw_reminder.get("category") == "vitamin" else "Essential"
                card = CardBox(
                    orientation="horizontal",
                    spacing=dp(10),
                    padding=dp(12),
                    size_hint_y=None,
                    height=dp(64),
                )
                card.add_widget(label(str(raw_reminder.get("time", "")), color=PRIMARY, bold=True, height=40))
                card.add_widget(label(f"{category}: {raw_reminder.get('name', '')}", height=40))
                self.content.add_widget(card)

    def _meal_card(self, meal: dict[str, object], date_key: str, meal_id: str, done: bool) -> CardBox:
        card = CardBox(
            orientation="vertical",
            spacing=dp(6),
            padding=dp(14),
            size_hint_y=None,
            height=dp(132),
        )
        top = BoxLayout(orientation="horizontal", spacing=dp(8), size_hint_y=None, height=dp(42))
        top.add_widget(label(str(meal.get("time", "")), color=PRIMARY, bold=True, height=42))
        top.add_widget(label(str(meal.get("label", "Meal")), font_size=18, bold=True, height=42))

        toggle = ToggleButton(
            text="Done" if done else "Mark done",
            state="down" if done else "normal",
            size_hint=(None, None),
            width=dp(104),
            height=dp(38),
            background_normal="",
            background_down="",
            background_color=PRIMARY if done else get_color_from_hex("#DCE9E0"),
            color=[1, 1, 1, 1] if done else PRIMARY_DARK,
        )
        toggle.bind(on_release=lambda button: self._set_completion(date_key, meal_id, button.state == "down"))
        top.add_widget(toggle)
        card.add_widget(top)
        card.add_widget(label(str(meal.get("meal", "")), color=MUTED, font_size=14, height=62))
        return card

    def _set_completion(self, date_key: str, meal_id: str, completed: bool) -> None:
        def mutate(data: dict[str, object]) -> None:
            completions = data.setdefault("completions", {})
            if not isinstance(completions, dict):
                completions = {}
                data["completions"] = completions
            today_completion = completions.setdefault(date_key, {})
            if not isinstance(today_completion, dict):
                today_completion = {}
                completions[date_key] = today_completion
            today_completion[meal_id] = completed

        self.get_app().store.update(mutate)
        self.refresh()


class PlanScreen(BaseScreen):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.inputs: list[tuple[str, TextInput, TextInput]] = []

        root = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(14))
        root.add_widget(label("Edit weekly meal plan", font_size=22, bold=True, height=46))

        self.day_spinner = Spinner(
            text=datetime.now().strftime("%A"),
            values=WEEKDAYS,
            size_hint_y=None,
            height=dp(48),
            background_normal="",
            background_color=get_color_from_hex("#E9F2EC"),
            color=PRIMARY_DARK,
        )
        self.day_spinner.bind(text=lambda _spinner, _text: self.refresh())
        root.add_widget(self.day_spinner)

        self.scroll = ScrollView()
        self.content = BoxLayout(orientation="vertical", spacing=dp(12), size_hint_y=None, padding=[0, 4, 0, dp(12)])
        self.content.bind(minimum_height=self.content.setter("height"))
        self.scroll.add_widget(self.content)
        root.add_widget(self.scroll)
        root.add_widget(action_button("Save this day", self._save))
        self.add_widget(root)

    def refresh(self) -> None:
        if not hasattr(self, "content"):
            return
        self.content.clear_widgets()
        self.inputs.clear()

        data = self.get_app().store.load()
        meal_plans = data.get("meal_plans", {})
        meals = meal_plans.get(self.day_spinner.text, []) if isinstance(meal_plans, dict) else []

        if not isinstance(meals, list):
            return

        for raw_meal in meals:
            if not isinstance(raw_meal, dict):
                continue
            meal_id = str(raw_meal.get("id", "meal"))
            card = CardBox(
                orientation="vertical",
                spacing=dp(8),
                padding=dp(12),
                size_hint_y=None,
                height=dp(182),
            )
            card.add_widget(label(str(raw_meal.get("label", "Meal")), font_size=18, bold=True, height=34))

            time_input = TextInput(
                text=str(raw_meal.get("time", "")),
                hint_text="HH:MM",
                multiline=False,
                size_hint_y=None,
                height=dp(42),
                padding=[dp(10), dp(10)],
                background_normal="",
                background_active="",
                background_color=get_color_from_hex("#F0F4F1"),
                foreground_color=TEXT,
            )
            meal_input = TextInput(
                text=str(raw_meal.get("meal", "")),
                hint_text="Meal description",
                multiline=True,
                size_hint_y=None,
                height=dp(76),
                padding=[dp(10), dp(10)],
                background_normal="",
                background_active="",
                background_color=get_color_from_hex("#F0F4F1"),
                foreground_color=TEXT,
            )
            card.add_widget(time_input)
            card.add_widget(meal_input)
            self.inputs.append((meal_id, time_input, meal_input))
            self.content.add_widget(card)

    def _save(self, _button) -> None:
        for _meal_id, time_input, _meal_input in self.inputs:
            if not is_valid_time(time_input.text):
                self.show_message("Invalid time", "Use 24-hour HH:MM format, for example 08:30.")
                return

        selected_day = self.day_spinner.text

        def mutate(data: dict[str, object]) -> None:
            meal_plans = data.get("meal_plans", {})
            if not isinstance(meal_plans, dict):
                return
            meals = meal_plans.get(selected_day, [])
            if not isinstance(meals, list):
                return
            by_id = {
                meal_id: (time_input.text.strip(), meal_input.text.strip())
                for meal_id, time_input, meal_input in self.inputs
            }
            for raw_meal in meals:
                if not isinstance(raw_meal, dict):
                    continue
                meal_id = str(raw_meal.get("id", ""))
                if meal_id in by_id:
                    raw_meal["time"], raw_meal["meal"] = by_id[meal_id]

        self.get_app().store.update(mutate)
        self.show_message("Saved", f"The {selected_day} meal plan was updated.")


class RemindersScreen(BaseScreen):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        root = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(14))
        root.add_widget(label("Daily reminders", font_size=22, bold=True, height=46))

        actions = BoxLayout(orientation="horizontal", spacing=dp(10), size_hint_y=None, height=dp(44))
        actions.add_widget(outlined_button("Add essential", lambda _button: self._open_editor("essential")))
        actions.add_widget(outlined_button("Add vitamin", lambda _button: self._open_editor("vitamin")))
        root.add_widget(actions)

        self.scroll = ScrollView()
        self.content = BoxLayout(orientation="vertical", spacing=dp(12), size_hint_y=None, padding=[0, 4, 0, dp(18)])
        self.content.bind(minimum_height=self.content.setter("height"))
        self.scroll.add_widget(self.content)
        root.add_widget(self.scroll)
        self.add_widget(root)

    def refresh(self) -> None:
        if not hasattr(self, "content"):
            return
        self.content.clear_widgets()
        data = self.get_app().store.load()
        reminders = data.get("reminders", [])

        if not isinstance(reminders, list):
            return

        for category, heading in (("essential", "Essentials"), ("vitamin", "Vitamins")):
            self.content.add_widget(label(heading, font_size=19, bold=True, height=40))
            category_items = [
                item
                for item in reminders
                if isinstance(item, dict) and str(item.get("category", "essential")) == category
            ]
            if not category_items:
                self.content.add_widget(label("No reminders yet.", color=MUTED, height=36))
                continue
            for raw_reminder in category_items:
                self.content.add_widget(self._reminder_card(raw_reminder))

    def _reminder_card(self, reminder: dict[str, object]) -> CardBox:
        reminder_id = str(reminder.get("id", ""))
        card = CardBox(
            orientation="vertical",
            spacing=dp(8),
            padding=dp(12),
            size_hint_y=None,
            height=dp(116),
        )
        top = BoxLayout(orientation="horizontal", spacing=dp(8), size_hint_y=None, height=dp(46))
        top.add_widget(label(str(reminder.get("time", "")), color=PRIMARY, bold=True, height=42))
        top.add_widget(label(str(reminder.get("name", "")), bold=True, height=42))

        enabled_switch = Switch(active=bool(reminder.get("enabled", True)), size_hint=(None, None), width=dp(56), height=dp(42))
        enabled_switch.bind(active=lambda _switch, active: self._toggle(reminder_id, active))
        top.add_widget(enabled_switch)
        card.add_widget(top)

        actions = BoxLayout(orientation="horizontal", spacing=dp(8), size_hint_y=None, height=dp(38))
        actions.add_widget(outlined_button("Edit", lambda _button: self._open_editor(str(reminder.get("category", "essential")), reminder_id), height=38))
        delete_button = Button(
            text="Delete",
            size_hint_y=None,
            height=dp(38),
            background_normal="",
            background_down="",
            background_color=get_color_from_hex("#FEE4E2"),
            color=DANGER,
            bold=True,
        )
        delete_button.bind(on_release=lambda _button: self._delete(reminder_id))
        actions.add_widget(delete_button)
        card.add_widget(actions)
        return card

    def _toggle(self, reminder_id: str, active: bool) -> None:
        def mutate(data: dict[str, object]) -> None:
            reminders = data.get("reminders", [])
            if not isinstance(reminders, list):
                return
            for raw_reminder in reminders:
                if isinstance(raw_reminder, dict) and raw_reminder.get("id") == reminder_id:
                    raw_reminder["enabled"] = active
                    return

        self.get_app().store.update(mutate)

    def _delete(self, reminder_id: str) -> None:
        def mutate(data: dict[str, object]) -> None:
            reminders = data.get("reminders", [])
            if isinstance(reminders, list):
                data["reminders"] = [
                    item
                    for item in reminders
                    if not isinstance(item, dict) or item.get("id") != reminder_id
                ]

        self.get_app().store.update(mutate)
        self.refresh()

    def _open_editor(self, category: str, reminder_id: str | None = None) -> None:
        existing: dict[str, object] | None = None
        data = self.get_app().store.load()
        reminders = data.get("reminders", [])
        if reminder_id and isinstance(reminders, list):
            existing = next(
                (
                    item
                    for item in reminders
                    if isinstance(item, dict) and item.get("id") == reminder_id
                ),
                None,
            )

        content = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(16))
        category_spinner = Spinner(
            text=str(existing.get("category", category)) if existing else category,
            values=("essential", "vitamin"),
            size_hint_y=None,
            height=dp(44),
        )
        name_input = TextInput(
            text=str(existing.get("name", "")) if existing else "",
            hint_text="Reminder name",
            multiline=False,
            size_hint_y=None,
            height=dp(46),
        )
        time_input = TextInput(
            text=str(existing.get("time", "08:30")) if existing else "08:30",
            hint_text="HH:MM",
            multiline=False,
            size_hint_y=None,
            height=dp(46),
        )
        enabled_checkbox = CheckBox(
            active=bool(existing.get("enabled", True)) if existing else True,
            size_hint=(None, None),
            width=dp(48),
            height=dp(42),
        )
        enabled_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(42))
        enabled_row.add_widget(label("Enabled", height=42))
        enabled_row.add_widget(enabled_checkbox)

        content.add_widget(label("Category", color=MUTED, height=28))
        content.add_widget(category_spinner)
        content.add_widget(label("Name", color=MUTED, height=28))
        content.add_widget(name_input)
        content.add_widget(label("Time", color=MUTED, height=28))
        content.add_widget(time_input)
        content.add_widget(enabled_row)

        popup = Popup(
            title="Edit reminder" if existing else "Add reminder",
            content=content,
            size_hint=(0.92, None),
            height=dp(500),
        )

        def save(_button) -> None:
            name = name_input.text.strip()
            reminder_time = time_input.text.strip()
            if not name:
                self.show_message("Missing name", "Enter a reminder name.")
                return
            if not is_valid_time(reminder_time):
                self.show_message("Invalid time", "Use 24-hour HH:MM format, for example 08:30.")
                return

            def mutate(data_to_change: dict[str, object]) -> None:
                reminder_list = data_to_change.setdefault("reminders", [])
                if not isinstance(reminder_list, list):
                    reminder_list = []
                    data_to_change["reminders"] = reminder_list

                if reminder_id:
                    for raw_reminder in reminder_list:
                        if isinstance(raw_reminder, dict) and raw_reminder.get("id") == reminder_id:
                            raw_reminder.update(
                                {
                                    "category": category_spinner.text,
                                    "name": name,
                                    "time": reminder_time,
                                    "enabled": enabled_checkbox.active,
                                }
                            )
                            return

                reminder_list.append(
                    {
                        "id": uuid4().hex,
                        "category": category_spinner.text,
                        "name": name,
                        "time": reminder_time,
                        "enabled": enabled_checkbox.active,
                    }
                )

            self.get_app().store.update(mutate)
            popup.dismiss()
            self.refresh()

        content.add_widget(action_button("Save reminder", save))
        popup.open()


class SettingsScreen(BaseScreen):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        self.content = BoxLayout(orientation="vertical", spacing=dp(12), padding=dp(14))
        self.add_widget(self.content)

    def refresh(self) -> None:
        if not hasattr(self, "content"):
            return
        self.content.clear_widgets()
        self.content.add_widget(label("Settings", font_size=22, bold=True, height=46))

        data = self.get_app().store.load()
        settings = data.get("settings", {})
        if not isinstance(settings, dict):
            settings = {}

        self.content.add_widget(
            self._switch_card(
                "All notifications",
                "Enable or disable every meal, essential, and vitamin notification.",
                bool(settings.get("notifications_enabled", True)),
                "notifications_enabled",
            )
        )
        self.content.add_widget(
            self._switch_card(
                "Meal notifications",
                "Notify at the time assigned to each meal in the weekly plan.",
                bool(settings.get("meal_notifications_enabled", True)),
                "meal_notifications_enabled",
            )
        )
        self.content.add_widget(action_button("Send test notification", self._test_notification))
        self.content.add_widget(outlined_button("Clear today's completion", self._clear_today))
        self.content.add_widget(action_button("Reset all plans and reminders", self._confirm_reset, danger=True))
        self.content.add_widget(
            label(
                "MealCare stores data only on this device. Vitamin reminders do not provide dosage or medical advice.",
                color=MUTED,
                font_size=13,
                height=76,
            )
        )
        self.content.add_widget(
            label(
                "Android may delay background notifications under battery-saving modes. Allow notifications and remove battery restrictions for MealCare when reliable timing is important.",
                color=MUTED,
                font_size=13,
                height=96,
            )
        )
        self.content.add_widget(BoxLayout())

    def _switch_card(self, title: str, description: str, active: bool, setting_key: str) -> CardBox:
        card = CardBox(
            orientation="horizontal",
            spacing=dp(10),
            padding=dp(12),
            size_hint_y=None,
            height=dp(100),
        )
        text_column = BoxLayout(orientation="vertical", spacing=dp(2))
        text_column.add_widget(label(title, bold=True, height=34))
        text_column.add_widget(label(description, color=MUTED, font_size=13, height=52))
        card.add_widget(text_column)

        setting_switch = Switch(active=active, size_hint=(None, None), width=dp(60), height=dp(64))
        setting_switch.bind(active=lambda _switch, value: self._save_setting(setting_key, value))
        card.add_widget(setting_switch)
        return card

    def _save_setting(self, key: str, value: bool) -> None:
        def mutate(data: dict[str, object]) -> None:
            settings = data.setdefault("settings", {})
            if not isinstance(settings, dict):
                settings = {}
                data["settings"] = settings
            settings[key] = value

        self.get_app().store.update(mutate)

    def _test_notification(self, _button) -> None:
        if send_notification("MealCare test", "Notifications are configured correctly."):
            self.show_message("Notification sent", "Check your Android notification area.")
        else:
            self.show_message("Notification unavailable", "Desktop systems or denied Android permission may not display it.")

    def _clear_today(self, _button) -> None:
        today_key = date.today().isoformat()

        def mutate(data: dict[str, object]) -> None:
            completions = data.get("completions", {})
            if isinstance(completions, dict):
                completions.pop(today_key, None)

        self.get_app().store.update(mutate)
        self.show_message("Cleared", "Today's meal completion marks were removed.")

    def _confirm_reset(self, _button) -> None:
        content = BoxLayout(orientation="vertical", spacing=dp(12), padding=dp(16))
        content.add_widget(label("This replaces your edited meal plans and reminders with the defaults.", height=78))
        popup = Popup(title="Reset everything?", content=content, size_hint=(0.9, None), height=dp(260))
        buttons = BoxLayout(orientation="horizontal", spacing=dp(10), size_hint_y=None, height=dp(48))
        buttons.add_widget(outlined_button("Cancel", lambda _item: popup.dismiss(), height=48))

        def reset(_item) -> None:
            self.get_app().store.reset()
            popup.dismiss()
            self.refresh()
            self.show_message("Reset complete", "Default plans and reminders were restored.")

        buttons.add_widget(action_button("Reset", reset, danger=True))
        content.add_widget(buttons)
        popup.open()


class MealCareRoot(BoxLayout):
    def __init__(self, **kwargs) -> None:
        super().__init__(orientation="vertical", **kwargs)

        header = BoxLayout(
            orientation="horizontal",
            spacing=dp(8),
            padding=[dp(16), dp(8)],
            size_hint_y=None,
            height=dp(64),
        )
        header.add_widget(label("MealCare", font_size=25, bold=True, color=PRIMARY_DARK, height=48))
        header.add_widget(label("Meals • Essentials • Vitamins", font_size=12, color=MUTED, height=48, halign="right"))
        self.add_widget(header)

        self.manager = ScreenManager(transition=NoTransition())
        self.screens: dict[str, BaseScreen] = {
            "today": TodayScreen(name="today"),
            "plan": PlanScreen(name="plan"),
            "reminders": RemindersScreen(name="reminders"),
            "settings": SettingsScreen(name="settings"),
        }
        for screen in self.screens.values():
            self.manager.add_widget(screen)
        self.add_widget(self.manager)

        navigation = BoxLayout(
            orientation="horizontal",
            spacing=dp(6),
            padding=[dp(8), dp(6)],
            size_hint_y=None,
            height=dp(66),
        )
        for title, screen_name in (
            ("Today", "today"),
            ("Plan", "plan"),
            ("Reminders", "reminders"),
            ("Settings", "settings"),
        ):
            button = Button(
                text=title,
                background_normal="",
                background_down="",
                background_color=get_color_from_hex("#E8F0EA"),
                color=PRIMARY_DARK,
                font_size=13,
            )
            button.bind(on_release=lambda _button, name=screen_name: self.navigate(name))
            navigation.add_widget(button)
        self.add_widget(navigation)

    def navigate(self, screen_name: str) -> None:
        self.manager.current = screen_name
        self.screens[screen_name].refresh()

    def refresh_current(self) -> None:
        self.screens[self.manager.current].refresh()


class MealCareApp(App):
    title = "MealCare"

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.store = DataStore()
        self.root_view: MealCareRoot | None = None

    def build(self) -> MealCareRoot:
        Window.clearcolor = BACKGROUND
        self.root_view = MealCareRoot()
        return self.root_view

    def on_start(self) -> None:
        request_notification_permission()
        start_reminder_service()
        Clock.schedule_once(lambda _dt: self.root_view.refresh_current() if self.root_view else None, 0)

    def on_resume(self) -> None:
        if self.root_view:
            self.root_view.refresh_current()

    def on_pause(self) -> bool:
        return True


if __name__ == "__main__":
    MealCareApp().run()
