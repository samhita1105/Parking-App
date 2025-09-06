import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from datetime import datetime
import bcrypt

app = Flask(__name__)
app.config['SECRET_KEY'] = 'samhitasiddamshetty'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///parking.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def check_password(hashed_password, user_password):
    return bcrypt.checkpw(user_password.encode('utf-8'), hashed_password)

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.LargeBinary, nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    bookings = db.relationship('Booking', backref='user', lazy=True, cascade="all, delete")

class ParkingLot(db.Model):
    __tablename__ = 'parking_lots'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    price_per_hour = db.Column(db.Float, nullable=False)
    spots = db.relationship('ParkingSpot', backref='lot', lazy=True, cascade="all, delete-orphan")

class ParkingSpot(db.Model):
    __tablename__ = 'parking_spots'
    id = db.Column(db.Integer, primary_key=True)
    spot_number = db.Column(db.String(20), nullable=False)
    lot_id = db.Column(db.Integer, db.ForeignKey('parking_lots.id'), nullable=False)
    is_occupied = db.Column(db.Boolean, default=False)
    
class Booking(db.Model):
    __tablename__ = 'bookings'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    spot_id = db.Column(db.Integer, db.ForeignKey('parking_spots.id'), nullable=False)
    lot_id = db.Column(db.Integer, db.ForeignKey('parking_lots.id'), nullable=False)
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime, nullable=True)
    total_cost = db.Column(db.Float, nullable=True)
    spot = db.relationship('ParkingSpot', backref=db.backref('booking', uselist=False))
    lot = db.relationship('ParkingLot', backref='bookings')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('user_dashboard'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'danger')
            return redirect(url_for('register'))
            
        hashed_password = hash_password(password)
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
        
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and check_password(user.password, password):
            login_user(user)
            flash('Logged in successfully.', 'success')
            if user.is_admin:
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('user_dashboard'))
        else:
            flash('Login failed. Check username and password.', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def user_dashboard():
    if current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
        
    lots = ParkingLot.query.all()

    for lot in lots:
        occupied_spots = ParkingSpot.query.filter_by(lot_id=lot.id, is_occupied=True).count()
        lot.available_spots = lot.capacity - occupied_spots
        
    active_booking = Booking.query.filter_by(user_id=current_user.id, end_time=None).first()
    
    return render_template('user_dashboard.html', lots=lots, active_booking=active_booking)

@app.route('/book/lot/<int:lot_id>')
@login_required
def book_spot(lot_id):
    if Booking.query.filter_by(user_id=current_user.id, end_time=None).first():
        flash('You already have an active booking.', 'warning')
        return redirect(url_for('user_dashboard'))

    available_spot = ParkingSpot.query.filter_by(lot_id=lot_id, is_occupied=False).first()
    
    if not available_spot:
        flash('Sorry, no spots are available in this lot right now.', 'danger')
        return redirect(url_for('user_dashboard'))

    available_spot.is_occupied = True
    new_booking = Booking(user_id=current_user.id, spot_id=available_spot.id, lot_id=lot_id)
    db.session.add(new_booking)
    db.session.commit()
    
    flash(f'Successfully booked Spot {available_spot.spot_number}!', 'success')
    return redirect(url_for('user_dashboard'))

@app.route('/release/booking/<int:booking_id>')
@login_required
def release_spot(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if booking.user_id != current_user.id:
        flash('This is not your booking.', 'danger')
        return redirect(url_for('user_dashboard'))
        
    booking.end_time = datetime.utcnow()

    duration_seconds = (booking.end_time - booking.start_time).total_seconds()
    duration_hours = duration_seconds / 3600
    cost = duration_hours * booking.lot.price_per_hour
    booking.total_cost = round(max(cost, booking.lot.price_per_hour / 2), 2)
    
    booking.spot.is_occupied = False
    db.session.commit()
    
    flash(f'Spot released. Your total cost is ${booking.total_cost:.2f}', 'success')
    return redirect(url_for('user_dashboard'))

def admin_required(f):
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    lots = ParkingLot.query.all()
    users = User.query.filter_by(is_admin=False).all()
    spots = ParkingSpot.query.all()
    return render_template('admin_dashboard.html', lots=lots, users=users, spots=spots)
    
@app.route('/admin/lot/new', methods=['GET', 'POST'])
@admin_required
def new_lot():
    if request.method == 'POST':
        name = request.form.get('name')
        address = request.form.get('address')
        capacity = int(request.form.get('capacity'))
        price_per_hour = float(request.form.get('price_per_hour'))
        
        new_lot = ParkingLot(name=name, address=address, capacity=capacity, price_per_hour=price_per_hour)
        db.session.add(new_lot)
        db.session.flush()
        
        for i in range(1, capacity + 1):
            spot = ParkingSpot(spot_number=f'S{i}', lot_id=new_lot.id)
            db.session.add(spot)
        
        db.session.commit()
        flash('New parking lot created successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
        
    return render_template('lot_form.html', title="Create New Lot")

@app.route('/admin/lot/edit/<int:lot_id>', methods=['GET', 'POST'])
@admin_required
def edit_lot(lot_id):
    lot = ParkingLot.query.get_or_404(lot_id)
    if request.method == 'POST':
        
        lot.name = request.form.get('name')
        lot.address = request.form.get('address')
        lot.price_per_hour = float(request.form.get('price_per_hour'))
        db.session.commit()
        flash('Parking lot updated.', 'success')
        return redirect(url_for('admin_dashboard'))
        
    return render_template('lot_form.html', title="Edit Lot", lot=lot)

@app.route('/admin/lot/delete/<int:lot_id>', methods=['POST'])
@admin_required
def delete_lot(lot_id):
    lot = ParkingLot.query.get_or_404(lot_id)
    
    occupied_spots = ParkingSpot.query.filter_by(lot_id=lot_id, is_occupied=True).count()
    if occupied_spots > 0:
        flash('Cannot delete lot with occupied spots.', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    db.session.delete(lot)
    db.session.commit()
    flash('Parking lot deleted.', 'success')
    return redirect(url_for('admin_dashboard'))
#cost calc implmeneted along with previous milestone
@app.before_first_request
def create_tables():
    db.create_all()
    
    if not User.query.filter_by(username='admin').first():
        admin_pass = 'admin123'
        hashed_pw = hash_password(admin_pass)
        admin_user = User(username='admin', password=hashed_pw, is_admin=True)
        db.session.add(admin_user)
        db.session.commit()
        print(f"Admin user created with username 'admin' and password '{admin_pass}'")

if __name__ == '__main__':
    app.run(debug=True)
