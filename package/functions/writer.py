import datetime, os, csv

# Write the File
def writer(log_head, log_tail):
    """Writes log data to a CSV file.

    Creates a CSV file named with the current date and time, stores it in a folder
    structure under 'Data' directory, and writes log data with a header and rows.

    Args:
        log_head (list): The header row for the CSV file.
        log_tail (list of lists): The list of data rows to write into the CSV file.

    Returns:
        None
    """
    current_datetime = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"{current_datetime}.csv"

    date_folder = datetime.datetime.now().strftime("%d-%m-%Y")
    folder = os.path.join("Data", date_folder)
    if not os.path.exists(folder):
        os.makedirs(folder)

    # Define the full file path
    file_path = os.path.join(folder, filename)

    with open(file_path, "w", newline="\n") as f:
        write = csv.writer(f)
        write.writerow(log_head)
        write.writerows(log_tail)
