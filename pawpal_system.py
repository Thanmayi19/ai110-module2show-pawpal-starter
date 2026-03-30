from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date, time
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
    notes: str = ""
    is_completed: bool = False
    task_id: str = field(default_factory=lambda: str(uuid4()))

    def mark_complete(self) -> None:
        self.is_completed = True

    def mark_incomplete(self) -> None:
        self.is_completed = False


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
        return self.total_duration <= max_minutes

    def get_summary(self) -> str:
        lines = [f"Schedule for {self.date} — {self.total_duration} min total"]
        for st in self.scheduled_tasks:
            lines.append(
                f"  {st.start_time.strftime('%H:%M')}–{st.end_time.strftime('%H:%M')} "
                f"[P{st.task.priority}] {st.task.name} ({st.task.duration} min)"
            )
        if self.reasoning:
            lines.append(f"\nReasoning: {self.reasoning}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Constraint
# ---------------------------------------------------------------------------

@dataclass
class Constraint:
    max_duration: int                           # total minutes allowed per day
    preferred_times: list[str] = field(default_factory=list)        # e.g. ["morning", "evening"]
    excluded_categories: list[TaskCategory] = field(default_factory=list)

    def is_satisfied(self, schedule: Schedule) -> bool:
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
        self._tasks.append(task)

    def remove_task(self, task_id: str) -> None:
        self._tasks = [t for t in self._tasks if t.task_id != task_id]

    def get_tasks(self) -> list[DailyTask]:
        return list(self._tasks)


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
        self._pets.append(pet)

    def remove_pet(self, pet_id: str) -> None:
        self._pets = [p for p in self._pets if p.pet_id != pet_id]

    def get_pets(self) -> list[Pet]:
        return list(self._pets)


# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------

@dataclass
class Scheduler:
    user: User
    pet: Pet
    constraints: list[Constraint] = field(default_factory=list)

    def add_constraint(self, constraint: Constraint) -> None:
        self.constraints.append(constraint)

    def generate_plan(self, plan_date: date | None = None) -> Schedule:
        if plan_date is None:
            plan_date = date.today()

        tasks = self.pet.get_tasks()

        # Filter out excluded categories from all constraints
        excluded = {cat for c in self.constraints for cat in c.excluded_categories}
        tasks = [t for t in tasks if t.category not in excluded]

        # Determine time budget
        max_minutes = min(
            (c.max_duration for c in self.constraints),
            default=self.user.time_available,
        )
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
            end_minutes = current_hour * 60 + current_minute + task.duration
            end = time(end_minutes // 60 % 24, end_minutes % 60)
            scheduled.append(ScheduledTask(task=task, start_time=start, end_time=end))
            total += task.duration
            current_hour, current_minute = end_minutes // 60 % 24, end_minutes % 60

        reasoning = self.explain_plan(tasks_sorted, scheduled, max_minutes)
        return Schedule(date=plan_date, scheduled_tasks=scheduled, reasoning=reasoning)

    def explain_plan(
        self,
        candidates: list[DailyTask],
        scheduled: list[ScheduledTask],
        max_minutes: int,
    ) -> str:
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
