from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError, ProgrammingError
import os
import sys
import pandas as pd
from tabulate import tabulate
from dotenv import load_dotenv
from IPython.display import display, Markdown
import pymysql
from datetime import time, datetime
import json
import secrets
# note to self: add ?token=285247389 for user authentication

# to run this file, must go to myEnv->Scripts at type "activate" in the command line
# then go to src and run "python app.py"
# for dates, use DATE_FORMAT(attributeName, '%M %D, %Y') AS attributeName
# for times, use TIME_FORMAT(attributeName, '%H:%i') AS attributeName

# the following code is from the hw9.qmd file

# configuring .env
# make sure to add FLASK_DATABASE to your .env file
config_map = {
    'user':'CMSC508_USER',
    'password':'CMSC508_PASSWORD',
    'host':'CMSC508_HOST',
    'database':'FLASK_DATABASE'
}
# load and store credentials
load_dotenv()
config = {}
for key in config_map.keys():
    config[key] = os.getenv(config_map[key])
flag = False
for param in config.keys():
    if config[param] is None:
        flag = True
        print(f"Missing {config_map[param]} in .env file")

# build a sqlalchemy engine string
engine_uri = f"mysql+pymysql://{config['user']}:{config['password']}@{config['host']}/{config['database']}"

# connecting to the database
try:
    conn = create_engine(engine_uri)
except ArgumentError as e:
    print(f"create_engine: Argument Error: {e}")
    #sys.exit(1)
except NoSuchModuleError as e:
    print(f"create_engine: No Such Module Error: {e}")
    #sys.exit(1)
except Exception as e:
    print(f"create_engine: An error occurred: {e}")
    #sys.exit(1)

# helper routines
def my_sql_statement( statement ):
    """ used with DDL, when the statement doesn't return any results. """
    try:
        with conn.begin() as x:
            x.execute(text(statement))
            x.commit()
        result = ""
    except Exception as e:
        result = f"Error: {str(e)}"
    return result


def testExecution(executionResult):
    rows = executionResult.fetchall()
    print("rows: ", rows)
    print()
    if rows:
        columns = executionResult.keys()
        print("columns: ", columns)
        return [dict(zip(columns, row)) for row in rows]
    else:
        return 0

def testKey(user_key):
    query = text("SELECT account_type FROM user WHERE user_key = :user_key;")
    result = db.session.execute(query, {'user_key': user_key})
    user_data = [{'account_type': user.account_type} for user in result]
    if(not user_data):
        return 0
    return user_data[0].get('account_type')

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{config['user']}:{config['password']}@{config['host']}/{config['database']}"
db = SQLAlchemy(app)

# API Methods:

@app.route('/login', methods=['PUT', 'PATCH'])
def login():
    data = request.json
    id = data.get('id')
    user_name = data.get('username')
    password = data.get('password')
    if(not id and not user_name):
        return jsonify({'error': 'Missing username or id.'}), 400
    if(not password):
        return jsonify({'error': 'Missing password.'}), 400
    query = text("SELECT * FROM user WHERE (user_name = :user_name OR id = :id) AND password = :password;")
    result = db.session.execute(query, {'user_name': user_name, 'id': id, 'password': password})
    user_data = [{'user_key': user.user_key} for user in result]
    if(not user_data):
        return jsonify({'error': 'Incorrect login credentials.'}), 400
    print("USER = ", user_data[0])
    if(user_data[0].get('user_key')):
        return jsonify({'error': 'You''re already logged in.'}), 400
    user_key = secrets.token_urlsafe(32)
    query = text("UPDATE user SET user_key = :user_key WHERE (user_name = :user_name OR id = :id) AND password = :password;")
    db.session.execute(query, {'user_key': user_key,'user_name': user_name, 'id': id, 'password': password})
    db.session.commit()
    myMessage = "You are now logged in. Your user key is " + str(user_key) + " , which you must use to access the database."
    return jsonify(message=myMessage), 200

@app.route('/logout', methods=['PUT', 'PATCH'])
def logout():
    data = request.json
    #id = data.get('id')
    #user_name = data.get('username')
    #password = data.get('password')
    #if(not id and not user_name):
        #return jsonify({'error': 'Missing username or id.'}), 400
    #if(not password):
        #return jsonify({'error': 'Missing password.'}), 400
    user_key = data.get('key')
    if(not user_key):
        return jsonify({'error': 'No key provided.'}), 400
    if(not testKey(user_key)):
        return jsonify({'error': 'Invalid key, or invalid key.'}), 400
    query = text("UPDATE user SET user_key = NULL WHERE user_key = :user_key;")
    db.session.execute(query, {'user_key': user_key})
    db.session.commit()
    myMessage = "You are now logged out."
    return jsonify(message=myMessage), 200

# Show users (with filter)
@app.route('/users', methods=['GET'])
def get_users():
    username_regex = request.args.get('username', None)
    account_type_regex = request.args.get('account_type', None)
    user_key = request.args.get('key', None)
    if(not user_key):
        return jsonify({'error': 'No key provided.'}), 400
    if(not testKey(user_key)):
        print(testKey(user_key))
        return jsonify({'error': 'Invalid key.'}), 400
    query = text("SELECT ID, user_name, account_type FROM user WHERE"
                 "(user.user_name REGEXP :username_regex OR :username_regex IS NULL) AND"
                 "(user.account_type REGEXP :account_type_regex OR :account_type_regex IS NULL);")
    result = db.session.execute(query, {'username_regex': username_regex,'account_type_regex': account_type_regex})
    user_list = [{'ID': user.ID, 'Username': user.user_name, 'Account type': user.account_type} for user in result]
    if(user_list):
        return jsonify(user_list), 200
    return jsonify({'error': 'No users fulfill this criteria.'}), 404

# Find user by id
@app.route('/users/<int:user_id>', methods=['GET'])
def get_user_by_id(user_id):
    user_key = request.args.get('key', None)
    if(not user_key):
        return jsonify({'error': 'No key provided.'}), 400
    if(not testKey(user_key)):
        print(testKey(user_key))
        return jsonify({'error': 'Invalid key.'}), 400
    query = text("SELECT ID, user_name, account_type FROM user WHERE id = :user_id;")
    user_list = testExecution(db.session.execute(query, {'user_id': user_id}))
    if(user_list):
        return jsonify(user=user_list)
    return jsonify(message='User not found.'), 404

# Artist methods:

@app.route('/artists', methods=['GET'])
def get_artists():
    name_regex = request.args.get('name', None)
    birth_date_regex = request.args.get('birth_date', None)
    debut_date_regex = request.args.get('debut_date', None)
    user_key = request.args.get('key', None)
    if(not user_key):
        return jsonify({'error': 'No key provided.'}), 400
    if(not testKey(user_key)):
        print(testKey(user_key))
        return jsonify({'error': 'Invalid key.'}), 400
    query = text("SELECT ID, name, DATE_FORMAT(birth_date, '%M %D, %Y') AS birth_date, DATE_FORMAT(debut_date, '%M %D, %Y') AS debut_date, description, user_ID FROM artist WHERE"
                 "(artist.name REGEXP :name_regex OR :name_regex IS NULL) AND"
                 "(artist.birth_date REGEXP :birth_date_regex OR :birth_date_regex IS NULL);")
    result = db.session.execute(query, {'name_regex': name_regex,'birth_date_regex': birth_date_regex, 'debut_date_regex': debut_date_regex})
    user_list = [{'ID': artist.ID, 'Name': artist.name, 'Birth date': artist.birth_date, 'Description': artist.description, 'Debut date': artist.debut_date, 'User ID': artist.user_ID} for artist in result]
    if(user_list):
        return jsonify(user_list), 200
    return jsonify({'error': 'No users fulfill this criteria.'}), 404

# Create a user with the given name, password, and the account type
# If the user exists with the given user name, then return error
# Create a user with the given, name, password, and account type
@app.route('/create_user', methods=['POST'])
def create_user():
    # Get the new user's name, password, and account type from the request
    data = request.json
    user_name = data.get('user_name', None)
    user_password = data.get('password', None)
    user_account_type = data.get('account_type', None)

    # If the request has name, password, and the account type for the user:
    # Check if there's already a user with the given name.
    # If there's no user already with the given name, then create it.        
    if user_name:
        if user_password:
            if user_account_type:

                # Check if there's any user with the asked name and set it to "database_user"
                result = db.session.execute(text("SELECT * FROM user WHERE user_name = :user_name"), {"user_name": user_name}).fetchone()

                # If the user already exists, print a message to the user to try a different name
                if result:
                    return jsonify({'message': 'A user with the given name already exists. Please try a different name.'})
                
                # If a user doesn't exist with the given name, then create it
                else:
                    db.session.execute(text("INSERT INTO user (user_name, password, account_type) VALUES (:user_name, :password, :account_type)"), {"user_name": user_name, "password": user_password, "account_type": user_account_type})
                    db.session.commit()

                    # Print success message
                    return jsonify({'message': 'The user is created successfully'})
            else:
                return jsonify({'error': "The required the account type is not provided."})
        else:
            return jsonify({'error': "The required password is not provided."})
    # If the request has no name/password/account type, then print an error 
    else:
        return jsonify({'error': "The required user name is not provided."})

# To create an artist
@app.route('/create_artist', methods=['POST'])
def create_artist():
    
    # Get artist details from the request
    name = request.json.get('name');
    birth_date = request.json.get('birth_date');
    # If the debut_date isn't given, set it to empty
    debut_date = request.json.get('debut_date', datetime.now());
    # If the description isn't given, set it to empty
    description = request.json.get('description', '');
    user_id = request.json.get('user_ID');

    if name is not None:
        if birth_date is not None:
            if user_id is not None:
                # Check if there's a user with the given user_id before creating an artist
                database_user_account_type = db.session.execute(text("SELECT account_type FROM user WHERE ID = :user_id"), {"user_id": user_id}).fetchone();
                # If there's no user ID before we create an artist account, then don't create the artist since user ID is needed
                if not database_user_account_type:
                    return {'message': 'There\'s no user account with the given ID. Please create an user account before creating an artist account.'};    

                # Create "database_artist" to check if there's already an artist with the given name. If there's return message and don't create the artist
                database_artist = db.session.execute(text("SELECT * FROM artist WHERE name = :name"), {"name": name},).fetchone();
                # If the artist exists, then display error message
                if database_artist:
                    return jsonify({'message': 'An artist with the given name already exists. Please try a different name.'});
                
                # If there's no artist with the given name, then create the artist if its user account's account type is 'artist'
                if not database_artist:
                    # Check if its user's account type is artist
                    if database_user_account_type[0] == 'artist':
                        db.session.execute(text("INSERT INTO artist (name, birth_date, description, debut_date, user_ID) VALUES (:name, :birth_date, :description, :debut_date, :user_ID)"),{"name": name, "birth_date": birth_date, "description": description, "debut_date": debut_date, "user_ID": user_id});
                        db.session.commit();

                        # Print the success message
                        success_message = ('The artist is created successfully');
                        return jsonify({'message': success_message});
                    
                    # If the account's user account's account type is not 'artist', then don't create the artist account
                    else:
                        return jsonify({'message':f"The account type is not artist, but it's {database_user_account_type[0]}"});
            
    # If any of the required info is not in the request, then print error.
            else:
                return jsonify({'error': "The required artist's user ID is not provided to create the artist."});    
        else:
            return jsonify({'error': "The required artist's birth date is not provided to create the artist."});
    else:
        return jsonify({'error': "The required artist name is not provided to create the artist."});

# Gets the artist's info by the ID
@app.route('/artists/<int:artist_id>', methods=['GET'])
def get_artist_by_id(artist_id):
    query = text("SELECT * FROM artist WHERE id = :artist_id;")
    result = db.session.execute(query, {'artist_id': artist_id})
    row = result.first()
    if row:
        columns = result.keys()
        artist_data = dict(zip(columns, row));
        return jsonify(artist=artist_data);
    else:
        return jsonify(message='The artist is not found');

# Deletes the user account by user's ID
@app.route('/delete_user/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    
    # Set "database_user" to the user account we want to delete
    database_user = db.session.execute(text("SELECT * FROM user WHERE ID = :user_id"), {"user_id": user_id}).fetchone();
    if not database_user:
        return jsonify({'message': 'The user is not found'});
    try:
        database_user_account_type_DB = db.session.execute(text("SELECT account_type FROM user WHERE ID = :user_id"), {"user_id": user_id}).fetchone()
        database_user_account_type = database_user_account_type_DB[0];
        
      #  print()
        # If the user doesn't exist, return a message
        if database_user:
            # If the user exists, delete the user
            db.session.execute(text("DELETE FROM user WHERE ID = :user_id"), {"user_id": user_id})
            db.session.commit()

            # If the user's account type is an artist type, delete its artist account too
            if database_user_account_type == 'artist':
                db.session.execute(text("DELETE FROM artist WHERE user_ID = :user_id"), {"user_id": user_id});
                
            # Print success message
            return jsonify({'message': 'The user is deleted successfully'});
        
        # If the user doesn't exist with the given ID, then return a message
    except Exception as e:
        return jsonify({'message': str(e)});


# Deletes the artist account by ID
@app.route('/delete_artist/<int:artist_id>', methods=['DELETE'])
def delete_artist(artist_id):
        
    # Set "database_artist" to the artist with the given ID
    database_artist = db.session.execute(text("SELECT * FROM artist WHERE ID = :artist_id"), {"artist_id": artist_id}).fetchone()

    # If the artist exists with the given ID
    if database_artist:
        
        # Delete the artist
        db.session.execute(text("DELETE FROM artist WHERE ID = :artist_id"), {"artist_id": artist_id});
        db.session.commit();

        # Print a success message
        return jsonify({'message': 'The artist account is deleted successfully'});
    # If the artist doesn't exist with the given ID, then return message
    else:
        return jsonify({'message': 'The artist account is not found'});


# Updates the user's info by ID
@app.route('/update_user/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    # Set "database_user" to the user with the given ID
    database_user = db.session.execute(text("SELECT * FROM user WHERE ID = :user_id"), {"user_id": user_id}).fetchone()

    # If the user doesn't exist, then return an error message
    if database_user is None:
        return jsonify({'message': 'There\'s no user with the given ID'})

    data = request.json
    # Get the changes from the request JSON or use the existing values if not provided
    new_user_name = data.get('user_name', database_user[1])
    new_password = data.get('password', database_user[2])
    new_account_type = data.get('account_type', database_user[3])

    # Check if the account type is changed from 'artist' to 'premium' or 'free'
    if database_user[3] == 'artist' and new_account_type in ['premium', 'free']:
        # Delete associated artist account
        db.session.execute(text("DELETE FROM artist WHERE user_ID = :user_id"), {"user_id": user_id})

    # Update the user's information
    db.session.execute(
        text("UPDATE user SET user_name = :user_name, password = :password, account_type = :account_type WHERE ID = :user_id"),
        {"user_name": new_user_name, "password": new_password, "account_type": new_account_type, "user_id": user_id}
    )
    db.session.commit()

    # Print a success message
    return jsonify({'message': 'The user is updated successfully'})

@app.route('/update_artist/<int:artist_id>', methods=['PUT'])
def update_artist(artist_id):
    # Fetch the artist details from the database
    artist_data = db.session.execute(
        text("SELECT * FROM artist WHERE ID = :artist_id"),
        {"artist_id": artist_id}
    ).fetchone()

    # If the artist doesn't exist, return an error message
    if not artist_data:
        return jsonify({'message': 'There\'s no artist with the given ID'})

    # Get the data from the request JSON or use the existing values if not provided
    data = request.json
    new_name = data.get('name', artist_data[1])
    new_birth_date = data.get('birth_date', artist_data[2])
    new_description = data.get('description', artist_data[3])
    new_debut_date = data.get('debut_date', artist_data[4])
    new_user_id = data.get('user_ID', artist_data[5])

    # Check if the user with the new user_ID exists
    user_data = db.session.execute(
        text("SELECT account_type FROM user WHERE ID = :user_id"),
        {"user_id": new_user_id}
    ).fetchone()

    if not user_data:
        return jsonify({'message': 'There\'s no user with the given user ID'})

    # Check if the user's account type is 'artist'
    if user_data[0] == 'artist':
        # Update the artist information
        db.session.execute(
            text("UPDATE artist SET name = :name, birth_date = :birth_date, debut_date = :debut_date, description = :description, user_ID = :user_id WHERE ID = :artist_id"),
            {"name": new_name, "birth_date": new_birth_date, "debut_date": new_debut_date, "description": new_description, "user_id": new_user_id, "artist_id": artist_id}
        )
        db.session.commit()
        return jsonify({'message': 'The artist is updated successfully'})
    else:
        return jsonify({'message': 'The account type is not artist'})

# Song methods:

@app.route('/songs', methods=['GET'])
def get_songs():
    name_regex = request.args.get('name')
    tempo_regex = request.args.get('tempo')
    key_regex = request.args.get('key')
    plays_regex = request.args.get('plays')
    duration_regex = request.args.get('duration')
    artist_regex = request.args.get('artist')
    artist_id_regex = request.args.get('artist_id')
    album_regex = request.args.get('album')
    album_id_regex = request.args.get('album_id')
    user_key = request.args.get('user_key', None)
    if(not user_key):
        return jsonify({'error': 'No key provided.'}), 400
    if(not testKey(user_key)):
        print(testKey(user_key))
        return jsonify({'error': 'Invalid key.'}), 400
    query = text("SELECT song.ID, song.name, tempo, song_key, plays, TIME_FORMAT(song.duration, '%H:%i') AS duration, song.artist_ID, artist.name AS artist_name, album_ID, album.name AS album_name FROM song JOIN artist ON song.artist_ID = artist.ID JOIN album ON song.album_ID = album.ID WHERE"
                 "(song.name REGEXP :name_regex OR :name_regex IS NULL) AND"
                 "(song.tempo REGEXP :tempo_regex OR :tempo_regex IS NULL) AND"
                 "(song.song_key REGEXP :key_regex OR :key_regex IS NULL) AND"
                 "(song.plays REGEXP :plays_regex OR :plays_regex IS NULL) AND"
                 "(song.duration REGEXP :duration_regex OR :duration_regex IS NULL) AND"
                 "(artist.name REGEXP :artist_regex OR :artist_regex IS NULL) AND"
                 "(artist.ID REGEXP :artist_id_regex OR :artist_id_regex IS NULL) AND"
                 "(album.name REGEXP :album_regex OR :album_regex IS NULL) AND"
                 "(album.ID REGEXP :album_id_regex OR :album_id_regex IS NULL);")
    result = db.session.execute(query, {'name_regex': name_regex,'tempo_regex': tempo_regex,'key_regex': key_regex,'plays_regex': plays_regex,'duration_regex': duration_regex,'artist_regex': artist_regex,'artist_id_regex': artist_id_regex, 'album_regex': album_regex,'album_id_regex': album_id_regex})
    songs_list = [{'Song ID': song.ID, 'Name': song.name, 'Artist ID': song.album_ID, 'Artist': song.artist_name, 'Album ID': song.album_ID, 'Album': song.album_name, 'Duration': song.duration, 'Plays': song.plays, 'Tempo': song.tempo, 'Key': song.song_key} for song in result]
    if(songs_list):
        return jsonify(songs_list), 200
    return jsonify({'error': 'No songs fulfill this criteria.'}), 404

@app.route('/songs/<int:song_id>', methods=['GET'])
def get_song_by_id(song_id):
    user_key = request.args.get('key', None)
    if(not user_key):
        return jsonify({'error': 'No key provided.'}), 400
    if(not testKey(user_key)):
        print(testKey(user_key))
        return jsonify({'error': 'Invalid key.'}), 400
    query = text("SELECT ID, name, tempo, song_key, plays, TIME_FORMAT(duration, '%H:%i') AS duration, artist_ID, album_ID FROM song WHERE id = :song_id;")
    song_list = testExecution(db.session.execute(query, {'song_id': song_id}))
    if(song_list):
        return jsonify(songs=song_list), 200
    return jsonify({'error': 'Song not found.'}), 404

@app.route('/add_song', methods=['POST'])
def add_song():
    data = request.json
    name = data.get('name')
    tempo = data.get('tempo', None)
    song_key = data.get('key', None)
    plays = data.get('plays', 0)
    duration = data.get('duration')
    album_ID = data.get('album_id')
    user_key = data.get('user_key', None)
    if(not user_key):
        return jsonify({'error': 'No key provided.'}), 400
    if(testKey(user_key) != 'artist'):
        print(testKey(user_key))
        return jsonify({'error': 'Invalid key.'}), 400
    if not name or not duration or not album_ID:
        return jsonify({'error': 'Missing required fields for adding a song (name, duration, album_id)'}), 400
    if(album_ID):
        query = text("SELECT album.name FROM user JOIN artist ON user.ID=artist.user_ID JOIN album ON album.artist_ID=artist_ID WHERE album.ID=:album_ID AND user.user_key = :user_key;")
        song_data = testExecution(db.session.execute(query, {'album_ID': album_ID, 'user_key': user_key}))
        if(not song_data):
            return jsonify({'error': 'Song''s album id cannot be changed to the given album id.'}), 404
    query = text("SELECT artist.ID FROM artist JOIN user ON artist.user_ID=user.ID WHERE user.user_key = :user_key")
    result = db.session.execute(query, {'user_key': user_key})
    artist_ID = [{'ArtistID': artist.ID} for artist in result][0].get('ArtistID')
    artist_ID = 1
    print("ARTIST ID = ", artist_ID)
    query = text("INSERT INTO song (name, tempo, song_key, plays, duration, artist_ID, album_ID) VALUES (:name, :tempo, :song_key, :plays, :duration, :artist_ID, :album_ID);")
    db.session.execute(query, {'name': name, 'tempo': tempo, 'song_key': song_key, 'plays': plays, 'duration': duration, 'artist_ID': artist_ID, 'album_ID': album_ID})
    db.session.commit()
    query = text("SELECT MAX(ID) AS ID FROM song")
    result = db.session.execute(query)
    song_id = [{'SongID': song.ID} for song in result]
    myMessage = "Added new song with ID = " + str(song_id[0].get('SongID')) + "."
    return jsonify(message=myMessage), 201

@app.route('/delete_song/<int:song_id>', methods=['DELETE'])
def delete_song(song_id):
    user_key = request.args.get('key', None)
    if(not user_key):
        return jsonify({'error': 'No key provided.'}), 400
    if(testKey(user_key) != 'artist'):
        print(testKey(user_key))
        return jsonify({'error': 'Invalid key.'}), 400
    query = text("SELECT song.name FROM song JOIN artist ON song.artist_ID=artist.ID JOIN user ON artist.user_ID=user.ID WHERE song.ID = :song_id AND user.user_key = :user_key;")
    song_data = testExecution(db.session.execute(query, {'song_id': song_id, 'user_key': user_key}))
    if(not song_data):
        return jsonify({'error': 'Song does not exist or cannot be deleted.'}), 404
    query = text("DELETE FROM song WHERE ID = :song_id;")
    try:
        with conn.begin() as x:
            x.execute(query, {'song_id': song_id})
            x.commit()
        result = ""
    except Exception as e:
        result = f"Error: {str(e)}"
    if result:
        return jsonify({'error': 'Invalid URL'}), 404
    result = "Song " + str(song_id) + " has been deleted."
    return jsonify(message=result), 201

@app.route('/update_song/<int:song_id>', methods=['PUT', 'PATCH'])
def update_song(song_id):
    print("song id = ", song_id)
    data = request.json
    name = data.get('name', None)
    tempo = data.get('tempo', None)
    song_key = data.get('key', None)
    plays = data.get('plays', None)
    duration = data.get('duration', None)
    album_ID = data.get('album_id', None)
    user_key = data.get('user_key', None)
    if(not user_key):
        return jsonify({'error': 'No key provided.'}), 400
    if(testKey(user_key) != 'artist'):
        print(testKey(user_key))
        return jsonify({'error': 'Invalid key.'}), 400
    if not name and not tempo and not song_key and not plays and not duration and not album_ID:
        return jsonify({'error': 'No values provided to update)'}), 400
    query = text("SELECT song.name FROM song JOIN artist ON song.artist_ID=artist.ID JOIN user ON artist.user_ID=user.ID WHERE song.ID = :song_ID AND user.user_key = :user_key;")
    song_data = testExecution(db.session.execute(query, {'song_ID': song_id, 'user_key': user_key}))
    if(not song_data):
        return jsonify({'error': 'Song does not exist or cannot be deleted.'}), 404
    if(album_ID):
        query = text("SELECT name FROM user JOIN artist ON user.ID=artist.user_ID JOIN album ON album.artist_ID=artist.ID WHERE album.ID=:album_ID AND user.user_key = :user_key;")
        song_data = testExecution(db.session.execute(query, {'album_ID': album_ID, 'user_key': user_key}))
        if(not song_data):
            return jsonify({'error': 'Song''s album id cannot be changed to the given album id.'}), 404
    query = text("UPDATE song SET "
                 "name = CASE WHEN :name is NULL THEN name ELSE :name END,"
                 "tempo = CASE WHEN :tempo is NULL THEN tempo ELSE :tempo END,"
                 "song_key = CASE WHEN :song_key is NULL THEN song_key ELSE :song_key END,"
                 "plays = CASE WHEN :plays is NULL THEN plays ELSE :plays END,"
                 "duration = CASE WHEN :duration is NULL THEN duration ELSE :duration END,"
                 "album_ID = CASE WHEN :album_ID is NULL THEN album_ID ELSE :album_ID END "
                 "WHERE ID = :song_id;")
    db.session.execute(query, {'name': name, 'tempo': tempo, 'song_key': song_key, 'plays': plays, 'duration': duration, 'artist_ID': artist_ID, 'album_ID': album_ID, 'song_id': song_id})
    db.session.commit()
    myMessage = "Song " + str(song_id) + " has been updated"
    return jsonify(message=myMessage), 200


# Album methods:

@app.route('/albums', methods=['GET'])
def get_albums():
    # get parameters 
    id_regex = request.args.get('id')
    name_regex = request.args.get('name')
    record_label_regex = request.args.get('record_label')
    genre_regex = request.args.get('genre')
    release_date_regex = request.args.get('release_date')
    classification_regex = request.args.get('classification')
    duration_regex = request.args.get('duration')
    artist_id_regex = request.args.get('artist_id')

    # build the query 
    query = text("SELECT album.ID, album.name, album.record_label, album.genre, album.release_date, album.classification, TIME_FORMAT(album.duration, '%H:%i') AS duration, album.artist_ID, artist.name AS artist_name FROM album JOIN artist ON album.artist_ID = artist.ID WHERE"
                "(album.ID REGEXP :id_regex OR :id_regex IS NULL) AND"
                "(album.name REGEXP :name_regex OR :name_regex IS NULL) AND"
                "(album.record_label REGEXP :record_label_regex OR :record_label_regex IS NULL) AND"
                "(album.genre REGEXP :genre_regex OR :genre_regex IS NULL) AND"
                "(album.release_date REGEXP :release_date_regex OR :release_date_regex IS NULL) AND"
                "(album.classification REGEXP :classification_regex OR :classification_regex IS NULL) AND"
                "(album.duration REGEXP :duration_regex OR :duration_regex IS NULL) AND"
                "(album.artist_ID REGEXP :artist_id_regex OR :artist_id_regex IS NULL);")

    # execute the query 
    result = testExecution(db.session.execute(query, {
        'id_regex': id_regex,
        'name_regex': name_regex,
        'record_label_regex': record_label_regex,
        'genre_regex': genre_regex,
        'release_date_regex': release_date_regex,
        'classification_regex': classification_regex,
        'duration_regex': duration_regex,
        'artist_id_regex': artist_id_regex,
    }))

    # get result
    albums_list = [{
        'ID': album['ID'],
        'name': album['name'],
        'record_label': album['record_label'],
        'genre': album['genre'],
        'release_date': album['release_date'],
        'classification': album['classification'],
        'duration': album['duration'],
        'artist_ID': album['artist_ID'],
        'artist_name': album['artist_name']
    } for album in result]

    if albums_list:
        return jsonify(albums_list)
    return jsonify(message='No albums match the criteria.'), 404


@app.route('/albums/<int:album_id>', methods=['GET'])
def get_album_by_id(album_id):
    query = text("SELECT ID, name, record_label, genre, release_date, classification, TIME_FORMAT(duration, '%H:%i') AS duration, artist_ID FROM album WHERE ID = :album_id;")
    album_list = testExecution(db.session.execute(query, {'album_id': album_id}))

    if album_list:
        return jsonify(albums=album_list)
    return jsonify(message='Album not found.'), 404


@app.route('/albums/artist/<int:artist_id>', methods=['GET'])
def get_albums_by_artist_id(artist_id):
    query = text("SELECT ID, name, record_label, genre, release_date, classification, TIME_FORMAT(duration, '%H:%i') AS duration, artist_ID FROM album WHERE artist_ID = artist_id;")
    album_list = testExecution(db.session.execute(query, {'artist_id': artist_id}))

    if album_list:
        return jsonify(albums=album_list)
    return jsonify(message='No albums found for the artist ID.'), 404

@app.route('/add_album', methods=['POST'])
def add_album():
    # request JSON
    data = request.json
    name = data.get('name')
    record_label = data.get('record_label')
    genre = data.get('genre', None)
    release_date = data.get('release_date', datetime.now().strftime('%Y-%m-%d'))
    classification = data.get('classification')
    duration = data.get('duration')
    artist_ID = data.get('artist_ID')

    if not name or not record_label or not classification or not duration or not artist_ID:
        return jsonify({'error': 'Missing required fields for adding an album (name, record_label, classification, duration, artist_ID)'}), 400

    # build query
    query = text("INSERT INTO album (name, record_label, genre, release_date, classification, duration, artist_ID) VALUES (:name, :record_label, :genre, :release_date, :classification, :duration, :artist_ID);")
    
    # execute the query to insert a new album
    db.session.execute(query, {'name': name, 'record_label': record_label, 'genre': genre, 'release_date': release_date, 'classification': classification, 'duration': duration, 'artist_ID': artist_ID})
    db.session.commit()

    # get new album
    query_get = text("SELECT ID, name, record_label, genre, release_date, classification, TIME_FORMAT(duration, '%H:%i') AS duration, artist_ID FROM album WHERE name = :name;")
    album_list = testExecution(db.session.execute(query_get, {'name': name}))

    return jsonify({'message': 'Album added successfully', 'album': album_list[0]}), 201

@app.route('/update_album/<int:album_id>', methods=['PUT'])
def update_album(album_id):
    # request JSON
    data = request.json
    name = data.get('name')
    record_label = data.get('record_label')
    genre = data.get('genre')
    release_date = data.get('release_date')
    classification = data.get('classification')
    duration = data.get('duration')
    artist_ID = data.get('artist_ID')

    if not name or not record_label or not classification or not duration or not artist_ID:
        return jsonify({'error': 'Missing required fields for updating an album (name, record_label, classification, duration, artist_ID)'}), 400

    query = text("UPDATE album SET name = :name, record_label = :record_label, genre = :genre, release_date = :release_date, classification = :classification, duration = :duration, artist_ID = :artist_ID WHERE ID = :album_id;")
    db.session.execute(query, {'name': name, 'record_label': record_label, 'genre': genre, 'release_date': release_date, 'classification': classification, 'duration': duration, 'artist_ID': artist_ID, 'album_id': album_id})
    db.session.commit()

    logging.info('Executing update_album method...')
    logging.debug(f'Input data: {data}')

    query_get = text("SELECT ID, name, record_label, genre, release_date, classification, TIME_FORMAT(duration, '%H:%i') AS duration, artist_ID FROM album WHERE ID = :album_id;")
    album_list = testExecution(db.session.execute(query_get, {'album_id': album_id}))

    return jsonify({'message': 'Album updated successfully', 'album': album_list[0]}), 200

@app.route('/albums/<int:album_id>', methods=['DELETE'])
def delete_album(album_id):
    # set "database_album" to the album with given ID
    database_album = db.session.execute(text("SELECT * FROM album WHERE ID = :album_id"), {"album_id": album_id}).fetchone()

    # if database_album exists with given ID
    if database_album:
        # Delete the album
        db.session.execute(text("DELETE FROM album WHERE ID = :album_id"), {"album_id": album_id})
        db.session.commit()

        return jsonify({'message': 'The album is deleted successfully'})

    else:
        return jsonify({'message': 'album not found'})
    
# Playlist methods:

@app.route('/playlists', methods=['GET'])
def get_playlists():
    # get parameters 
    id_regex = request.args.get('id')
    name_regex = request.args.get('name')
    description_regex = request.args.get('description')
    duration_regex = request.args.get('duration')
    #user_regex = request.args.get('user')
    user_id_regex = request.args.get('user_id')

    # build the query 
    query = text("SELECT playlist.ID, playlist.name, playlist.description, TIME_FORMAT(playlist.duration, '%H:%i') AS duration, playlist.user_ID, user.user_name AS user_name FROM playlist JOIN user ON playlist.user_ID = user.ID WHERE"
                "(playlist.ID REGEXP :id_regex OR :id_regex IS NULL) AND"
                "(playlist.name REGEXP :name_regex OR :name_regex IS NULL) AND"
                "(playlist.description REGEXP :description_regex OR :description_regex IS NULL) AND"
                "(playlist.duration REGEXP :duration_regex OR :duration_regex IS NULL) AND"
                #"(user.user_name REGEXP :user_regex OR user_regex IS NULL) AND" 
                "(user.ID REGEXP :user_id_regex OR :user_id_regex IS NULL);")
    # execute the query 
    result =  testExecution(db.session.execute(query, {'id_regex': id_regex, 'name_regex': name_regex, 'description_regex': description_regex, 'duration_regex': duration_regex, 'user_id_regex': user_id_regex}))


    # get result
    #playlists_list = [{'ID': playlist.ID, 'name': playlist.name, 'description': playlist.description, 'duration': playlist.duration, 'user_ID': playlist.user_ID, 'Username': playlist.user_name} for playlist in result]
    playlists_list = [{'ID': playlist['ID'], 'name': playlist['name'], 'description': playlist['description'], 'duration': playlist['duration'], 'user_ID': playlist['user_ID'], 'Username': playlist['user_name']} for playlist in result]

    if playlists_list:
        return jsonify(playlists_list)
    return jsonify(message='No playlists match the criteria.'), 404

@app.route('/playlists/<int:playlist_id>', methods=['GET'])
def get_playlist_by_id(playlist_id):
    query = text("SELECT ID, name, description, TIME_FORMAT(duration, '%H:%i') AS duration, user_ID FROM playlist WHERE id = :playlist_id;")
    playlist_list = testExecution(db.session.execute(query, {'playlist_id': playlist_id}))
    if playlist_list:
        return jsonify(playlists=playlist_list)
    return jsonify(message='Playlist not found.'), 404

@app.route('/playlists/user/<int:user_id>', methods=['GET'])
def get_playlists_by_user_id(user_id):
    query = text("SELECT ID, name, description, TIME_FORMAT(duration, '%H:%i') AS duration, user_ID FROM playlist WHERE user_ID = :user_id;")
    playlist_list = testExecution(db.session.execute(query, {'user_id': user_id}))
    if playlist_list:
        return jsonify(playlists=playlist_list)
    return jsonify(message='No playlists found for the user ID.'), 404

@app.route('/add_playlist', methods=['POST'])
def add_playlist():
    # request JSON
    data = request.json
    name = data.get('name')
    description = data.get('description', None)
    duration = data.get('duration')
    user_ID = data.get('user_ID')

    if not name or not duration or not user_ID:
        return jsonify({'error': 'Missing required fields for adding a playlist (name, duration, user_ID)'}), 400

    # build query
    query = text("INSERT INTO playlist (name, description, duration, user_ID) VALUES (:name, :description, :duration, :user_ID);")
    # execute the query to insert a new playlist
    db.session.execute(query, {'name': name, 'description': description, 'duration': duration, 'user_ID': user_ID})
    db.session.commit()

    # get new playlist 
    query_get = text("SELECT ID, name, description, TIME_FORMAT(duration, '%H:%i') AS duration, user_ID FROM playlist WHERE name = :name;")
    playlist_list = testExecution(db.session.execute(query_get, {'name': name}))

    return jsonify({'message': 'Playlist added successfully', 'playlist': playlist_list[0]}), 201

@app.route('/update_playlist/<int:playlist_id>', methods=['PUT'])
def update_playlist(playlist_id):
    # request JSON
    data = request.json
    name = data.get('name')
    description = data.get('description', None)
    duration = data.get('duration')
    user_ID = data.get('user_ID')

    if not name or not duration or not user_ID:
        return jsonify({'error': 'Missing required fields for updating a playlist (name, duration, user_ID)'}), 400

    query = text("UPDATE playlist SET name = :name, description = :description, duration = :duration, user_ID = :user_ID WHERE ID = :playlist_id;")
    db.session.execute(query, {'name': name, 'description': description, 'duration': duration, 'user_ID': user_ID, 'playlist_id': playlist_id})
    db.session.commit()

    logging.info('Executing update_playlist method...')
    logging.debug(f'Input data: {data}')

    query_get = text("SELECT ID, name, description, TIME_FORMAT(duration, '%H:%i') AS duration, user_ID FROM playlist WHERE ID = :playlist_id;")
    playlist_list = testExecution(db.session.execute(query_get, {'playlist_id': playlist_id}))

    return jsonify({'message': 'Playlist updated successfully', 'playlist': playlist_list[0]}), 200


@app.route('/playlists/<int:playlist_id>', methods=['DELETE'])
def delete_playlist(playlist_id):
    # set "database_playlist" to the playlist with given ID
    database_playlist = db.session.execute(text("SELECT * FROM playlist WHERE ID = :playlist_id"), {"playlist_id": playlist_id}).fetchone()

    # if database_playlist exists with given ID
    if database_playlist:
        # Delete the playlist
        db.session.execute(text("DELETE FROM playlist WHERE ID = :playlist_id"), {"playlist_id": playlist_id})
        db.session.commit()

        return jsonify({'message': 'The playlist is deleted successfully'})


    else:
        return jsonify({'message': 'Playlist not found'})
    
if __name__ == '__main__':
    app.run(port=5000, debug=True)
