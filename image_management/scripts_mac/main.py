from filemaker import FilemakerAPI
from wasabi import Wasabi
from webscraper import Webscraper
from progress import Progress
import time
import os
import warnings

print("Author: Evan Meeks\n",
      "Version: 1.0"
      )

warnings.warn("WARNING: this script can take a while to run, depending on how many PNs don't have photos and your internet connection.\n All progress will be lost if it stops!")

time.sleep(.5)
progress_instance = Progress()
directory = os.getcwd() + "/product_photos"
if directory[-1] != "/":
    directory = directory + "/"

if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"created: {directory}")
wasabi = Wasabi()
################################ Querying FileMaker for PNs with Missing Photos ##################################
# FileMaker-specific vars
base_url = "https://ipointlibrary.ipointconnect.com/"
database = "iPoint Library"
layout = "API_iPointMasterItemsList"
find_criteria = {"flag_HasPhoto": "="}

print("Connecting to FileMaker")
fm = FilemakerAPI(base_url, database, layout)
offset = 1
found_count = float('inf')
partNumbers = []
recordIds = {}

print("Finding PNs with Missing Photos")

while offset <= found_count:
    try:
        missing_photos = fm.find_records(find_criteria, offset, 100)
        found_count = fm.found_count

        for i in missing_photos.get("response").get("data"):
            partNumbers.append([i["fieldData"]["manufacturer"], i["fieldData"]["Part Number"]])
            recordIds[i["fieldData"]["Part Number"]] = i["recordId"]
        if (offset-1) % 2000 == 0:
            print(f"Records remaining to process: {found_count - offset}")
        elif (offset -1) % 5000 == 0:
           progress_instance.update()
        offset += 100

    except:
        pass
print(f"PN count: {len(partNumbers)}")
fm.session_close()

###################### Web Scraping based off of PN List from FileMaker ##################################

if len(partNumbers) == 0:
    print("No PNs in FileMaker Found!")

else:
    scraper = Webscraper()
    scraper.scrape_list(partNumbers, directory)

################################ Resizing Photos & Uploading to Wasabi ##################################


wasabi.resize_images(directory, 300)
wasabi.upload(directory)
print("Photo upload(s) complete!")

################################ Creating uploaded PN list ##################################

wasabi_pns_urls = wasabi.save_parts_list(directory, skip_file_creation=True)

################### Updating FileMaker with the new URLs #################################
print("updating URLs in FileMaker")

fm = FilemakerAPI(base_url, database, layout)
counter = 0

for row in wasabi_pns_urls:
    if row[0] in recordIds:
        if counter % 1000 == 0:
            progress_instance.update()
        print(f"Updating Image URL in Filemaker for PN: {row[0]}")
        find_criteria = {"Part Number": row[0]}
        find_response = fm.find_records(find_criteria, 1, 1)
        recordId = recordIds[row[0]]
        try:
            update_response = fm.update_records(recordId, {"image_url": row[-1], "flag_HasPhoto": 1})
        except:
            print(f"failed to update record: {row[0]}")
        counter += 1

fm.session_close()


print(f"Purging your machine of the downloaded photos.\n")
for obj in os.listdir(directory):
    obj_path = os.path.join(directory, obj)
    try:
        os.remove(obj_path)
    except Exception as e:
        print(f"failed to delete object at: {obj_path}")

print("Script Complete!")
exit()
