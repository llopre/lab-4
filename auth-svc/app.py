from bottle import Bottle, route, run, get, template, post, request, response
import pymysql
import os
import datetime
import python_jwt as jwt
import Crypto.PublicKey.RSA as RSA
# import json


def createUser(user,password,admin):
	mysql_config = {
		'host':'localhost',
		'db': 'users',
		'user':'lucas',
		'passwd':'1234'
	}
	cnx = None
	try: 
		cnx = pymysql.connect(**mysql_config)
		insertStr = "INSERT INTO credentials (username,password,admin) VALUES(%s,%s,%s)"
		data = (user,password,admin)
		cursor = cnx.cursor()
		cursor.execute(insertStr,data)
		cnx.commit()
		cursor.close()
		cnx.close()
	except pymysql.MySQLError as err:
		print ("MySQLError: {0}".format(err))
		return False, False
		
	cnx = pymysql.connect(**mysql_config)
	selectid = "select id from credentials where username='{0}' and password='{1}'".format(user, password)
	cursor = cnx.cursor()
	cursor.execute(selectid)
	row = cursor.fetchone()
	cursor.close()
	cnx.close()
	return True, row[0]

def searchUser(user,password):
	mysql_config = {
		'host':'localhost',
		'db': 'users',
		'user':'lucas',
		'passwd':'1234'
	}
	cnx = None
	try: 
		cnx = pymysql.connect(**mysql_config)

		selectStr = "select id , count(*) from credentials where username='{0}' and password='{1}'".format(user, password)
		cursor = cnx.cursor()
		cursor.execute(selectStr)
		row = cursor.fetchone()
		cursor.close()
		cnx.close()
		if row[1] > 0:
			return True, row[0] 
		else:
			return False, False	
	except pymysql.MySQLError as err:
		print ("Failed to select.....{0}".format(err))
		return False, False

def auditEvent(event, userid):
	mysql_config = {
		'host':'localhost',
		'db': 'users',
		'user':'lucas',
		'passwd':'1234'
	}
	cnx = None
	try: 
		cnx = pymysql.connect(**mysql_config)
		insertStr = "INSERT INTO audit_event (event,userid) VALUES('{0}',{1})".format(event,userid)
		print (insertStr)
		cursor = cnx.cursor()
		cursor.execute(insertStr)
		cnx.commit()
		cursor.close()
		cnx.close()
	except pymysql.MySQLError as err:
		print ("MySQLError: {0}".format(err))
		return False

	return True

def getEvents(userid,admin):
	mysql_config = {
		'host':'localhost',
		'db': 'users',
		'user':'lucas',
		'passwd':'1234'
	}
	cnx = None
	try: 
		cnx = pymysql.connect(**mysql_config)
		if admin == "s":
			resultStr = "SELECT * FROM audit_event"
		else:	 	
			resultStr = "SELECT event, userid FROM audit_event WHERE userid='{0}'".format(userid)
		print (resultStr)
		cursor = cnx.cursor()
		cursor.execute(resultStr)
		events = dict()
		i = 0
		for res in cursor:
			dict_event = {"id": None, "event": None}
			dict_event['id'] = res[1]
			dict_event['event'] = res[0]
			events[i] = dict_event
			i = i+1

		cnx.commit()
		cursor.close()
		cnx.close()
		
	except pymysql.MySQLError as err:
		print ("MySQLError: {0}".format(err))
		return None

	return events


app = Bottle()



@app.route('/hello', method="GET")
def hello():
	return "Hello World!"

@app.get('/')
@app.get('/hello/<name>', method="GET")
def greet(name='Stranger'):
	return template('Hello {{name}}',name=name)


@app.post('/param')
def hello_json():
	data = request.json
	param = data['param']
	ret = {"status": "OK", "param": param}
	return ret

@app.post('/login')
def login_json():
	data = request.json
	a,userid = searchUser(data["username"], data["password"])
	if a:
		auditEvent("Correct Login",userid)
		payload = {'userid': userid, 'username': data["username"] }
		token = generate_token(payload)
		return { "status": "OK","token": token ,"message": "Bienvenido"}
	auditEvent("Wrong Login", "NULL")
	
	return {"status": "ERROR", "message": "se ingreso mal el usuario"}

@app.post('/register')
def register_json():
	data = request.json
	a, userid = createUser(data["username"], data["password"],data["admin"])
	if a:
		auditEvent("Correct Register",userid)
		return {"status": "OK", "message": "se registro correctamente el usuario"}
	else:
		return {"status": "ERROR", "message": "No se pudo registrar"}
		auditEvent("Wrong Register", "NULL")

@app.post('/logout')
def logout_json():
	data = request.json
	a, userid = searchUser(data["username"], data["password"])
	if a:
		auditEvent("Correct Logout",userid)
		return { "status": "OK", "message": "ADIOS"}
	else:
		auditEvent("Correct Logout","NULL")
		return { "status": "OK", "message": "ADIOS"}

@app.post('/home')
def events_json():
	print "entro a home"
	data = request.json
	events = getEvents(data["userid"],data["admin"])
	print events
	return events

def generate_token(payload):
	private_key_file = os.path.join(os.path.dirname(__file__), 'keypair.priv')
	with open(private_key_file, 'r') as fd:
		private_key = RSA.importKey(fd.read())
	token = jwt.generate_jwt(payload,private_key,'RS256',datetime.timedelta(minutes=5))
	return token

def validate_token(token):
	public_key_file = os.path.join(os.path.dirname(__file__), 'keypair.pub')
	with open(public_key_file, 'r') as fd:
		public_key = RSA.importKey(fd.read())
	try:
		header, claims = jwt.verify_jwt(token,public_key,['RS256'])
	except jwt.exceptions.SignatureError:
		print ('invalid token signature')
		raise SystemExit()




run(app,host='127.0.0.1',port=8081)
