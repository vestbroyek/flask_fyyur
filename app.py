# ----------------------------------------------------------------------------#
# Imports
# ----------------------------------------------------------------------------#
import json
import dateutil.parser
from datetime import datetime
import babel
from flask import (
    Flask,
    render_template,
    request,
    Response,
    flash,
    redirect,
    url_for,
)
from flask_migrate import Migrate
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from config import SQLALCHEMY_DATABASE_URI
import sys

# ----------------------------------------------------------------------------#
# App Config.
# ----------------------------------------------------------------------------#
app = Flask(__name__)
moment = Moment(app)
app.config.from_object("config")
app.config["DEBUG"] = True
app.config["FLASK_ENV"] = "development"
app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI

db = SQLAlchemy(app)

migrate = Migrate(app, db)

artist_fields = [
    "name",
    "city",
    "state",
    "phone",
    "image_link",
    "genres",
    "facebook_link",
    "website",
    "seeking_venue",
    "seeking_description",
]

venue_fields = [
    "id",
    "name",
    "city",
    "state",
    "address",
    "phone",
    "image_link",
    "facebook_link",
    "genres",
    "website",
    "seeking_talent",
    "seeking_description",
]

# ----------------------------------------------------------------------------#
# Models.
# ----------------------------------------------------------------------------#
class Venue(db.Model):
    __tablename__ = "venues"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    website = db.Column(db.String(500))
    seeking_talent = db.Column(db.Boolean)
    seeking_description = db.Column(db.String(500))
    shows = db.relationship("Show", backref="venue")


class Artist(db.Model):
    __tablename__ = "artists"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(500))
    seeking_venue = db.Column(db.Boolean)
    seeking_description = db.Column(db.String(500))
    shows = db.relationship("Show", backref="artist")


class Show(db.Model):
    __tablename__ = "shows"

    id = db.Column(db.Integer, primary_key=True)
    venue_id = db.Column(db.Integer, db.ForeignKey("venues.id"))
    artist_id = db.Column(db.Integer, db.ForeignKey("artists.id"))
    start_time = db.Column(db.DateTime)


# ----------------------------------------------------------------------------#
# Filters.
# ----------------------------------------------------------------------------#
def format_datetime(value, format="medium"):
    if isinstance(value, str):
        date = dateutil.parser.parse(value)
    else:
        date = value
    if format == "full":
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == "medium":
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format, locale="en")


app.jinja_env.filters["datetime"] = format_datetime


# ----------------------------------------------------------------------------#
# Controllers.
# ----------------------------------------------------------------------------#
@app.route("/")
def index():
    return render_template("pages/home.html")


#  Venues
#  ----------------------------------------------------------------
@app.route("/venues")
def venues():
    # Get unique city-state combinations
    city_states = db.session.query(Venue.city, Venue.state).distinct().all()
    data = []

    for city, state in city_states:
        # Fetch venues for this city and state
        venues = db.session.query(Venue).filter_by(city=city, state=state).all()

        venue_data = []

        for venue in venues:
            # Count upcoming shows for this venue
            num_upcoming_shows = len(
                [show for show in venue.shows if show.start_time > datetime.now()]
            )

            venue_data.append(
                {
                    "id": venue.id,
                    "name": venue.name,
                    "num_upcoming_shows": num_upcoming_shows,
                }
            )

        data.append({"city": city, "state": state, "venues": venue_data})

    return render_template("pages/venues.html", areas=data)


@app.route("/venues/search", methods=["POST"])
def search_venues():
    # Get search term
    search_term = request.form.get("search_term", "")

    # Find venues based on substring search
    venues = Venue.query.filter(Venue.name.icontains(search_term)).all()

    # Check count of results
    result_count = len(venues)
    
    response = {
        "count": result_count,
        "data": venues
    }
    return render_template(
        "pages/search_venues.html",
        results=response,
        search_term=request.form.get("search_term", ""),
    )


@app.route("/venues/<int:venue_id>")
def show_venue(venue_id):
    # Get venue using venue_id
    venue = Venue.query.get(venue_id)

    if venue:
        # Get upcoming shows
        # print(type(venue.shows[0].start_time))
        venue.upcoming_shows = [
            show for show in venue.shows if show.start_time > datetime.now()
        ]
        # Get past shows
        venue.past_shows = [
            show for show in venue.shows if show.start_time < datetime.now()
        ]

        return render_template("pages/show_venue.html", venue=venue)
    else:
        # If no such venue exists, flash and redirect to venues home
        flash("Venue not found.")
        return redirect(url_for("venues"))


#  Create Venue
#  ----------------------------------------------------------------
@app.route("/venues/create", methods=["GET"])
def create_venue_form():
    form = VenueForm()
    return render_template("forms/new_venue.html", form=form)


@app.route("/venues/create", methods=["POST"])
def create_venue_submission():
    # Set up error handling
    error = False

    try:
        # Grab form data
        venue_data = {
            field: request.form.getlist(field)
            if field == "genres"
            else request.form.get(field)
            for field in venue_fields
        }

        # Need to figure out best way to convert this to bool
        if venue_data["seeking_talent"] == "y":
            venue_data["seeking_talent"] = True
        else:
            pass

        new_venue = Venue(**venue_data)

        db.session.add(new_venue)
        db.session.commit()

    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
    if error:
        flash(
            "An error occurred. Venue "
            + request.form.get("name")
            + " could not be listed."
        )
        return render_template("pages/home.html")
    else:
        flash("Venue " + request.form.get("name") + " was successfully listed!")
        return render_template("pages/home.html")


@app.route("/venues/<venue_id>", methods=["POST"])
def delete_venue(venue_id):
    method = request.form.get('_method', 'POST')

    if method == 'DELETE':
        try:
            Venue.query.filter_by(id=venue_id).delete()
            db.session.commit()
            flash("Venue successfully deleted.")
        except:
            print(sys.exc_info())
            db.session.rollback()
            flash("Venue could not be deleted.")
        finally:
            db.session.close()
        return redirect(url_for("venues"))


#  Artists
#  ----------------------------------------------------------------
@app.route("/artists")
def artists():
    artists = Artist.query.all()
    return render_template("pages/artists.html", artists=artists)


@app.route("/artists/search", methods=["POST"])
def search_artists():
    # Get search term
    search_term = request.form.get("search_term", "")
    # Find venues based on substring search
    artists = Artist.query.filter(Artist.name.icontains(search_term)).all()

    # Check count of results
    result_count = len(artists)
    
    response = {
        "count": result_count,
        "data": artists
    }

    return render_template(
        "pages/search_artists.html",
        results=response,
        search_term=request.form.get("search_term", ""),
    )


@app.route("/artists/<int:artist_id>")
def show_artist(artist_id):
    # Get artist by ID
    artist = Artist.query.get(artist_id)

    # Set shows
    artist.upcoming_shows = [
        show for show in artist.shows if show.start_time > datetime.now()
    ]
    artist.past_shows = [
        show for show in artist.shows if show.start_time < datetime.now()
    ]

    return render_template("pages/show_artist.html", artist=artist)


#  Update
#  ----------------------------------------------------------------
@app.route("/artists/<int:artist_id>/edit", methods=["GET"])
def edit_artist(artist_id):
    # Get artist
    artist = db.session.get(Artist, artist_id)

    # Fix genres field so that it can prepopulate
    artist.genres = artist.genres.strip('{}').split(',')

    # Populate form
    form = ArtistForm(obj=artist)

    return render_template("forms/edit_artist.html", form=form, artist=artist)


@app.route("/artists/<int:artist_id>/edit", methods=["POST"])
def edit_artist_submission(artist_id):

    # Get artist
    # Updated syntax to avoid deprecation warning
    artist = db.session.get(Artist, artist_id)

    try:
        # Get data from form
        artist_data = {
            field: request.form.getlist(field)
            if field == "genres"
            else request.form.get(field)
            for field in artist_fields
        }

        for field, value in artist_data.items():
            setattr(artist, field, value)

        # Deal with 'y' for seeking venue rather than bool
        if artist.seeking_venue == 'y':
            artist.seeking_venue = True
        else:
            artist.seeking_venue = False

        # Save to database
        db.session.add(artist)
        db.session.commit()
        return redirect(url_for("show_artist", artist_id=artist_id))

    except:
        flash('Could not update this artist')
        return redirect(url_for("show_artist", artist_id=artist_id))


@app.route("/venues/<int:venue_id>/edit", methods=["GET"])
def edit_venue(venue_id):
    # Get artist
    venue = db.session.get(Venue, venue_id)

    # Fix genres field so that it can prepopulate
    venue.genres = venue.genres.strip('{}').split(',')

    # Populate form
    form = VenueForm(obj=venue)

    return render_template("forms/edit_venue.html", form=form, venue=venue)


@app.route("/venues/<int:venue_id>/edit", methods=["POST"])
def edit_venue_submission(venue_id):

    # Get venue
    # Updated syntax to avoid deprecation warning
    venue = db.session.get(Venue, venue_id)

    print("Venue ID: ", venue.id)

    try:
        # Get data from form
        venue_data = {
            field: request.form.getlist(field)
            if field == "genres"
            else request.form.get(field)
            for field in venue_fields
        }

        for field, value in venue_data.items():
            setattr(venue, field, value)

        # Unsure why venue ID gets set to None, set again manually
        venue.id = venue_id

        # Deal with 'y' for seeking venue rather than bool
        if venue.seeking_talent == 'y':
            venue.seeking_talent = True
        else:
            venue.seeking_talent = False

        # Save to database
        db.session.add(venue)
        db.session.commit()
        return redirect(url_for("show_venue", venue_id=venue_id))

    except:
        print(sys.exc_info())
        flash('Could not update this venue')
        return redirect(url_for("show_venue", venue_id=venue_id))


#  Create Artist
#  ----------------------------------------------------------------
@app.route("/artists/create", methods=["GET"])
def create_artist_form():
    form = ArtistForm()
    return render_template("forms/new_artist.html", form=form)


@app.route("/artists/create", methods=["POST"])
def create_artist_submission():
    # Set up error handling
    error = False

    try:
        artist_data = {
            field: request.form.getlist(field)
            if field == "genres"
            else request.form.get(field)
            for field in artist_fields
        }

        if artist_data["seeking_venue"] == "y":
            artist_data["seeking_venue"] = True
        else:
            artist_data["seeking_venue"] = False

        new_artist = Artist(**artist_data)

        db.session.add(new_artist)
        db.session.commit()

    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()

    if error:
        flash(
            "An error occurred. Artist "
            + request.form.get("name")
            + " could not be listed."
        )
        return render_template("pages/home.html")
    else:
        flash("Artist " + request.form["name"] + " was successfully listed!")
        return render_template("pages/home.html")


#  Shows
#  ----------------------------------------------------------------
@app.route("/shows")
def shows():
    shows = Show.query.all()

    # Set details from related models
    for show in shows:
        show.venue_name = show.venue.name
        show.artist_name = show.artist.name
        show.artist_image_link = show.artist.image_link

    return render_template("pages/shows.html", shows=shows)


@app.route("/shows/create")
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template("forms/new_show.html", form=form)


@app.route("/shows/create", methods=["POST"])
def create_show_submission():
    # Set up error handling
    error = False

    try:
        show_fields = ["artist_id", "venue_id", "start_time"]
        show_data = {field: request.form.get(field) for field in show_fields}
        new_show = Show(**show_data)

        db.session.add(new_show)
        db.session.commit()

    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()

    if error:
        flash("An error occurred. Show could not be listed.")
        return render_template("pages/home.html")
    else:
        flash("Show was successfully listed!")
        return render_template("pages/home.html")


@app.errorhandler(404)
def not_found_error(error):
    return render_template("errors/404.html"), 404


@app.errorhandler(500)
def server_error(error):
    return render_template("errors/500.html"), 500


if not app.debug:
    file_handler = FileHandler("error.log")
    file_handler.setFormatter(
        Formatter("%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]")
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info("errors")

# ----------------------------------------------------------------------------#
# Launch.
# ----------------------------------------------------------------------------#
# Default port:
if __name__ == "__main__":
    app.run()
