import unittest
from datetime import datetime, timedelta
import uuid

from pawpal_system import Task, TaskPriority, Scheduler


class TestPawPalSystem(unittest.TestCase):
    def test_task_urgency_reflects_overdue_and_priority(self):
        now = datetime.now()
        overdue_task = Task(
            id=str(uuid.uuid4()),
            name="Overdue med",
            type="medication",
            due_at=now - timedelta(hours=2),
            priority=TaskPriority.MEDIUM,
        )
        soon_task = Task(
            id=str(uuid.uuid4()),
            name="Soon walk",
            type="walk",
            due_at=now + timedelta(minutes=30),
            priority=TaskPriority.HIGH,
        )

        self.assertGreater(overdue_task.estimate_urgency(now), soon_task.estimate_urgency(now))

    def test_scheduler_schedule_day_includes_only_today_tasks(self):
        now = datetime.now()
        today_task = Task(
            id=str(uuid.uuid4()),
            name="Today feeding",
            type="feeding",
            due_at=now.replace(hour=12, minute=0, second=0, microsecond=0),
            priority=TaskPriority.LOW,
        )
        tomorrow_task = Task(
            id=str(uuid.uuid4()),
            name="Tomorrow checkup",
            type="appointment",
            due_at=(now + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0),
            priority=TaskPriority.HIGH,
        )

        scheduler = Scheduler(tasks=[today_task, tomorrow_task])
        scheduled = scheduler.schedule_day(now)

        self.assertIn(today_task, scheduled)
        self.assertNotIn(tomorrow_task, scheduled)


if __name__ == "__main__":
    unittest.main()
