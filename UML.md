# PawPal+ UML Design

This document captures the high-level UML design for PawPal+, a smart pet care management system.

## Class Diagram (Mermaid)

```mermaid
classDiagram
    direction TB

    %% Core Entities
    class Owner {
        +str name
        +str email
        +List~Pet~ pets
        +add_pet(pet: Pet)
        +remove_pet(pet: Pet)
    }

    class Pet {
        +str name
        +str species
        +date birthday
        +List~Task~ tasks
        +get_age() int
        +is_senior() bool
        +add_task(task: Task)
        +remove_task(task_id: UUID)
    }

    class Task {
        +UUID id
        +str name
        +str type
        +TaskPriority priority
        +datetime due_at
        +timedelta duration
        +bool completed
        +datetime completed_at
        +str notes
        +mark_done()
        +reschedule(next_due: datetime)
        +is_overdue(now: datetime) bool
        +estimate_urgency(now: datetime) float
    }

    class Scheduler {
        +List~Task~ tasks
        +schedule_day(date: date) List~Task~
        +add_task(task: Task)
        +remove_task(task_id: UUID)
        +get_next_task(now: datetime) Task
        +prioritize_tasks(tasks: List~Task~, now: datetime) List~Task~
    }

    %% Enums / Types
    class TaskPriority {
        <<enumeration>>
        +LOW
        +MEDIUM
        +HIGH
        +CRITICAL
    }

    %% Relationships
    Owner "1" o-- "*" Pet : owns
    Pet "1" o-- "*" Task : manages
    Scheduler "1" o-- "*" Task : schedules
```

## Class Relationships (Mapping to Python)

- **Owner → Pet**: An `Owner` can own multiple `Pet` instances. Pets live under their owner and are managed through the `Owner` class.
- **Pet → Task**: Each `Pet` maintains a list of `Task` objects. Tasks represent daily routines (feeding, walks, medication, appointments).
- **Scheduler → Task**: The `Scheduler` consumes a list of `Task` objects (often gathered from one or more pets) and produces a prioritized schedule.

---

## Notes

- This simplified design uses only **4 core classes**: **Owner**, **Pet**, **Task**, and **Scheduler**.
- Tasks are represented with a **generic `type` field** (e.g., "feeding", "walk", "medication", "appointment") to keep the model small while still allowing diverse behaviors in the scheduler.
- The scheduler focuses on daily priorities and due-dates, making this architecture easy to exercise via a CLI demo script.
