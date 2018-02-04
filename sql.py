#!/web/cs2041/bin/python3.6.3
#this file is used to create the database that stores all info of the student

import sqlite3, csv, os, re

stuColumns = ['zid', 'full_name', 'email', 'program', 'birthday', 'home_latitude', 'home_longitude', 'home_suburb']
userColumns = ['zid', 'password']
coursesColumns = ['zid', 'courses']
postColumns = ['from','message', 'longitude', 'latitude', 'time', 'directory']


def add_data ():
	root_dir = "dataset-medium";
	#ADD TO TABLES
	for subdir, dirs, files in os.walk(root_dir):
		stu = {}

		for file in files:

			#Select student.txt file only
			if re.search(r'student.txt$', os.path.join(subdir, file)):
				with open(os.path.join(subdir, file)) as f:	
					reader = csv.reader(f, delimiter=':')
					for row in reader:
						stu[row[0]] = row[1].lstrip()
						#ADDING INTO TABLES

					#Deals with empty spaces
					for column in stuColumns:
						if column not in stu:
							stu[column] = ""
						
					#INSERT VALUES FOR STUDENT TABLE
					stu_values = (stu['zid'],stu['full_name'],stu['email'], stu['program'], stu['birthday'], stu['home_latitude'], stu['home_longitude'], stu['home_suburb'] )
					c.execute("INSERT INTO student VALUES (?, ?, ?, ? ,? ,? ,?, ?)",stu_values)

					
					#INSERT VALUES FOR USER TABLE
					user_values = (stu['zid'], stu['password'])	
					c.execute("INSERT INTO user VALUES (?, ?)",user_values)	

					#INSERT VALUES INTO COURSES TABLE
					#courses is a list (line separated by ,)
					#courses is encased with () remove this first

					stu['courses'] = stu['courses'][1:]
					stu['courses'] = stu['courses'][:-1]
					for courses in re.split(", ", stu['courses']):
						courses_value = (stu['zid'], courses)
						c.execute("INSERT INTO courses VALUES (?, ?)", courses_value)

					stu['friends'] = stu['friends'][1:]
					stu['friends'] = stu['friends'][:-1]

					for friend in re.split(", ", stu['friends']):
						friend_value = (stu['zid'], friend)
						c.execute("INSERT INTO friend VALUES (?, ?)", friend_value)


			#ORDER
			#[ zid, post_id, message long, message lat, time, message, parent_id ]
			#the case when its not student.txt (0.txt 0-1.txt etc...)
			else:
				posts = {}
				post_id = ""
				parent_id = ""
				origin_id = ""

				#grab the zid and put it in the table (we need to maintain whos folder we're in)
				
				origin_id = re.sub('^.*/', '', subdir)
				#xprint(origin_id)

				if  re.search(r'[0-9].txt$', os.path.join(subdir, file)):
					with open(os.path.join(subdir, file)) as f:	
						reader = csv.reader(f, delimiter=':')
						for row in reader:
							posts[row[0]] = row[1].lstrip()
							#ADDING INTO TABLES



					#get the name of the file (1-1.txt) ->
					#separate by either parent and post id
					#2-1-1 beomces 2-1 and 2-1-1
					filename = os.path.join(subdir, file)
					search = re.search('([0-9]\-*[0-9]*\-*[0-9]*)\.txt', filename)
					
					if search:
						post_id = search.group(1)

					#dash indicates it is a reply to something
					if "-" in post_id:
						parent_id = re.sub('\-[0-9]*$', '', post_id)
					#already a parent comment
					else:
						parent_id = ""

			#Deals with empty spaces elements
			for column in postColumns:
				if column not in posts:
					posts[column] = ""

			#list of stuff to add to the posts table
			#remmeber to maintain order
			if not posts['from'] == "":
				post_values = [posts['from'], post_id, posts['longitude'], posts['latitude'], posts['time'], posts['message'], parent_id, origin_id]
			#	print(post_values)
				c.execute("INSERT INTO posts VALUES(?, ?, ?, ? ,? ,? ,?,?)",post_values)
				
	return;



#removes the file if it already exists
try:
   os.remove("the_database.db")
except OSError:
   pass


with sqlite3.connect("the_database.db") as connection:
	c = connection.cursor()

	#INITIALIZE TABLES

	#STUDENT TABLE
	c.execute("""CREATE TABLE student(
		Z_ID VARCHAR(8), 
		FULL_NAME VARCHAR(20), 
		EMAIL VARCHAR(20), 
		PROGRAM VARCHAR(20), 
		BIRTHDAY VARCHAR(20), 
		HOME_LONG VARCHAR(20), 
		HOME_LAT VARCHAR(20),
		HOME_SUB VARCHAR(20),
		PRIMARY KEY(Z_ID))""");


	#USER TABLE
	c.execute("""CREATE TABLE user(
		Z_ID VARCHAR(8), 
		PASSWORD VARCHAR(20),
		FOREIGN KEY (Z_ID) REFERENCES student(Z_ID))
		""")

	#COURSES TABLE
	#z3461590 
	c.execute("""CREATE TABLE courses(
		Z_ID VARCHAR(8), 
		COURSES VARCHAR(20),
		PRIMARY KEY (Z_ID, COURSES),
		FOREIGN KEY (Z_ID) REFERENCES student(Z_ID))
		""")	



	c.execute("""CREATE TABLE posts(
		Z_ID VARCHAR(8),
		POST_ID VARCHAR(20),
		MESSAGE_LONG VARCHAR(20), 
		MESSAGE_LAT VARCHAR(20),
		M_TIME VARCHAR(20),
		MESSAGE VARCHAR(100),
		PARENT_ID VARCHAR(20),
		ORIG_DIRECTORY VARCHAR(20),
		FOREIGN KEY (Z_ID) REFERENCES student(Z_ID))
		""")	
	#not really sure how to deal with unique issues (splitting comments and posts wont work i think)
	#	PRIMARY KEY (Z_ID, POST_ID, PARENT_ID),

	c.execute("""CREATE TABLE friend(
		Z_ID VARCHAR(8),
		FRIEND_ID VARCHAR(8),
		PRIMARY KEY (Z_ID, FRIEND_ID),
		FOREIGN KEY (Z_ID) REFERENCES student(Z_ID)) 
		""")	


	add_data()











