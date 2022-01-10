from flask import Flask,send_file
import requests
import flask.scaffold
flask.helpers._endpoint_from_view_func = flask.scaffold._endpoint_from_view_func
from flask_restful import Api,Resource,reqparse,marshal_with,fields,abort
from  flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

API_KEY="6073dee017e4bfeb41c29456aa4ccb06"
BASE_URL_IMAGES="https://image.tmdb.org/t/p/w500"
app = Flask(__name__)
api = Api(app)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///web.db'
db = SQLAlchemy(app)


def average(ratings_of_movie):
    score_sum=0
    counter=0
    for current_rating in ratings_of_movie:
        score_sum+=current_rating.score
        counter=counter+1
    average_score=score_sum/counter
    return average_score

#data base functions
def get_actor_name_by_actorId(actor_id):
    actor_by_actorId = Actor.query.filter_by(actorId=actor_id).first()
    if not actor_by_actorId:
        return None
    actor_name=actor_by_actorId.actorName
    return actor_name

def get_movie_id_by_movie_name(movie_name):
    movie_by_movie_name = Movies.query.filter_by(movieName=movie_name).first()
    if not movie_by_movie_name:
        return False
    movie_id = movie_by_movie_name.movieId
    return movie_id

def get_actorId_by_actorName(actor_name):
    actor_by_actorName = Actor.query.filter_by(actorName=actor_name).first()
    if not actor_by_actorName:
        return None
    actor_id = actor_by_actorName.actorId
    return actor_id

def insert_now_playing_movies():
    search_latest_movies=requests.get("https://api.themoviedb.org/3/movie/now_playing?api_key="+API_KEY).json()
    latest_movies_results=search_latest_movies['results']
    if not latest_movies_results:
        return
    for current_movie_info in latest_movies_results:
        insert_movie_by_movie_info(current_movie_info)


#tmdb api functions
def insert_movie_by_movie_info(movie_info):#main function for insert movies with all details (actors,trailer,poster)
    movie_tmdb_id = str(movie_info['id'])
    movie_title = movie_info['title']
    movie_tmdb_genre_id = movie_info['genre_ids'][0]
    movie_genre_id=check_genreId_by_genreAPI_id(movie_tmdb_genre_id)
    movie_description = movie_info['overview']
    print(movie_title)
    is_movie_exist = Movies.query.filter_by(movieName=movie_title).first()
    if is_movie_exist:
        print("movie already exist")
        return movie_title
    new_movie = Movies(movieName=movie_title, movieIdAPI=movie_tmdb_id, description=movie_description,genreId=movie_genre_id)
    db.session.add(new_movie)
    db.session.commit()
    # insert poster to Poster table
    current_movie = Movies.query.filter_by(movieName=movie_title, movieIdAPI=movie_tmdb_id,description=movie_description, genreId=movie_genre_id).first()
    movie_id = current_movie.movieId
    movie_poster_link = BASE_URL_IMAGES + movie_info['poster_path']
    new_poster = Posters(movieId=movie_id, posterLink=movie_poster_link)
    db.session.add(new_poster)
    db.session.commit()
    # insert the actors of the movie for Actor table and Movie-Actor table
    crew = requests.get("https://api.themoviedb.org/3/movie/" + str(movie_tmdb_id) + "/credits?api_key=" + API_KEY).json()
    actors_list = crew['cast']
    for x in range(5):
        current_actor_name = actors_list[x]['name']
        is_current_actor_exsist = Actor.query.filter_by(actorName=current_actor_name).first()
        if not is_current_actor_exsist:
            new_actor = Actor(actorName=current_actor_name)
            db.session.add(new_actor)
            db.session.commit()
        current_actor_key = Actor.query.filter_by(actorName=current_actor_name).first().actorId
        new_actor_movie = Actor_Movies(actorId=current_actor_key, movieId=movie_id)
        db.session.add(new_actor_movie)
        db.session.commit()
    # insert trailer for Trailers table
    search_trailer = requests.get("https://api.themoviedb.org/3/movie/"+movie_tmdb_id+"/videos?api_key=" + API_KEY).json()
    search_trailer_results = search_trailer['results']
    if not search_trailer_results:
        print("no trailer")
        return
    for current_video in search_trailer_results:
        trailer_site = current_video['site']
        trailer_key = current_video['key']
        video_type=current_video['type']
        if trailer_site == "YouTube" and video_type=="Trailer":
            youtube_link = "https://www.youtube.com/embed/" + trailer_key
            new_trailer = Trailers(trailerLink=youtube_link, movieId=movie_id)
            db.session.add(new_trailer)
            db.session.commit()
            break
def insert_movie_by_movie_name(movie_name):
    search_movie = requests.get("https://api.themoviedb.org/3/search/movie?api_key=" + API_KEY + "&query="+movie_name).json()
    search_movie_results = search_movie['results']
    if not search_movie_results:
        print("no results")
        return False
    movie_info=search_movie_results[0]
    return insert_movie_by_movie_info(movie_info)
def check_genreId_by_genreAPI_id(genre_api_id):
    genre_by_genreAPI_id=Genre.query.filter_by(genreAPIId=genre_api_id).first()
    if not genre_by_genreAPI_id:
        print("no such genre")
        return
    genre_id=genre_by_genreAPI_id.genreId
    return genre_id
def update_current_popular_movies():
    db.session.query(Popular_Movies).delete()
    db.session.commit()
    search_popular_movies = requests.get("https://api.themoviedb.org/3/movie/popular?api_key=" + API_KEY).json()
    popular_movies_results = search_popular_movies['results']
    if not popular_movies_results:
        return False
    counter=0
    for current_movie in popular_movies_results:
        counter=counter+1
        movie_info =current_movie
        insert_movie_by_movie_info(movie_info)
        movie_by_movieName=Movies.query.filter_by(movieName= movie_info['title']).first()
        current_movie_id=movie_by_movieName.movieId
        current_popular_movie=Popular_Movies(movieId=current_movie_id)
        db.session.add(current_popular_movie)
        db.session.commit()
        if(counter==3):
            return True


class Users(db.Model):
    userId = db.Column(db.Integer, primary_key=True,autoincrement=True)
    username = db.Column(db.String(20), nullable=False)
    password = db.Column(db.String(20), nullable=False)


class Rating(db.Model):
    ratingId = db.Column(db.Integer, primary_key=True,autoincrement=True)
    userId = db.Column(db.Integer, nullable=False)
    score=db.Column(db.Integer,nullable=False)
    movieId = db.Column(db.Integer, nullable=False)
    comment=db.Column(db.String(500),nullable=True)


class Movies(db.Model):
    movieId = db.Column(db.Integer, primary_key=True,autoincrement=True)
    movieName = db.Column(db.String(30), nullable=False)
    movieIdAPI=db.Column(db.String,nullable=False)
    description = db.Column(db.String(200), nullable=False)
    genreId=db.Column(db.Integer,nullable=False)

class Genre(db.Model):
    genreId=db.Column(db.Integer, primary_key=True,autoincrement=True)
    genreName = db.Column(db.String(15), nullable=False)
    genreAPIId = db.Column(db.Integer, nullable=False)


class Posters(db.Model):
    posterId=db.Column(db.Integer, primary_key=True,autoincrement=True)
    movieId=db.Column(db.Integer, nullable=False)
    posterLink=db.Column(db.Integer,nullable=False)


class History(db.Model):
    eventId=db.Column(db.Integer, primary_key=True,autoincrement=True)
    userId = db.Column(db.Integer, nullable=False)
    eventType=db.Column(db.Integer,nullable=False)


class Actor(db.Model):
    actorId=db.Column(db.Integer, primary_key=True,autoincrement=True)
    actorName=db.Column(db.String(20), nullable=False)

class Actor_Movies(db.Model):
    actorMovieId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    actorId=db.Column(db.Integer,nullable=False)
    movieId=db.Column(db.Integer,nullable=False)

class Trailers(db.Model):
    trailerId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    trailerLink = db.Column(db.String(100), nullable=False)
    movieId = db.Column(db.Integer, nullable=False)

class Popular_Movies(db.Model):
    key = db.Column(db.Integer, primary_key=True, autoincrement=True)
    movieId = db.Column(db.Integer, nullable=False)


rating_put_args=reqparse.RequestParser()
rating_put_args.add_argument("score",type=int,help="score is required",required=True)
rating_put_args.add_argument("comment",type=str,required=False)

register_put_args=reqparse.RequestParser()
register_put_args.add_argument("username",type=str,help="username is required",required=True)
register_put_args.add_argument("password",type=str,help="password is required",required=True)



class ratings(Resource):
    def get(self,movie_id,user_id):
        ratings_by_movieId = Rating.query.filter_by(movieId=movie_id).all()
        if not ratings_by_movieId:
            return {
                'average': False,
                'userScore': False
            }
        avg=average(ratings_by_movieId)
        rating_by_userId=Rating.query.filter_by(userId=user_id,movieId=movie_id).first()
        if not rating_by_userId:
            score_by_user=False
        else:
            score_by_user=rating_by_userId.score
        info={
            'average':avg,
            'userScore':score_by_user
        }
        return info

    def post(self,movie_id,user_id):
        args=rating_put_args.parse_args()
        score=args['score']
        if not args['comment']:
            new_rating=Rating(userId=user_id,score=score,movieId=movie_id)
        else:
            rating_comment=args['comment']
            new_rating=Rating(userId=user_id,score=score,movieId=movie_id,comment=rating_comment)
        already_voted=Rating.query.filter_by(userId=user_id,movieId=movie_id).first()
        if already_voted!=None:
            already_voted.score=score
            db.session.commit()
        else:
            db.session.add(new_rating)
            db.session.commit()
        return True

class posters(Resource):
    def get(self,movie_id):
        poster_by_movieId = Posters.query.filter_by(movieId=movie_id).first()
        if not poster_by_movieId:
            print("no poster for this movie id")
            return
        poster_link =poster_by_movieId.posterLink
        return poster_link

class movies_with_actor(Resource):
    def get(self,actor_name):
        all_movies=[]
        actor_id=get_actorId_by_actorName(actor_name)
        movies_by_actorId=Actor_Movies.query.filter_by(actorId=actor_id).all()
        if not movies_by_actorId:
            return False
        for movie in movies_by_actorId:
            movie_id=movie.movieId
            all_movies.append(movie_id)
        return all_movies

class search_movie(Resource):
    def get(self,movie_name):#search title
        movie_title_search=Movies.query.filter_by(movieName=movie_name).first()
        if movie_title_search!=None:
            print("didnt work hard")
            return movie_title_search.movieId
        movie_title=insert_movie_by_movie_name(movie_name)
        if movie_title==None:
            movie_title=insert_movie_by_movie_name(movie_name)
        movie_id=get_movie_id_by_movie_name(movie_title)
        return movie_id

class register(Resource):
    def post(self):
        args=register_put_args.parse_args()
        username=args['username']
        password=args['password']
        user_by_username=Users.query.filter_by(username=username).first()
        if user_by_username!=None:
            return False
        new_user=Users(username=username,password=password)
        db.session.add(new_user)
        db.session.commit()
        fo=open("gg.txt","w")
        fo.write(username)
        fo.close()
        return True

class movie_info(Resource):
    def get(self,movie_id):
        movie_by_movieId = Movies.query.filter_by(movieId=movie_id).first()
        if movie_by_movieId == None:
            return False
        movie_title = movie_by_movieId.movieName
        genre_id=movie_by_movieId.genreId
        genre_by_genreId=Genre.query.filter_by(genreId=genre_id).first()
        genre_name=genre_by_genreId.genreName
        all_actors_in_movie = []
        actors_by_movieId = Actor_Movies.query.filter_by(movieId=movie_id).all()
        if not actors_by_movieId:
            all_actors_in_movie=False
        else:
            for actor_in_movie in actors_by_movieId:
                actor_name = get_actor_name_by_actorId(actor_in_movie.actorId)
                all_actors_in_movie.append(actor_name)
        poster_link=False
        poster_by_movieId = Posters.query.filter_by(movieId=movie_id).first()
        if  poster_by_movieId!=None:
            poster_link = poster_by_movieId.posterLink
        movie_description=False
        movie_description_by_movieId = Movies.query.filter_by(movieId=movie_id).first()
        if movie_description_by_movieId != None:
            movie_description = movie_description_by_movieId.description
        trailer_link=False
        trailer_link_by_movieId = Trailers.query.filter_by(movieId=movie_id).first()
        if  trailer_link_by_movieId:
            trailer_link = trailer_link_by_movieId.trailerLink

        all_movie_info={
            'title':movie_title,
            'description':movie_description,
            'actors':all_actors_in_movie,
            'poster':poster_link,
            'trailer':trailer_link,
            'genre':genre_name
        }
        return all_movie_info


class login(Resource):
    def get(self,username,password):
        user_by_conditions=Users.query.filter_by(username=username,password=password).first()
        if not user_by_conditions:
            return False
        else:
            response={
                'userId':user_by_conditions.userId,
                'username':user_by_conditions.username
            }
            return response


class popular_movies(Resource):
    def get(self):
        popular_movies_list=Popular_Movies.query.all()
        movies_id_list=[]
        if not popular_movies_list:
            return False
        for current_movie in popular_movies_list:
            movies_id_list.append(current_movie.movieId)
        return movies_id_list

api.add_resource(ratings,"/rating/<int:movie_id>/<int:user_id>")
api.add_resource(posters,"/poster/<int:movie_id>")
api.add_resource(movies_with_actor,"/actor/<string:actor_name>")
api.add_resource(search_movie,"/search/<string:movie_name>")
api.add_resource(register,"/register")
api.add_resource(movie_info,"/movie_info/<int:movie_id>")
api.add_resource(login,"/login/<string:username>/<string:password>")
api.add_resource(popular_movies,"/popular_movies")


if __name__ == "__main__":
    app.run(debug=True,host='0.0.0.0')
