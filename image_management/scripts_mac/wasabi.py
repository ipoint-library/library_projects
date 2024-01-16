from PIL import Image, ImageFilter
import os
import sys
import boto3
import pytesseract
import shutil
import csv
from botocore.exceptions import ClientError
from datetime import datetime, timedelta
from progress import Progress
import getpass
timestamp = datetime.now().strftime("%m%d%y%H%M%S")



class Wasabi:
    def __init__(self):
        try:
            session = boto3.Session(profile_name="default")
            credentials = session.get_credentials()
            self.aws_access_key_id = credentials.access_key
            self.aws_secret_access_key = credentials.secret_key

            s3 = boto3.resource('s3',
                                endpoint_url='https://s3.US-central-1.wasabisys.com',
                                aws_access_key_id=self.aws_access_key_id,
                                aws_secret_access_key=self.aws_secret_access_key
                                )
            self.bucket = s3.Bucket("mpdb")
            self.check_aws_credentials()
        except:
            self.prompt_aws_credentials(None, None)

    def prompt_aws_credentials(self, access_key, secret_key):
        access_key = access_key
        secret_key = secret_key
        while not access_key:
            access_key = input("Enter your Wasabi access key:")
            if not access_key:
                print("Wasabi Access Key required.")
        while not secret_key:
            secret_key = getpass.getpass("Enter your Wasabi secret key:")
            if not secret_key:
                print("Wasabi Secret Key required.")

        self.aws_access_key_id = access_key
        self.aws_secret_access_key = secret_key
        self.create_aws_credentials_file(access_key, secret_key)
        self.check_aws_credentials()

    def create_aws_credentials_file(self, access_key, secret_key):
        aws_credentials_path = os.path.expanduser("~/.aws/credentials")
        os.makedirs(os.path.dirname(aws_credentials_path), exist_ok=True)
        with open(aws_credentials_path, "w") as f:
            f.write("[default]\n")
            f.write(f"aws_access_key_id = {access_key}\n")
            f.write(f"aws_secret_access_key = {secret_key}\n")

    def check_aws_credentials(self):
        try:
            session = boto3.Session(profile_name="default")
            credentials = session.get_credentials()
            self.aws_access_key_id = credentials.access_key
            self.aws_secret_access_key = credentials.secret_key

            s3 = boto3.resource('s3',
                                endpoint_url='https://s3.US-central-1.wasabisys.com',
                                aws_access_key_id=self.aws_access_key_id,
                                aws_secret_access_key=self.aws_secret_access_key
                                )
            self.bucket = s3.Bucket("mpdb")
            temp = s3.meta.client.list_buckets()
        except:
            os.remove(os.path.expanduser("~/.aws/credentials"))
            print("Invalid Credentials. Please try again.")
            self.prompt_aws_credentials(None, None)

    def resize_images_in_directory(self, input_directory, output_directory, max_size):
        """
        Resizes all images in a given directory to a maximum size.

        Args:
            input_directory (str): The directory containing the images you wish to resize.
            output_directory (str): The directory in which you wish to place the resized photos.
            max_size (int): The number in pixels you wish to have as the maximum photo size.
                            Used for both width and height.
        """
        # Create the output directory if it doesn't exist
        os.makedirs(output_directory, exist_ok=True)

        # Get a list of all files in the input directory
        file_list = os.listdir(input_directory)

        # Loop through each file in the input directory
        Count = 0
        for file_name in file_list:
            Count += 1
            # Construct the full path of the input and output files
            input_path = os.path.join(input_directory, file_name)
            output_path = os.path.join(output_directory, file_name)

            # Check if the file is an image
            if is_image_file(input_path):
                try:
                    # Resize the image and save it to the output directory
                    resize_image(input_path, output_path, max_size)
                    if Count % 1000 == 0:
                        itemPath = input_path.split(".")[0]
                        itemName = itemPath.split("/")[-1]
                        print(f"{itemName} resized: Record {Count}")
                except Exception as e:
                    print(f"Error resizing file: {file_name} - {str(e)}")

    def is_image_file(self, file_path):
        """
        Checks if a file has a supported image extension.

        Args:
            file_path (str): The path to the file.

        Returns:
            bool: True if the file has a supported image extension, False otherwise.
        """
        # Check if the file has a supported image extension
        supported_extensions = ['.jpg', '.jpeg', '.png', '.gif']
        _, file_extension = os.path.splitext(file_path)
        return file_extension.lower() in supported_extensions

    def resize_images(self, directory, max_size):
        """
        Resizes an image to fit within a maximum size while preserving its aspect ratio.

        Args:
            directory (str): Path to the input image files.
            max_size (int): The maximum size (in pixels) for both width and height.
        """
        for obj in os.listdir(directory):
            if self.is_image_file(obj):
                print(f"Resizing {obj}")
                try:
                    # Open the image file
                    image = Image.open(os.path.join(directory, obj).replace("/", "\\"))

                    # Convert the image to RGB mode if it is in RGBA mode
                    if image.mode == 'RGBA':
                        image = image.convert('RGB')

                    # Calculate the aspect ratio
                    width, height = image.size
                    aspect_ratio = width / height

                    # Determine the new dimensions
                    if width > height:
                        new_width = max_size
                        new_height = int(max_size / aspect_ratio)
                    else:
                        new_width = int(max_size * aspect_ratio)
                        new_height = max_size

                    # Resize the image
                    resized_image = image.resize((new_width, new_height), Image.LANCZOS)
                    if obj[-3:] == "jpg" or obj[-3] == "jpeg":
                        # Save the resized image as JPEG
                        resized_image.save(os.path.join(directory, obj), 'JPEG')
                    else:
                        resized_image.save(os.path.join(directory, obj), 'PNG')
                except:
                    pass

    def count_uploads(self, bucket):
        """
        Counts the number of files present inside the given Wasabi bucket.

        Args:
            bucket (str): The name of the Wasabi bucket.

        Requires accurate Wasabi credentials in '/.aws/credentials' inside the root directory.
        """

        counting_bucket = self.s3.Bucket(bucket)
        count = 0
        progress = "Counting."
        print(progress)
        for _ in counting_bucket.objects.all():
            count += 1
            if count % 10000 == 0:
                progress+="."
                print(progress)
        print(f"{count} objects found in the {counting_bucket.name} bucket")

    def delete_object_from_bucket(file_name, bucket="mpdb", folder=""):
        """
        Deletes a given file from the Wasabi bucket.

        Args:
            file_name (str): The name of the file (including extension) you wish to delete.
            bucket (str, optional): The name of the Wasabi bucket where the file is located. Defaults to 'mpdb'.
            folder (str, optional): The name of the folder (if present) where the desired file is located.
                                   Defaults to an empty string.

        Requires accurate Wasabi credentials in '/.aws/credentials' inside the root directory.
        """
        delete_session = boto3.Session(profile_name="default")
        delete_credentials = delete_session.get_credentials()
        delete_aws_access_key_id = delete_credentials.access_key
        delete_aws_secret_access_key = delete_credentials.secret_key

        delete_s3 = boto3.resource('s3',
                                   endpoint_url='https://s3.US-central-1.wasabisys.com',
                                   aws_access_key_id=delete_aws_access_key_id,
                                   aws_secret_access_key=delete_aws_secret_access_key
                                   )

        try:
            delete_s3.Object(bucket, folder + "/" + file_name).delete()
            print(f"{file_name} deleted from {bucket}/{folder}")
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchKey':
                print(f"Error: {file_name} not found in {bucket}/{folder}")
            else:
                print(f"Error deleting {file_name} from {bucket}/{folder}: {error_code}")

    def count_items_in_part_list(self):
        """
        Counts the number of items inside the part number upload log created by the Image Uploader.

        Assumes the log file is located at '/Users/evanmeeks/Documents/Wasabi_UploadedPNS.txt'.
        """
        with open('/Users/evanmeeks/Documents/Wasabi_UploadedPNS.txt', 'r') as f:
            x = len(f.readlines())
        f.close()
        print(f"{x} items in the part number log")

    def count_files_in_directory(self, directory):
        """
        Counts the number of files in a given directory.

        Args:
            directory (str): The directory path to count files in.
        """
        count = 0

        # Loop through each file in the directory
        for _, _, files in os.walk(directory):
            count += len(files)

        print(f'{count} files found in the directory')

    def rename_files_in_directory(self, directory):
        """
        Renames all files in a given directory by extracting the last part of the filename.

        Args:
            directory (str): The directory path containing files to be renamed.
        """
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)

            if os.path.isfile(file_path):
                new_name = filename.split()[-1]
                new_path = os.path.join(directory, new_name)
                os.rename(file_path, new_path)
                print(f"File renamed: {filename} -> {new_name}")

    def check_images_for_text(self, input_directory, output_directory):
        """
        Moves images with text content from an input directory to an output directory for review.

        Args:
            input_directory (str): The directory containing the images to check for text.
            output_directory (str): The directory to move images with text content for review.
        """
        # Create the output directory if it doesn't exist
        os.makedirs(output_directory, exist_ok=True)

        # Get a list of all files in the input directory
        file_list = os.listdir(input_directory)

        # Iterate over the files in the input directory
        for file_name in file_list:
            # Construct the full path of the input file
            input_path = os.path.join(input_directory, file_name)

            # Check if the file is an image
            if is_image_file(input_path):
                # Perform OCR on the image
                text = perform_ocr(input_path)

                # If text is found, move the file to the output directory for review
                if text:
                    output_path = os.path.join(output_directory, file_name)
                    shutil.move(input_path, output_path)
                    print(f"File moved for review: {file_name}")

    def perform_ocr(self, image_path):
        """
        Performs OCR on an image to extract text content.

        Args:
            image_path (str): The path to the image file.

        Returns:
            str: Extracted text content from the image.
        """
        # Configure the OCR engine with additional options
        custom_config = r'--oem 3 --psm 6'  # Example: Use LSTM OCR engine and assume a single uniform block of text

        # Use pytesseract to perform OCR on the image with the custom configuration
        text = pytesseract.image_to_string(image_path, config=custom_config)
        return text.strip()

    def check_file_exists(self, file_key):
        """
        Checks if a file with the given key exists in the chosen bucket.

        Args:
            file_key (str): The key of the file in the chosen bucket.

        Returns:
            bool: True if the file exists, False otherwise.
        """

        return any(obj.key == file_key for obj in bucket.objects.all())

    def list_items_in_bucket(self, bucket):
        """
        Lists all items (objects) in a Wasabi bucket.

        Args:
            bucket (str): The name of the Wasabi bucket.

        Requires accurate Wasabi credentials in '/.aws/credentials' inside the root directory.

        Returns:
            list: A list of object keys in the specified bucket.
        """
        list_session = boto3.Session(profile_name="default")
        list_credentials = list_session.get_credentials()
        list_aws_access_key_id = list_credentials.access_key
        list_aws_secret_access_key = list_credentials.secret_key

        list_s3 = boto3.resource('s3',
                                 endpoint_url='https://s3.US-central-1.wasabisys.com',
                                 aws_access_key_id=list_aws_access_key_id,
                                 aws_secret_access_key=list_aws_secret_access_key
                                 )

        list_bucket = list_s3.Bucket(bucket)
        print("Creating list of PNs inside the MPDB Bucket")
        object_keys = []
        counter = 0
        for obj in list_bucket.objects.all():
            object_keys.append(obj.key)
            counter +=1
            if counter % 20000 == 0:
                self.progress_instance.update()
        print("List created")
        return object_keys

    def delete_all_items_in_bucket(self, bucket):
        """
        Deletes all items (objects) in a Wasabi bucket.

        Args:
            bucket (str): The name of the Wasabi bucket.

        Requires accurate Wasabi credentials in '/.aws/credentials' inside the root directory.
        """

        for obj in self.s3.bucket_to_delete.objects.all():
            obj.delete()

        print(f'All items in the {bucket} bucket have been deleted.')

    def save_parts_list(self, directory, skip_file_creation=False):
        """Creates a CSV file of all PNs in the MPDB bucket and saves it to the specified directory

        Args:
            string directory required to determine where the file is saved to.
            (optional) BOOL skip_file_creation to forgo the CSV and only return the array.

        Returns:
            Array of [Part Number, PN with Extension, URL]

        """
        photoNames = self.list_items_in_bucket("mpdb")
        partNumbersExt = []
        print("Splitting PN from filepath name")
        for i in photoNames:
            partNumbersExt.append(i.split("/")[1])

        partNumbers = [i.split(".")[0] for i in partNumbersExt]
        urls = []
        print("Creating list of URLS based off of PNs")
        for i in partNumbersExt:
            urls.append(f"https://s3.us-central-1.wasabisys.com/mpdb/productimages/{i}")
        combined = [[x, y, z] for x, y, z in zip(partNumbers, partNumbersExt, urls)]

        if not skip_file_creation:
            print("Writing to file")
            desktop_path = os.path.expanduser(f"{directory}WasabiUploads-{timestamp}.csv")
            with open(desktop_path, mode="w", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(["Part Number", "PN with Extension", "URL"])

                for row in combined:
                    writer.writerow(row)
            print("File created.")
        print("Completed. Returning array")
        return combined

    def file_older_than(self, file_path, max_time):
        """
        Check if the file's creation time is greater than a specified maximum time.

        Args:
            file_path (str): The path to the file.
            max_time (int): The maximum age of the file in minutes for the comparison.

        Returns:
            bool: True if the file's creation time is greater than the specified maximum time, False otherwise.
        """
        creation_timestamp = os.path.getctime(file_path)
        creation_date = datetime.fromtimestamp(creation_timestamp)
        time_difference = datetime.now() - creation_date
        return time_difference.total_seconds() > (max_time * 60)

        ############################### Wasabi Uploader Function(s)#########################

    def upload(self, directory, max_file_age=60):
        """
        Uploads files from the specified directory to Wasabi storage, avoiding duplicates,
            system files and the 'Wasabi_UploadedPNs.txt' file.

        Parameters:
        - directory (str): The local folder path containing files to be uploaded.
        - max_file_age (int): The maximum age (in minutes) that the Wasabi_UploadedPNS.txt
            file may be before creating a new one. Defaults to 60 minutes
        Returns:
            None
        """

        if len(os.listdir(directory)) == 0 or \
                len(os.listdir(directory)) > 0 \
                and os.listdir(directory)[0] == "Wasabi_UploadedPNS.txt":
            print(f"No files to upload. Please check the directory and try again.\nDirectory:{directory}")
            return

        UploadedPNsFileLocation = "/".join(
            directory.split("/"))  # Creating a variable to store the PN list based off directory chosen

        existing_pns = f'{UploadedPNsFileLocation}/Wasabi_UploadedPNS.txt'

        if not os.path.isfile(existing_pns) or self.file_older_than(existing_pns, max_file_age):
            # Creating a list of existing PNs in Wasabi to compare against before uploading new
            print("Creating list of existing uploads in bucket.")
            with open(f'{UploadedPNsFileLocation}/Wasabi_UploadedPNS.txt', 'a+', encoding='utf-8') as f:
                existing_contents = f.read()

                for obj in self.bucket.objects.all():
                    item = obj.key.split("/", 1)[1]
                    if item not in existing_contents:
                        f.write(f"{item}\n")
            f.close()

            print("Wasabi Data processed, PN file created.")
        else:
            print(f"Existing Wasabi PN list utilized (created in the last {max_file_age} minutes)")
        # Opening the file created in the last step, verifying files in the directory to be uploaded are files, and uploading
        # them if they don't already exist in Wasabi.
        recordNumber = 0
        recordsAdded = 0

        for filename in os.listdir(directory):

            recordNumber += 1
            if filename.startswith("."):
                continue

            with open(f'{UploadedPNsFileLocation}/Wasabi_UploadedPNS.txt', 'a+', encoding="utf-8") as f:
                existing_contents = f.read()
                file = os.path.join(directory, filename)
                PN = filename.split(".")[0]  # Remove the file extension

                if os.path.isfile(file):
                    if f"{PN}\n" not in existing_contents and filename != "Wasabi_UploadedPNS.txt":
                        try:
                            # self.upload_file(file, f"productimages/{filename}")
                            self.s3.meta.client.upload_file(file, "mpdb", f"productimages/{filename}")
                            f.write(f"{filename}\n")
                            recordsAdded += 1
                            if recordNumber % 1 == 0:
                                print(f"'{PN}' successfully uploaded to Wasabi ({recordsAdded} images uploaded)")
                        except Exception as e:
                            print(f"Failed to upload {PN} to Wasabi. Exception: {e}")
            f.close()  # Closing after each iteration to keep the file intact.

        print(f"Complete! Records Added: {recordsAdded}")