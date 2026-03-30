from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date, time, timedelta
from enum import Enum
from uuid import uuid4


# ---------------------------------------------------------------------------
# Enum
# ---------------------------------------------------------------------------

class TaskCategory(Enum):
    WALK = "Walk"
    FEEDING = "Feeding"
    MEDICATION = "Medication"
    ENRICHMENT = "Enrichment"
    GROOMING = "Grooming"
    OTHER = "Other"


# ---------------------------------------------------------------------------
# DailyTask
# ---------------------------------------------------------------------------

@dataclass
class DailyTask:
    name: str
    category: TaskCategory
    duration: int           # minutes
    priority: int           # 1 (low) – 5 (high)

    def __post_init__(self) -> None:
        if not (1 <= self.priority <= 5):
            raise ValueError(f"priority must be 1–5, got {self.priority}")
        if self.frequency not in (None, "daily", "weekly"):
            raise ValueError(f"frequency must be 'daily', 'weekly', or None, got {self.frequency!r}")

    notes: str = ""
    is_completed: bool = False
    frequency: str | None = None        # "daily", "weekly", or None (one-shot)
    due_date: date | None = None        # when this task is next due
    task_id: str = field(default_factory=lambda: str(uuid4()))

    def mark_complete(self) -> DailyTask | None:
        """Mark this task as completed and return a successor for recurring tasks.

        Returns a new DailyTask with an updated due_date if frequency is 'daily'
        or 'weekly', otherwise returns None.
        """
        self.is_completed = True

        if self.frequency == "daily":
            next_due = (self.due_date or date.today()) + timedelta(days=1)
        elif self.frequency == "weekly":
            next_due = (self.due_date or date.today()) + timedelta(weeks=1)
        else:
            return None

        return DailyTask(
            name=self.name,
            category=self.category,
            duration=self.duration,
            priority=self.priority,
            notes=self.notes,
            frequency=self.frequency,
            due_date=next_due,
        )

    def mark_incomplete(self) -> None:
        """Mark this task as not yet completed."""
        self.is_completed = False

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "name": self.name,
            "category": self.category.value,
            "duration": self.duration,
            "priority": self.priority,
            "notes": self.notes,
            "is_completed": self.is_completed,
            "frequency": self.frequency,
            "due_date": self.due_date.isoformat() if self.due_date else None,
        }


# ---------------------------------------------------------------------------
# ScheduledTask  (DailyTask + time placement)
# ---------------------------------------------------------------------------

@dataclass
class ScheduledTask:
    task: DailyTask
    start_time: time
    end_time: time


# ---------------------------------------------------------------------------
# Schedule  (output of Scheduler)
# ---------------------------------------------------------------------------

@dataclass
class Schedule:
    date: date
    scheduled_tasks: list[ScheduledTask] = field(default_factory=list)
    reasoning: str = ""

    @property
    def total_duration(self) -> int:
        return sum(st.task.duration for st in self.scheduled_tasks)

    def is_feasible(self, max_minutes: int) -> bool:
        """Return True if total task duration fits within max_minutes."""
        return self.total_duration <= max_minutes

    def get_summary(self) -> str:
        """Return a formatted multi-line string summarising the day's schedule."""
        lines = [f"Schedule for {self.date} — {self.total_duration} min total"]
        for st in self.scheduled_tasks:
            lines.append(
                f"  {st.start_time.strftime('%H:%M')}–{st.end_time.strftime('%H:%M')} "
                f"[P{st.task.priority}] {st.task.name} ({st.task.duration} min)"
            )
        if self.reasoning:
            lines.append(f"\nReasoning: {self.reasoning}")
        return "\n".join(lines)

    def add_task(self, scheduled_task: ScheduledTask) -> None:
        """Append a ScheduledTask to this schedule."""
        self.scheduled_tasks.append(scheduled_task)

    def remove_task(self, task_id: str) -> None:
        """Remove the ScheduledTask whose underlying DailyTask has the given task_id."""
        self.scheduled_tasks = [
            st for st in self.scheduled_tasks if st.task.task_id != task_id
        ]

    def to_dict(self) -> dict:
        """Serialize the schedule to a plain dict suitable for JSON or display."""
        return {
            "date": self.date.isoformat(),
            "total_duration": self.total_duration,
            "reasoning": self.reasoning,
            "scheduled_tasks": [
                {
                    "start_time": st.start_time.strftime("%H:%M"),
                    "end_time": st.end_time.strftime("%H:%M"),
                    "task": st.task.to_dict(),
                }
                for st in self.scheduled_tasks
            ],
        }


# ---------------------------------------------------------------------------
# Constraint
# ---------------------------------------------------------------------------

@dataclass
class Constraint:
    max_duration: int                                                    # total minutes allowed per day
    preferred_times: list[str] = field(default_factory=list)            # e.g. ["morning", "evening"]
    excluded_categories: list[TaskCategory] = field(default_factory=list)

    def is_satisfied(self, schedule: Schedule) -> bool:
        """Return True if the schedule respects this constraint's duration cap and category exclusions."""
        if schedule.total_duration > self.max_duration:
            return False
        for st in schedule.scheduled_tasks:
            if st.task.category in self.excluded_categories:
                return False
        return True


# ---------------------------------------------------------------------------
# Pet
# ---------------------------------------------------------------------------

@dataclass
class Pet:
    name: str
    species: str
    breed: str
    age: int
    health_notes: str = ""
    pet_id: str = field(default_factory=lambda: str(uuid4()))
    _tasks: list[DailyTask] = field(default_factory=list, repr=False)

    def add_task(self, task: DailyTask) -> None:
        """Add a DailyTask to this pet's task list."""
        self._tasks.append(task)

    def remove_task(self, task_id: str) -> None:
        """Remove the task with the given task_id from this pet's task list."""
        self._tasks = [t for t in self._tasks if t.task_id != task_id]

    def get_tasks(self) -> list[DailyTask]:
        """Return a copy of all tasks assigned to this pet."""
        return list(self._tasks)

    def get_pending_tasks(self) -> list[DailyTask]:
        """Return only tasks that have not yet been completed."""
        return [t for t in self._tasks if not t.is_completed]

    @property
    def task_completion_rate(self) -> float:
        """Fraction of tasks that are completed (0.0 if no tasks)."""
        if not self._tasks:
            return 0.0
        completed = sum(1 for t in self._tasks if t.is_completed)
        return completed / len(self._tasks)


# ---------------------------------------------------------------------------
# User
# ---------------------------------------------------------------------------

@dataclass
class User:
    name: str
    email: str
    time_available: int                         # minutes per day
    preferences: list[str] = field(default_factory=list)
    user_id: str = field(default_factory=lambda: str(uuid4()))
    _pets: list[Pet] = field(default_factory=list, repr=False)

    def add_pet(self, pet: Pet) -> None:
        """Register a pet under this user's account."""
        self._pets.append(pet)

    def remove_pet(self, pet_id: str) -> None:
        """Remove the pet with the given pet_id from this user's account."""
        self._pets = [p for p in self._pets if p.pet_id != pet_id]

    def get_pets(self) -> list[Pet]:
        """Return a copy of all pets registered to this user."""
        return list(self._pets)

    def get_all_tasks(self) -> list[DailyTask]:
        """Return every DailyTask across all of this user's pets."""
        tasks: list[DailyTask] = []
        for pet in self._pets:
            tasks.extend(pet.get_tasks())
        return tasks

    def create_scheduler(self, pet: Pet) -> Scheduler:
        """Convenience factory: return a new Scheduler for the given pet."""
        return Scheduler(user=self, pet=pet)


# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------

@dataclass
class Scheduler:
    user: User
    pet: Pet
    constraints: list[Constraint] = field(default_factory=list)

    def add_constraint(self, constraint: Constraint) -> None:
        """Add a scheduling constraint that generate_plan will respect."""
        self.constraints.append(constraint)

    def mark_task_complete(self, task_id: str) -> DailyTask | None:
        """Mark a task complete by ID and register its successor if it recurs.

        Finds the task on the scheduler's pet, calls mark_complete(), and — for
        recurring tasks — adds the returned successor task back to the pet so it
        appears in future plans.  Returns the successor task, or None for
        one-shot tasks.

        Raises ValueError if no task with the given task_id exists on the pet.
        """
        task = next((t for t in self.pet.get_tasks() if t.task_id == task_id), None)
        if task is None:
            raise ValueError(f"No task with id {task_id!r} found on pet '{self.pet.name}'.")

        successor = task.mark_complete()
        if successor is not None:
            self.pet.add_task(successor)
        return successor

    def filter_tasks(
        self,
        completed: bool | None = None,
        pet_name: str | None = None,
    ) -> list[DailyTask]:
        """Return tasks from the scheduler's pet filtered by completion status and/or pet name.

        Args:
            completed: If True, return only completed tasks. If False, return only
                       pending tasks. If None, completion status is not filtered.
            pet_name: If provided, return tasks only when the pet's name matches
                      (case-insensitive). Returns an empty list when it doesn't match.

        Returns:
            A list of DailyTask objects that satisfy all supplied filters.
        """
        if pet_name is not None and self.pet.name.lower() != pet_name.lower():
            return []

        tasks = self.pet.get_tasks()

        if completed is not None:
            tasks = [t for t in tasks if t.is_completed == completed]

        return tasks

    def detect_conflicts(self, schedule: Schedule) -> list[str]:
        """Return a warning string for every pair of tasks that share the same start time.

        Warnings are formatted as:
            "Conflict: <name A> and <name B> both scheduled at HH:MM for <pet name>"
        An empty list means no conflicts were found.
        """
        warnings: list[str] = []
        seen: dict[time, str] = {}  # start_time → task name of first task at that time

        for st in schedule.scheduled_tasks:
            start = st.start_time
            if start in seen:
                warnings.append(
                    f"Conflict: {seen[start]} and {st.task.name} both scheduled at "
                    f"{start.strftime('%H:%M')} for {self.pet.name}"
                )
            else:
                seen[start] = st.task.name

        return warnings

    def validate_schedule(self, schedule: Schedule) -> list[str]:
        """Check all constraints against the schedule.

        Returns a list of human-readable violation strings.
        An empty list means the schedule satisfies every constraint.
        """
        violations: list[str] = []

        # Check each constraint individually
        for i, constraint in enumerate(self.constraints, start=1):
            label = f"Constraint {i}"

            if schedule.total_duration > constraint.max_duration:
                violations.append(
                    f"{label}: total duration {schedule.total_duration} min "
                    f"exceeds max_duration {constraint.max_duration} min."
                )

            for st in schedule.scheduled_tasks:
                if st.task.category in constraint.excluded_categories:
                    violations.append(
                        f"{label}: task '{st.task.name}' has excluded category "
                        f"'{st.task.category.value}'."
                    )

        # Check against user's overall time budget
        if schedule.total_duration > self.user.time_available:
            violations.append(
                f"User budget: total duration {schedule.total_duration} min "
                f"exceeds owner's available time {self.user.time_available} min."
            )

        return violations

    def reschedule(self, plan_date: date | None = None, max_retries: int = 3) -> Schedule:
        """Try up to max_retries times to generate a feasible schedule.

        On each retry the effective budget is tightened by 10 % to nudge the
        greedy algorithm toward a smaller, constraint-satisfying plan.  Returns
        the last generated schedule even if no fully feasible plan was found,
        so callers can inspect violations themselves.
        """
        if plan_date is None:
            plan_date = date.today()

        best_schedule: Schedule | None = None

        for attempt in range(max_retries):
            schedule = self.generate_plan(plan_date)
            violations = self.validate_schedule(schedule)

            if not violations:
                return schedule  # found a valid plan

            # Tighten the budget for the next attempt by temporarily reducing
            # time_available on the user object (restored after the loop).
            if attempt < max_retries - 1:
                tightened = int(self.user.time_available * (0.9 ** (attempt + 1)))
                original_time = self.user.time_available
                self.user.time_available = max(tightened, 1)
                best_schedule = schedule
                self.user.time_available = original_time  # restore for next iter
            else:
                best_schedule = schedule

        return best_schedule  # type: ignore[return-value]  # always set if max_retries >= 1

    def generate_plan(self, plan_date: date | None = None) -> Schedule:
        """Greedily build a Schedule for plan_date, respecting all constraints and user budget."""
        if plan_date is None:
            plan_date = date.today()

        tasks = self.pet.get_tasks()

        # Exclude already-completed tasks
        tasks = [t for t in tasks if not t.is_completed]

        # Filter out excluded categories from all constraints
        excluded = {cat for c in self.constraints for cat in c.excluded_categories}
        tasks = [t for t in tasks if t.category not in excluded]

        constraint_budgets = [c.max_duration for c in self.constraints]
        max_minutes = min(constraint_budgets) if constraint_budgets else self.user.time_available
        max_minutes = min(max_minutes, self.user.time_available)

        # Sort by priority descending, then duration ascending (greedy)
        tasks_sorted = sorted(tasks, key=lambda t: (-t.priority, t.duration))

        scheduled: list[ScheduledTask] = []
        total = 0
        current_hour, current_minute = 8, 0  # start at 08:00

        for task in tasks_sorted:
            if total + task.duration > max_minutes:
                continue
            start = time(current_hour, current_minute)
            end_total = current_hour * 60 + current_minute + task.duration
            if end_total >= 24 * 60:
                break  # no more room in the day
            end = time(end_total // 60, end_total % 60)
            scheduled.append(ScheduledTask(task=task, start_time=start, end_time=end))
            total += task.duration
            current_hour, current_minute = end_total // 60, end_total % 60

        reasoning = self.explain_plan(tasks_sorted, scheduled, max_minutes)
        return Schedule(date=plan_date, scheduled_tasks=scheduled, reasoning=reasoning)

    def explain_plan(
        self,
        candidates: list[DailyTask],
        scheduled: list[ScheduledTask],
        max_minutes: int,
    ) -> str:
        """Return a human-readable string explaining which tasks were scheduled and why others were skipped."""
        scheduled_ids = {st.task.task_id for st in scheduled}
        skipped = [t for t in candidates if t.task_id not in scheduled_ids]

        lines = [
            f"Time budget: {max_minutes} min. "
            f"Scheduled {len(scheduled)} of {len(candidates)} tasks "
            f"({sum(st.task.duration for st in scheduled)} min used).",
            "Tasks are ordered by priority (high→low), then shortest duration first.",
        ]
        if skipped:
            skipped_names = ", ".join(t.name for t in skipped)
            lines.append(f"Skipped (would exceed budget): {skipped_names}.")
        return " ".join(lines)
