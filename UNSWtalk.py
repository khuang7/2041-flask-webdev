#!/web/cs2041/bin/python3.6.3

# written by Kevin Huang October 2017
# as a starting point for COMP[29]041 assignment 2
# https://cgi.cse.unsw.edu.au/~cs2041/assignments/UNSWtalk/


#1. run python3 UNSWtalk.py
#2. access via cgi


import os
from flask import Flask, render_template, session, g, redirect, url_for, request
import sqlite3, re

students_dir = "dataset-medium";

app = Flask(__name__, static_url_path='', static_folder=students_dir) #static folder needed because images not all images in static
app.database = "the_database.db"
DATABASE = "the_database.db"

#HELPER FUNCTIONS
#https://www.youtube.com/watch?v=_vrAjAHhUsA


def connect_db():
    """Connect to specific database file"""
    return sqlite3.connect(app.database)


def returnName(user_id):
    """returns the full name given a user id"""

    g.db = connect_db()
    cur = g.db.execute("SELECT FULL_NAME FROM student WHERE Z_ID = '%s'" %(user_id))
    name_list = [dict(FULL_NAME = row[0]) for row in cur.fetchall()]
    return name_list[0]['FULL_NAME']


#HOME PAGE
@app.route('/', methods=['GET','POST'])
@app.route('/start', methods=['GET','POST'])
def start():
    """
       Redirects to Home Page
       If not logged in then login page appears
       If logged in then post page appears 
    """
    #if not logged in
    if not session.get('logged_in'):
        return render_template('start.html')

    #if logged in already
    else:
        #just go to posts page
        return posts()
    return render_template('start.html')


#LOGIN
@app.route('/login', methods=['GET','POST'])
def login():
    """ Login authentication portion """

    error = None
    #once the thing has been clicked on
    if request.method == 'POST':
        zid = request.form['zid']
        password = request.form['password']
       
        #captures all the user and password into a dict users
        g.db = connect_db() #g is used for temporary objects
        cur = g.db.execute('select * from user')
        users = {}
        for row in cur.fetchall():
            users[row[0]] = row[1]
        
        
        #check if username/password combo exists
        if zid in users:
            #username definitely exists
            #check if password is correct
            if (users[zid] == password):
                #authenticated
                #create session
                session['logged_in'] = True
                session['user'] = zid #store user id
                session['name'] = returnName(zid)
                #should i reset all these?
                return profile(zid)

            else:
                #incorrect password
                error = "Incorrect password but account exists"
                return render_template('start.html', error = error)
            
        else:
            error = "Username doesn't exist"
            return render_template('start.html', error = error)
        
    else:
        return render_template('start.html')



#POSTS
@app.route('/posts', methods=['GET','POST'])
def posts():
    search_results = []
    g.db = connect_db() #g is used for temporary objects
    cur = g.db.execute('SELECT POST_ID, MESSAGE, Z_ID, M_TIME FROM posts ORDER BY M_TIME desc')

    posts = []
    for row in cur.fetchall():
        if re.search(r'^[0-9]$', row[0]):
            posts.append(dict(POST_ID=row[0], MESSAGE=row[1], Z_ID=row[2], M_TIME=row[3], POSTER_NAME = returnName(row[2])))

    cur = g.db.execute('SELECT POST_ID, MESSAGE, Z_ID, M_TIME FROM posts ORDER BY M_TIME desc')
    if request.method == 'POST':
        query = request.form['query']
        for row in cur.fetchall():
            if query in row[1]:
                search_results.append(dict(POST_ID=row[0], MESSAGE=row[1], Z_ID=row[2], 
                    M_TIME=row[3], POSTER_NAME = returnName(row[2])))
    return render_template('posts.html', posts = posts, search_results = search_results) #render template



#LOGOUT
@app.route("/logout")
def logout():
    """ Processes a log out by changing session """
    session['logged_in'] = False
    return start()


#Profile
@app.route('/profile/<userid>', methods=['GET','POST'])
def profile(userid):
    """ Shows profile given a specific userid """
    user = userid
    profile_type = "Not Logged in"

    #List of friends for that particular user
    g.db = connect_db() #g is used for temporary objects
    cur = g.db.execute("select f.Z_ID, f.FRIEND_ID, s.FULL_NAME FROM friend f JOIN STUDENT s on f.FRIEND_ID = s.Z_ID where f.Z_ID = '%s'" % (user))
    friend_list = [dict(Z_ID = row[0], FRIEND_ID = row[1], FRIEND_NAME = row[2]) for row in cur.fetchall()]


    
    if session['logged_in']:
        cur = g.db.execute("select f.Z_ID, f.FRIEND_ID, s.FULL_NAME FROM friend f JOIN STUDENT s on f.FRIEND_ID = s.Z_ID where f.Z_ID = '%s'" % (session['user']))
        session_friend_list = [dict(Z_ID = row[0], FRIEND_ID = row[1], FRIEND_NAME = row[2]) for row in cur.fetchall()]
    
    #Determines whether the profile is the current user, a friend of the logged in person or not a friend
    if session['user'] == userid:
        profile_type = "you"
    else: 
        profile_type = "not_friend"

    for row in session_friend_list:
        if row['FRIEND_ID'] == user:
            profile_type = "friend"
    g.db.close()


    #list of posts by specific profile user
    g.db = connect_db()
    cur = g.db.execute("SELECT POST_ID, MESSAGE, Z_ID, M_TIME FROM posts WHERE ORIG_DIRECTORY = '%s' ORDER BY M_TIME desc" %(userid))
    posts = []
    for row in cur.fetchall():
        if re.search(r'^[0-9]$', row[0]):
            posts.append(dict(POST_ID=row[0], MESSAGE=row[1], Z_ID=row[2], M_TIME = row[3], NAME = returnName(row[2])))

    g.db.close()
    g.db = connect_db()
    cur = g.db.execute("SELECT * from student WHERE Z_ID = '%s'"%(user))
    #Grab important profile info    
    profile_info = [dict(Z_ID = row[0], FULL_NAME = row[1], EMAIL = row[2], PROGRAM = row[3], BIRTHDAY = row[4], HOME_LONG = row[5], HOME_LAT = row[6], HOME_SUB = row[7]) for row in cur.fetchall()]


    return render_template('profile.html', name = returnName(userid), user=userid, friend_list = friend_list, posts = posts, profile_info = profile_info, profile_type = profile_type)


#DELETE FRIEND
@app.route('/delete_friend/<userid>', methods=['GET','POST'])
def delete_friend(userid):
    """ Deletes a friend in the argument from user currently logged in list """
    g.db = connect_db()
    g.db.execute("DELETE from friend WHERE Z_ID = '%s' AND FRIEND_ID = '%s'" %(session['user'], userid))
    g.db.commit()
    g.db.close()

    message = returnName(userid) + "has been deleted"

    #need to warn user that user has been deleted
    return profile(session['user'])



#ADD FRIEND
@app.route('/add_friend/<userid>', methods=['GET','POST'])
def add_friend(userid):
    """ Adds a friend in the argument from user currently logged in list """
   
    g.db = connect_db()
    values = [session['user'], userid]
    g.db.execute("INSERT INTO friend VALUES (?, ?)",values)
    g.db.commit()
    g.db.close

    return profile(session['user'])



#User Search
@app.route('/search', methods=['GET','POST'])
def search():
    if request.method == 'POST':
        query = request.form['query']
        #query can be like a name or part of a name even
        g.db = connect_db()            #like operators searches for the pattern
        cur = g.db.execute("SELECT Z_ID, FULL_NAME FROM student WHERE FULL_NAME LIKE '%s'" % ('%' + query + '%') )

        search_list = [dict(Z_ID = row[0], FULL_NAME = row[1]) for row in cur.fetchall()]

        return render_template('search_results.html', search_list = search_list)

    else: 
        return start()

#Displaying Comments
@app.route('/comments/<zid>/<post_id>/<orig_directory>', methods=['GET','POST'])
def comments(zid, post_id, orig_directory):
    """ displays comments from a certain post """
    g.db = connect_db() 


    #grabs comments that have replied to the postid
    cur = g.db.execute("SELECT posts.Z_ID, POST_ID, MESSAGE, M_TIME, PARENT_ID FROM posts JOIN student on posts.Z_ID = student.Z_ID WHERE posts.ORIG_DIRECTORY = '%s' ORDER BY POST_ID" %(orig_directory))
    main_posts = []
    comments = []

    #we have the zid set, but we have to ensure we get the post numbers
    for row in cur.fetchall():
        compare1 = str(row[4])
        compare2 = str(post_id)

        
        if re.search(r'^%s$' %(post_id), row[1]):
            main_posts.append(dict(Z_ID=row[0], NAME = returnName(row[0]), POST_ID=row[1], MESSAGE=row[2], M_TIME=row[3], PARENT_ID = row[4]) )  
    
        if compare1 == compare2:

            comments.append(dict(Z_ID=row[0], NAME = returnName(row[0]), POST_ID=row[1], MESSAGE=row[2], M_TIME=row[3], PARENT_ID = row[4], orig_directory = orig_directory))



    if not comments:
        #returns back to the page we were currently on -> if comments don't exist
        return redirect(request.referrer)
    else:
        comment_length = len(comments)
        return render_template('comments.html', post = main_posts, comments=comments, orig_directory = orig_directory, comment_length = comment_length)



# Direct to comment form
@app.route('/make_comment_form/<zid>/<post_id>/<orig_directory>', methods=['GET','POST'])
def make_comment_form(zid, post_id, orig_directory, methods=['GET','POST']):
    """ links to the direct form, giving neccessary arguments so process comment knows where to make the comment """
    zid = zid
    post_id = post_id
    orig_directory = orig_directory

    return render_template('comment_form.html', zid = zid, name = returnName(zid), post_id = post_id, orig_directory = orig_directory)

# Process the comment
@app.route('/process_comment/<zid>/<post_id>/<orig_directory>', methods=['GET','POST'])
def process_comment(zid, post_id, orig_directory):
    """ adds the comment to the certain reply by incrementing the post_id appropriately """
    if request.method == 'POST':
        message = request.form['reply']

        #indicating its an empty string
        if not message:
            message = "You have entered nothing!"
            #Go back to make a form page
            return "pls enter something in the form man"

        g.db = connect_db() 
        cur = g.db.execute("SELECT Z_ID, POST_ID, ORIG_DIRECTORY FROM posts WHERE ORIG_DIRECTORY = '%s'" %(orig_directory))

        post_name = []
        for row in cur.fetchall():
            if re.search(r'^%s\-[0-9]*$' %(post_id), row[1]):

                post_name.append(dict(Z_ID = row[0], POST_ID = row[1]))
            g.db.close()


        another_list = []
        #post name contains all the replies we want
        #indicates that the list is empty and hence no comments for this has been made
        if not post_name:
            new_post_num = str(post_id) + "-0"

        else:
            for post in post_name:
                another_list.append(int(re.match('.*?([0-9]+)$', post['POST_ID']).group(1)))


            new_post_num = int(max(another_list))
            new_post_num = int(new_post_num) + 1
           
            new_post_num = str(post_id)+ "-"+ str(new_post_num)
            

        #NOW WE ADD TO DATABASE with our newly generated post_num

        g.db = connect_db() 
        values = [zid, new_post_num, "", "", "", message, post_id, orig_directory]
        g.db.execute("INSERT INTO posts VALUES (?, ?, ?, ? ,? ,? ,?, ?)",values)
            #have to commit for changes to occur
        g.db.commit()
        g.db.close()

        return profile(session['user'])


    return profile(session['user'])


#Directs to post form
@app.route('/makePost', methods=['GET','POST'])
def makePost():
    return render_template('post_form.html')


#Adding the post
@app.route('/processPost/<userid>', methods=['GET','POST'])
def processPost(userid):

    message = ""

    if request.method == 'POST':
        message = request.form['message']


        #indicating its an empty string
        if not message:
            message = "You have entered nothing!"
            #Go back to make a form page
            return "pls enter something in the form man"

        #indicating that a message has been put in (not empty)
        else:
            g.db = connect_db() 
            cur = g.db.execute("SELECT Z_ID, POST_ID, ORIG_DIRECTORY FROM posts WHERE ORIG_DIRECTORY = '%s'" %(userid))
            
            post_name = []
            for row in cur.fetchall():
                if re.search(r'^[0-9]*$', row[1]):
                    post_name.append(dict(Z_ID = row[0], POST_ID = row[1]))
            g.db.close()


            #clOSE DATABASE HERE COZ I HAVE TO OPEN AGAIN TO INSERT
            #conveniently it is already ordered but i might have ot make sure its ordered
            #now we have to sort posts so we have the highest number, (then +1 for next post)
            prev_highest_post = post_name[-1]['POST_ID']
            new_post_num = int(prev_highest_post) + 1

            #put all the values in a list
            values = [userid, new_post_num, "", "", "", message, "", userid]
            g.db = connect_db() 
            g.db.execute("INSERT INTO posts VALUES (?, ?, ?, ? ,? ,? ,?, ?)",values)
            #have to commit for changes to occur
            g.db.commit()
            g.db.close()
        
            #would send back to posts but return posts() gives an error (think it has to do with post form..)
            return profile(session['user'])

    else:
        return start()

#Create Account
@app.route('/create_account_form', methods=['GET','POST'])
def create_account_form():
    
    error_message = ""
    g.db = connect_db() 
    cur = g.db.execute("SELECT * from student")


    return render_template('account_form.html')




@app.route('/process_account_creation', methods=['GET','POST'])
def process_account_creation():
    g.db = connect_db() 
    cur = g.db.execute("SELECT Z_ID FROM student")
    current_list = []
    
    #grabs all current sutdents in the database
    for row in cur.fetchall():
        current_list.append(row[0])

    error_message = ""

    if request.method == 'POST':
        name = request.form['Full Name']
        email = request.form['Email']
        z_id = request.form['Z_ID']
        password = request.form['password']
        date = request.form['date']
        program = request.form['program']


        if not request.form.get('terms'):
            error_message = "Please accept the terms and conditions"
            return render_template('account_form.html', error_message = error_message)

        compulsory_forms = dict(full_name = name, email = email, z_id = z_id, password = password)

        #all compulsory fields have been entered
        complete = 1;
        uncomplete_list = []

        #checks if any values are missing in the compulsory forms
        for key, value in compulsory_forms.items():
            

            if key == 'z_id':
                #checks if zid already exists
                if value in current_list:
                    error_message = "zid already exists"
                    return render_template('account_form.html', error_message = error_message)

            if not value:
                uncomplete_list.append(key)
                complete = 0;

        if complete == 0:

            error_message = uncomplete_list
            return render_template('account_form.html', error_message = error_message)

        #otherwise we actually make the account
        else: 
            #this creates an account in student table
            values_student = [z_id, name, email, program, date, "", "", ""]
            g.db.execute("INSERT into student VALUES (?, ?, ?, ?, ?, ?, ?, ?)", values_student)

            values_users = [z_id, password]
            g.db.execute("INSERT into user VALUES (?, ?)", values_users)

            g.db.commit()
            g.db.close()
            message = "Account Created"
            return render_template('start.html', message= message)



#necessary code
if __name__ == '__main__':
    app.secret_key = os.urandom(12)
    app.run(debug=True)






