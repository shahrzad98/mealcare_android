# MealCare — Python/Kivy Android app

MealCare provides:

- A complete editable seven-day meal plan
- Breakfast, two snacks, lunch, and dinner
- Daily meal completion tracking
- Daily essential-food and hydration reminders
- User-editable vitamin reminders
- Android notifications
- A sticky Python background service that checks reminders
- Local JSON storage; no account, server, or internet connection

## Important health note

The included meal plan is a general example, not a medical diet. Vitamin reminders only remember the entries and times you choose. They do not recommend a vitamin, dosage, or treatment. People with allergies, medical conditions, pregnancy, or prescription medicines should personalize the plan with a qualified clinician.

## Run on a desktop

Python 3.10 or newer is recommended.

```bash
python -m venv .venv
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1

python -m pip install -r requirements.txt
python main.py
```

Desktop notification behavior depends on Plyer support for the operating system.

## Build an Android APK

Buildozer uses the included `buildozer.spec`.

### Ubuntu 24.04 / WSL2

Install Android build prerequisites:

```bash
sudo apt update
sudo apt install -y git zip unzip openjdk-17-jdk python3-pip \
  python3-virtualenv autoconf libtool pkg-config zlib1g-dev \
  libncurses5-dev libncursesw5-dev libtinfo6 cmake libffi-dev \
  libssl-dev automake autopoint gettext
```

Install Rust, which current python-for-android builds may require:

```bash
curl https://sh.rustup.rs -sSf | sh
. "$HOME/.cargo/env"
```

Create a Buildozer environment:

```bash
python3 -m virtualenv ~/.venvs/mealcare-build
source ~/.venvs/mealcare-build/bin/activate
python -m pip install --upgrade pip
python -m pip install buildozer setuptools cython==0.29.34
```

Build:

```bash
cd mealcare_android
buildozer -v android debug
```

The APK is created in `bin/`.

Build, install, run, and show logs on a connected device:

```bash
buildozer -v android debug deploy run logcat
```

On Windows, build inside WSL2 and keep the project in the Linux filesystem, such as `~/projects/mealcare_android`, rather than under `/mnt/c`.

## Android setup after installation

1. Open MealCare once so it can request notification permission and start its reminder service.
2. Allow notifications.
3. For more reliable timing, open Android Settings → Apps → MealCare → Battery and choose an unrestricted or equivalent option.
4. Some Android vendors aggressively stop background services. After rebooting the phone, open MealCare again.

Android may delay background work during Doze or manufacturer-specific battery-saving modes. A production app that requires exact alarms should add a native Android AlarmManager/WorkManager integration.

## Project files

- `main.py` — Kivy interface and app logic
- `app_data.py` — default plans, reminders, validation, due-notification selection
- `storage.py` — atomic local JSON persistence and notification deduplication
- `notifications.py` — Android permission, background-service startup, and Plyer notifications
- `service.py` — sticky background reminder loop
- `buildozer.spec` — Android packaging configuration

## Change the Android package name

The current application ID is:

```text
org.mealcare.planner
```

When changing `package.domain` or `package.name` in `buildozer.spec`, also change `PACKAGE_NAME` in `notifications.py`, because it is used to start the generated Python service.
