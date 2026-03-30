from pawpal_system import DailyTask, Pet, TaskCategory


def test_mark_complete_changes_status():
    task = DailyTask(name="Morning walk", category=TaskCategory.WALK, duration=30, priority=3)
    assert not task.is_completed
    task.mark_complete()
    assert task.is_completed


def test_add_task_increases_pet_task_count():
    pet = Pet(name="Mochi", species="dog", breed="Shiba Inu", age=3)
    assert len(pet.get_tasks()) == 0
    pet.add_task(DailyTask(name="Feeding", category=TaskCategory.FEEDING, duration=10, priority=4))
    assert len(pet.get_tasks()) == 1
