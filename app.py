from flask import Flask, render_template, request, session, Response
import io
import csv
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.remote.remote_connection import LOGGER as seleniumLogger
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Suppress logging from webdriver_manager by setting its logger to WARNING level or higher
logging.getLogger('selenium').setLevel(logging.WARNING)

# Suppress logging from webdriver_manager by setting its logger to WARNING level or higher
logging.getLogger('webdriver_manager').setLevel(logging.WARNING)

app = Flask(__name__)
app.secret_key = 'PJsSecretKey1'  # Set a secret key for the session

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        resource_calculator_url = request.form.get('resourceCalculatorURL')
        text_instructions = scrape_resource_calculator(resource_calculator_url)
        logging.debug(f"URL submitted: {resource_calculator_url}")
        logging.debug(f"Extracted instructions: {text_instructions}")

        # No file_type is involved here since we're just submitting URL
        # Store URL and text_instructions for later use, such as in the download step
        session['text_instructions'] = text_instructions
        session['url'] = resource_calculator_url

        # Render template with instructions to show to the user and potentially choose file type later
        return render_template('index.html', text_instructions=text_instructions)
    else:
        # Just show the initial form if no POST request has been made
        return render_template('index.html', text_instructions=None)

@app.route('/download')
def download_file():
    # Retrieve stored data for file generation
    text_instructions = session.get('text_instructions', '')
    url = session.get('url', '')

    # Determine file type from query parameters; default to CSV
    file_type = request.args.get('filetype', 'csv')

    # Based on the file type, process the text instructions accordingly
    if file_type == 'csv':
        filename, file_content, content_type = convert_to_csv(text_instructions, url)
    elif file_type == 'json':
        filename, file_content, content_type = convert_to_json(text_instructions, url)
    else:  # Default to plain text
        filename, file_content, content_type = convert_to_txt(text_instructions, url)

    # Send the processed file to the user
    return Response(
        file_content,
        mimetype=content_type,
        headers={"Content-disposition": f"attachment; filename={filename}"})

def convert_to_csv(text_instructions, url):
    output = io.StringIO()
    csv_writer = csv.writer(output)

    # Assuming 'text_instructions' contains the relevant data split by 'Instructions'
    sections = text_instructions.split('Instructions')
    base_ingredients_section = sections[0].strip()
    instructions_section = sections[1].strip() if len(sections) > 1 else ""

    # Write headers and sections to CSV
    csv_writer.writerow(["Resource Calculator URL:", url])
    csv_writer.writerow([])
    csv_writer.writerow(["Ingredient", "Quantity"])
    for line in base_ingredients_section.split('\n')[1:]:
        line = line.strip()
        if line and not line.lower().startswith("text"):
            if '(' in line:  # Quantities with parentheses indicating details
                quantity_end_index = line.find(')') + 1
                quantity = line[:quantity_end_index].strip()
                name = line[quantity_end_index:].strip()
            else:  # Quantities without parentheses
                parts = line.split(' ', 1)
                if len(parts) == 2:
                    quantity, name = parts[0], parts[1]
                else:
                    # Fallback in case of unexpected format
                    quantity = ""
                    name = line

            csv_writer.writerow([name, quantity])

    csv_writer.writerow([])  # Blank line before instructions
    csv_writer.writerow(["Instructions"])  # Instructions header

    # Remove "[Beta]" from each instruction, then strip again to remove any leading/trailing whitespace
    for instruction in instructions_section.split('\n'):
        cleaned_instruction = instruction.replace("[Beta]", "").strip()
        if cleaned_instruction:  # Check that the instruction is not empty after cleaning
            csv_writer.writerow([cleaned_instruction])

    file_content = output.getvalue()
    content_type = "text/csv"
    return 'instructions.csv', file_content, content_type

def convert_to_txt(text_instructions, url):
    output = io.StringIO()

    # Write the URL at the top
    output.write(f"Resource Calculator URL: {url}\n\n")

    # Split the text_instructions into base ingredients and instructions sections
    # Make sure to split only on the first occurrence in case "Instructions" appears within the content
    sections = text_instructions.split('Instructions', 1)
    base_ingredients_section = sections[0].strip()
    instructions_section = sections[1].strip() if len(sections) > 1 else ""

    # Write the Base Ingredients section
    output.write("Base Ingredients:\n")
    for line in base_ingredients_section.split('\n'):
        cleaned_line = line.strip()
        if cleaned_line and not cleaned_line.lower().startswith("base ingredients") and not cleaned_line.lower() == "text":
            output.write(f"{cleaned_line}\n")

    # If there's an instructions section, add a newline for spacing before writing it
    if instructions_section:
        output.write("\nInstructions:\n")
        for instruction in instructions_section.split('\n'):
            cleaned_instruction = instruction.replace("[Beta]", "").strip()
            if cleaned_instruction and cleaned_instruction.lower() != "text":
                output.write(f"{cleaned_instruction}\n")

    file_content = output.getvalue()
    output.close()

    return 'instructions.txt', file_content, 'text/plain'

def convert_to_json(text_instructions, url):
    sections = text_instructions.split("Instructions")
    base_ingredients_section = sections[0].strip() if len(sections) > 0 else ""
    instructions_section = sections[1].strip() if len(sections) > 1 else ""

    ingredients = []
    for line in base_ingredients_section.split('\n')[1:]:  # Assuming the first line is a header
        line = line.strip()
        if line:  # Check that line is not empty
            if '(' in line and ')' in line:  # If line contains details within parentheses
                # Find the index where quantity ends (right after the closing parenthesis)
                quantity_end_index = line.find(')') + 1
                # Extract quantity and name based on the parenthesis
                quantity = line[:quantity_end_index].strip()
                name = line[quantity_end_index:].strip()
                ingredients.append({"Ingredient": name, "Quantity": quantity})
            else:  # If there are no parentheses, split normally
                parts = line.split(' ', 1)  # Split into two parts at the first space
                if len(parts) == 2:
                    quantity, name = parts
                    ingredients.append({"Ingredient": name, "Quantity": quantity})
                else:
                    # If splitting went wrong, assume whole line is the name or log an error
                    logging.warning(f"Line format is incorrect: {line}")

    # Remove any instructions that are exactly "[Beta]" or contain it
    instructions = [instr.strip() for instr in instructions_section.split('\n') 
                    if instr.strip() and "[Beta]" not in instr.strip()]
    json_output = {
        "ResourceCalculatorURL": url,
        "BaseIngredients": ingredients,
        "Instructions": instructions
    }

    return 'instructions.json', json.dumps(json_output, indent=4), 'application/json'

def scrape_resource_calculator(url):
    driver = None
    try:
        # Set up the WebDriver options to enable headless mode
        options = ChromeOptions()
        options.add_argument('--headless')  # Only if you want to run headless
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)


        # Navigate to the page
        driver.get(url)

        # Wait for the text instructions element to be available and extract text
        try:
            text_instructions_element = WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.ID, "text_instructions"))
            )
            text_instructions = text_instructions_element.text
            return text_instructions
        except TimeoutException:
            return "Timed out waiting for text instructions to appear."

    except Exception as e:
        return f"An error occurred: {e}"

    finally:
        # Make sure to close the browser
        if driver:
            driver.quit()


if __name__ == '__main__':
    app.run(debug=True)