import json
import asyncio
import time
from app.worker.resume_worker import process_resume

# In-memory queue for tasks
in_memory_queue = []

QUEUE_NAME = "resume_parsing_queue"


async def enqueue_resume_task(candidate_uid: str, resume_link: str):
    """
    Enqueue a resume parsing task to the in-memory queue.
    """
    task = {
        "candidate_uid": candidate_uid,
        "resume_link": resume_link
    }

    in_memory_queue.append(task)
    print(f"Enqueued task for candidate {candidate_uid} in memory queue")


async def process_queue():
    """
    Process tasks from the in-memory queue.
    This should be run in a separate process or thread.
    """
    print(f"Starting in-memory queue processor for {QUEUE_NAME}")

    while True:
        try:
            # Check if there are any tasks in the queue
            if in_memory_queue:
                task = in_memory_queue.pop(0)
                print(f"Processing task from in-memory queue: {task}")

                try:
                    candidate_uid = task.get("candidate_uid")
                    resume_link = task.get("resume_link")

                    if candidate_uid and resume_link:
                        # Create a new task for processing to isolate it from the main worker loop
                        await process_resume(candidate_uid, resume_link)
                        print(
                            f"Successfully processed task for candidate {candidate_uid}")
                    else:
                        print(f"Invalid task format: {task}")
                except Exception as e:
                    print(f"Error processing task: {e}")
                    # Re-queue the task if processing failed
                    in_memory_queue.append(task)
                    print("Task re-queued due to processing error")

            # Small delay to prevent CPU spinning
            await asyncio.sleep(0.1)

        except Exception as e:
            print(f"Error in queue processing loop: {e}")
            await asyncio.sleep(1)  # Longer delay on unexpected errors


def start_worker():
    """
    Start the worker in a separate process.
    Call this when your application starts.
    """
    print("Starting in-memory worker process...")
    # Create and set new event loop for the worker process
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        loop.run_until_complete(process_queue())
    except KeyboardInterrupt:
        print("Worker process stopped by user")
    except Exception as e:
        print(f"Error in worker process: {e}")
    finally:
        loop.close()
