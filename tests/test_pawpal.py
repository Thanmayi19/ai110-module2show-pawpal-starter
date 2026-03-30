from datetime import date, time, timedelta

from pawpal_system import (
    DailyTask,
    Pet,
    Schedule,
    ScheduledTask,
    Scheduler,
    TaskCategory,
    User,
)


def test_mark_complete_changes_status():
    task = DailyTask(name="Morning walk", category=TaskCategory.WALK, duration=30, priority=3)
    assert not task.is_completed
    task.mark_complete()
    assert task.is_completed


def test_add_task_increases_pet_task_count():
    pet = Pet(name="Mochi", species="dog", breed="Shiba Inu", age=3)
    assert len(pet.get_tasks()) == 0
    pet.add_task(DailyTask(name="Feeding", category=TaskCategory.FEEDING, duration=10, priority=4))
    assert len(pet.get_tasks()) == 1


# ---------------------------------------------------------------------------
# Sorting
# ---------------------------------------------------------------------------

def test_sorting_schedule_is_chronological():
    """generate_plan() scheduled_tasks list has strictly ascending start times."""
    pet = Pet(name="Rex", species="dog", breed="Lab", age=2)
    pet.add_task(DailyTask(name="Grooming", category=TaskCategory.GROOMING, duration=20, priority=1))
    pet.add_task(DailyTask(name="Walk", category=TaskCategory.WALK, duration=30, priority=3))
    pet.add_task(DailyTask(name="Medication", category=TaskCategory.MEDICATION, duration=10, priority=5))
    user = User(name="Alex", email="alex@example.com", time_available=120)
    scheduler = Scheduler(user=user, pet=pet)

    schedule = scheduler.generate_plan()

    start_times = [st.start_time for st in schedule.scheduled_tasks]
    assert start_times == sorted(start_times)


def test_sorting_equal_priority_shorter_task_scheduled_first():
    """When two tasks share the same priority, the shorter one appears earlier in the schedule."""
    pet = Pet(name="Rex", species="dog", breed="Lab", age=2)
    pet.add_task(DailyTask(name="Long Walk", category=TaskCategory.WALK, duration=60, priority=3))
    pet.add_task(DailyTask(name="Quick Feed", category=TaskCategory.FEEDING, duration=10, priority=3))
    user = User(name="Alex", email="alex@example.com", time_available=120)
    scheduler = Scheduler(user=user, pet=pet)

    schedule = scheduler.generate_plan()

    assert len(schedule.scheduled_tasks) == 2
    assert schedule.scheduled_tasks[0].task.name == "Quick Feed"
    assert schedule.scheduled_tasks[1].task.name == "Long Walk"


# ---------------------------------------------------------------------------
# Recurrence
# ---------------------------------------------------------------------------

def test_recurrence_daily_task_creates_successor_for_next_day():
    """Marking a daily task complete returns a successor due exactly one day later."""
    today = date(2026, 3, 30)
    task = DailyTask(
        name="Morning Feeding",
        category=TaskCategory.FEEDING,
        duration=10,
        priority=4,
        frequency="daily",
        due_date=today,
    )

    successor = task.mark_complete()

    assert successor is not None
    assert successor.due_date == today + timedelta(days=1)
    assert successor.name == task.name
    assert not successor.is_completed


def test_recurrence_daily_task_without_due_date_falls_back_to_today():
    """A daily task with due_date=None uses date.today() as the base for the successor."""
    task = DailyTask(
        name="Evening Walk",
        category=TaskCategory.WALK,
        duration=30,
        priority=3,
        frequency="daily",
        due_date=None,
    )

    successor = task.mark_complete()

    assert successor is not None
    assert successor.due_date == date.today() + timedelta(days=1)


# ---------------------------------------------------------------------------
# Conflict detection
# ---------------------------------------------------------------------------

def _make_scheduler() -> Scheduler:
    pet = Pet(name="Mochi", species="dog", breed="Shiba Inu", age=3)
    user = User(name="Sam", email="sam@example.com", time_available=240)
    return Scheduler(user=user, pet=pet)


def test_conflict_detection_no_conflict_returns_empty_list():
    """detect_conflicts() returns [] when all scheduled tasks have distinct start times."""
    scheduler = _make_scheduler()
    walk = DailyTask(name="Walk", category=TaskCategory.WALK, duration=30, priority=3)
    feed = DailyTask(name="Feeding", category=TaskCategory.FEEDING, duration=10, priority=4)
    schedule = Schedule(
        date=date(2026, 3, 30),
        scheduled_tasks=[
            ScheduledTask(task=walk, start_time=time(8, 0), end_time=time(8, 30)),
            ScheduledTask(task=feed, start_time=time(8, 30), end_time=time(8, 40)),
        ],
    )

    assert scheduler.detect_conflicts(schedule) == []


def test_conflict_detection_same_start_time_returns_warning():
    """detect_conflicts() returns one warning message when two tasks share the same start time."""
    scheduler = _make_scheduler()
    walk = DailyTask(name="Walk", category=TaskCategory.WALK, duration=30, priority=3)
    feed = DailyTask(name="Feeding", category=TaskCategory.FEEDING, duration=10, priority=4)
    schedule = Schedule(
        date=date(2026, 3, 30),
        scheduled_tasks=[
            ScheduledTask(task=walk, start_time=time(8, 0), end_time=time(8, 30)),
            ScheduledTask(task=feed, start_time=time(8, 0), end_time=time(8, 10)),
        ],
    )

    conflicts = scheduler.detect_conflicts(schedule)

    assert len(conflicts) == 1
    assert "Walk" in conflicts[0]
    assert "Feeding" in conflicts[0]
    assert "08:00" in conflicts[0]
    assert "Mochi" in conflicts[0]
