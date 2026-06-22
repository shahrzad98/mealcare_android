from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from typing import TypedDict


WEEKDAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")


class MealItem(TypedDict):
    id: str
    label: str
    time: str
    meal: str


class ReminderItem(TypedDict):
    id: str
    category: str
    name: str
    time: str
    enabled: bool


class NotificationItem(TypedDict):
    id: str
    title: str
    message: str
    time: str


_DEFAULT_MEALS: dict[str, list[MealItem]] = {
    "Monday": [
        {"id": "breakfast", "label": "Breakfast", "time": "07:30", "meal": "Oatmeal with banana, berries, nuts, and milk or a fortified alternative."},
        {"id": "morning-snack", "label": "Morning snack", "time": "10:30", "meal": "Apple or pear with a small handful of unsalted nuts."},
        {"id": "lunch", "label": "Lunch", "time": "13:00", "meal": "Grilled chicken, brown rice, mixed vegetables, and yogurt."},
        {"id": "afternoon-snack", "label": "Afternoon snack", "time": "16:30", "meal": "Carrot and cucumber sticks with hummus."},
        {"id": "dinner", "label": "Dinner", "time": "19:30", "meal": "Baked salmon, roasted potatoes, and a green salad."},
    ],
    "Tuesday": [
        {"id": "breakfast", "label": "Breakfast", "time": "07:30", "meal": "Two eggs, whole-grain toast, tomato, and one orange."},
        {"id": "morning-snack", "label": "Morning snack", "time": "10:30", "meal": "Plain yogurt with berries."},
        {"id": "lunch", "label": "Lunch", "time": "13:00", "meal": "Lentil soup, whole-grain bread, and a side salad."},
        {"id": "afternoon-snack", "label": "Afternoon snack", "time": "16:30", "meal": "Banana with peanut or seed butter."},
        {"id": "dinner", "label": "Dinner", "time": "19:30", "meal": "Turkey or tofu stir-fry with vegetables and noodles."},
    ],
    "Wednesday": [
        {"id": "breakfast", "label": "Breakfast", "time": "07:30", "meal": "Greek yogurt, oats, chopped fruit, and seeds."},
        {"id": "morning-snack", "label": "Morning snack", "time": "10:30", "meal": "A piece of fruit and a small portion of cheese."},
        {"id": "lunch", "label": "Lunch", "time": "13:00", "meal": "Tuna or chickpea wrap with lettuce, tomato, and avocado."},
        {"id": "afternoon-snack", "label": "Afternoon snack", "time": "16:30", "meal": "Air-popped popcorn or roasted chickpeas."},
        {"id": "dinner", "label": "Dinner", "time": "19:30", "meal": "Bean chili with brown rice and steamed broccoli."},
    ],
    "Thursday": [
        {"id": "breakfast", "label": "Breakfast", "time": "07:30", "meal": "Whole-grain cereal, milk or fortified alternative, and sliced banana."},
        {"id": "morning-snack", "label": "Morning snack", "time": "10:30", "meal": "Kiwi or orange with a few walnuts."},
        {"id": "lunch", "label": "Lunch", "time": "13:00", "meal": "Quinoa bowl with beans, vegetables, greens, and tahini dressing."},
        {"id": "afternoon-snack", "label": "Afternoon snack", "time": "16:30", "meal": "Yogurt or kefir."},
        {"id": "dinner", "label": "Dinner", "time": "19:30", "meal": "Lean beef or tempeh, sweet potato, and mixed vegetables."},
    ],
    "Friday": [
        {"id": "breakfast", "label": "Breakfast", "time": "07:30", "meal": "Vegetable omelet with whole-grain toast and fruit."},
        {"id": "morning-snack", "label": "Morning snack", "time": "10:30", "meal": "Dates with almonds or another fruit-and-nut combination."},
        {"id": "lunch", "label": "Lunch", "time": "13:00", "meal": "Chicken or falafel salad bowl with whole-grain pita."},
        {"id": "afternoon-snack", "label": "Afternoon snack", "time": "16:30", "meal": "Bell pepper slices with hummus."},
        {"id": "dinner", "label": "Dinner", "time": "19:30", "meal": "Whole-wheat pasta with tomato sauce, vegetables, and a protein."},
    ],
    "Saturday": [
        {"id": "breakfast", "label": "Breakfast", "time": "08:30", "meal": "Whole-grain pancakes, berries, yogurt, and a small amount of nut butter."},
        {"id": "morning-snack", "label": "Morning snack", "time": "11:00", "meal": "Seasonal fruit."},
        {"id": "lunch", "label": "Lunch", "time": "13:30", "meal": "Homemade chicken, bean, or tofu sandwich with salad."},
        {"id": "afternoon-snack", "label": "Afternoon snack", "time": "17:00", "meal": "Trail mix with unsalted nuts, seeds, and dried fruit."},
        {"id": "dinner", "label": "Dinner", "time": "20:00", "meal": "Grilled fish, chicken, or tofu with couscous and vegetables."},
    ],
    "Sunday": [
        {"id": "breakfast", "label": "Breakfast", "time": "08:30", "meal": "Avocado and egg or tofu on whole-grain toast with fruit."},
        {"id": "morning-snack", "label": "Morning snack", "time": "11:00", "meal": "Yogurt with seeds."},
        {"id": "lunch", "label": "Lunch", "time": "13:30", "meal": "Roast chicken or lentil loaf with potatoes and vegetables."},
        {"id": "afternoon-snack", "label": "Afternoon snack", "time": "17:00", "meal": "Fruit smoothie without added sugar."},
        {"id": "dinner", "label": "Dinner", "time": "19:30", "meal": "Vegetable soup, whole-grain bread, and beans or cheese."},
    ],
}

_DEFAULT_REMINDERS: list[ReminderItem] = [
    {"id": "water-morning", "category": "essential", "name": "Drink water", "time": "09:00", "enabled": True},
    {"id": "fruit", "category": "essential", "name": "Eat a serving of fruit", "time": "10:30", "enabled": True},
    {"id": "water-midday", "category": "essential", "name": "Drink water", "time": "12:00", "enabled": True},
    {"id": "vegetables", "category": "essential", "name": "Include vegetables today", "time": "13:00", "enabled": True},
    {"id": "water-afternoon", "category": "essential", "name": "Drink water", "time": "15:30", "enabled": True},
    {"id": "protein", "category": "essential", "name": "Include a protein source today", "time": "19:00", "enabled": True},
    {"id": "vitamins-morning", "category": "vitamin", "name": "Take your scheduled vitamins", "time": "08:30", "enabled": True},
]


def make_default_data() -> dict[str, object]:
    return {
        "version": 1,
        "meal_plans": deepcopy(_DEFAULT_MEALS),
        "reminders": deepcopy(_DEFAULT_REMINDERS),
        "completions": {},
        "settings": {
            "notifications_enabled": True,
            "meal_notifications_enabled": True,
        },
    }


def is_valid_time(value: str) -> bool:
    try:
        datetime.strptime(value.strip(), "%H:%M")
    except ValueError:
        return False
    return True


def collect_due_notifications(data: dict[str, object], at: datetime) -> list[NotificationItem]:
    settings = data.get("settings", {})
    if not isinstance(settings, dict) or not bool(settings.get("notifications_enabled", True)):
        return []

    current_time = at.strftime("%H:%M")
    notifications: list[NotificationItem] = []

    if bool(settings.get("meal_notifications_enabled", True)):
        meal_plans = data.get("meal_plans", {})
        if isinstance(meal_plans, dict):
            meals = meal_plans.get(at.strftime("%A"), [])
            if isinstance(meals, list):
                for raw_meal in meals:
                    if not isinstance(raw_meal, dict):
                        continue
                    meal_time = str(raw_meal.get("time", ""))
                    if meal_time != current_time:
                        continue
                    meal_id = str(raw_meal.get("id", "meal"))
                    meal_label = str(raw_meal.get("label", "Meal"))
                    meal_text = str(raw_meal.get("meal", "Open MealCare to view your meal."))
                    notifications.append(
                        {
                            "id": f"meal-{at.strftime('%A')}-{meal_id}",
                            "title": f"{meal_label} time",
                            "message": meal_text,
                            "time": meal_time,
                        }
                    )

    reminders = data.get("reminders", [])
    if isinstance(reminders, list):
        for raw_reminder in reminders:
            if not isinstance(raw_reminder, dict):
                continue
            if not bool(raw_reminder.get("enabled", True)):
                continue
            reminder_time = str(raw_reminder.get("time", ""))
            if reminder_time != current_time:
                continue
            category = str(raw_reminder.get("category", "essential"))
            title = "Vitamin reminder" if category == "vitamin" else "Daily essential"
            notifications.append(
                {
                    "id": f"reminder-{raw_reminder.get('id', 'item')}",
                    "title": title,
                    "message": str(raw_reminder.get("name", "Open MealCare")),
                    "time": reminder_time,
                }
            )

    return notifications
