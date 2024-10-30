from flask import Flask, render_template, request, jsonify, redirect
from pymongo import MongoClient
from dotenv import load_dotenv
import os
import random
import string

# Load environment variables from a .env file
load_dotenv()

# Initialize Flask application
app = Flask(__name__)

# Setup MongoDB client and connect to the specified database and collection
client = MongoClient(os.getenv('MONGO_PATH'), int(os.getenv('MONGO_PORT')))
database = client.ShortUrlDatabase
ShortUrlDatabase = database.URLData

# Function to generate a random string for the short URL keyword
def generate_random_string(length=5):
    '''
    Generates a random string of specified length using uppercase and lowercase letters.
    '''
    print('Generating a random keyword')
    letters = string.ascii_letters
    random_string = ''.join(random.choices(letters, k=length))
    print('Keyword generated: ' + str(random_string))
    return random_string

# Function to check if a given keyword is already present in the database
def is_keyword_present(keyword):
    '''
    Checks if the specified keyword exists in the database.
    Returns True if the keyword is found, False otherwise.
    '''
    print('Checking if keyword is present in DB:', keyword)
    return ShortUrlDatabase.find_one({'keyword': keyword}) is not None

# Route for the home page
@app.route('/')
def home():
    '''
    Index page for URL Shortener (Project OSUS - Open Source URL Shortener).
    '''
    print('Home Page API Called, rendering template')
    return render_template('index.html')

# Route to render documentation page
@app.route('/documentation')
def documentation():          
    return render_template('documentation.html')

# Route to get the current URL of the application
@app.route('/getURL')
def currentURl():
    '''
    Returns the base URL of the current application instance.
    '''
    print('getURL API Called')
    current_url = request.host_url
    print('Current URL: ' + str(current_url))
    return f'The app is running on {current_url}'

# Route to handle URL shortening requests
@app.route('/shorten', methods=['POST'])
def shortenAPI():
    '''
    Accepts a long URL and an optional keyword, and returns a shortened URL.
    Generates a unique short URL if no keyword is provided.
    '''
    print('URL Shorten Called')
    print('Mongo Connection: ' + str(os.getenv('MONGO_PATH')[:6]))
    
    # Process only POST requests
    if request.method == 'POST':
        data = request.json or {}
        longUrl = data.get("longUrl")  # Get long URL from request data
        keyword = data.get("keyword") or generate_random_string()  # Get keyword or generate one

        # Logs
        print('Long URL Received: ' + str(longUrl))
        print('Keyword Received: ' + str(keyword))

        # Return an error if long URL is missing
        if not longUrl:
            return jsonify({'error': 'No long URL provided'}), 400

        # Check for duplicate keyword in the database
        if is_keyword_present(keyword):
            print('Keyword is present, throwing error')
            return jsonify({'error': 'Keyword already exists, choose a different one'}), 409

        # Insert the new short URL mapping into the database
        ShortUrlDatabase.insert_one({'keyword': keyword, 'url': longUrl, 'clicks': 0})
        print('DB insert successful')
        
        # Construct the shortened URL and return it in JSON format
        shortUrl = f"{request.host_url}{keyword}"
        return jsonify({'shortUrl': shortUrl})

    # Return an error if GET request is used on the shorten endpoint
    if request.method == 'GET':
        print('Called get method on shorten end-point, throwing error')
        return "GET Method Not Allowed On This End Point"

# Route for analytics (not fully implemented)
@app.route('/analytics', methods=['GET', 'POST'])
def analyticsAPI():
    '''
    Returns analytics for a specific keyword if provided.
    Currently under development.
    '''
    print('Analytics API Called')
    return 'Under Development'

# Route to check if the application is running and accessible
@app.route('/heartbeat')
def hearBeat():
    '''
    Simple health check endpoint to confirm that the service is running.
    '''
    print('Heartbeat API called')
    return 'The website is up'

# Route to handle short URL redirection
@app.route('/<keyword>')
def reroute(keyword):
    '''
    Redirects to the original long URL based on the provided short URL keyword.
    Increments the click count for the keyword in the database.
    '''
    print('Clicked on shortURL')
    print('Finding the URL Keyword')
    print('Mongo Connection: ' + str(os.getenv('MONGO_PATH')[:6]))
    
    # Find and increment the click count for the keyword, if found
    item = ShortUrlDatabase.find_one_and_update(
        {'keyword': keyword},
        {'$inc': {'clicks': 1}}
    )

    # Redirect to the long URL if found, otherwise return error message
    if item:
        print('Short URL <> Long URL mapping found in DB')
        redirection = item['url']
        print('Redirecting to long URL: ' + str(redirection))
        return redirect(redirection, code=302)
    
    print('Link Not Found in DB')
    return "Link Not Found", 404

# Main function to run the Flask app
if __name__ == '__main__':
    app.run(debug=True, port=5000)
