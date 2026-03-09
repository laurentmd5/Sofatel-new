import flask_session
print('module:', flask_session)
print('attrs sample:', dir(flask_session)[:80])
print('__file__:', getattr(flask_session, '__file__', None))
try:
    print('Session attribute:', getattr(flask_session, 'Session', None))
except Exception as e:
    print('error', e)
