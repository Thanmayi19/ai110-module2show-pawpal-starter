from __future__ import annotations

import streamlit as st
from datetime import date

from pawpal_system import (
    DailyTask,
    Constraint,
    Pet,
    Schedule,
    Scheduler,
    TaskCategory,
    User,
)

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")
st.caption("A smart pet care scheduling assistant.")

# ---------------------------------------------------------------------------
# Session-state initialisation
# ---------------------------------------------------------------------------

if "tasks" not in st.session_state:
    st.session_state.tasks: list[DailyTask] = []

if "last_schedule" not in st.session_state:
    st.session_state.last_schedule: Schedule | None = None

# ---------------------------------------------------------------------------
# Section 1 – Owner info
# ---------------------------------------------------------------------------

st.header("1. Owner Information")

col_a, col_b, col_c = st.columns(3)
with col_a:
    owner_name = st.text_input("Full name", value="Jordan Smith", key="owner_name")
with col_b:
    owner_email = st.text_input("Email", value="jordan@example.com", key="owner_email")
with col_c:
    time_available = st.number_input(
        "Time available today (minutes)",
        min_value=10,
        max_value=480,
        value=120,
        step=10,
        key="time_available",
    )

# ---------------------------------------------------------------------------
# Section 2 – Pet info
# ---------------------------------------------------------------------------

st.header("2. Pet Information")

col_d, col_e, col_f = st.columns(3)
with col_d:
    pet_name = st.text_input("Pet name", value="Mochi", key="pet_name")
    species = st.selectbox("Species", ["dog", "cat", "rabbit", "bird", "other"], key="species")
with col_e:
    breed = st.text_input("Breed", value="Shiba Inu", key="breed")
    pet_age = st.number_input("Age (years)", min_value=0, max_value=30, value=3, key="pet_age")
with col_f:
    health_notes = st.text_area(
        "Health notes (optional)", value="", height=100, key="health_notes"
    )

# ---------------------------------------------------------------------------
# Section 3 – Task entry
# ---------------------------------------------------------------------------

st.header("3. Add Care Tasks")

col1, col2, col3 = st.columns(3)
with col1:
    task_name = st.text_input("Task name", value="Morning walk", key="task_name")
    task_category = st.selectbox(
        "Category",
        options=list(TaskCategory),
        format_func=lambda c: c.value,
        key="task_category",
    )
with col2:
    task_duration = st.number_input(
        "Duration (minutes)", min_value=1, max_value=240, value=20, key="task_duration"
    )
    task_priority = st.slider(
        "Priority (1 = low, 5 = high)", min_value=1, max_value=5, value=3, key="task_priority"
    )
with col3:
    task_notes = st.text_area("Notes (optional)", value="", height=100, key="task_notes")

col_add, col_clear = st.columns([1, 1])
with col_add:
    if st.button("Add task", use_container_width=True):
        new_task = DailyTask(
            name=task_name,
            category=task_category,
            duration=int(task_duration),
            priority=int(task_priority),
            notes=task_notes,
        )
        st.session_state.tasks.append(new_task)
        st.success(f"Added: {task_name}")

with col_clear:
    if st.button("Clear all tasks", use_container_width=True):
        st.session_state.tasks = []
        st.session_state.last_schedule = None
        st.info("All tasks cleared.")

# Display current task list
if st.session_state.tasks:
    st.subheader("Current task list")
    task_rows = [
        {
            "Name": t.name,
            "Category": t.category.value,
            "Duration (min)": t.duration,
            "Priority": t.priority,
            "Notes": t.notes or "—",
        }
        for t in st.session_state.tasks
    ]
    st.table(task_rows)
else:
    st.info("No tasks added yet. Use the form above to add care tasks.")

# ---------------------------------------------------------------------------
# Section 4 – Constraints
# ---------------------------------------------------------------------------

st.header("4. Scheduling Constraints")

col_x, col_y = st.columns(2)
with col_x:
    max_duration = st.number_input(
        "Max total task duration (minutes)",
        min_value=10,
        max_value=480,
        value=int(time_available),
        step=10,
        key="max_duration",
    )
    preferred_times = st.multiselect(
        "Preferred times of day",
        options=["morning", "afternoon", "evening"],
        default=["morning"],
        key="preferred_times",
    )
with col_y:
    excluded_categories = st.multiselect(
        "Exclude task categories",
        options=list(TaskCategory),
        format_func=lambda c: c.value,
        default=[],
        key="excluded_categories",
    )

# ---------------------------------------------------------------------------
# Section 5 – Generate schedule
# ---------------------------------------------------------------------------

st.header("5. Generate Schedule")

plan_date = st.date_input("Plan date", value=date.today(), key="plan_date")

if st.button("Generate Schedule", type="primary", use_container_width=True):
    if not owner_name.strip():
        st.error("Please enter the owner's name.")
    elif not owner_email.strip():
        st.error("Please enter the owner's email.")
    elif not pet_name.strip():
        st.error("Please enter a pet name.")
    elif not st.session_state.tasks:
        st.error("Please add at least one task before generating a schedule.")
    else:
        # Build the object graph
        user = User(
            name=owner_name.strip(),
            email=owner_email.strip(),
            time_available=int(time_available),
        )

        pet = Pet(
            name=pet_name.strip(),
            species=species,
            breed=breed.strip(),
            age=int(pet_age),
            health_notes=health_notes.strip(),
        )

        for task in st.session_state.tasks:
            pet.add_task(task)

        user.add_pet(pet)

        constraint = Constraint(
            max_duration=int(max_duration),
            preferred_times=list(preferred_times),
            excluded_categories=list(excluded_categories),
        )

        scheduler = user.create_scheduler(pet)
        scheduler.add_constraint(constraint)

        schedule = scheduler.generate_plan(plan_date=plan_date)
        st.session_state.last_schedule = schedule

# ---------------------------------------------------------------------------
# Section 6 – Display results
# ---------------------------------------------------------------------------

if st.session_state.last_schedule is not None:
    schedule: Schedule = st.session_state.last_schedule

    st.divider()
    st.header("📅 Today's Schedule")

    # Top-level metrics
    m1, m2, m3 = st.columns(3)
    m1.metric("Plan date", str(schedule.date))
    m2.metric("Tasks scheduled", len(schedule.scheduled_tasks))
    m3.metric("Total time (min)", schedule.total_duration)

    # Task cards
    if schedule.scheduled_tasks:
        st.subheader("Scheduled tasks")
        for st_task in schedule.scheduled_tasks:
            task = st_task.task
            with st.container(border=True):
                tc1, tc2, tc3 = st.columns([2, 1, 1])
                with tc1:
                    st.markdown(f"**{task.name}**  —  `{task.category.value}`")
                    if task.notes:
                        st.caption(task.notes)
                with tc2:
                    st.markdown(
                        f"🕐 {st_task.start_time.strftime('%H:%M')} – "
                        f"{st_task.end_time.strftime('%H:%M')}"
                    )
                with tc3:
                    st.markdown(f"⏱ {task.duration} min  |  Priority **{task.priority}/5**")
    else:
        st.warning("No tasks could be scheduled within the given constraints.")

    # Reasoning / explanation
    with st.expander("Scheduling reasoning", expanded=True):
        st.info(schedule.reasoning)

    # Constraint validation
    if "last_schedule" in st.session_state and st.session_state.last_schedule is not None:
        # Rebuild a lightweight scheduler just for validation display
        _user_v = User(
            name=owner_name.strip() or "Owner",
            email=owner_email.strip() or "owner@example.com",
            time_available=int(time_available),
        )
        _pet_v = Pet(
            name=pet_name.strip() or "Pet",
            species=species,
            breed=breed.strip() or "",
            age=int(pet_age),
        )
        _scheduler_v = Scheduler(user=_user_v, pet=_pet_v)
        _constraint_v = Constraint(
            max_duration=int(max_duration),
            preferred_times=list(preferred_times),
            excluded_categories=list(excluded_categories),
        )
        _scheduler_v.add_constraint(_constraint_v)
        violations = _scheduler_v.validate_schedule(schedule)

        with st.expander("Constraint validation", expanded=False):
            if violations:
                for v in violations:
                    st.error(v)
            else:
                st.success("All constraints satisfied.")

    # Raw serialised view
    with st.expander("Raw schedule data (JSON)", expanded=False):
        st.json(schedule.to_dict())
