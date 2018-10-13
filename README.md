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

If you like, you can put the variable declarations in your virtualenv's `bin/activate` script and simply run `flask run`.

## Running celery

`celery worker -A leopard_lavatory.web.tasks`

`celery -A leopard_lavatory.web.tasks beat`

`flower --broker=redis://localhost:6379`
