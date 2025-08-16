import datetime
from flask import Flask, abort, request
from flask_restful import Api, Resource, reqparse, marshal_with, fields
from flask_sqlalchemy import SQLAlchemy
import sys

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///events.db'
db = SQLAlchemy(app)

api = Api(app)

class Event(db.Model):
    __tablename__ = 'Events'
    id = db.Column(db.Integer, primary_key=True)
    event = db.Column(db.String(80), nullable=False)
    date = db.Column(db.Date, nullable=False)

with app.app_context():
    db.create_all()

class DateFormat(fields.Raw):
    def format(self, value):
        return value.strftime('%Y-%m-%d')

events_fields = {
    'id': fields.Integer,
    'event': fields.String,
    'date': DateFormat
}

class EventResource(Resource):
    def post(self):
        post_parser = reqparse.RequestParser()
        post_parser.add_argument(
            'event',
            type=str,
            help='The event name is required!',
            required=True,
            location='form'
        )
        post_parser.add_argument(
            'date',
            type=str,
            help="The event date with the correct format is required! The correct format is YYYY-MM-DD!",
            required=True,
            location='form'
        )
        args = post_parser.parse_args()

        try:
            event_date = datetime.datetime.strptime(args['date'], '%Y-%m-%d').date()
        except ValueError:
            return {'message': {
                'date': "The event date with the correct format is required! The correct format is YYYY-MM-DD!"}}, 400

        new_event = Event(
            event=args['event'],
            date=event_date
        )
        db.session.add(new_event)
        db.session.commit()
        return {
            "id": new_event.id,
            "event": new_event.event,
            "date": new_event.date.strftime("%Y-%m-%d"),
            "message": "The event has been added!"
        }, 200

    @marshal_with(events_fields)
    def get(self):
        start_time_str = request.args.get('start_time')
        end_time_str = request.args.get('end_time')

        if start_time_str and end_time_str:
            try:
                start_time = datetime.datetime.strptime(start_time_str, '%Y-%m-%d').date()
                end_time = datetime.datetime.strptime(end_time_str, '%Y-%m-%d').date()
                events = Event.query.filter(
                    Event.date >= start_time,
                    Event.date <= end_time
                ).all()
            except ValueError:
                return {'message': 'Invalid date format. Use YYYY-MM-DD.'}, 400
        else:
            events = Event.query.all()

        return events

class EventTodayResource(Resource):
    @marshal_with(events_fields)
    def get(self):
        events_today = Event.query.filter(Event.date == datetime.date.today()).all()
        return events_today

class EventByIdResource(Resource):

    @marshal_with(events_fields)
    def get(self, event_id):
        event = Event.query.filter(Event.id == event_id).first()
        if event is None:
            abort(404, "The event doesn't exist!")
        return event

    def delete(self, event_id):
        event = Event.query.filter(Event.id == event_id).first()
        if event is None:
            abort(404, "The event doesn't exist!")
        db.session.delete(event)
        db.session.commit()
        return {"message": "The event has been deleted!"}, 200

api.add_resource(EventResource, '/event')
api.add_resource(EventTodayResource, '/event/today')
api.add_resource(EventByIdResource, '/event/<int:event_id>')

if __name__ == '__main__':
    if len(sys.argv) > 1:
        arg_host, arg_port = sys.argv[1].split(':')
        app.run(host=arg_host, port=arg_port)
    else:
        app.run()