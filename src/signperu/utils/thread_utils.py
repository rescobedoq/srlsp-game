#src/signperu/utils/thread_utils.py
import queue

def make_event_queue(maxsize=0):
    return queue.Queue(maxsize=maxsize)
