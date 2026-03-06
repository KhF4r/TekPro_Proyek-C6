def delete_task(tasks, index):
    if 0 < index <= len(tasks):
        tasks.pop(index-1)