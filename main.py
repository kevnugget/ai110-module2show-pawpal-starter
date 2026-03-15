"""PawPal+ CLI demo entry point.

This script creates a sample owner with two pets, adds a variety of tasks,
then prints today's schedule using the core scheduling engine.
"""

from datetime import datetime, timedelta
import uuid

from pawpal_system import Owner, Pet, Task, TaskPriority, Scheduler


def create_sample_data() -> Owner:
    owner = Owner(name="Jamie", email="jamie@example.com")

    # Pet 1: dog
    dog = Pet(name="Rex", species="dog", birthday=datetime(2020, 3, 17))
    dog.add_task(
        Task(
            id=str(uuid.uuid4()),
            name="Morning walk",
            type="walk",
            due_at=datetime.now().replace(hour=8, minute=0, second=0, microsecond=0),
            priority=TaskPriority.HIGH,
            notes="Try the new trail",
        )
    )
    dog.add_task(
        Task(
            id=str(uuid.uuid4()),
            name="Evening meal",
            type="feeding",
            due_at=datetime.now().replace(hour=18, minute=0, second=0, microsecond=0),
            priority=TaskPriority.MEDIUM,
            notes="Provide extra kibble for training",
        )
    )

    # Pet 2: cat
    cat = Pet(name="Mittens", species="cat", birthday=datetime(2018, 6, 1))
    cat.add_task(
        Task(
            id=str(uuid.uuid4()),
            name="Medication",
            type="medication",
            due_at=datetime.now().replace(hour=9, minute=30, second=0, microsecond=0),
            priority=TaskPriority.CRITICAL,
            notes="Administer vitamin drops",
        )
    )

    owner.add_pet(dog)
    owner.add_pet(cat)

    return owner


def print_todays_schedule(owner: Owner) -> None:
    now = datetime.now()
    all_tasks = []
    for pet in owner.pets:
        for task in pet.tasks:
            all_tasks.append((pet, task))

    scheduler = Scheduler(tasks=[task for pet, task in all_tasks])
    today_tasks = scheduler.schedule_day(now)

    print(f"Today's schedule for {owner.name} ({now.strftime('%Y-%m-%d')}):\n")
    for idx, task in enumerate(today_tasks, start=1):
        pet = next(p for p, t in all_tasks if t.id == task.id)
        status = "✅" if task.completed else "⏳"
        due_time = task.due_at.strftime("%H:%M")
        print(f"{idx}. [{pet.name}] {task.name} ({task.type}) @ {due_time} {status}")


if __name__ == "__main__":
    owner = create_sample_data()
    print_todays_schedule(owner)
