import csv
import json
import os.path
import random
import secrets
import sqlite3
import string
import time
from configparser import ConfigParser
import pandas as pd


def check_for_LIST(value):
    """
    Check if the input value contains the word 'LIST'.

    Args:
        value (str): The input string to check.

    Returns:
        bool: True if 'LIST' is found in the input string, False otherwise.
    """
    if value is None:
        return False

    words = value.split()
    for word in words:
        if word == 'LIST':
            return True

    return False


class UserManager:
    # Class to handle user management
    def __init__(self, db_name='users.db'):
        """
        Initializes the UserManager class.

        Args:
            db_name (str, optional): The name of the database. Defaults to 'users.db'.

        Returns:
            None
        """
        self.db_name = db_name
        self.conn = None
        self.cursor = None

    def connect(self):
        """
        Connects to the SQLite database.

        This function establishes a connection to the SQLite database specified by the `db_name` attribute.
        If a connection has not been established yet, it creates a new connection and assigns it to the `conn` attribute.
        It also creates a cursor object and assigns it to the `cursor` attribute.

        Returns:
            None
        """
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_name)
            self.cursor = self.conn.cursor()

    def disconnect(self):
        """
        Closes the connection to the SQLite database.

        This function closes the connection to the SQLite database and clears the `conn` and `cursor` attributes.

        Returns:
            None
        """
        if self.conn:
            self.conn.close()
            self.conn = None
            self.cursor = None

    @staticmethod
    def create_db_initial():
        """
        Connects to the SQLite database. This function creates the database file if it doesn't exist, creates a table named Users with specific columns, and commits the transaction before closing the connection.
        """
        # Connect to the SQLite database
        # This will create the database file if it doesn't already exist
        conn = sqlite3.connect('users.db')

        # Create a cursor object using the cursor() method
        cursor = conn.cursor()

        # Drop the table if it already exists to start fresh
        cursor.execute('''DROP TABLE IF EXISTS Users;''')

        # Create a table named Users with id, username, password, and titles_to_exclude columns
        cursor.execute('''CREATE TABLE Users (
                            id INTEGER PRIMARY KEY,
                            username TEXT NOT NULL UNIQUE,
                            password TEXT NOT NULL,
                            titles_to_exclude TEXT);''')

        # Commit the transaction
        conn.commit()

        # Close the connection
        conn.close()

    def verify_password(self, username, password):
        """
        Verify the password for a given username.

        Args:
            username (str): The username to verify.
            password (str): The password to verify.

        Returns:
            bool: True if the password is correct, False otherwise.
        """
        try:
            self.connect()
            self.cursor.execute("SELECT password FROM Users WHERE username=?", (username,))
            result = self.cursor.fetchone()
            self.disconnect()

            if result:
                stored_password = result[0]
                if password == stored_password:
                    return True
            return False
        except Exception:
            return False

    def create_db(self, username, exclusion_titles):
        """
        Creates a new database entry for a user with the given username and exclusion titles.

        Args:
            username (str): The username of the user.
            exclusion_titles (str): The exclusion titles for the user.

        Returns:
            str: The password for the newly created user, or an error message if the username already exists or an exception occurs.

        Raises:
            Exception: If an exception occurs during the execution of the function.
        """
        try:
            self.connect()
            self.cursor.execute("SELECT * FROM users WHERE username=?", (username,))
            existing_user = self.cursor.fetchone()
            self.disconnect()

            if existing_user:
                return "LIST Username already exists. && 409"

            alphabet = string.ascii_letters + string.digits
            password_new = ''.join(secrets.choice(alphabet) for _ in range(12))

            self.connect()
            self.cursor.execute("INSERT INTO users (username, password) VALUES (?,?)", (username, password_new))
            self.conn.commit()
            self.disconnect()

            password_str = "Password is " + password_new

            um.add_exclusion_db(username, exclusion_titles, password_new, "CDB")

            return password_str
        except Exception as e:
            return f'LIST {e} && 500'

    def remove(self, username, password):
        """
        Removes a user from the database if the provided password matches the user's password.

        Args:
            username (str): The username of the user to be removed.
            password (str): The password of the user.

        Returns:
            str: A success message if the user is successfully removed.
            str: An error message if the password is incorrect.
            str: An error message if an exception occurs.

        Raises:
            Exception: If an exception occurs during the execution of the function.
        """
        try:
            if self.verify_password(username, password):
                self.connect()
                self.cursor.execute('''DELETE FROM Users WHERE username=?''', (username,))
                self.conn.commit()
                self.disconnect()
                return f"Successfully removed data for user {username}."
            else:
                return "LIST Incorrect password. && 401"
        except Exception as e:
            return f'LIST {e} && 500'

    def add_exclusion_db_main(self, name, titles, password):
        """
        Adds new titles to the exclusion list for a user in the database.

        Args:
            name (str): The username of the user.
            titles (str): The new titles to be added to the exclusion list.
            password (str): The password of the user.

        Returns:
            str: A success message if the titles are successfully added to the exclusion list for the user.
                If there are no new titles to add, returns "LIST No new titles to add. && 400".
                If the password is incorrect, returns "LIST Incorrect password. && 401".
                If an exception occurs during the execution of the function, returns a formatted error message.

        Raises:
            None.

        """
        try:
            if self.verify_password(name, password):
                self.connect()
                try:
                    self.cursor.execute('''SELECT titles_to_exclude FROM Users WHERE username=?''', (name,))
                    result = self.cursor.fetchone()

                    # Check if the result is None or NULL and replace with a placeholder
                    if result is None or result[0] is None:
                        initial_titles = "PLACEHOLDER"  # Placeholder for empty titles_to_exclude
                    else:
                        initial_titles = result[0]

                    current_titles = initial_titles.strip()

                    # Convert current_titles and titles to sets for comparison
                    current_titles_set = set(current_titles.split(','))
                    titles_set = set(titles)

                    # Calculate the difference between the two sets
                    new_titles_set = titles_set - current_titles_set

                    # If there are new titles to add, proceed with the update
                    if new_titles_set:
                        updated_titles = ','.join(list(new_titles_set))  # Join the new titles with a comma and space
                        self.cursor.execute(
                            '''UPDATE Users SET titles_to_exclude = COALESCE(titles_to_exclude ||?, '') WHERE username =?''',
                            (updated_titles, name))
                        self.conn.commit()
                        return f"Successfully updated titles for user {name}."
                    else:
                        return "LIST No new titles to add. && 400"

                except Exception as e:
                    return f'LIST {e} && 500'
            else:
                return "LIST Incorrect password. && 401"
        except Exception as e:
            return f'LIST {e} && 520]'

    @staticmethod
    def add_exclusion_db(name, titles, password, special=None):
        """
        Adds an exclusion to the database for a given user.

        Args:
            name (str): The name of the user.
            titles (str): The titles to exclude.
            password (str): The password of the user.
            special (Optional[str]): An optional parameter indicating if the exclusion is special.

        Returns:
            str: The result of adding the exclusion to the database. If successful, it returns the value returned by `um.add_exclusion_db_main()`. If an error occurs, it returns a formatted string indicating the error.

        Raises:
            Exception: If an error occurs during the execution of the function.

        Note:
            - The `um.add_exclusion_db_main()` function is called to add the exclusion to the database.
            - If the `check_for_LIST()` function returns True for the value returned by `um.add_exclusion_db_main()`, it is returned.
            - If the `special` parameter is not provided, the `um.add_exclusion_db_main()` function is called with a comma and the password as arguments.
            - If an error occurs, a formatted string indicating the error is returned.

        """
        try:
            value = um.add_exclusion_db_main(name, titles, password)
            if check_for_LIST(value):
                return value
            if not special:
                msg = um.add_exclusion_db_main(name, ",", password)
                if check_for_LIST(msg):
                    return msg
            return value
        except Exception as e:
            return f'LIST {e} && 520'

    def get_excluded_titles(self, username):
        """
        Retrieves the titles to exclude for a given user from the database.

        Args:
            username (str): The name of the user.

        Returns:
            list: A list of titles to exclude for the user.

        Raises:
            Exception: If an error occurs during the execution of the function.

        """
        try:
            self.connect()
            self.cursor.execute('''SELECT titles_to_exclude FROM Users WHERE username=?''', (username,))
            result = self.cursor.fetchone()
            self.disconnect()

            if result:
                titles_list = result[0].split(',')
                titles_to_exclude = [title.strip() for title in titles_list]
            else:
                titles_to_exclude = []

            return titles_to_exclude
        except Exception as e:
            return f'LIST {e} && 520'

    @staticmethod
    def extract_user_info(data):
        """
        Extracts the username, password, and exclusion titles from the provided dictionary.

        Args:
            data (dict): A dictionary containing the username, password, and exclusion titles.

        Returns:
            tuple: A tuple containing the username, password, and exclusion titles.

        Raises:
            Exception: If an error occurs during the execution of the function.

        """
        try:
            # Safely accessing the values from the user_data dictionary
            username = data.get('Username', 'Unknown')
            if check_for_LIST(username):
                return username
            password = data.get('Password', 'Unknown')
            if check_for_LIST(password):
                return username
            exclusion_titles = data.get('Exclusion_titles', [])
            if isinstance(exclusion_titles, str):
                if check_for_LIST(exclusion_titles):
                    return exclusion_titles

            return username, password, exclusion_titles
        except Exception as e:
            return f'LIST {e} && 520'


# Function to read and validate the CSV file
def read_csv(file_path):
    """
    Reads a CSV file and returns a list of questions.

    Args:
        file_path (str): The path to the CSV file.

    Returns:
        list: A list of questions.

    Raises:
        FileNotFoundError: If the file is not found.
        Exception: If an error occurs while reading the file.

    The function reads a CSV file located at the specified file path. It returns a list of questions, where each question is a list of values from the CSV file. The function also performs some validation on the data in the CSV file.

    If the file is not found, a `FileNotFoundError` is raised. If an error occurs while reading the file, an `Exception` is raised.

    The function assumes that the CSV file has a header row and that the URL column is the fifth column (index starts at 0).

    The function checks for empty values in the specified columns (excluding the URL column) and returns an error message if any empty values are found.

    The function also checks the difficulty level and returns an error message if the difficulty level is not one of 'Hard', 'Medium', or 'Easy'.

    The function also checks the score and returns an error message if the score is not an integer or is not in the range of 0 to 100.

    The function appends the row to the list of questions, including the URL if it is present.

    The function returns the list of questions.
    """
    try:
        questions = []
        with open(file_path, mode='r', encoding='utf-8') as file:
            reader = csv.reader(file)
            next(reader)  # Skip header row if present
            for row in reader:
                # Initialize a list to hold the indices to check
                indices_to_check = []

                # Populate the list with indices to check, excluding the URL column index
                for i in range(len(row)):
                    if i != 4:  # Excluding the URL column index (assuming it's always the 5th column)
                        indices_to_check.append(i)

                # Use a generator expression to strip values and check for emptiness across the specified indices
                if not all(value.strip() for value in (row[i] for i in indices_to_check)):
                    return "LIST Empty value found in CSV. && 400"

                difficulty = row[2].strip()
                if difficulty not in ['Hard', 'Medium', 'Easy']:
                    return f"LIST Invalid difficulty level at line {reader.line_num}: {difficulty}. && 400"
                try:
                    score = int(row[3].strip())
                except ValueError:
                    return f"LIST Invalid score format at line {reader.line_num}: {row[3]}. && 400"
                if not 0 <= score <= 100:
                    return f"LIST Invalid score range at line {reader.line_num}: {score}. && 400"

                # Adjusted to allow the URL column to be empty
                url_column_index = 4  # Assuming the URL is in the 5th column (index starts at 0)
                url = row[url_column_index].strip() if url_column_index < len(row) else None

                questions.append(
                    [*row[:url_column_index], url])  # Append the row with the URL if present, otherwise append None
        return questions
    except FileNotFoundError as fnfe:
        return f"LIST {fnfe} && 404"
    except Exception as e:
        return f'LIST {e} && 520'


# Function to read and validate the config file
def read_config(file_path):
    """
    Reads a configuration file and validates its contents.

    Args:
        file_path (str): The path to the configuration file.

    Returns:
        dict or str: A dictionary containing the configuration values if the file is valid, or a string
        containing an error message if the file is invalid.

    Raises:
        FileNotFoundError: If the configuration file is not found.
        Exception: If an unexpected error occurs.

    The function reads a configuration file using the `ConfigParser` class. It checks that the file contains
    exactly one section, and that it contains all the required options. It also checks that the values of
    certain options are integers. If the file is valid, the function returns a dictionary containing the
    configuration values. If the file is invalid, the function returns a string containing an error message.

    Note:
        The function assumes that the configuration file is in the INI format.

    Example:
        >>> read_config('config.ini')
        {'questions_amount': 10, 'minimum_titles': 5, 'hard': 3, 'medium': 4, 'easy': 3, 'points': 100, 'debug': False}
        >>> read_config('invalid_config.ini')
        'LIST Config file must contain exactly one section. && 400'
    """
    try:
        config = ConfigParser()
        config.read(file_path)
        sections = config.sections()
        if len(sections) != 1:
            return "LIST Config file must contain exactly one section. && 400"
        section = sections[0]
        options = config.options(section)
        required_options = ['questions_amount', 'minimum_titles', 'hard', 'medium', 'easy', 'points', 'debug']
        missing_options = [option for option in required_options if option not in options]
        if missing_options:
            return f"LIST Missing required options in config file: {missing_options} && 400"
        for option in required_options[:-2]:  # Exclude 'debug' and 'points' from this check
            try:
                int(config.get(section, option))
            except ValueError:
                return f"LIST Invalid value type for {option}: expected integer. && 400"
        if config.getint(section, 'hard') + config.getint(section, 'medium') + config.getint(section, 'easy') != config.getint(section, 'questions_amount'):
            return "LIST The sum of hard, medium, and easy questions must equal the total questions amount. && 400"
        return {
            'questions_amount': config.getint(section, 'questions_amount'),
            'minimum_titles': config.getint(section, 'minimum_titles'),
            'hard': config.getint(section, 'hard'),
            'medium': config.getint(section, 'medium'),
            'easy': config.getint(section, 'easy'),
            'points': config.getint(section, 'points'),
            'debug': config.getboolean(section, 'debug')
        }
    except FileNotFoundError as fnfe:
        return f"LIST {fnfe} && 404"
    except Exception as e:
        return f'LIST {e} && 520'


def create_excel_from_txt(debug):
    """
    Create an Excel file from text data.

    Parameters:
    - debug (bool): A flag indicating whether to include additional columns in the Excel file based on debug mode.

    Returns:
    - None
    """
    try:
        # Initialize an empty list to hold our data
        data = []

        # Define headers based on the debug flag
        if debug:
            headers = ['URL', 'Question', 'Title', 'Difficulty', 'Score']
        else:
            headers = ['URL', 'Question', 'Score']

        # Open the text file and read it line by line
        with open('Exam.txt', 'r') as file:
            lines = file.readlines()
            for i, line in enumerate(lines):
                # Skip odd-numbered lines (starting count from 0)
                if i % 2 != 0:
                    continue

                # Split the line at '&' to separate the components
                parts = line.strip().split('&')

                # Process the parts based on the debug flag
                if debug:
                    if len(parts) == 5:  # Ensure there are exactly 4 parts
                        data.append(parts)  # Directly append the parts as a new row
                else:
                    if len(parts) == 3:  # Ensure there are exactly 2 parts
                        data.append(parts)  # Directly append the parts as a new row

        # Convert the list of lists into a DataFrame
        df = pd.DataFrame(data, columns=headers)

        # Write the DataFrame to an Excel file
        df.to_excel('Exam.xlsx', index=False)

        os.remove('Exam.txt')
    except FileExistsError as fnfe:
        return f"LIST {fnfe} && 409"
    except Exception as e:
        return f'LIST {e} && 520'


# Function to generate the exam
def generate_exam(questions, config_data, exclude_list):
    """
    Generate an exam based on the provided questions and configuration data while excluding certain titles.

    Parameters:
    - questions (list): A list of questions to generate the exam from.
    - config_data (dict): A dictionary containing configuration data such as the number of questions, difficulty levels, and points.
    - exclude_list (list): A list of titles to exclude from the exam generation.

    Returns:
    - tuple: A tuple containing the generated exam as a list of selected questions, the total points of the exam, the difficulty ratios of each difficulty level, and the list of unique titles included in the exam.
    - str: If an exception occurs during the exam generation, a string indicating the error.
    """
    try:
        while True:
            if not questions:
                # Retry if a questions' list is empty
                questions = read_csv('Test.csv')
                if not questions:
                    return "LIST Failed to load questions from CSV file. && 500"

            exam = []
            total_points = 0
            total_titles = []
            difficulty_counts = {'Hard': 0, 'Medium': 0, 'Easy': 0}

            # Split the exclude_list by comma and strip whitespace
            excluded_titles = [title.strip() for title in exclude_list[0].split(',')]

            # Filter out questions with titles in the exclude_list
            filtered_questions = [q for q in questions if q[1] not in excluded_titles]

            # Generate the exam using the filtered questions
            for i in range(config_data['questions_amount']):
                if not filtered_questions:
                    break  # Exit loop if no more questions are available
                if i < config_data['hard']:
                    difficulty = 'Hard'
                elif i < config_data['hard'] + config_data['medium']:
                    difficulty = 'Medium'
                else:
                    difficulty = 'Easy'

                selected_question_index = random.randint(0, len(filtered_questions) - 1)
                selected_question = filtered_questions[selected_question_index]
                if selected_question not in exam and selected_question[2] == difficulty:
                    exam.append(selected_question)
                    total_points += int(selected_question[3])
                    difficulty_counts[selected_question[2]] += 1
                    filtered_questions.pop(selected_question_index)  # Remove the selected question from the pool
                    title_value = selected_question[1]
                    if title_value not in total_titles:
                        # Append the value if it doesn't exist
                        total_titles.append(title_value)

            # Validate that the total number of questions added matches the final question total
            if len(exam) != config_data['questions_amount']:
                continue  # Regenerate the exam if the total number of questions does not match the requirement

            # Calculate difficulty ratios based on the actual distribution of questions in the exam
            total_difficulties = sum(difficulty_counts.values())
            if total_difficulties == 0:  # Check for division by zero
                return None, total_points, {}  # Return early with empty ratios if no questions were added

            difficulty_ratios = {k: v / total_difficulties * 100 for k, v in difficulty_counts.items()}

            # Final checks
            if total_points != config_data['points']:
                continue  # Regenerate the exam if total points do not match the required points
            if len(total_titles) < config_data['minimum_titles']:
                continue  # Regenerate the exam if it does not meet the title requirement

            # If the exam passes all checks, including the difficulty ratio validation, break out of the loop
            break

        return exam, total_points, difficulty_ratios, total_titles
    except Exception as e:
        return f'LIST {e} && 520'


def read_api():
    try:
        with open('API.json') as f:
            config = json.load(f)

        api = config['api']
        username = config['username']
        password = config['password']
        exclusion_titles = config['exclusion_titles']
        return api, username, password, exclusion_titles
    except Exception as e:
        return f'LIST {e} && 520'


# Main execution flow
def exam_generator(username):
    try:
        # Read the CSV file and validate the config file
        questions = read_csv('Test.csv')
        if isinstance(questions, str):
            if check_for_LIST(questions):
                return questions

        config_data = read_config('db.config')
        if isinstance(config_data, str):
            if check_for_LIST(config_data):
                return config_data

        Exclude_list = um.get_excluded_titles(username)
        if isinstance(Exclude_list, str):
            if check_for_LIST(Exclude_list):
                return Exclude_list

        temp = generate_exam(questions, config_data, Exclude_list)
        if isinstance(temp, str):
            if check_for_LIST(temp):
                return temp
        else:
            exam, total_points, difficulty_ratios, total_titles = temp

        # Check if the file Exam.txt exists
        if os.path.exists('Exam.txt'):
            # If the file exists, delete it
            os.remove('Exam.txt')

        with open('Exam.txt', 'w') as file:
            # Write the data to the file
            if config_data['debug'] == 1:
                file.write("Debug mode is on.\n\n")
                for sublist in exam:
                    file.write(
                        f"{sublist[4]} & {sublist[0]} & Type: {sublist[1]} & Difficulty: {sublist[2]} & [{sublist[3]}]\n")

                    file.write(
                        f"{sublist[4]} & {sublist[0]} & Type: {sublist[1]} & Difficulty: {sublist[2]} & [{sublist[3]}]\n")
            else:
                for sublist in exam:
                    file.write(
                        f"{sublist[4]} & {sublist[0]} & [{sublist[3]}]\n")

                    file.write(
                        f"{sublist[4]} & {sublist[0]} & [{sublist[3]}]\n")

            file.write(f"\n\nTotal exam is out of {config_data['points']} points.")

        time.sleep(1)

        msg = create_excel_from_txt(config_data['debug'])
        if check_for_LIST(msg):
            return msg

        return fr'''DOWNLOAD
        <p>Exam Generated and saved to Exam.xlsx
        <p>Exam Generation info;
        <p>Total Points in exam: {total_points}
        <p>Number of Questions Included in exam: {len(exam)}
        <p>Total Titles Used in exam: {len(total_titles)}
        <p>Difficulty Ratio used: Hard: {round(difficulty_ratios['Hard'], 2)}%, Medium: {round(difficulty_ratios['Medium'], 2)}%, Easy: {round(difficulty_ratios['Easy'], 2)}%
        '''

    except Exception as e:
        return f'LIST {e} && 520'


def database_thread():
    """
    Reads the API configuration from the 'API.json' file and extracts the API, username, password, and exclusion titles.

    Returns:
    - tuple: A tuple containing the API, username, password, and exclusion titles.
    - str: If an exception occurs, returns a formatted error message.
    """
    try:
        def init():
            # Initialize the UserManager and API values
            temp = read_api()
            if isinstance(temp, str):
                if check_for_LIST(temp):
                    return temp
            else:
                api, username, password, exclusion_titles = temp

            if api == "REC":
                DATA = exam_generator(username)
            elif api == "RUG":
                DATA = um.create_db(username, exclusion_titles)
            elif api == "RUD":
                DATA = um.add_exclusion_db(username, exclusion_titles, password)
            elif api == "RUR":
                DATA = um.remove(username, password)
            else:
                DATA = "LIST Invalid API, 404"

            return DATA

        # Main startup
        return init()

    except Exception as e:
        return f'LIST {e} && 520'


um = UserManager(db_name='users.db')
if not os.path.exists("users.db"):
    um.create_db_initial()
