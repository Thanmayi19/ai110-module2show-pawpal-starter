# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
  The design is organized around three concerns: data, rules, and output. User and Pet sit at the top as the data layer, a user owns pets, and each pet owns its tasks. The scheduling side is kept separate: Scheduler acts as a service that reads from the data layer, applies any active Constraint objects, and produces a Schedule as its output. I made Constraint its own class rather than hardcoding rules inside Scheduler so that new rules could be plugged in without changing the core logic. The Schedule then breaks down into individual ScheduledTask objects, each one linking a task to a specific time slot.

- What classes did you include, and what responsibilities did you assign to each?
  I included eight classes: User, Pet, DailyTask, TaskCategory, Scheduler, Schedule, ScheduledTask, and Constraint.
  1- User holds the owner's profile and available time for the day, and acts as the top-level entry point that owns one or more pets.
  2- Pet stores the animal's basic info and maintains its list of care tasks.
  3- DailyTask represents a single care item — its name, category, duration, priority, and whether it's been completed.
  4- TaskCategory is an enum that keeps category values consistent so loose strings don't cause bugs.
  5- Scheduler is the core logic class — it takes a user and a pet, applies constraints, and produces a schedule.
  6- Constraint holds individual scheduling rules like a time cap or excluded categories, separate from the scheduler itself so rules can be added or changed without touching the scheduling logic.
  7- Schedule is the output object — it holds the final list of scheduled tasks, total duration, and a reasoning string.
  8- ScheduledTask is a lightweight wrapper that pairs a DailyTask with a concrete start and end time.

**b. Design changes**

- Did your design change during implementation?
  Yes, my design changed during implementation in a few ways.

- If yes, describe at least one change and why you made it.
  The most notable one was adding input validation to DailyTask. In the UML, priority was just typed as int with no constraints, but during implementation it became clear that the entire scheduling order depends on sorting by that field so a value like -1 or 99 would silently corrupt the output without any indication something was wrong. I added a **post_init** validator to enforce that priority stays within the expected range, which wasn't something I thought about at the design stage.
  I also had to fix how generate_plan handled completed tasks. The UML included is_completed on DailyTask and it made sense conceptually, but I hadn't explicitly thought through whether generate_plan should filter those out. During implementation it was obvious it needed to, otherwise completing a task does nothing, since it just gets rescheduled the next time you generate a plan.
  The bigger lesson was that the UML captured the structure well but didn't force me to think through the runtime behavior carefully enough. Things like time arithmetic edge cases and how constraints interact with the scheduling loop only became apparent once I was actually writing the logic.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
