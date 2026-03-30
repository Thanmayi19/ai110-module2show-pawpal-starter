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
  My scheduler considers three constraints: the owner's total available time for the day, task priority, and excluded categories defined in the Constraint class.

- How did you decide which constraints mattered most?
  Available time came first because it's a hard limit the scheduler can't work around. Priority came second since missing a medication is more serious than skipping enrichment. Excluded categories were treated as least critical since skipping them doesn't break the schedule, just refines it.

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
  My conflict detection only flags tasks that share the exact same start time, not ones that overlap in duration. A 30-minute walk at 08:00 and a feeding at 08:20 wouldn't be flagged even though they overlap.

- Why is that tradeoff reasonable for this scenario?
  It's reasonable because the scheduler already packs tasks sequentially, so duration overlaps can't occur during normal plan generation. The simple check covers the common case, is easy to test, and can be upgraded to full interval detection later if manual task editing or earliest_start is added.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
  I used Claude Code throughout the entire project — from reviewing my UML before writing any code, to converting class stubs into working logic, to refactoring methods and wiring the backend to the Streamlit UI.

- What kinds of prompts or questions were most helpful?
  Specific prompts that referenced actual file names and method names worked best. Asking Claude to look at a specific method and suggest improvements got much better results than describing the problem in general terms.

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
  When Claude suggested replacing my conflict detection loop with a defaultdict version I didn't accept it immediately. I traced through a three-task scenario manually to check whether my original actually handled it correctly first.

- How did you evaluate or verify what the AI suggested?
  I ran both versions against the same input by hand. My original silently dropped the third task in a three-way conflict. I only accepted the suggestion after confirming it fixed a real bug, not just because it looked cleaner.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
  I tested three behaviors: tasks returning in chronological order after sorting, a daily task generating a new instance for the next day after being marked complete, and detect_conflicts() flagging two tasks at the same start time.

- Why were these tests important?
  They cover the three main features added in Phase 3. If any of them broke silently the scheduler would produce wrong output with no indication something was wrong.

**b. Confidence**

- How confident are you that your scheduler works correctly?
  Moderately confident. The happy paths all pass and the core scheduling logic works for normal inputs, but there are edge cases I haven't covered yet.

- What edge cases would you test next if you had more time?
  A pet with no tasks, two recurring tasks where only one completes on the same day, and a schedule where available time exactly equals total task duration with no buffer left over.

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?
  The Constraint class. Keeping scheduling rules separate from the Scheduler logic made it easy to add and test new constraints without touching the core planning code. It was the decision I was most unsure about during design but turned out to be the most useful in practice.

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?
  I'd fix preferred_times in Constraint. It's stored but never actually used during scheduling, which means the UML promises a feature the code doesn't deliver. I'd map time preferences to real hour windows and use them to set task start times instead of always defaulting to 08:00.

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
  Having a UML design before writing code gave me something concrete to evaluate Claude's suggestions against. The design didn't survive implementation perfectly, but having it meant every change was a deliberate decision rather than something that just crept in.
