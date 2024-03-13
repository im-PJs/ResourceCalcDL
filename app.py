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
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

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
            # Assuming instructions are in a list of dicts; adjust as needed
            output = io.StringIO()
            writer = csv.writer(output)
            for item in text_instructions:
                writer.writerow([item['ingredient'], item['amount']])
            file_content = output.getvalue()
            filename = 'instructions.csv'
        
        session['file_content'] = file_content
        # Store file content in the session or another mechanism as needed
        # For now, return the content and filename to be used in the template
        return render_template('index.html', text_instructions=text_instructions, file_content=file_content, filename=filename, file_type=file_type)
    else:
        return render_template('index.html', text_instructions=None, filename=filename)  # Pass filename for 'GET' request


@app.route('/download')
def download_file():
    filename = request.args.get('filename', default='None.txt')  # Retrieve filename from request parameters
    file_type = request.args.get('filetype')
    file_content = session.get('file_content')

    # Set the appropriate content-type based on file_type
    content_type = "text/plain"
    if file_type == 'json':
        content_type = "application/json"
    elif file_type == 'csv':
        content_type = "text/csv"

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
