from datetime import date

from pawpal_system import (
    Constraint,
    DailyTask,
    Pet,
    TaskCategory,
    User,
)

# ---------------------------------------------------------------------------
# Owner
# ---------------------------------------------------------------------------

jordan = User(
    name="Jordan Smith",
    email="jordan@example.com",
    time_available=120,  # 2 hours available today
)

# ---------------------------------------------------------------------------
# Pets
# ---------------------------------------------------------------------------

mochi = Pet(name="Mochi", species="dog", breed="Shiba Inu", age=3)
luna = Pet(name="Luna", species="cat", breed="Domestic Shorthair", age=5, health_notes="Needs daily thyroid medication.")

jordan.add_pet(mochi)
jordan.add_pet(luna)

# ---------------------------------------------------------------------------
# Tasks for Mochi (dog)
# ---------------------------------------------------------------------------

mochi.add_task(DailyTask(name="Morning walk",       category=TaskCategory.WALK,       duration=30, priority=5, frequency="daily",  due_date=date.today()))
mochi.add_task(DailyTask(name="Breakfast feeding",  category=TaskCategory.FEEDING,    duration=10, priority=4, frequency="daily",  due_date=date.today()))
mochi.add_task(DailyTask(name="Fetch in the yard",  category=TaskCategory.ENRICHMENT, duration=20, priority=2, frequency="weekly", due_date=date.today(), notes="Use the tennis ball."))

# ---------------------------------------------------------------------------
# Tasks for Luna (cat)
# ---------------------------------------------------------------------------

luna.add_task(DailyTask(name="Thyroid medication",  category=TaskCategory.MEDICATION, duration=5,  priority=5, frequency="daily",  due_date=date.today(), notes="Mix into wet food."))
luna.add_task(DailyTask(name="Breakfast feeding",   category=TaskCategory.FEEDING,    duration=10, priority=4, frequency="daily",  due_date=date.today()))
luna.add_task(DailyTask(name="Brush fur",           category=TaskCategory.GROOMING,   duration=15, priority=2))  # one-shot

# ---------------------------------------------------------------------------
# Demonstrate mark_task_complete() with recurring task successor creation
# ---------------------------------------------------------------------------

mochi_scheduler = jordan.create_scheduler(mochi)
luna_scheduler  = jordan.create_scheduler(luna)

print("=" * 60)
print("          Recurring task demo")
print("=" * 60)

# Complete Mochi's daily "Breakfast feeding" → expect a successor due tomorrow
feeding = mochi.get_tasks()[1]
print(f"\nCompleting '{feeding.name}' (frequency={feeding.frequency}, due={feeding.due_date})")
successor = mochi_scheduler.mark_task_complete(feeding.task_id)
if successor:
    print(f"  Successor created: '{successor.name}', due={successor.due_date}")

# Complete Mochi's weekly "Fetch in the yard" → expect a successor due in 7 days
fetch = mochi.get_tasks()[2]
print(f"\nCompleting '{fetch.name}' (frequency={fetch.frequency}, due={fetch.due_date})")
successor = mochi_scheduler.mark_task_complete(fetch.task_id)
if successor:
    print(f"  Successor created: '{successor.name}', due={successor.due_date}")

# Complete Luna's one-shot "Brush fur" → no successor expected
brush = luna.get_tasks()[2]
print(f"\nCompleting '{brush.name}' (frequency={brush.frequency})")
successor = luna_scheduler.mark_task_complete(brush.task_id)
print(f"  Successor: {successor} (expected None)")

print()
print(f"Mochi now has {len(mochi.get_tasks())} tasks (3 original + 2 successors):")
for t in mochi.get_tasks():
    status = "done" if t.is_completed else "pending"
    freq   = t.frequency or "one-shot"
    due    = str(t.due_date) if t.due_date else "—"
    print(f"  [{status}] {t.name}  freq={freq}  due={due}")

# ---------------------------------------------------------------------------
# Generate and print schedules
# ---------------------------------------------------------------------------

constraint = Constraint(max_duration=120, preferred_times=["morning", "afternoon"])

print("=" * 60)
print("          🐾  PawPal+  —  Today's Schedule")
print("=" * 60)

for pet in jordan.get_pets():
    scheduler = jordan.create_scheduler(pet)
    scheduler.add_constraint(constraint)
    schedule = scheduler.generate_plan(plan_date=date.today())

    print()
    print(f"  Pet: {pet.name} ({pet.breed})")
    print("-" * 60)
    print(schedule.get_summary())
    print()

print("=" * 60)

# ---------------------------------------------------------------------------
# Demonstrate filter_tasks()
# ---------------------------------------------------------------------------

print()
print("=" * 60)
print("          Filter demos")
print("=" * 60)

mochi_scheduler = jordan.create_scheduler(mochi)
luna_scheduler  = jordan.create_scheduler(luna)

# Filter 1: pending tasks for Mochi
pending_mochi = mochi_scheduler.filter_tasks(completed=False, pet_name="Mochi")
print(f"\nPending tasks for Mochi ({len(pending_mochi)}):")
for t in pending_mochi:
    print(f"  - {t.name} [{t.category.value}]")

# Filter 2: completed tasks for Luna
done_luna = luna_scheduler.filter_tasks(completed=True, pet_name="Luna")
print(f"\nCompleted tasks for Luna ({len(done_luna)}):")
for t in done_luna:
    print(f"  - {t.name} [{t.category.value}]")

# Filter 3: all tasks for Mochi regardless of status
all_mochi = mochi_scheduler.filter_tasks(pet_name="Mochi")
print(f"\nAll tasks for Mochi ({len(all_mochi)}):")
for t in all_mochi:
    status = "done" if t.is_completed else "pending"
    print(f"  - {t.name} [{status}]")

# Filter 4: pet_name mismatch returns empty list
wrong_pet = mochi_scheduler.filter_tasks(pet_name="Luna")
print(f"\nFilter 'Luna' on Mochi's scheduler → {len(wrong_pet)} tasks (expected 0)")

print()
print("=" * 60)

# ---------------------------------------------------------------------------
# Demonstrate detect_conflicts()
# ---------------------------------------------------------------------------

from datetime import time as dt_time
from pawpal_system import Schedule, ScheduledTask

print()
print("=" * 60)
print("          Conflict detection demo")
print("=" * 60)

biscuit = Pet(name="Biscuit", species="dog", breed="Beagle", age=2)
jordan.add_pet(biscuit)

walk    = DailyTask(name="Walk",    category=TaskCategory.WALK,     duration=30, priority=5)
feeding = DailyTask(name="Feeding", category=TaskCategory.FEEDING,  duration=10, priority=4)
groom   = DailyTask(name="Groom",   category=TaskCategory.GROOMING, duration=20, priority=3)

# Manually build a schedule where Walk and Feeding both start at 08:00
conflict_schedule = Schedule(date=date.today())
conflict_schedule.add_task(ScheduledTask(task=walk,    start_time=dt_time(8, 0),  end_time=dt_time(8, 30)))
conflict_schedule.add_task(ScheduledTask(task=feeding, start_time=dt_time(8, 0),  end_time=dt_time(8, 10)))  # conflict
conflict_schedule.add_task(ScheduledTask(task=groom,   start_time=dt_time(8, 30), end_time=dt_time(8, 50)))  # no conflict

biscuit_scheduler = jordan.create_scheduler(biscuit)
conflicts = biscuit_scheduler.detect_conflicts(conflict_schedule)

print(f"\nSchedule has {len(conflict_schedule.scheduled_tasks)} tasks, {len(conflicts)} conflict(s):")
for warning in conflicts:
    print(f"  !! {warning}")

# Confirm a clean schedule produces no warnings
clean_schedule = Schedule(date=date.today())
clean_schedule.add_task(ScheduledTask(task=walk,    start_time=dt_time(8, 0),  end_time=dt_time(8, 30)))
clean_schedule.add_task(ScheduledTask(task=feeding, start_time=dt_time(8, 30), end_time=dt_time(8, 40)))
clean_schedule.add_task(ScheduledTask(task=groom,   start_time=dt_time(8, 40), end_time=dt_time(9, 0)))

clean_conflicts = biscuit_scheduler.detect_conflicts(clean_schedule)
print(f"\nClean schedule conflicts: {len(clean_conflicts)} (expected 0)")

print()
print("=" * 60)
