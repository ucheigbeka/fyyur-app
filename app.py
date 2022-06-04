# ----------------------------------------------------------------------------#
# Imports
# ----------------------------------------------------------------------------#

from datetime import datetime

import dateutil.parser
import babel
from flask import Flask, render_template, request, flash, redirect, url_for, abort
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from forms import *


# ----------------------------------------------------------------------------#
# Utils
# ----------------------------------------------------------------------------#
def populate_model(data, model):
	for k, v in data.items():
		if hasattr(model, k) and v is not None:
			setattr(model, k, v)


def get_genre_names(genres):
	return [genre.name for genre in genres]


def parse_show(show):
	"""
	Output Schema
		"venue_id": int
		"venue_name": str
		"artist_id": int
		"artist_name": str
		"artist_image_link": str
		"start_time": str
	"""
	return {
		'venue_id': show.venue_id,
		'venue_name': show.venue.name,
		'artist_id': show.artist_id,
		'artist_name': show.artist.name,
		'artist_image_link': show.artist.image_link,
		'start_time': show.start_time.strftime('%Y-%m-%dT%H:%M:%S.000Z')
	}


def get_shows(model, attr):
	shows = getattr(model, attr)
	data = {
		'upcoming_shows': [],
		'past_shows': []
	}
	for show in shows:
		if datetime.today() > show.start_time:
			data['past_shows'].append(show)
		else:
			data['upcoming_shows'].append(show)

	return data


def parse_show_for_venue(show):
	artist = show.artist
	return {
		"artist_id": artist.id,
		"artist_name": artist.name,
		"artist_image_link": artist.image_link,
		"start_time": show.start_time.strftime('%Y-%m-%dT%H:%M:%S.000Z')
	}


def parse_show_for_artist(show):
	venue = show.venue
	return {
		"venue_id": venue.id,
		"venue_name": venue.name,
		"venue_image_link": venue.image_link,
		"start_time": show.start_time.strftime('%Y-%m-%dT%H:%M:%S.000Z')
	}


def parse_venue(venue):
	"""
	Output Schema
		"id": int
		"name": str
		"genres": list,
		"address": str,
		"city": str,
		"state": str,
		"phone": str,
		"website": str,
		"facebook_link": str,
		"seeking_talent": bool,
		"seeking_description": str,
		"image_link": str,
		"past_shows": [{
			"artist_id": int,
			"artist_name": str,
			"artist_image_link": str,
			"start_time": str
		}],
		"upcoming_shows": [
			{
				"artist_id": int,
				"artist_name": str,
				"artist_image_link": str,
				"start_time": str
			}
		],
		"past_shows_count": int,
		"upcoming_shows_count": int,
	"""
	shows = get_shows(venue, 'artists')
	past_shows = list(map(parse_show_for_venue, shows['past_shows']))
	upcoming_shows = list(map(parse_show_for_venue, shows['upcoming_shows']))
	return {
		"id": venue.id,
		"name": venue.name,
		"genres": get_genre_names(venue.genres),
		"address": venue.address,
		"city": venue.city,
		"state": venue.state,
		"phone": venue.phone,
		"website": venue.website_link,
		"facebook_link": venue.facebook_link,
		"seeking_talent": venue.seeking_talent,
		"seeking_description": venue.seeking_description,
		"image_link": venue.image_link,
		"past_shows": past_shows,
		"upcoming_shows": upcoming_shows,
		"past_shows_count": len(past_shows),
		"upcoming_shows_count": len(upcoming_shows),
	}


def parse_artist(artist):
	shows = get_shows(artist, 'venues')
	past_shows = list(map(parse_show_for_artist, shows['past_shows']))
	upcoming_shows = list(map(parse_show_for_artist, shows['upcoming_shows']))
	return {
		"id": artist.id,
		"name": artist.name,
		"genres": get_genre_names(artist.genres),
		"city": artist.city,
		"state": artist.state,
		"phone": artist.phone,
		"website": artist.website_link,
		"facebook_link": artist.facebook_link,
		"seeking_venue": artist.seeking_venue,
		"seeking_description": artist.seeking_description,
		"image_link": artist.image_link,
		"past_shows": past_shows,
		"upcoming_shows": upcoming_shows,
		"past_shows_count": len(past_shows),
		"upcoming_shows_count": len(upcoming_shows),
	}

# ----------------------------------------------------------------------------#
# App Config.
# ----------------------------------------------------------------------------#


app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)


# ----------------------------------------------------------------------------#
# Association Tables
# ----------------------------------------------------------------------------#
venue_genres = db.Table(
	'venue_genres',
	db.Column('venue_id', db.Integer, db.ForeignKey('Venue.id'), primary_key=True),
	db.Column('genre_id', db.Integer, db.ForeignKey('Genre.id'), primary_key=True)
)

artist_genres = db.Table(
	'artist_genres',
	db.Column('artist_id', db.Integer, db.ForeignKey('Artist.id'), primary_key=True),
	db.Column('genre_id', db.Integer, db.ForeignKey('Genre.id'), primary_key=True)
)


class Show(db.Model):
	__tablename__ = 'Show'

	venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'), primary_key=True)
	artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'), primary_key=True)
	start_time = db.Column(db.DateTime, nullable=False)
	venue = db.relationship('Venue', back_populates='artists')
	artist = db.relationship('Artist', back_populates='venues')

# ----------------------------------------------------------------------------#
# Models.
# ----------------------------------------------------------------------------#


class Venue(db.Model):
	# Parent

	# A combination of "name", "city" and "state" should uniquely
	# identify a venue

	__tablename__ = 'Venue'

	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String)
	city = db.Column(db.String(120))
	state = db.Column(db.String(120))
	address = db.Column(db.String(120))
	phone = db.Column(db.String(120))
	genres = db.relationship('Genre', secondary=venue_genres, backref=db.backref('venues', lazy=True))
	image_link = db.Column(db.String(500))
	facebook_link = db.Column(db.String(120))
	website_link = db.Column(db.String(120))
	seeking_talent = db.Column(db.Boolean, default=False)
	seeking_description = db.Column(db.String())
	artists = db.relationship('Show', back_populates='venue')


class Artist(db.Model):
	# Child

	__tablename__ = 'Artist'

	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String)
	city = db.Column(db.String(120))
	state = db.Column(db.String(120))
	phone = db.Column(db.String(120))
	genres = db.relationship('Genre', secondary=artist_genres, backref=db.backref('artists', lazy=True))
	image_link = db.Column(db.String(500))
	facebook_link = db.Column(db.String(120))
	website_link = db.Column(db.String(120))
	seeking_venue = db.Column(db.Boolean, default=False)
	seeking_description = db.Column(db.String())
	venues = db.relationship('Show', back_populates='artist')


class Genre(db.Model):
	__tablename__ = 'Genre'

	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(120), unique=True, nullable=False)

# ----------------------------------------------------------------------------#
# Filters.
# ----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
	date = dateutil.parser.parse(value)
	if format == 'full':
		format = "EEEE MMMM, d, y 'at' h:mma"
	elif format == 'medium':
		format = "EE MM, dd, y h:mma"
	return babel.dates.format_datetime(date, format, locale='en')


app.jinja_env.filters['datetime'] = format_datetime


# ----------------------------------------------------------------------------#
# Controllers.
# ----------------------------------------------------------------------------#

@app.route('/')
def index():
	return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
	venues = Venue.query.all()
	data = []
	for venue in venues:
		city, state = venue.city, venue.state
		shows = get_shows(venue, 'artists')
		for venue_data in data:
			if venue_data.get('state') == state and venue_data.get('city') == city:
				venue_data['venues'].append({
					'id': venue.id,
					'name': venue.name,
					'num_upcoming_shows': len(shows['upcoming_shows'])
				})
				break
		else:
			venue_data = {
				'city': city,
				'state': state,
				'venues': [
					{
						'id': venue.id,
						'name': venue.name,
						'num_upcoming_shows': len(shows['upcoming_shows'])
					}
				]
			}
			data.append(venue_data)
	print(data)
	return render_template('pages/venues.html', areas=data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
	search_term = request.form.get('search_term', '')
	pattern = f'%{search_term}%'
	venues = Venue.query.filter(Venue.name.ilike(pattern)).all()
	data = []
	for venue in venues:
		shows = get_shows(venue, 'artists')
		data.append({
			'id': venue.id,
			'name': venue.name,
			'num_upcoming_shows': len(shows['upcoming_shows'])
		})
	response = {
		'count': len(data),
		'data': data
	}

	return render_template(
		'pages/search_venues.html', results=response, search_term=search_term
	)


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
	venue = Venue.query.get(venue_id)
	if not venue:
		abort(404)
	data = parse_venue(venue)
	return render_template('pages/show_venue.html', venue=data)


#  Create Venue
#  ----------------------------------------------------------------


@app.route('/venues/create', methods=['GET'])
def create_venue_form():
	form = VenueForm()
	genre_list = Genre.query.with_entities(Genre.id, Genre.name).all()
	form.genres.choices = [(str(genre[0]), genre[1]) for genre in genre_list]
	return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
	form = VenueForm(request.form)
	genre_list = Genre.query.with_entities(Genre.id, Genre.name).all()
	form.genres.choices = [(str(genre[0]), genre[1]) for genre in genre_list]

	# Ensures that the "name" and "city" fields are in
	# camel case
	form.name.data = str(form.name.data).title()
	form.city.data = str(form.city.data).title()
	for attr in dir(form):
		if hasattr(getattr(form, attr), 'data'):
			print(f'{attr}: {getattr(getattr(form, attr), "data")}')
	print(form.data)

	if form.validate():
		data = form.data
		genres_ids = data.pop('genres')
		# Accounts for multiple venues with same name across different locations
		venue = Venue.query.filter(
			Venue.name == form.name.data,
			Venue.city == form.city.data,
			Venue.state == form.state.data
		).first()
		if not venue:
			venue = Venue()
		populate_model(data, venue)
		for genre_id in genres_ids:
			genre = Genre.query.get(genre_id)
			venue.genres.append(genre)
		db.session.add(venue)
		db.session.commit()
		flash('Venue ' + form.name.data + ' was successfully listed!')
		return render_template('pages/home.html')
	flash('An error occurred. Venue ' + form.name.data + ' could not be listed.')
	return render_template('forms/new_venue.html', form=form)


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
	venue = Venue.query.get(venue_id)
	db.session.delete(venue)
	db.session.commit()
	flash('Venue ' + venue.name + ' successfully deleted')
	return redirect(url_for('index'))


#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
	artists = Artist.query.all()
	data = []
	for artist in artists:
		data.append({
			'id': artist.id,
			'name': artist.name
		})
	return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
	search_term = request.form.get('search_term', '')
	pattern = f'%{search_term}%'
	artists = Artist.query.filter(Artist.name.ilike(pattern)).all()
	data = []
	for artist in artists:
		shows = get_shows(artist, 'venues')
		data.append({
			'id': artist.id,
			'name': artist.name,
			'num_upcoming_shows': len(shows['upcoming_shows'])
		})
	response = {
		'count': len(data),
		'data': data
	}
	return render_template(
		'pages/search_artists.html', results=response, search_term=search_term
	)


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
	artist = Artist.query.get(artist_id)
	if not artist:
		abort(404)
	data = parse_artist(artist)
	return render_template('pages/show_artist.html', artist=data)


#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
	form = ArtistForm()
	artist = Artist.query.get(artist_id)
	if not artist:
		abort(404)
	data = parse_artist(artist)
	return render_template('forms/edit_artist.html', form=form, artist=data)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
	form = ArtistForm(request.form)
	genre_list = Genre.query.with_entities(Genre.id, Genre.name).all()
	form.genres.choices = [(str(genre[0]), genre[1]) for genre in genre_list]

	if form.validate():
		data = form.data
		genres_ids = data.pop('genres')
		artist = Artist.query.get(artist_id)
		populate_model(data, artist)
		for genre_id in genres_ids:
			genre = Genre.query.get(genre_id)
			artist.genres.append(genre)
		db.session.add(artist)
		db.session.commit()
		flash('Artist ' + form.name.data + ' updated successfully')
		return redirect(url_for('show_artist', artist_id=artist_id))

	abort(404)


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
	form = VenueForm()
	venue = Venue.query.get(venue_id)
	if not venue:
		abort(404)
	data = parse_venue(venue)
	return render_template('forms/edit_venue.html', form=form, venue=data)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
	form = VenueForm(request.form)
	genre_list = Genre.query.with_entities(Genre.id, Genre.name).all()
	form.genres.choices = [(str(genre[0]), genre[1]) for genre in genre_list]

	if form.validate():
		data = form.data
		genres_ids = data.pop('genres')
		venue = Venue.query.get(venue_id)
		populate_model(data, venue)
		for genre_id in genres_ids:
			genre = Genre.query.get(genre_id)
			venue.genres.append(genre)
		db.session.add(venue)
		db.session.commit()
		flash('Venue ' + form.name.data + ' updated successfully')
		return redirect(url_for('show_venue', venue_id=venue_id))

	abort(404)


#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
	form = ArtistForm()
	genre_list = Genre.query.with_entities(Genre.id, Genre.name).all()
	form.genres.choices = [(str(genre[0]), genre[1]) for genre in genre_list]
	return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
	form = ArtistForm(request.form)
	genre_list = Genre.query.with_entities(Genre.id, Genre.name).all()
	form.genres.choices = [(str(genre[0]), genre[1]) for genre in genre_list]

	form.name.data = str(form.name.data).title()

	if form.validate():
		data = form.data
		genres_ids = data.pop('genres')
		artist = Artist.query.filter_by(name=form.name.data).first()
		if not artist:
			artist = Artist()
		populate_model(data, artist)
		for genre_id in genres_ids:
			genre = Genre.query.get(genre_id)
			artist.genres.append(genre)
		db.session.add(artist)
		db.session.commit()
		flash('Artist ' + form.name.data + ' was successfully listed!')
		return render_template('pages/home.html')
	flash('An error occurred. Artist ' + form.name.data + ' could not be listed.')
	return render_template('forms/new_artist.html', form=form)


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
	shows = Show.query.all()
	data = list(map(parse_show, shows))
	return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
	form = ShowForm()
	return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
	form = ShowForm(request.form)

	if form.validate():
		venue = Venue.query.get(form.venue_id.data)
		artist = Artist.query.get(form.artist_id.data)
		if not venue or not artist:
			abort(404)
		show = Show(start_time=form.start_time.data)
		show.artist = artist
		with db.session.no_autoflush:
			venue.artists.append(show)
		db.session.add(venue)
		db.session.commit()
		flash('Show was successfully listed!')
		return render_template('pages/home.html')
	flash('An error occurred. Show could not be listed.')
	return render_template('forms/new_show.html', form=form)


@app.errorhandler(404)
def not_found_error(error):
	return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
	return render_template('errors/500.html'), 500


if not app.debug:
	file_handler = FileHandler('error.log')
	file_handler.setFormatter(
		Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
	)
	app.logger.setLevel(logging.INFO)
	file_handler.setLevel(logging.INFO)
	app.logger.addHandler(file_handler)
	app.logger.info('errors')

# ----------------------------------------------------------------------------#
# Launch.
# ----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
	app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
	port = int(os.environ.get('PORT', 5000))
	app.run(host='0.0.0.0', port=port)
'''
