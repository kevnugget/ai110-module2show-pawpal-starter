"""PawPal+ core system logic.

This module defines the core domain classes for the PawPal+ pet care scheduling system.

Classes:
- Owner
- Pet
- Task
- Scheduler

The classes are intentionally lightweight to support a CLI-first workflow and make it easy
to add a Streamlit UI on top of the scheduling engine.
"""

from __future__ import annotations

import dataclasses
import enum
from datetime import datetime, timedelta
from typing import List, Optional, Dict
import uuid


class TaskPriority(enum.Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class TaskFrequency(enum.Enum):
    ONCE = "once"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


@dataclasses.dataclass
class Task:
    id: str
    name: str
    type: str
    due_at: datetime
    duration: timedelta = timedelta(minutes=15)
    priority: TaskPriority = TaskPriority.MEDIUM
    completed: bool = False
    completed_at: Optional[datetime] = None
    notes: Optional[str] = None
    frequency: TaskFrequency = TaskFrequency.ONCE

    def mark_done(self, when: Optional[datetime] = None) -> None:
        self.completed = True
        self.completed_at = when or datetime.now()

    def reschedule(self, next_due: datetime) -> None:
        self.due_at = next_due
        self.completed = False
        self.completed_at = None

    def is_overdue(self, now: Optional[datetime] = None) -> bool:
        now = now or datetime.now()
        return not self.completed and self.due_at < now

    def next_due_after(self, after: Optional[datetime] = None) -> datetime:
        """Return the next due date after a given point in time.

        For recurring tasks, this will advance the due date until it is after `after`.
        """
        after = after or datetime.now()
        due = self.due_at

        if self.frequency == TaskFrequency.ONCE:
            return due

        while due <= after:
            if self.frequency == TaskFrequency.DAILY:
                due += timedelta(days=1)
            elif self.frequency == TaskFrequency.WEEKLY:
                due += timedelta(weeks=1)
            elif self.frequency == TaskFrequency.MONTHLY:
                # Rough monthly advance; keeps the same day-of-month when possible.
                month = due.month + 1
                year = due.year + (month - 1) // 12
                month = (month - 1) % 12 + 1
                day = min(due.day, 28)
                due = due.replace(year=year, month=month, day=day)
            else:
                break

        return due

    def occurs_on(self, date: datetime) -> bool:
        """Does this task happen on the given date?"""
        target_start = datetime(year=date.year, month=date.month, day=date.day)
        target_end = target_start + timedelta(days=1)

        if self.frequency == TaskFrequency.ONCE:
            return target_start <= self.due_at < target_end

        # For recurring tasks, see if the task would have a due time on that date
        due_on_date = self.next_due_after(target_start - timedelta(seconds=1))
        return target_start <= due_on_date < target_end

    def estimate_urgency(self, now: Optional[datetime] = None) -> float:
        """Returns a score where higher means more urgent.

        Base urgency is driven by how overdue the task is + its priority.
        """
        now = now or datetime.now()
        base = float(self.priority.value)
        if self.completed:
            return 0.0

        delta = (now - self.due_at).total_seconds()
        overdue_score = max(delta / 60.0, 0.0)
        # Boost urgency by priority
        return base * (1.0 + overdue_score / 60.0)


@dataclasses.dataclass
class Pet:
    name: str
    species: str
    birthday: datetime
    tasks: List[Task] = dataclasses.field(default_factory=list)

    def get_age(self, at: Optional[datetime] = None) -> int:
        at = at or datetime.now()
        return int((at - self.birthday).days / 365)

    def is_senior(self, at: Optional[datetime] = None) -> bool:
        return self.get_age(at) >= 7

    def add_task(self, task: Task) -> None:
        self.tasks.append(task)

    def remove_task(self, task_id: str) -> None:
        self.tasks = [t for t in self.tasks if t.id != task_id]


@dataclasses.dataclass
class Owner:
    name: str
    email: str
    pets: List[Pet] = dataclasses.field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        self.pets.append(pet)

    def remove_pet(self, pet_name: str) -> None:
        self.pets = [p for p in self.pets if p.name != pet_name]

    def summary(self) -> str:
        """Return a human-readable summary of the owner and their pets."""
        lines = [f"Owner: {self.name} <{self.email}>", f"Pets: {len(self.pets)}"]
        now = datetime.now()
        for pet in self.pets:
            lines.append(f"  - {pet.name} ({pet.species}, age {pet.get_age()}) - {len(pet.tasks)} task(s)")
            for task in pet.tasks:
                next_due = task.next_due_after(now)
                recurrence = task.frequency.value
                lines.append(
                    f"      • {task.name} [{task.type}] — next: {next_due.strftime('%Y-%m-%d %H:%M')} "
                    f"({recurrence}, priority {task.priority.name})"
                )
        return "\n".join(lines)


def format_owner(owner: Owner) -> str:
    """Format an Owner instance into a user-friendly report string."""
    return owner.summary()


class Scheduler:
    """Schedules tasks for one or more pets."""

    def __init__(self, tasks: Optional[List[Task]] = None):
        self.tasks: List[Task] = tasks or []

    def add_task(self, task: Task) -> None:
        self.tasks.append(task)

    def remove_task(self, task_id: str) -> None:
        self.tasks = [t for t in self.tasks if t.id != task_id]

    def get_next_task(self, now: Optional[datetime] = None) -> Optional[Task]:
        now = now or datetime.now()
        unscheduled = [t for t in self.tasks if not t.completed]
        if not unscheduled:
            return None
        return max(unscheduled, key=lambda t: t.estimate_urgency(now))

    def filter_tasks(
        self,
        pet_name: Optional[str] = None,
        task_type: Optional[str] = None,
        min_priority: Optional[TaskPriority] = None,
    ) -> List[Task]:
        """Return tasks matching optional filter criteria."""
        results = self.tasks
        if pet_name is not None:
            results = [t for t in results if getattr(t, "pet_name", None) == pet_name]
        if task_type is not None:
            results = [t for t in results if t.type == task_type]
        if min_priority is not None:
            results = [t for t in results if t.priority.value >= min_priority.value]
        return results

    def prioritize_tasks(self, tasks: List[Task], now: Optional[datetime] = None, sort_by: str = "urgency") -> List[Task]:
        now = now or datetime.now()
        if sort_by == "due":
            return sorted(tasks, key=lambda t: t.due_at)
        if sort_by == "priority":
            return sorted(tasks, key=lambda t: t.priority.value, reverse=True)
        # default: urgency
        return sorted(tasks, key=lambda t: t.estimate_urgency(now), reverse=True)

    def schedule_day(
        self,
        date: datetime,
        pet_name: Optional[str] = None,
        task_type: Optional[str] = None,
        min_priority: Optional[TaskPriority] = None,
        sort_by: str = "urgency",
    ) -> List[Task]:
        """Return a list of tasks ordered for the given day.

        Supports filtering and sorting.
        """
        day_start = datetime(year=date.year, month=date.month, day=date.day)

        # Include recurring tasks and normal tasks due today
        candidates = [t for t in self.tasks if t.occurs_on(day_start)]

        # Filters
        if pet_name or task_type or min_priority:
            candidates = self.filter_tasks(pet_name=pet_name, task_type=task_type, min_priority=min_priority)
            candidates = [t for t in candidates if t.occurs_on(day_start)]

        return self.prioritize_tasks(candidates, now=day_start, sort_by=sort_by)


# Demo helper
def demo_schedule():
    owner = Owner(name="Sam", email="sam@example.com")

    pet = Pet(name="Mittens", species="cat", birthday=datetime(2018, 6, 1))
    owner.add_pet(pet)

    now = datetime.now()
    tasks = [
        Task(id=str(uuid.uuid4()), name="Morning meal", type="feeding", due_at=now.replace(hour=8, minute=0), priority=TaskPriority.HIGH),
        Task(id=str(uuid.uuid4()), name="Walk", type="walk", due_at=now.replace(hour=17, minute=0), priority=TaskPriority.MEDIUM),
        Task(id=str(uuid.uuid4()), name="Vet appointment", type="appointment", due_at=now + timedelta(days=1, hours=9), priority=TaskPriority.CRITICAL),
    ]

    for t in tasks:
        pet.add_task(t)

    scheduler = Scheduler(tasks=pet.tasks)
    today_tasks = scheduler.schedule_day(now)

    print(f"Schedule for {pet.name} ({now.strftime('%Y-%m-%d')}):")
    for idx, task in enumerate(today_tasks, start=1):
        status = "✅" if task.completed else "⏳"
        print(f"{idx}. {task.name} ({task.type}) - due {task.due_at.strftime('%H:%M')} - {status}")


if __name__ == "__main__":
    demo_schedule()
