import streamlit as st
from datetime import datetime, date, timedelta
import uuid

from pawpal_system import Owner, Pet, Task, TaskPriority, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to the PawPal+ starter app.

This file is intentionally thin. It gives you a working Streamlit app so you can start quickly,
but **it does not implement the project logic**. Your job is to design the system and build it.

Use this app as your interactive demo once your backend classes/functions exist.
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

You will design and implement the scheduling logic and connect it to this Streamlit UI.
"""
    )

with st.expander("What you need to build", expanded=True):
    st.markdown(
        """
At minimum, your system should:
- Represent pet care tasks (what needs to happen, how long it takes, priority)
- Represent the pet and the owner (basic info and preferences)
- Build a plan/schedule for a day that chooses and orders tasks based on constraints
- Explain the plan (why each task was chosen and when it happens)
"""
    )

st.divider()

st.subheader("Quick Demo Inputs (UI only)")
owner_name = st.text_input("Owner name", value="Jordan")

st.markdown("### Pets")
st.caption("Add one or more pets that belong to the owner.")

if "pets" not in st.session_state:
    st.session_state.pets = []

pet_col1, pet_col2, pet_col3 = st.columns(3)
with pet_col1:
    new_pet_name = st.text_input("Pet name", value="Mochi")
with pet_col2:
    new_species = st.selectbox("Species", ["dog", "cat", "other"])
with pet_col3:
    add_pet = st.button("Add pet")

if add_pet and new_pet_name:
    st.session_state.pets.append({"name": new_pet_name, "species": new_species})

if st.session_state.pets:
    st.write("Current pets:")
    st.table(st.session_state.pets)
else:
    st.info("No pets yet. Add at least one pet.")

st.markdown("### Tasks")
st.caption("Add a few tasks and assign them to a pet.")

if "tasks" not in st.session_state:
    st.session_state.tasks = []

if st.session_state.pets:
    pet_names = [p["name"] for p in st.session_state.pets]
    selected_pet = st.selectbox("Pet", pet_names)
else:
    selected_pet = None

col1, col2, col3, col4 = st.columns(4)
with col1:
    task_title = st.text_input("Task title", value="Morning walk")
with col2:
    duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
with col3:
    priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
with col4:
    due_time = st.time_input("Due time", value=datetime.now().time().replace(second=0, microsecond=0))

if st.button("Add task"):
    if not selected_pet:
        st.warning("Add a pet first before adding tasks.")
    else:
        st.session_state.tasks.append(
            {
                "pet": selected_pet,
                "title": task_title,
                "duration_minutes": int(duration),
                "priority": priority,
                "due_time": due_time.strftime("%H:%M"),
            }
        )

if st.session_state.tasks:
    st.write("Current tasks:")
    st.table(st.session_state.tasks)
else:
    st.info("No tasks yet. Add one above.")

st.divider()

st.subheader("Build Schedule")
st.caption("This button should call your scheduling logic once you implement it.")

def _priority_from_ui(value: str) -> TaskPriority:
    mapping = {"low": TaskPriority.LOW, "medium": TaskPriority.MEDIUM, "high": TaskPriority.HIGH}
    return mapping.get(value.lower(), TaskPriority.MEDIUM)


def _parse_time(today: date, time_str: str) -> datetime:
    hour, minute = map(int, time_str.split(":"))
    return datetime.combine(today, datetime.min.time()).replace(hour=hour, minute=minute)


def _render_owner_summary(owner: Owner) -> None:
    st.markdown("### Owner & Pets")
    st.code(owner.summary(), language="text")


if st.button("Generate schedule"):
    if not st.session_state.tasks:
        st.warning("Add at least one task before generating a schedule.")
    else:
        owner = Owner(name=owner_name, email=f"{owner_name.lower()}@example.com")
        today = datetime.now().date()

        # Build pets and assign tasks to them
        pet_map = {}
        for p in st.session_state.pets:
            pet = Pet(name=p["name"], species=p["species"], birthday=datetime.now())
            owner.add_pet(pet)
            pet_map[p["name"]] = pet

        for task_data in st.session_state.tasks:
            due_at = _parse_time(today, task_data["due_time"])
            task = Task(
                id=str(uuid.uuid4()),
                name=task_data["title"],
                type="generic",
                due_at=due_at,
                duration=timedelta(minutes=task_data["duration_minutes"]),
                priority=_priority_from_ui(task_data["priority"]),
            )
            pet_map[task_data["pet"]].add_task(task)

        # Schedule across all pets
        all_tasks = []
        for pet in owner.pets:
            all_tasks.extend(pet.tasks)

        scheduler = Scheduler(tasks=all_tasks)
        today_schedule = scheduler.schedule_day(datetime.now())

        st.success("Schedule generated!")
        _render_owner_summary(owner)

        st.markdown("### Today's schedule")
        for idx, task in enumerate(today_schedule, start=1):
            # find which pet owns this task
            owner_pet = next((p for p in owner.pets if task in p.tasks), None)
            pet_label = owner_pet.name if owner_pet else "(unknown)"
            st.markdown(
                f"**{idx}. [{pet_label}] {task.name}** ({task.type}) — due {task.due_at.strftime('%H:%M')} — priority {task.priority.name.title()}"
            )
