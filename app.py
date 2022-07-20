#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

#import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
#from flask_wtf import Form
from forms import *
from flask_migrate import Migrate

from sqlalchemy import and_, func
from models import *
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
db.init_app(app)
app.config.from_object('config')
moment = Moment(app)
migrate = Migrate(app,db)


def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(str(value))
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime


@app.route('/')
def index():
  return render_template('pages/home.html')


@app.route('/venues')
def venues():
  
  cities = db.session.query(Venue.city, Venue.state).group_by(Venue.city, Venue.state).all()

  data =[]
  for city in cities:
    cityinfo = dict(city)
    venues = db.session.query(Venue.id,Venue.name).filter(
      and_(
        Venue.city == city.city,
        Venue.state == city.state
      )
    ).all()
    cityinfo['venues'] = [{
      'id' : v.id,
      'name' : v.name,
      'num_upcoming_shows' : Show.query.filter(Show.venue_id == v.id).count()
    } for v in venues]
    data.append(cityinfo)
  
  return render_template('pages/venues.html', areas=data)
  
  

@app.route('/venues/search', methods=['POST'])
def search_venues():
  search_term = request.form.get('search_term', '')
  results = Venue.query.filter(func.lower(Venue.name).like(f'%{search_term.lower()}%')).all()
  response = {
    "count": len(results),
    "data": [{
      "id": result.id,
      "name": result.name,
      "num_upcoming_shows": Show.query.filter(Show.start_time > datetime.now(), Show.venue_id == result.id).count()
    } for result in results]
  }
  return render_template('pages/search_venues.html', results=response, search_term=search_term)

  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  
  

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):

  #venue = Venue.query.filter(venue_id).first()
  venue = Venue.query.get(venue_id).as_dict()
  venue['genres'] = [genre for genre in venue['genres'].split(',')]
  venue['past_shows'] = Show.query.filter(Show.start_time <= datetime.now(),Show.venue_id== venue_id).all()
  venue['past_shows_count'] = Show.query.filter(Show.start_time <= datetime.now(), Show.venue_id == venue_id).count()
  venue['upcoming_shows'] = Show.query.filter(Show.start_time > datetime.now(),Show.venue_id== venue_id).all()
  venue['upcoming_shows_count'] = Show.query.filter(Show.start_time > datetime.now(), Show.venue_id == venue_id).count()

  return render_template('pages/show_venue.html', venue=venue)
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  
  # return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  try:
    form =VenueForm(request.form)
    venue = Venue(
      name = form.name.data,
      city = form.city.data,
      state = form.state.data,
      address = form.address.data,
      phone = form.phone.data,
      genres = form.genres.data,
      facebook_link = form.facebook_link.data,
      image_link = form.image_link.data,
      website = form.website_link.data,
      seeking_talent = form.seeking_talent.data, 
      seeking_description = form.seeking_description.data
      
    )
    db.session.add(venue)
    db.session.commit()
    flash('Venue ' + form.name.data + ' was successfully listed!')

  except Exception as err:
    flash('An error occurred. Venue ' + form.name.data + ' could not be listed. ' + str(err))
    db.session.rollback()
  finally:
    db.session.close()
  return render_template('pages/home.html')
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion

  # on successful db insert, flash success
  #flash('Venue ' + request.form['name'] + ' was successfully listed!')
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  #return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):

  try:
    venue = Venue.query.get(venue_id)
    db.session.delete(venue)
    db.session.commit()
    flash('Venue' + venue.name + ' was deleted!')
  except Exception as err:
    flash('Error deleting Venue! ' + str(err))
    db.session.rollback()
  finally:
    db.session.close()
  return render_template('pages/home.html')
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  #return None

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  data = Artist.query.all()
  return render_template('pages/artists.html', artists=data)
  # TODO: replace with real data returned from querying the database

@app.route('/artists/search', methods=['POST'])
def search_artists():

  search_term = request.form.get('search_term', '')
  results = Artist.query.filter(func.lower(Artist.name).like(f'%{search_term.lower()}%')).all()
  response = {
    "count": len(results),
    "data": [{
      "id": result.id,
      "name": result.name,
      "num_upcoming_shows": Show.query.filter(Show.start_time > datetime.now(), Show.artist_id == result.id).count()
    } for result in results]
  }
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))
  
  #return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  artist = Artist.query.get(artist_id).as_dict()
  artist['genres'] = [genre for genre in artist['genres'].split(',')]
  past_shows = Show.query.filter(Show.start_time <= datetime.now(), Show.artist_id == artist_id).all()
  upcoming_shows = Show.query.filter(Show.start_time > datetime.now(), Show.artist_id == artist_id).all()
  
  artist['past_shows'] = [{
    "venue_id": show.venue_id,
    "venue_name": Venue.query.get(show.venue_id).name,
    "venue_image_link": Venue.query.get(show.venue_id).image_link,
    "start_time": show.start_time
  } for show in past_shows]

  artist['upcoming_shows'] = [{
    "venue_id": show.venue_id,
    "venue_name": Venue.query.get(show.venue_id).name,
    "venue_image_link": Venue.query.get(show.venue_id).image_link,
    "start_time": show.start_time
  } for show in upcoming_shows]
  artist['past_shows_count'] = len(past_shows)
  artist['upcoming_shows_count'] = len(upcoming_shows)

  return render_template('pages/show_artist.html', artist=artist)
  # shows the artist page with the given artist_id
  # TODO: replace with real artist data from the artist table, using artist_id
  

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()

  artist = Artist.query.get(artist_id)
  form.name.process_data(artist.name)
  form.genres.process_data(artist.genres)
  form.city.process_data(artist.city)
  form.state.process_data(artist.state)
  form.phone.process_data(artist.phone)
  form.website_link.process_data(artist.website)
  form.facebook_link.process_data(artist.facebook_link)
  form.seeking_venue.process_data(artist.seeking_venue)
  form.seeking_description.process_data(artist.seeking_description)
  form.image_link.process_data(artist.image_link)

  return render_template('forms/edit_artist.html', form=form, artist=artist)
  
  # TODO: populate form with fields from artist with ID <artist_id>
  #return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):

  try:
    artist = Artist.query.get(artist_id)
    artist.name = request.form.get('name')
    artist.genres = request.form.get('genres')
    artist.city = request.form.get('city')
    artist.state = request.form.get('state')
    artist.phone = request.form.get('phone')
    artist.website = request.form.get('website_link')
    artist.facebook_link = request.form.get('facebook_link')
    artist.seeking_venue = request.form.get('seeking_venue')
    artist.seeking_description = request.form.get('seeking_description')
    artist.image_link = request.form.get('image_link')
    db.session.commit()
    flash('Artist updated successfully!')

  except Exception as err:
    db.session.rollback()
    flash('Error updating artist! ' + str(err))
  finally:
    db.session.close()
  return redirect(url_for('show_artist', artist_id=artist_id))
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes

  #return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue = Venue.query.get(venue_id)
  form.name.process_data(venue.name)
  for genre in venue.genres:
    for c in form.genres.iter_choices():
      if c[0] == genre:
        form.genres.process_data(c)
        form.address.process_data(venue.address)
        form.city.process_data(venue.city)
        form.state.process_data(venue.state)
        form.phone.process_data(venue.phone)
        form.website_link.process_data(venue.website)
        form.facebook_link.process_data(venue.facebook_link)
        form.seeking_talent.process_data(venue.seeking_talent)
        form.seeking_description.process_data(venue.seeking_description)
        form.image_link.process_data(venue.image_link)

      return render_template('forms/edit_venue.html', form=form, venue=venue)

  
  # TODO: populate form with values from venue with ID <venue_id>
  #return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):

  try:
    venue = Venue.query.get(venue_id)
    venue.name = request.form.get('name')
    venue.city = request.form.get('city')
    venue.state = request.form.get('state')
    venue.address = request.form.get('address')
    venue.phone = request.form.get('phone')
    venue.genres = request.form.get('genres')
    venue.facebook_link = request.form.get('facebook_link')
    venue.image_link = request.form.get('image_link')
    venue.website = request.form.get('website_link')
    venue.seeking_talent = request.form.get('seeking_talent')
    venue.seeking_description = request.form.get('seeking_description')
    db.session.commit()
    flash('Venue updated successfully!')
  except Exception as err:
      db.session.rollback()
      flash('Error updating venue!' + str(err))
  finally:
      db.session.close()

  return redirect(url_for('show_venue', venue_id=venue_id))

  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  #return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  try:
    form = ArtistForm(request.form)
    artist = Artist(
      name=form.name.data,
      city=form.city.data,
      genres=form.genres.data,
      state=form.state.data,
      phone=form.phone.data,
      image_link=form.image_link.data,
      seeking_description=form.seeking_description.data,
      seeking_venue=form.seeking_venue.data,
      website=form.website_link.data,
      facebook_link=form.facebook_link.data
    )

    db.session.add(artist)
    db.session.commit()
    flash('Artist ' + artist.name + ' was successfully listed!')
  
  except Exception as err:
    flash('Error adding new artist! ' + str(err))
    db.session.rollback()
  finally:
    db.session.close()
  return render_template('pages/home.html')
  
  # called upon submitting the new artist listing form
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion

  # on successful db insert, flash success
  #flash('Artist ' + request.form['name'] + ' was successfully listed!')
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
  #return render_template('pages/home.html')

str()
#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  shows = Show.query.all()
  for show in shows:
    show = show.as_dict()
    show['venue_name'] = Venue.query.get(show['venue_id']).name
    show['artist_name'] = Artist.query.get(show['artist_id']).name
    show['artist_image_link'] = Artist.query.get(show['artist_id']).image_link

  return render_template('pages/shows.html', shows=shows)

  # displays list of shows at /shows
  # TODO: replace with real venues data.

  #return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  try:
    show = Show(
      artist_id=request.form.get('artist_id'),
      venue_id=request.form.get('venue_id'),
      start_time=request.form.get('start_time')
    )
    db.session.add(show)
    db.session.commit()
    flash('Show was successfully listed!')
  except Exception as err:
    db.session.rollback()
    flash('An error occured. Show could not be listed.')
  finally:
    db.session.close()

  return render_template('pages/home.html')
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead

  # on successful db insert, flash success
  #flash('Show was successfully listed!')
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Show could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  #return render_template('pages/home.html')

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

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
