from storage import save_tasks

def update_task(tasks):

    # Pilih task berdasarkan nomor
    pilihan = int(input("Pilih nomor task: "))

    # Cek apakah pilihan valid
    if pilihan > 0 and pilihan <= len(tasks):

        # Tanya mau ubah status atau tidak
        ubah = input("Ingin mengganti status? (y/n): ")

        if ubah == "y":

            # Balik status
            if tasks[pilihan-1]["done"] == True:
                tasks[pilihan-1]["done"] = False

            else:
                tasks[pilihan-1]["done"] = True

            save_tasks(tasks)
            print("Status berhasil diubah!")

        else:
            print("Batal mengubah status")

    else:
        print("Nomor tidak valid.") 