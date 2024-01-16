import os
import sys
import boto3
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog

# Get the directory of the Python script
script_dir = os.path.dirname(os.path.abspath(__file__))


def browse_files():
    root = tk.Tk()
    root.withdraw()
    file_paths = filedialog.askopenfilenames()
    root.destroy()
    if not file_paths:
        if upload_count == 0:
            messagebox.showinfo("Information", "File selection canceled. Script terminated.")
            sys.exit()
        else:
            summary_message = f"{upload_count} item(s) successfully uploaded!"
            messagebox.showinfo("Summary", summary_message)
            root.destroy()
            sys.exit()

    return file_paths


def check_aws_credentials(access_key, secret_key):
    try:
        session = boto3.Session(
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key
        )
        s3 = session.resource(
            's3',
            endpoint_url='https://s3.US-central-1.wasabisys.com'
        )
        s3.meta.client.list_buckets()  # Verify credentials by listing buckets
        return True
    except Exception:
        return False


def prompt_aws_credentials():
    root = tk.Tk()
    root.withdraw()
    access_key = simpledialog.askstring("Wasabi Credentials", "Enter your Wasabi access key:")
    if access_key is None:
        messagebox.showinfo("Information", "Wasabi credentials required. Script terminated.")
        sys.exit()
    secret_key = simpledialog.askstring("Wasabi Credentials", "Enter your Wasabi secret key:")
    if secret_key is None:
        messagebox.showinfo("Information", "Wasabi credentials required. Script terminated.")
        sys.exit()
    return access_key, secret_key


def create_aws_credentials_file(access_key, secret_key):
    aws_credentials_path = os.path.expanduser("~/.aws/credentials")
    os.makedirs(os.path.dirname(aws_credentials_path), exist_ok=True)
    with open(aws_credentials_path, "w") as f:
        f.write("[default]\n")
        f.write(f"aws_access_key_id = {access_key}\n")
        f.write(f"aws_secret_access_key = {secret_key}\n")


def read_aws_credentials_file():
    aws_credentials_path = os.path.expanduser("~/.aws/credentials")
    if not os.path.exists(aws_credentials_path):
        return None, None

    with open(aws_credentials_path, "r") as f:
        lines = f.readlines()

    access_key = None
    secret_key = None
    for line in lines:
        if line.strip().startswith("aws_access_key_id"):
            access_key = line.strip().split("=")[1].strip()
        elif line.strip().startswith("aws_secret_access_key"):
            secret_key = line.strip().split("=")[1].strip()

    return access_key, secret_key


PICTURE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif']

def is_picture_file(file_path):
    _, file_extension = os.path.splitext(file_path)
    return file_extension.lower() in PICTURE_EXTENSIONS


# BEGIN SCRIPTING
root = tk.Tk()
root.withdraw()

access_key, secret_key = read_aws_credentials_file()

if access_key and secret_key:
    if not check_aws_credentials(access_key, secret_key):
        access_key = None
        secret_key = None

if not access_key or not secret_key:
    access_key, secret_key = prompt_aws_credentials()

    while not check_aws_credentials(access_key, secret_key):
        messagebox.showerror("Error", "Invalid credentials. Please try again.")
        access_key, secret_key = prompt_aws_credentials()

    create_aws_credentials_file(access_key, secret_key)

upload_count = 0

messagebox.showinfo("Information", "Please select the photos to upload. Make sure the file name is only the item's "
                                   "part number plus file extension (ie: '008FP-BK.jpg')")
while True:
    file_paths = browse_files()
    invalid_files = []
    for file_path in file_paths:
        if not is_picture_file(file_path):
            invalid_files.append(file_path)
    if invalid_files:
        invalid_file_list = "\n".join(invalid_files)
        error_message = f"The following files are not valid picture files:\n{invalid_file_list}"
        messagebox.showerror("Error", error_message)
        continue

    for file_path in file_paths:
        wasabiFileLocation = os.path.basename(file_path)

        try:
            bucket_name = 'mpdb'
            s3 = boto3.resource(
                's3',
                endpoint_url='https://s3.US-central-1.wasabisys.com',
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key
            )
            s3.meta.client.upload_file(file_path, bucket_name, f"productimages/{wasabiFileLocation}")
            upload_count += 1
        except Exception as e:
            error_message = f"Error uploading file '{wasabiFileLocation}':\n{str(e)}"
            messagebox.showerror("Error", error_message)

    choice = messagebox.askyesno("Confirmation", "Do you want to upload more files?")

    if not choice:
        break

summary_message = f"{upload_count} item(s) successfully uploaded!"
messagebox.showinfo("Summary", summary_message)

root.destroy()
sys.exit()
