[![Build Status](
https://travis-ci.com/sheep7/leopard-lavatory.svg?branch=master)](
https://travis-ci.com/sheep7/leopard-lavatory)
[![codecov](
https://codecov.io/gh/sheep7/leopard-lavatory/branch/master/graph/badge.svg)](
https://codecov.io/gh/sheep7/leopard-lavatory)



# leopard-lavatory
fetch public information from Swedish authorities and make them available as alerts

---

inspired by the frustrating similarity of reality with _The Hitchhikers Guide to the Galaxy_

> 'But the plans were on display...'
> 'On display? I eventually had to go down to the cellar to find them.'
> 'That's the display department.'
> 'With a flashlight.'
> 'Ah, well, the lights had probably gone.'
> 'So had the stairs.'
> 'But look, you found the notice, didn't you?
> 'Yes' said Arthur, 'yes I did. It was on display in the bottom of a locked filing cabinet stuck in
  a disused lavatory with a sign on the door saying "Beware of the Leopard".'

> 'There's no point acting all surprised about it. All the planning charts and demolition orders 
  have been on display in your local planning department in Alpha Centauri for fifty of your Earth
  years, so you've had plenty of time to lodge any formal complaint and it's far too late to start 
  making a fuss about it now.'

## Running in development

Install all requirements (preferably in a `virtualenv`):

```
$ pip install -r requirements.txt
```

Then run the app using:

```
$ FLASK_APP=leopard_lavatory/web FLASK_SECRET_KEY=somesecretkey flask run
```

If you like, you can put the variable declarations in your virtualenv's `bin/activate` script and simply run
`flask run`.

## Running celery

To run celery, we need at least one worker (a process that awaits tasks, runs them and returns the results).
A worker needs RabbitMQ or redis to be running as well. Please install one of the two.

To run the worker itself, run the following command from the root of the project:

```
$ celery -A leopard_lavatory.celery.tasks worker
```

If there are periodally scheduled tasks, we also need a beat process to send tasks to the worker(s) according to the
schedule:

```
$ celery -A leopard_lavatory.celery.tasks beat
```

Optionally, to see our tasks on a web interface, run flower (the example uses redis with default config as a broker):

```
$ flower --broker=redis://localhost:6379
```

## Email templates

### Previewing

To preview available emails, run the `email_preview.py` server:

```
FLASK_APP=leopard_lavatory/emailer/email_preview FLASK_ENV=development flask run
```

Then, open http://localhost:5000 as usual. Using it should be self-explanatory.

### Adding

To add a new email template, three files are needed: one for the HTML body of the new email, one for the text body, and a YAML file with defaults for the variables in the template.

Name all of the files the same, with the appropriate extension (eg. newfile.html, newfile.txt, newfile.yml). The YAML file should at least have the subject, everything else is optional (but might be nice to have to inspect your template properly in the email preview app).

Extend the base template if you want to add your own content. If the email is a call to action (ie, it will have a short text and a button for the user to perform an action), consider extending the cta (call to action) template instead.
