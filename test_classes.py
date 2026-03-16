import unittest
from datetime import datetime, timedelta
import uuid

from pawpal_system import (
    Owner,
    Pet,
    Task,
    TaskFrequency,
    TaskPriority,
    Scheduler,
)


class TestPawPalSystem(unittest.TestCase):
    def setUp(self) -> None:
        # Use a fixed datetime for predictability
        self.now = datetime(2026, 3, 15, 8, 0, 0)

    def test_task_urgency_reflects_overdue_and_priority(self):
        overdue_task = Task(
            id=str(uuid.uuid4()),
            name="Overdue med",
            type="medication",
            due_at=self.now - timedelta(hours=2),
            priority=TaskPriority.MEDIUM,
        )
        soon_task = Task(
            id=str(uuid.uuid4()),
            name="Soon walk",
            type="walk",
            due_at=self.now + timedelta(minutes=30),
            priority=TaskPriority.HIGH,
        )

        self.assertGreater(overdue_task.estimate_urgency(self.now), soon_task.estimate_urgency(self.now))

    def test_task_next_due_for_recurring(self):
        task = Task(
            id=str(uuid.uuid4()),
            name="Daily check",
            type="check",
            due_at=self.now,
            frequency=TaskFrequency.DAILY,
        )

        # Next due after now should be tomorrow
        next_due = task.next_due_after(self.now + timedelta(minutes=1))
        self.assertEqual(next_due.date(), (self.now + timedelta(days=1)).date())

    def test_task_occurs_on_for_monthly_recurring(self):
        task = Task(
            id=str(uuid.uuid4()),
            name="Monthly refill",
            type="medication",
            due_at=self.now,
            frequency=TaskFrequency.MONTHLY,
        )

        # It should occur on the base day
        self.assertTrue(task.occurs_on(self.now))
        # It should occur on the same day next month
        next_month = (self.now.replace(day=1) + timedelta(days=32)).replace(day=self.now.day)
        self.assertTrue(task.occurs_on(next_month))

    def test_scheduler_filter_and_sort(self):
        task_a = Task(
            id=str(uuid.uuid4()),
            name="A",
            type="walk",
            due_at=self.now.replace(hour=9),
            priority=TaskPriority.LOW,
        )
        task_b = Task(
            id=str(uuid.uuid4()),
            name="B",
            type="feeding",
            due_at=self.now.replace(hour=8),
            priority=TaskPriority.HIGH,
        )
        # Attach pet_name metadata so filtering works
        task_a.pet_name = "Rex"
        task_b.pet_name = "Mittens"

        scheduler = Scheduler(tasks=[task_a, task_b])

        filtered = scheduler.schedule_day(
            self.now,
            pet_name="Mittens",
            sort_by="due",
        )
        self.assertEqual(filtered, [task_b])

        sorted_by_priority = scheduler.prioritize_tasks([task_a, task_b], sort_by="priority")
        self.assertEqual(sorted_by_priority[0], task_b)

    def test_owner_summary_includes_next_occurrence(self):
        owner = Owner(name="Jordan", email="jordan@example.com")
        pet = Pet(name="Mochi", species="cat", birthday=self.now)
        task = Task(
            id=str(uuid.uuid4()),
            name="Daily play",
            type="play",
            due_at=self.now,
            frequency=TaskFrequency.DAILY,
        )
        pet.add_task(task)
        owner.add_pet(pet)

        summary = owner.summary()
        self.assertIn("next:", summary)
        self.assertIn("daily", summary.lower())


if __name__ == "__main__":
    unittest.main()
