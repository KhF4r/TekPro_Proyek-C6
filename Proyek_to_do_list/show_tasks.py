def show_tasks(tasks):
    if not tasks:
        print("Belum ada tugas yang ditambahkan.")
    for i, task in enumerate(tasks):

        print(f"Tugas {i+1} ")
        print(f"Judul Tugas : {task['title']}")
        print(f"Status Tugas : {task['done']}")
        print(f"Tanggal ditambahkan : {task['created_at']}")
        print(f"Deadline : {task['deadline']}\n")
        