from flask import Flask,render_template,request,session,redirect,url_for,flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager,login_required,current_user
from flask_login import UserMixin
from werkzeug.security import generate_password_hash,check_password_hash
from flask_login import login_user,logout_user,login_manager,LoginManager
from datetime import datetime
import os

# MY db connection
local_server = True
app = Flask(__name__)
app.secret_key = 'ankita_se_lab'

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)

# Set up database connection
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:@localhost:3307/alumini_connect'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# this is for getting unique user access
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Define SQLAlchemy models
class User(UserMixin,db.Model):
    __tablename__='users'
    id = db.Column(db.Integer, primary_key=True,autoincrement=True)
    email = db.Column(db.String(120),unique=True)
    password_hash = db.Column(db.String(200))
    role= db.Column(db.String(50))
    name = db.Column(db.String(100))

class Discussion(db.Model):
    __tablename__='discussion'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())
    # Define relationship with User model
    user = db.relationship('User', backref=db.backref('discussions', lazy='dynamic'))

# Define DMessage Model
class DMessage(db.Model):
    __tablename__='dmessage'
    id = db.Column(db.Integer, primary_key=True)
    discussion_id = db.Column(db.Integer, db.ForeignKey('discussion.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())
    # Define relationship with User model
    user = db.relationship('User', backref=db.backref('messages', lazy='dynamic'))

class Departments(db.Model):
    __tablename__='departments'
    dept_id=db.Column(db.Integer,primary_key=True)
    dept_name=db.Column(db.String(100))

class Students(db.Model):
    __tablename__='students'
    usn = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(120))
    graduation_year = db.Column(db.Integer)

class Alumni(db.Model):
    __tablename__='alumni'
    email = db.Column(db.String(120), primary_key=True)
    name = db.Column(db.String(100))
    passout_year = db.Column(db.Integer)
    dept_id = db.Column(db.Integer, db.ForeignKey('departments.dept_id'), nullable=False)
    current_location = db.Column(db.String(100))
    working_at = db.Column(db.String(100))
    linked_in_profile_link = db.Column(db.String(200))
    about_me=db.Column(db.Text)
    department = db.relationship('Departments', backref='alumni')

class JobPosting(db.Model):
    __tablename__ = 'jobposting'
    id = db.Column(db.Integer, primary_key=True)
    alumni_email = db.Column(db.String(120), db.ForeignKey('alumni.email'), nullable=False)
    company = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(100), nullable=False)
    ctc = db.Column(db.String(50))
    job_location = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text)
    timestamp = db.Column(db.DateTime)
    alumni = db.relationship('Alumni', backref='job_postings')


class Faculty(db.Model):
    __tablename__='faculty'
    email = db.Column(db.String(120), primary_key=True)
    name = db.Column(db.String(100))
    dept_id = db.Column(db.Integer, db.ForeignKey('departments.dept_id'), nullable=False)
    designation = db.Column(db.String(100))
    department = db.relationship('Departments', backref='faculty')
    

class Messages(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    sender_email = db.Column(db.String(120))
    receiver_email = db.Column(db.String(120))
    content = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    reply_to_id = db.Column(db.Integer, db.ForeignKey('messages.id'), nullable=True)
    replies = db.relationship('Messages', backref=db.backref('parent', remote_side=[id]), lazy='dynamic')

class College_Updates(db.Model):
    __tablename__='college_updates'
    update_id = db.Column(db.Integer, primary_key=True,autoincrement=True)
    updater_email = db.Column(db.String(120),db.ForeignKey('faculty.email'),nullable=False)
    content = db.Column(db.Text)
    timestamp = db.Column(db.DateTime)
    updater= db.relationship('Faculty', backref='college_updates')

class Alumni_Achievement(db.Model):
    __tablename__='alumni_achievements'
    achievement_id = db.Column(db.Integer, primary_key=True,autoincrement=True)
    achiever_email = db.Column(db.String(120), db.ForeignKey('alumni.email'), nullable=False)
    content = db.Column(db.Text)
    timestamp = db.Column(db.DateTime)
    achiever = db.relationship('Alumni', backref='alumni_achievements')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET'])
def register_options():
    return render_template('register.html')

@app.route('/register_student', methods=['GET', 'POST'])
def register_student():
    if request.method == 'POST':
        name = request.form['name']
        usn = request.form['usn']
        email = request.form['email']
        password = request.form['password']
        graduation_year = request.form['graduation_year']

        # Check if email ends with @rvce.edu.in
        if not email.endswith('@rvce.edu.in'):
            flash('Only RVCE student emails are allowed for registration.', 'danger')
            return redirect(url_for('register_student'))

        # Check if the email is already registered
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('User with this email is already registered. Please log in instead.', 'warning')
            return redirect(url_for('register'))

        # Save to students table
        new_student = Students(name=name, usn=usn, email=email, graduation_year=graduation_year)
        db.session.add(new_student)
        
        # Save to users table with role ID 1 for student
        new_user = User(name=name, email=email, password_hash=generate_password_hash(password), role="student")
        db.session.add(new_user)

        db.session.commit()

        flash('Registration successful! You can now log in.', 'success')
        #return redirect(url_for('login'))

    return render_template('register_student.html')

@app.route('/register_faculty', methods=['GET', 'POST'])
def register_faculty():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        faculty_member = Faculty.query.filter_by(email=email).first()
        if not email.endswith('@rvce.edu.in'):
            flash('Only RVCE emails are allowed for registration.', 'danger')
            return redirect(url_for('register_faculty'))
        if not faculty_member:
            flash('Faculty member not found in our records.')
            return redirect(url_for('register_faculty'))
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('User already registered.')
            return redirect(url_for('register_faculty'))
        new_user = User(name=name,email=email, password_hash=generate_password_hash(password), role="faculty")
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! You can now log in.')
        return redirect(url_for('index'))
    return render_template('register_faculty.html')

@app.route('/register_alumnus', methods=['GET', 'POST'])
def register_alumnus():
    if request.method == 'POST':
        email = request.form['email']
        name = request.form['name']
        password = request.form['password']
        department = request.form['department']
        passout_year = request.form['passout_year']

        # Check if the email already exists in the users table
        user = User.query.filter_by(email=email).first()
        if user:
            flash('User with this email is already registered.', 'danger')
            return redirect(url_for('register_alumnus'))

        # Create new user and alumnus
        new_user = User(name=name,email=email, password_hash=generate_password_hash(password), role="alumni")  # Role ID 3 for alumnus
        db.session.add(new_user)
        db.session.commit()

        new_alumnus = Alumni(
            email=email,
            name=name,
            passout_year=passout_year,
            dept_id=department
        )
        db.session.add(new_alumnus)
        db.session.commit()

        flash('Alumnus registered successfully!', 'success')
        return redirect(url_for('index'))

    return render_template('register_alumnus.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']

        # Query the database for the user
        user = User.query.filter_by(email=email).first()

        if user:
            # Check if the password is correct
            if check_password_hash(user.password_hash, password):
                # Check if the user role matches
                if user.role == role:
                    session['email'] = email
                    session['role']=role
                    login_user(user)
                    flash('Logged in successfully!', 'success')
                    # Redirect to the appropriate dashboard based on role
                    if role == 'student':
                        return redirect(url_for('student_dashboard'))
                    elif role == 'faculty':
                        return redirect(url_for('faculty_dashboard'))
                    elif role == 'alumni':
                        return redirect(url_for('alumni_dashboard'))
                else:
                    flash('Invalid role!', 'danger')
            else:
                flash('Invalid email or password!', 'danger')
        else:
            flash('User not found!', 'danger')

    return render_template('login.html')

@app.route('/student_dashboard')
def student_dashboard():
    return render_template('student_dashboard.html')

@app.route('/faculty_dashboard')
def faculty_dashboard():
    return render_template('faculty_dashboard.html')

@app.route('/alumni_details', methods=['GET', 'POST'])
def alumni_details():
    # Retrieve all departments for the filter dropdown
    departments = Departments.query.all()
    
    # Start with the base query
    alumni_query = Alumni.query
    
    # Handle form submissions
    if request.method == 'POST':
        # Get filter criteria from the form
        department_id = request.form.get('department')
        passout_year = request.form.get('passout_year')
        company = request.form.get('company')
        
        # Apply filters based on the form inputs
        if department_id:
            alumni_query = alumni_query.filter_by(dept_id=department_id)
        if passout_year:
            alumni_query = alumni_query.filter_by(passout_year=passout_year)
        if company:
            alumni_query = alumni_query.filter(Alumni.working_at.ilike(f'%{company}%'))
    
    # Execute the query to get the filtered results
    alumni_details = alumni_query.all()
    
    # Render the template with the filtered results and the departments for the dropdown
    return render_template('alumni_details.html', alumni_details=alumni_details, departments=departments)


@app.route('/alumni_dashboard')
def alumni_dashboard():
    return render_template('alumni_dashboard.html')

@app.route('/discussion_list')
def discussion_list():
    discussions = Discussion.query.all()
    return render_template('discussion_list.html', discussions=discussions)

@app.route('/create_discussion', methods=['GET', 'POST'])
def create_discussion():
    if request.method == 'POST':
        title = request.form['discussion_title']
        email = session.get('email')
        if email:
            user = User.query.filter_by(email=email).first()
            if user:
                new_discussion = Discussion(title=title, user_id=user.id)
                db.session.add(new_discussion)
                db.session.commit()
                return redirect(url_for('discussion_list'))
            else:
                return "User not found"
        else:
            return "User not logged in"
    return render_template('create_discussion.html')

@app.route('/discussion/<int:discussion_id>')
def view_discussion(discussion_id):
    discussion = Discussion.query.get(discussion_id)
    messages = DMessage.query.filter_by(discussion_id=discussion_id).all()
    return render_template('view_discussion.html', discussion=discussion, messages=messages)

@app.route('/add_message/<int:discussion_id>', methods=['POST'])
def add_message(discussion_id):
    if request.method == 'POST':
        message_content = request.form['new_message']
        email = session.get('email')
        if email:
            user = User.query.filter_by(email=email).first()
            if user:
                new_message = DMessage(discussion_id=discussion_id, user_id=user.id, message=message_content)
                db.session.add(new_message)
                db.session.commit()
                return redirect(url_for('view_discussion', discussion_id=discussion_id))
            else:
                return "User not found"
        else:
            return "User not logged in"
        
@app.route('/alumni_form')
def alumni_form():
    # Check if email is in session
    if 'email' not in session:
        return redirect('/')
    email = session['email']
    alumni = Alumni.query.get(email)
    return render_template('alumni_form.html', alumni=alumni)

# Route for updating alumni details
@app.route('/update_details', methods=['POST'])
def update_details():
    # Check if email is in session
    if 'email' not in session:
        return redirect('/')
    email = session['email']
    alumni = Alumni.query.get(email)
    if alumni:
        # Update alumni details
        alumni.current_location = request.form['current_location']
        alumni.working_at = request.form['working_at']
        alumni.linked_in_profile_link = request.form['linked_in_profile_link']
        alumni.about_me = request.form['about_me']
        db.session.commit()
    return redirect('/alumni_form')

@app.route('/achievements')
def achievements():
    achievements = Alumni_Achievement.query.order_by(Alumni_Achievement.timestamp.desc()).all()
    return render_template('achievements.html', achievements=achievements)

# Route for the add achievement page
@app.route('/add_achievement')
def add_achievement():
    # Check if email is in session
    if 'email' not in session:
        return redirect('/')
    return render_template('add_achievement.html')

# Route for adding an achievement
@app.route('/add_achievement', methods=['POST'])
def add_achievement_post():
    # Check if email is in session
    if 'email' not in session:
        return redirect('/')
    content = request.form['content']
    email = session['email']
    achievement = Alumni_Achievement(achiever_email=email, content=content, timestamp=datetime.now())

    db.session.add(achievement)
    db.session.commit()
    return redirect('/achievements')
        
@app.route('/view_faculty', methods=['GET', 'POST'])
def view_faculty():
    departments = Departments.query.all()
    selected_department = None
    faculty_list = None
    
    if request.method == 'POST':
        dept_id = request.form['department']
        selected_department = Departments.query.get(dept_id)
        faculty_list = Faculty.query.filter_by(dept_id=dept_id).all()
    
    return render_template('view_faculty.html', departments=departments, faculty_list=faculty_list, selected_department=selected_department)


@app.route('/view_achievement')
def view_achievement():
    achievements = Alumni_Achievement.query.order_by(Alumni_Achievement.timestamp.desc()).all()
    return render_template('achievements.html', achievements=achievements)

@app.route('/add_update', methods=['GET', 'POST'])
def add_update():
    if request.method == 'POST':
        updater_email = session.get('email')
        content = request.form['content']
        timestamp = datetime.now()

        update = College_Updates(updater_email=updater_email, content=content, timestamp=timestamp)
        db.session.add(update)
        db.session.commit()
        return redirect('/view_updates')
    
    return render_template('add_update.html')

# Route for viewing updates
@app.route('/view_updates')
def view_updates():
    updates = College_Updates.query.order_by(College_Updates.timestamp.desc()).all()
    return render_template('view_updates.html', updates=updates)

@app.route('/alumni_job_postings', methods=['GET', 'POST'])
def alumni_job_postings():
    if request.method == 'POST':
        # Handle form submission to add job posting
        # Extract form data
        company = request.form.get('company')
        role = request.form.get('role')
        ctc = request.form.get('ctc')
        job_location = request.form.get('job_location')
        content = request.form.get('content')
        # Create new job posting
        new_job_posting = JobPosting(alumni_email=session['email'], company=company, role=role, ctc=ctc, 
                                    job_location=job_location, content=content, 
                                    timestamp=datetime.now())
        db.session.add(new_job_posting)
        db.session.commit()
        flash('Job posting added successfully', 'success')
        return redirect(url_for('alumni_job_postings'))

    # Retrieve job postings for the current alumni
    job_postings = JobPosting.query.filter_by(alumni_email=current_user.email).all()
    return render_template('alumni_job_postings.html', job_postings=job_postings)

@app.route('/students_job_postings')
def students_job_postings():
    # Retrieve all job postings for students to view
    job_postings = JobPosting.query.all()
    return render_template('students_job_postings.html', job_postings=job_postings)

@app.route('/alumni_job_postings_view')
def alumni_job_postings_view():
    # Retrieve job postings made by the current alumni
    job_postings = JobPosting.query.filter_by(alumni_email=current_user.email).all()
    return render_template('alumni_job_postings_view.html', job_postings=job_postings)


    
if __name__ == '__main__':
    app.run(debug=True)
