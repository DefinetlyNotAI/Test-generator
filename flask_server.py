import os
from flask import Flask, request, render_template, send_from_directory
from DataBase import *


app = Flask(__name__)
base_path = os.path.dirname(os.path.realpath(__file__))

err_codes = {
    400: 'Bad Request - Failed to access database or Bad Inputs <p> Most likely either Client-Side Issue or Frontend Issue </p>',
    401: 'Unauthorized Access - Incorrect password <p> Most likely either Client-Side Issue or Frontend Issue </p>',
    404: 'Not found - API request not correct/not found <p> Most likely either Client-Side Issue or Frontend Issue </p>',
    409: 'Conflict - Already exists, Duplicate entry <p> <p> Most likely a Backend Issue, please report it here:  <a href="https://github.com/DefinetlyNotAI/Test-generator/issues/new/choose">Here</a> </p>',
    500: 'Internal Server Error - SQLite error <p> Most likely either Client-Side Issue or Frontend Issue </p>',
    520: 'Unknown error - Caught exception <p> Most likely a Backend Issue, please report it here:  <a href="https://github.com/DefinetlyNotAI/Test-generator/issues/new/choose">Here</a></p>',
}


@app.route('/')
def index():
    return render_template('upload.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    """
    Uploads files to the server.

    This function is a route handler for the '/upload' endpoint. It expects a POST request with two files: 'db.config' and 'API.json'.

    Returns:
        An HTML message indicating success if both files are successfully uploaded and saved.
        An HTML message indicating an error if either 'db.config' or 'API.json' is missing, including an error number.
    """
    # Check if both required files are present in the request
    # Get the files from the request
    config_file = request.files['db.config']
    api_file = request.files['API.json']
    csv_file = request.files['Test.csv']

    if config_file.filename != '' and api_file.filename != '' and csv_file.filename != '':
        # Define the path for saving the files in the current working directory
        base_path = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(base_path, 'db.config')
        api_path = os.path.join(base_path, 'API.json')
        csv_file_path = os.path.join(base_path, 'Test.csv')

        # Replace any existing files
        if os.path.exists(config_path):
            os.remove(config_path)
        if os.path.exists(api_path):
            os.remove(api_path)
        if os.path.exists(csv_file_path):
            os.remove(csv_file_path)

        # Save the new files
        config_file.save(config_path)
        api_file.save(api_path)
        csv_file.save(csv_file_path)

        if os.path.exists('db.config') and os.path.exists('API.json') and os.path.exists('Test.csv'):
            # Return an HTML success message
            message = database_thread()
            if message.startswith('LIST'):
                # Removing 'LIST' from the beginning of the message
                message = message.replace('LIST', '', 1)

                parts = message.split(' && ')

                # Check if there are exactly two parts
                if len(parts) == 2:
                    # Strip spaces from the text part and convert the number part to an integer
                    error_message_key = parts[0].strip()
                    error_number = int(parts[1]) if parts[1].isdigit() else None

                else:
                    raise ValueError("The message does not match the expected format.")

                # Checking if the error number exists in err_codes
                if error_number in err_codes:
                    # Returning an HTML response with the error number and corresponding message
                    return f"<html><body><h1>Error</h1><h2>Error Number: {error_number}</h2><p>{error_message_key}</p><p>{err_codes[error_number]}</p></body></html>", error_number
                else:
                    return f"<html><body><h1>Error</h1><h2>Error Number: 501</h2><p>Unknown error - Not Defined - {error_message_key}</p></body></html>", 501
            else:
                if not message.startswith("DOWNLOAD"):
                    return f"<html><body><h1>Success</h1>{message}</body></html>", 200
                else:
                    return f"<html><body><h1>Success</h1>{message.replace('DOWNLOAD', '', 1)}</body></html>", 201
        else:
            return f"<html><body><h1>Error</h1><h2>Error Number: 404</h2><p>db.config, Test.csv and API.json files are required and cannot be empty.</p><p>{err_codes[404]}</p></body></html>", 404
    else:
        return f"<html><body><h1>Error</h1><h2>Error Number: 404</h2><p>db.config, Test.csv and API.json files are required and cannot be empty.</p><p>{err_codes[404]}</p></body></html>", 404


@app.route('/download_exam', methods=['GET'])
def download_exam():
    """
    Serves the Exam.xlsx file for download.
    """
    # Define the path for the Exam.xlsx file
    exam_path = os.path.join(base_path, 'Exam.xlsx')

    # Check if the file exists before attempting to send it
    if os.path.exists(exam_path):
        return send_from_directory(directory=base_path, path='Exam.xlsx')
    else:
        return f"<html><body><h1>Error</h1><h2>Error Number: 404</h2><p>Exam.xlsx does not exist.</p></body></html>", 404


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=int(os.environ.get("PORT", 5000)), debug=False)
