from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import jwt
from functools import wraps
import datetime
import base64
import cv2
from moviepy.editor import VideoFileClip, AudioFileClip,ImageSequenceClip,concatenate_audioclips
import numpy as np
from PIL import Image
import io
import os
from moviepy.video.fx import all as vfx
from moviepy.editor import concatenate_videoclips
import psycopg2
import os
from cryptography.fernet import Fernet
import tempfile
import subprocess
import time


app = Flask(__name__, static_url_path='/static')
app.secret_key = 'your_secret_key'
key = b'xOcVTh1VfE-H7lSWzw3uyssImCQ5nX_5EFmuo0wByb0='
cipher_suite = Fernet(key)

def connect_to_database():
    conn_params = {
        'host': 'web-weavers-4063.7s5.aws-ap-south-1.cockroachlabs.cloud',
        'port': 26257,
        'user': 'web-weavers',
        'password': 'a5NRl19lKJDIE9V22ye3zA',
        'database': 'ISS_users',
        'sslmode': 'verify-full',
        'sslrootcert': 'root.crt' # Replace with the correct path
    }

    conn_str = "host={host} port={port} user={user} password={password} dbname={database} sslmode={sslmode} sslrootcert={sslrootcert}".format(**conn_params)
    #postgresql://web-weavers:<ENTER-SQL-USER-PASSWORD>@web-weavers-4063.7s5.aws-ap-south-1.cockroachlabs.cloud:26257/ISS_users?sslmode=verify-full
    # Connect to the database
    try:
        conn = psycopg2.connect(conn_str)
        return conn
    except psycopg2.OperationalError as e:
        return None

con = connect_to_database()# pymysql.connect(host='localhost', user="root", password="Root@1234", db='db_user')
cur = con.cursor()

def create_table():
    # Define the SQL statement to create the tables
    create_table_query = """
    CREATE TABLE IF NOT EXISTS UserDetails (
        UserId SERIAL PRIMARY KEY,
        UserName VARCHAR(255) NOT NULL UNIQUE,
        UserEmail VARCHAR(255) UNIQUE,
        UserPassword VARCHAR(255) NOT NULL
    );
    """
    cur.execute(create_table_query)
    con.commit()
    create_table_query = """
    CREATE TABLE IF NOT EXISTS UserImages (
        ImageId SERIAL PRIMARY KEY,
        UserId INT, 
        ImageData BYTEA,
        ImageMetadata VARCHAR(255)
    );
    """
    cur.execute(create_table_query)
    con.commit()
    create_table_query = """
    CREATE TABLE IF NOT EXISTS Audio (
        AudioID SERIAL PRIMARY KEY,
        AudioBlob BYTEA,
        AudioMetadata TEXT
    );
    """
    cur.execute(create_table_query)
    con.commit()

        
create_table()
i = 1

# Configure your secret key for JWT
app.config['SECRET_KEY'] = '$%#GJdjsklwJLqwn321QDdjaA'

# Define a decorator to require authentication
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    return render_template('Index.html')

# Function to generate JWT token

# Function to generate JWT token with expiration time
def generate_token(username):
    # Set the token expiration time (e.g., 10 minutes from now)
    expiration_time = datetime.datetime.utcnow() + datetime.timedelta(minutes=10)
    payload = {
        'username': username,
        'exp': expiration_time
    }
    token = jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')
    return token



# Function to read users from file
def read_users():
    cur.execute("SELECT * FROM UserDetails;")
    users = cur.fetchall()
    return users

# Function to write users to file
def write_user(username, email, password):
    global i
    try:
        cipher_text = cipher_suite.encrypt(password.encode('utf-8'))
        cur.execute("INSERT INTO UserDetails (UserName, UserEmail, UserPassword) VALUES (%s, %s, %s);", (username, email, cipher_text.decode('utf-8')))
        con.commit()
        i += 1
        print("User added successfully")
    except Exception as e:
        print("Error adding user:", e)

# Signup route
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        cur.execute("SELECT * FROM UserDetails WHERE UserName = %s", (username,))
        user = cur.fetchone()
        if user:
            return "User already exists. Please login."
        email = request.form['email']
        password = request.form['password']
        print(username, email, password)
        # Store hashed password in database instead of plain text (you need to implement this)
        write_user(username, email, password)
        return redirect(url_for('login'))
    return render_template('signup.html')

# Login route
# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        print(username, password)
        cur.execute("SELECT * FROM UserDetails WHERE UserName=%s", (username,))
        user = cur.fetchone()
        if username == "admin" and password == "chilling":
            session['username'] = username
            token = generate_token(username)
            session['token'] = token
            return redirect(url_for('dashboard'))
        if user:
            plain_text = cipher_suite.decrypt(user[3].encode('utf-8')).decode('utf-8')
            print(username, plain_text)
            if password == plain_text:
                session['username'] = username
                token = generate_token(username)
                session['token'] = token
                session['user_id'] = user[0]
                return redirect(url_for('home', username=username))
            return "Invalid Username or Password. Please Try Again."
        return "User doesnt Exist. Please Signup."
    
    # Check if the user has a valid session token
    if 'username' in session and 'token' in session:
        # Validate the token
        try:
            username=session['username']
            jwt.decode(session['token'], app.config['SECRET_KEY'], algorithms=['HS256'])
            if username == "admin":
                return redirect(url_for('dashboard'))
            # Token is valid, redirect to the dashboard
            return redirect(url_for('home',username=username))
        except jwt.ExpiredSignatureError:
            # Token has expired, require the user to log in again
            session.pop('username', None)
            session.pop('token', None)
    return render_template('login.html')


# Logout route
@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('token', None)
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    cur.execute("SELECT UserId, UserName, UserEmail FROM UserDetails")
    users = cur.fetchall()

    user_data = []
    for user in users:
        user_id = user[0]
        cur.execute("SELECT ImageData FROM UserImages WHERE UserId = %s", (user_id,))
        images = cur.fetchall()
        images_base64 = [base64.b64encode(image[0]).decode('utf-8') for image in images]
        user_data.append((user, images_base64))

    return render_template('dashboard.html', user_data=user_data)

@app.route('/home/<username>')
@login_required
def home(username):
    user_id=session.get('user_id')
    cur.execute("SELECT ImageData FROM UserImages WHERE UserId = %s", (user_id,))
    images = cur.fetchall()
    # Convert each image to a base64 string
    images_base64 = [base64.b64encode(image[0]).decode('utf-8') for image in images]
    return render_template('home.html',username=username,images_base64=images_base64)

@app.route('/upload/<username>' ,methods = ['POST','GET'])
@login_required
def upload(username):
    user_id = session.get('user_id')
    if request.method == 'POST':
        # Get the list of image files from the form
        image_files = request.files.getlist('fileInput')
        
        # Loop through each image file
        for image_file in image_files:
            # Read the image data
            image_data = image_file.read()
            if image_data:
                print("confirmed2")
            else:
                print("No image files provided")    
            # Insert the image data into the database
            cur.execute("INSERT INTO UserImages (UserId, ImageData) VALUES (%s, %s);", (user_id, image_data))
            con.commit()
        return redirect(url_for('home',username=username))
    cur.execute("SELECT ImageData FROM UserImages WHERE UserId = %s", (user_id,))
    images = cur.fetchall()

    # Convert each image to a base64 string
    images_base64 = [base64.b64encode(image[0]).decode('utf-8') for image in images]
    return render_template('upload.html', images_base64=images_base64,username=username)

@app.route('/delete/<username>', methods=['POST', 'GET'])
@login_required
def delete(username):
    user_id = session.get('user_id')
    cur.execute("SELECT ImageData FROM UserImages WHERE UserId = %s", (user_id,))
    images = cur.fetchall()

    # Convert each image to a base64 string
    images_base64 = [base64.b64encode(image[0]).decode('utf-8') for image in images]

    if request.method == 'POST':
        images_to_delete = request.form.getlist('delete_images[]')

        # Loop through the selected images and delete them from the database
        for index in images_to_delete:
            cur.execute("DELETE FROM UserImages WHERE UserId = %s AND ImageData = %s", (user_id, images[int(index)][0]))
            con.commit()

        # After deletion, fetch the updated images
        cur.execute("SELECT ImageData FROM UserImages WHERE UserId = %s", (user_id,))
        images = cur.fetchall()
        images_base64 = [base64.b64encode(image[0]).decode('utf-8') for image in images]

    return render_template('delete.html', images_base64=images_base64, username=username)

@app.route('/create/<username>', methods=['POST','GET'])
@login_required
def create(username):
    if os.path.exists("audio.mp3"):
        os.remove("audio.mp3")
    user_id = session.get('user_id')
    cur.execute("SELECT ImageData FROM UserImages WHERE UserId = %s", (user_id,))
    images = cur.fetchall()
    # Convert each image to a base64 string
    images_base64 = [base64.b64encode(image[0]).decode('utf-8') for image in images]

    # Check if the form is submitted with audio selection

    return render_template('create.html', username=username, images_base64=images_base64)

def create_transition(input_video1, input_video2, transition,output_video, duration, offset):
    print("cr8 trns")
    command = [
        "ffmpeg",
        '-i', input_video1,
        '-i', input_video2,
        '-filter_complex', f'xfade=transition={transition}:duration={duration}:offset={offset}',
        output_video
    ]
    subprocess.run(command)

def get_audio(audio,duration):
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp_audio_file:
        tmp_audio_file.write(audio[0][0])  # Assuming audio_data is a bytes object
        tmp_audio_file_path = tmp_audio_file.name
        audio_clip = AudioFileClip(tmp_audio_file_path)
        if duration < audio_clip.duration:
            audio_clip = audio_clip.subclip(0, duration)
        os.unlink(tmp_audio_file_path)
    return audio_clip

def create_video(image_list, audio,durations,transitions,quality):
    # Initialize a list to store frames
    print(transitions)
    print(len(transitions),len(image_list),len(durations),len(audio))
    print("q",quality)
    clips=[]
    clips_audio=[]
    # Set a common size for all images
    if quality=="high":
        common_size = (1920, 1080)
    elif quality=="low":
        common_size = (640, 480)
    elif quality=="veryhigh":
        common_size = (3840, 2160)
    elif quality=="verylow":
        common_size = (480, 360)
    if quality=="medium":
        common_size = (1280, 720)  # Adjust the size as needed
    j=0
    k=0
    i=0
    output_clip=None
    # Read each image using cv2, resize, and append to the frame list
    for image in image_list:
        print(i)
        frame_list = []
        # print("image type ",type(image[0]))
        # images_base64 = base64.b64encode(image[0]).decode('utf-8')  # Decode the base64 string

        # print("after encode ",type(image))
        # print(len(images_base64))
        # Convert the base64 string back to bytes
        # base64_decoded = base64.b64decode(images_base64)
        base64_decoded = base64.b64decode(image)
        # Convert the bytes to a NumPy array
        image_np = np.frombuffer(base64_decoded, dtype=np.uint8)

        # Decode the image using cv2
        img = cv2.imdecode(image_np, cv2.IMREAD_COLOR)

        if img is not None:
            # Resize the image to a common size
            img_resized = cv2.resize(img, common_size)

            # Convert the color from RGB to BGR
            img_bgr = cv2.cvtColor(img_resized, cv2.COLOR_RGB2BGR)
            # Inside the 'create_video' function

            for _ in range(24*durations[i]):
                frame_list.append(img_bgr)
            video_clip = ImageSequenceClip(frame_list, fps=24)
            if transitions[i]!="None":
                if j==0:
                    video_clip.write_videofile(f"clip{k}.mp4", codec="libx264", audio=True, fps=24)
                    vid=VideoFileClip(f"clip{k}.mp4")
                    clips.append(vid)
                    k+=1
                else:
                    video_clip.write_videofile(f"clip{k}.mp4", codec="libx264", audio=True, fps=24)
                    create_transition(f"clip{k-1}.mp4", f"clip{k}.mp4", transitions[i], f"output_video{k}.mp4", 0.5, 0)
                    vid=VideoFileClip(f"output_video{k}.mp4")
                    clips.append(vid)
                    k+=1
            else:
                video_clip.write_videofile(f"clip{k}.mp4", codec="libx264", audio=True, fps=24)
                k+=1
                clips.append(video_clip)
            j+=durations[i]
            # if audios[i]:
            i+=1
                
            # video_clip.write_videofile(f"output_video{i}.mp4", codec="libx264", audio=True, fps=24)
        else:
            print("Error decoding image")

    if not frame_list:
        print("No frames found. Aborting video creation.")
        return None
    # Concatenate all the clips
    final_clip = concatenate_videoclips(clips)
    if os.path.exists("audio.mp3"):
        final_audio = AudioFileClip("audio.mp3")
        if final_clip.duration < final_audio.duration:
            final_audio = final_audio.subclip(0, final_clip.duration)
        final_clip = final_clip.set_audio(final_audio)
    elif audio:
        final_audio=get_audio(audio,final_clip.duration)
        final_clip = final_clip.set_audio(final_audio)

    # Set the audio of the final video clip
    if os.path.exists("clip0.mp4"):
        os.remove("clip0.mp4")
    for i in range(1,k):
        if os.path.exists(f"clip{i}.mp4"):
            os.remove(f"clip{i}.mp4")
        if os.path.exists(f"output_video{i}.mp4"):
            os.remove(f"output_video{i}.mp4")

    

    # Write the final video file
    final_clip.write_videofile("static/output_video.mp4", codec="libx264", audio=True, fps=24)

    return

@app.route('/send_selected_images', methods=['POST','GET'])
def send_selected_images():
    data = request.json
    selected_images = data.get('selectedImages', [])
    images_base64=[]
    durations=[]
    transitions=[]
    quality=selected_images[0]["quality"]
    cur.execute("SELECT AudioBlob FROM Audio WHERE AudioID = %s", (int(selected_images[0]["audio"]),))
    audio = cur.fetchall()
    # print("audioid",audioid,type(audioid))
    # Process the selected_images array as needed
    for image in selected_images:
        images_base64.append(image["src"][13:])
        durations.append(int(image["duration"]))
        transitions.append(image["transition"])
        # print(len(image["src"]))
        # print(type(image))
    # for base in images_base64:
    #     print("base type",type(base))
    l=len(selected_images)
    create_video(images_base64,audio,durations,transitions,quality)
    # Return the path or URL of the generated video file
    video_path = '/static/output_video.mp4'
    return jsonify({'message': f'{l} images received successfully!', 'video_path': video_path})
    # Return a response (if needed)
    #return render_template('new.html', images_base64=selected_images)

@app.route('/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    try:
        # Delete the user from the database based on the user_id
        cur.execute("DELETE FROM UserImages WHERE UserId = %s", (user_id,))
        con.commit()
        cur.execute("DELETE FROM UserDetails WHERE UserId = %s", (user_id,))
        con.commit()
        # Redirect back to the dashboard after deletion
        return redirect(url_for('dashboard'))
    except Exception as e:
        # Handle any errors that may occur during deletion
        print("Error deleting user:", e)
        return "Error deleting user"


@app.route('/save_audio_file', methods=['POST'])
def save_audio_file():
    UPLOAD_FOLDER = ''  # Update with the path to your uploaded audio folder
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file uploaded'}), 400

    audio_file = request.files['audio']
    if audio_file.filename == '':
        return jsonify({'error': 'No audio file selected'}), 400

    # Save the audio file to the specified folder
    filename = os.path.join(app.config['UPLOAD_FOLDER'], "audio.mp3")
    audio_file.save(filename)

    return jsonify({'message': 'Audio file uploaded successfully', 'filename': filename}), 200



if __name__ == '__main__':
    app.run(debug=True)
    cur.close()
    con.close()