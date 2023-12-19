import os
import sys
import zipfile
import tarfile
import fnmatch
import concurrent.futures


def find_string_in_text(text, search_string):
    return search_string.lower() in text.lower()


def find_string_in_file(file_path, search_string):
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
            for line in file:
                if find_string_in_text(line, search_string):
                    return True
    except Exception as e:
        #print(f"Error reading file {file_path}: {e}")
        pass
    return False


def find_string_in_archive(archive_path, search_string):
    try:
        if zipfile.is_zipfile(archive_path):
            with zipfile.ZipFile(archive_path, 'r') as zip:
                for zip_info in zip.infolist():
                    if not zip_info.is_dir():
                        with zip.open(zip_info) as file:
                            for line in file:
                                if find_string_in_text(line.decode('utf-8', errors='ignore'), search_string):
                                    return True

        elif tarfile.is_tarfile(archive_path):
            with tarfile.open(archive_path, 'r:*') as tar:
                for member in tar.getmembers():
                    if member.isfile():
                        file = tar.extractfile(member)
                        if file:
                            for line in file:
                                if find_string_in_text(line.decode('utf-8', errors='ignore'), search_string):
                                    return True

    except Exception as e:
        #print(f"Error reading archive {archive_path}: {e}")
        pass
    return False


def search_in_user_folder(search_string):
    home_dir = os.path.expanduser('~')
    found_files = []
    search_tasks = []

    file_counter = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        # search in home directory
        for root, dirs, files in os.walk(home_dir):
            for file in files:
                file_counter += 1
                if file_counter % 10000 == 0:
                    print(f"Processed {file_counter} files...")
                file_path = os.path.join(root, file)
                try:
                    file_size = os.path.getsize(file_path)
                    if file_size < 500 * 1024 * 1024:  # less than 500 MB for regular files
                        task = executor.submit(find_string_in_file, file_path, search_string)
                        search_tasks.append(task)
                    elif file_size < 100 * 1024 * 1024 and (file_path.lower().endswith('.zip') \
                            or file_path.lower().endswith('.tar') or file_path.lower().endswith('.gz') \
                            or file_path.lower().endswith('.tar.gz')): 
                        task = executor.submit(find_string_in_archive, file_path, search_string)
                        search_tasks.append(task)

                except OSError as e:
                    #print(f"Error accessing file {file_path}: {e}")
                    continue

        for future in concurrent.futures.as_completed(search_tasks):
            file_path, found = future.result()
            if found:
                found_files.append(file_path)

    return found_files


if __name__ == "__main__":
    search_string = sys.argv[1]
    files_with_string = search_in_user_folder(search_string)
    print(f"Files containing `{search_string}`:")
    for file in files_with_string:
        print(file)
