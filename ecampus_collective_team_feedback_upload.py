import json
import time
from pathlib import Path
import os

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select


# Function to load credentials from the JSON file
def load_credentials(cred_file):
    with open(cred_file, "r") as f:
        return json.load(f)

# Function to set up the WebDriver
def setup_driver():
    options = Options()
    options.headless = True
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    return webdriver.Chrome(options=options)

# Separate function to perform login
def perform_login(driver, login_url, username, password):
    # 1. Open the login page
    driver.get(login_url)

    # 2. Click on 'Anmelden' button
    button = driver.find_element(By.LINK_TEXT, "Anmelden")
    button.click()

    # 3. Wait for redirection
    time.sleep(5)

    # 4. Fill in Uni-ID and password
    username_field = driver.find_element(By.NAME, "j_username")
    password_field = driver.find_element(By.NAME, "j_password")

    username_field.send_keys(username)
    password_field.send_keys(password)

    # 5. Click on the login button
    login_button = driver.find_element(By.NAME, "_eventId_proceed")
    login_button.click()

    # 6. Wait for the redirection to complete
    time.sleep(5)

# Function to scrape assignment data after login
def scrape_assignments(driver, ref_id, ass_id_file):
    # 7. After login, open the tutorial hand-in page
    tutorial_hand_in_link = f"https://ecampus.uni-bonn.de/ilias.php?ref_id={ref_id}&cmd=members&cmdClass=ilexercisemanagementgui&cmdNode=bu:o9:bv&baseClass=ilexercisehandlergui"
    driver.get(tutorial_hand_in_link)

    # 8. Locate the <select> element for assignments by its ID
    dropdown = driver.find_element(By.ID, "ass_id")

    # 9. Interact with the dropdown using Select
    select = Select(dropdown)

    # 10. Extract assignment data (ass_id and name)
    options = select.options
    assignment_data = {}
    # Loop through the options and extract their value and text
    for option in options:
        ass_id = option.get_attribute("value")
        name = option.text.strip()  # To remove any leading/trailing spaces
        
        # Store the name as the key and ass_id as the value
        assignment_data[name] = ass_id

    # Write the assignment data to the specified JSON file
    with open(ass_id_file, 'w') as json_file:
        json.dump(assignment_data, json_file, indent=4)

    print(f"Assignments saved to '{ass_id_file}'.")


def upload_assignments(driver,student_data,ref_id,ass_id):
    for UploadID, file_path in student_data:
        
    # Check extraction
        if ref_id and ass_id:
            member_id = UploadID  
            upload_page_url = (
                f"https://ecampus.uni-bonn.de/ilias.php?"
                f"ref_id={ref_id}&ass_id={ass_id}&vw=1&member_id={member_id}"
                "&cmd=listFiles&cmdClass=ilfilesystemgui"
                "&cmdNode=bu:o9:bv:cw&baseClass=ilexercisehandlergui"
            )

        # 1. Go to upload Page
        print("Visting:\n")
        print(upload_page_url)
        driver.get(upload_page_url)

        # 2. Wait a few seconds, so the page can load
        time.sleep(5)  

        # 3. Find filei-upload-field (example 'input[type="file"]')
        upload_input = driver.find_element(By.ID, 'new_file')

        # 4. Path to file
        file_path = os.path.abspath(file_path) 
        # Set upload-field to file path
        upload_input.send_keys(file_path)

        # 4. click upload button
        upload_button = driver.find_element(By.NAME, 'cmd[uploadFile]')
        upload_button.click()
        print(f"Uploaded: {file_path}")



# Functions to scrape Teams and their single file    
def extract_student_info(folder_path):
    " Extracts the team identifier and the feedbackfile, which is a *.pdf"
    if folder_path.startswith('"') and folder_path.endswith('"'):
        folder_path = folder_path[1:-1]
    if folder_path.startswith("'") and folder_path.endswith("'"):
        folder_path = folder_path[1:-1]
    result = []
    # Traverse through all files and folders in the root folder
    for student_folder in Path(folder_path).rglob("*.*"):  # Only look for files
        if student_folder.is_file():
            # Parent folder name (the folder containing the file)
            parent_folder_name = student_folder.parent.name

            # Extract the last part after the last underscore "_"
            parts = parent_folder_name.split("_")
            if len(parts) > 1:
                UploadID = parts[-1]  # Get the last part after "_"

                # Add the student data to the result list
                result.append((UploadID, str(student_folder.resolve())))

    return result

# Main function to handle the entire process
def main(username,password,ass_id_file,folder_path,ref_id,assignment_name=None):
 

    # URL for login
    login_url = "https://ecampus.uni-bonn.de/login.php?client_id=ecampus&cmd=force_login&lang=de"

    # Set up the WebDriver
    driver = setup_driver()

    try:
        # Perform login
        perform_login(driver, login_url, username, password)

        # Scrape assignment data after login
        
        if not assignment_name:
            if not load_credentials(ass_id_file):
                scrape_assignments(driver, ref_id, ass_id_file)
            ass_dict =load_credentials(ass_id_file)
            print("Select the assignment from:")
            print(ass_dict)
        
            assignment_name= input("The assigment:")

        else:
            ass_dict =load_credentials(ass_id_file)
        ass_id=ass_dict[assignment_name]

        
        # Perform upload
        student_data = extract_student_info(folder_path)
        print("Student data extracted")
        upload_assignments(driver,student_data,ref_id,ass_id)
        
    finally:
        driver.quit()

if __name__ == "__main__":

    # Load credentials from the given JSON file
    creds = load_credentials(cred_file="credentials_sample.json")

    # User data to be used for login
    username = creds["username"]
    password = creds["password"]
    
    main(username=username, password=password, ass_id_file="assignments_sample.json", folder_path="absolut/path/to/Folder/of/one/assignment/feedback", ref_id="XXXXXX",assignment_name="Blatt 01")
