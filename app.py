from flask import Flask, render_template, request, session, Response
import io
import csv
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.edge.service import Service
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.remote.remote_connection import LOGGER as seleniumLogger
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Suppress logging from webdriver_manager by setting its logger to WARNING level or higher
logging.getLogger('selenium').setLevel(logging.WARNING)

# Suppress logging from webdriver_manager by setting its logger to WARNING level or higher
logging.getLogger('webdriver_manager').setLevel(logging.WARNING)

app = Flask(__name__)
app.secret_key = 'PJsSecretKey'  # Set a secret key for the session

@app.route('/', methods=['GET', 'POST'])
def index():
    filename = "None.txt"  # Default filename
    if request.method == 'POST':
        logging.debug(f"File Type: {request.form['fileType']}")
        resource_calculator_url = request.form['resourceCalculatorURL']
        file_type = request.form['fileType']
        text_instructions = scrape_resource_calculator(resource_calculator_url)
        logging.debug(f"text instructions: {text_instructions}")
        file_content = text_instructions
        logging.debug(f"file content: {file_content}")
        # Convert the instructions to the selected file format
        if file_type == 'txt':
            print(f"File Content: {file_content}")
            filename = 'instructions.txt'
        elif file_type == 'json':
            # Assuming instructions are in a dict format; adjust as needed
            file_content = json.dumps(text_instructions)
            filename = 'instructions.json'
        elif file_type == 'csv':
            output = io.StringIO()
            writer = csv.writer(output)
            # Split the instructions into lines and write each line to the CSV
            for line in text_instructions.split('\n'):  # Split the text into lines
                writer.writerow([line])  # Write the line to the CSV file
            file_content = output.getvalue()
            filename = 'instructions.csv'
        
        session['file_content'] = file_content
        session['url'] = resource_calculator_url
        # Store file content in the session or another mechanism as needed
        # For now, return the content and filename to be used in the template
        return render_template('index.html', text_instructions=text_instructions, file_content=file_content, filename=filename, file_type=file_type)
    else:
        return render_template('index.html', text_instructions=None, filename=filename)  # Pass filename for 'GET' request

from flask import Flask, render_template, request, session, Response
import io
import csv
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.edge.service import Service
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.remote.remote_connection import LOGGER as seleniumLogger
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Suppress logging from webdriver_manager by setting its logger to WARNING level or higher
logging.getLogger('selenium').setLevel(logging.WARNING)

# Suppress logging from webdriver_manager by setting its logger to WARNING level or higher
logging.getLogger('webdriver_manager').setLevel(logging.WARNING)

app = Flask(__name__)
app.secret_key = 'PJsSecretKey'  # Set a secret key for the session

@app.route('/', methods=['GET', 'POST'])
def index():
    filename = "None.txt"  # Default filename
    if request.method == 'POST':
        logging.debug(f"File Type: {request.form['fileType']}")
        resource_calculator_url = request.form['resourceCalculatorURL']
        file_type = request.form['fileType']
        text_instructions = scrape_resource_calculator(resource_calculator_url)
        logging.debug(f"text instructions: {text_instructions}")
        file_content = text_instructions
        logging.debug(f"file content: {file_content}")
        # Convert the instructions to the selected file format
        if file_type == 'txt':
            print(f"File Content: {file_content}")
            filename = 'instructions.txt'
        elif file_type == 'json':
            # Assuming instructions are in a dict format; adjust as needed
            file_content = json.dumps(text_instructions)
            filename = 'instructions.json'
        elif file_type == 'csv':
            output = io.StringIO()
            writer = csv.writer(output)
            # Split the instructions into lines and write each line to the CSV
            for line in text_instructions.split('\n'):  # Split the text into lines
                writer.writerow([line])  # Write the line to the CSV file
            file_content = output.getvalue()
            filename = 'instructions.csv'
        
        session['file_content'] = file_content
        session['url'] = resource_calculator_url
        # Store file content in the session or another mechanism as needed
        # For now, return the content and filename to be used in the template
        return render_template('index.html', text_instructions=text_instructions, file_content=file_content, filename=filename, file_type=file_type)
    else:
        return render_template('index.html', text_instructions=None, filename=filename)  # Pass filename for 'GET' request
@app.route('/download')
def download_file():
    filename = request.args.get('filename', 'instructions.csv')
    file_type = request.args.get('filetype', 'csv')
    file_content = session.get('file_content', '')
    url = session.get('url', '')

    if file_type == 'csv':
        output = io.StringIO()
        csv_writer = csv.writer(output)

        sections = file_content.split('Instructions')
        base_ingredients_section = sections[0].strip()
        instructions_section = sections[1].strip() if len(sections) > 1 else ""

        csv_writer.writerow(["Ingredient", "Quantity"])
        for line in base_ingredients_section.split('\n')[1:]:
            line = line.strip()
            if line and not line.lower().startswith("text"):
                if '(' in line:  # Handle quantities with parentheses
                    quantity_start_index = line.rfind('(')
                    quantity_end_index = line.rfind(')') + 1
                    name = line[:quantity_start_index].strip()
                    quantity = line[quantity_start_index:quantity_end_index].strip()
                    extra = line[quantity_end_index:].strip()  # Capture any extra text after the parenthesis
                    if extra:  # Append any extra text after the parenthesis to the quantity string
                        quantity += " " + extra
                else:  # Handle quantities without parentheses
                    parts = line.rsplit(' ', 1)
                    if len(parts) == 2:
                        name, quantity = parts
                    else:
                        # Fallback in case of unexpected format
                        name = line
                        quantity = ""

                csv_writer.writerow([name, quantity])

        csv_writer.writerow([])
        csv_writer.writerow(["Instructions"])
        for instruction in instructions_section.split('\n'):
            instruction = instruction.strip().replace("[Beta]", "").strip()
            if instruction:
                csv_writer.writerow([instruction])

        csv_writer.writerow([])
        csv_writer.writerow(['URL', url])

        file_content = output.getvalue()
        content_type = "text/csv"
    else:
        content_type = "application/json" if file_type == 'json' else "text/plain"

    return Response(
        file_content,
        mimetype=content_type,
        headers={"Content-disposition": f"attachment; filename={filename}"})

def scrape_resource_calculator(url):
    driver = None
    try:
        # Set up the WebDriver
        service = Service(EdgeChromiumDriverManager().install())
        driver = webdriver.Edge(service=service)

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


def scrape_resource_calculator(url):
    driver = None
    try:
        # Set up the WebDriver
        service = Service(EdgeChromiumDriverManager().install())
        driver = webdriver.Edge(service=service)

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
