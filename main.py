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

mochi.add_task(DailyTask(name="Morning walk",       category=TaskCategory.WALK,        duration=30, priority=5))
mochi.add_task(DailyTask(name="Breakfast feeding",  category=TaskCategory.FEEDING,     duration=10, priority=4))
mochi.add_task(DailyTask(name="Fetch in the yard",  category=TaskCategory.ENRICHMENT,  duration=20, priority=2, notes="Use the tennis ball."))

# ---------------------------------------------------------------------------
# Tasks for Luna (cat)
# ---------------------------------------------------------------------------

luna.add_task(DailyTask(name="Thyroid medication",  category=TaskCategory.MEDICATION,  duration=5,  priority=5, notes="Mix into wet food."))
luna.add_task(DailyTask(name="Breakfast feeding",   category=TaskCategory.FEEDING,     duration=10, priority=4))
luna.add_task(DailyTask(name="Brush fur",           category=TaskCategory.GROOMING,    duration=15, priority=2))

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
