from add_task import add_task
from delete_task import delete_task
from task_update import update_task
from show_tasks import show_tasks
from storage import load_tasks, save_tasks
from datetime import date

def main():
    tasks = load_tasks()

    while True:
        show_tasks(tasks)
        print("\n Daftar Menu")
        print("1. Tambah Tugas \n2. Update Status  \n3. Hapus Tugas  \n4. Keluar")
        choice = input("Pilih aksi: ")

        if choice == "1":
            title = input("Judul: ")
            deadline = input("Deadline : ")
            created_at = date.today().strftime("%d-%m-%Y")
            add_task(tasks, title, created_at, deadline)

        elif choice == "2":
            update_task(tasks)

        elif choice == "3":
            i = int(input("Nomor : "))
            delete_task(tasks, i)

        elif choice == "4":
            save_tasks(tasks)
            break

main()
