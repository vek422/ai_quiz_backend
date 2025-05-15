from langgraph.types import interrupt
from app.langgraph.models import UserState


def level1_evaluation(user_state: UserState) -> UserState:
    user_answers = interrupt("Please submit your answers for Level 1 MCQs.")

    level1_progress = user_state.progress.get(1)
    if not level1_progress:
        raise ValueError("Level 1 progress not found.")

    correct_count = 0
    total_questions = len(level1_progress.questions)

    for q in level1_progress.questions:
        # Assuming first option is correct (you can change logic)
        correct_answer = q.options[0]
        user_answer = user_answers.get(q.id)
        if user_answer == correct_answer:
            correct_count += 1

    score = (correct_count / total_questions) * 100

    # Update the user state
    level1_progress.answers = user_answers
    level1_progress.score = score
    level1_progress.completed = True
    user_state.progress[1] = level1_progress

    return user_state
