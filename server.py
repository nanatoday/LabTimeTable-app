
from flask import Flask,render_template,redirect, request, send_file,url_for,session,g,flash,make_response,Response
from flask_mysqldb import MySQL,MySQLdb
from flask_mail import Mail, Message
import bcrypt 
import os,random
import pdfkit 
import re
import pandas
from itsdangerous import URLSafeTimedSerializer
from dotenv import load_dotenv

##---------creating flask object----------
app=Flask(__name__)


##---------connecting to DB----------
app.config['MYSQL_HOST']="localhost"
app.config['MYSQL_USER']="root"
app.config['MYSQL_PASSWORD']=os.getenv('MYSQL_PASSWORD')
app.config['MYSQL_DB']=os.getenv('MYSQL_DB')
app.config['MYSQL_CURSORCLASS']="DictCursor"

##---------connecting to Mail server----------
app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] =os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] =os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] =os.getenv('MAIL_USERNAME')
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

UPLOAD_FOLDER = 'static/files'
app.config['UPLOAD_FOLDER'] =  UPLOAD_FOLDER

load_dotenv()
mysql=MySQL(app)
mail=Mail(app)
app.secret_key=os.urandom(64).hex()

ts = URLSafeTimedSerializer(app.config["SECRET_KEY"])


##---------Home Page----------
@app.route('/')
def home():
    return render_template('index.html')

##---------About Page----------
@app.route('/about')
def about():
    session["surname"]=g.lname
    nameOfUser=session['surname']
    return render_template('about.html',nameOfUser=nameOfUser)

##---------SIGN UP----------
@app.route('/signup', methods=["GET","POST"])
def signup():
    msg=""
    if request.method=="POST":
        lname=request.form["surName"]
        fname=request.form["firstName"]
        email=request.form["email"]
        password=request.form["password"].encode('utf-8')
        confirmPassword=request.form["confirmPassword"].encode('utf-8')
        hash_password=bcrypt.hashpw(password,bcrypt.gensalt())

        cur=mysql.connection.cursor()
        cur.execute("SELECT * FROM USERS WHERE EMAIL=%s",[email])
        account=cur.fetchall()
        if account:
            msg="account already exist"
        elif password!=confirmPassword:
            msg = 'Passwords do not match' 
            

        else:
            cur.execute("INSERT INTO USERS(lastName,firstName,email,lecPassword) values (%s,%s,%s,%s)",[lname,fname,email,hash_password])
            mysql.connection.commit()
#           cur.execute("SELECT * FROM users WHERE email= %s",[email])
 #           account= cur.fetchone()
 #           cur.close()
 #           session['loggedin']=True
 #           session['id']=account["lecId"]
  #          session['surname']=account["lastName"]
 #           session['email']=account["email"]
 #           nameOfUser=session['surname']

 #           return render_template('dashboard.html',nameOfUser=nameOfUser)
            
            token = ts.dumps(email, salt='email-confirm-key')

            confirm_url = url_for(
            'confirm_email',
            token=token,
            _external=True)

            html = render_template(
            'verifymail.html',
            confirm_url=confirm_url)

        # We'll assume that send_email has been defined in myapp/util.py
            msg=Message(sender="mensahmolar@gmail.com",recipients = [email])
            msg.subject="Confirm your email"
            msg.html=html
            mail.send(msg)
            return redirect(url_for("home"))

    return render_template('signup.html',msg=msg)

#-----------------------
#------confirm email----
#-----------------------
@app.route('/confirm/<token>')
def confirm_email(token):
    try:
        email = ts.loads(token, salt="email-confirm-key", max_age=86400)
        cur=mysql.connection.cursor()
        cur.execute("UPDATE USERS SET verification='YES' WHERE EMAIL=%s",[email])
        mysql.connection.commit()
        
    except:
        msg='Link expired'
        return render_template('resendmail.html',msg=msg)
    flash('Account verified.Please log in')
    return redirect(url_for('login'))


##---------LOGIN----------
@app.route('/login',methods=["POST","GET"])
def login():
    msg=""
    if request.method=="POST":
        email=request.form["email"]
        password=request.form["password"].encode('utf-8')
        cur=mysql.connection.cursor()
        cur.execute("SELECT * FROM USERS WHERE EMAIL=%s",[email])
        account=cur.fetchone()
        cur.close()
        if account:
            if account['verification']=="NO":
                hash_password=account['lecPassword']
                if bcrypt.checkpw(password,hash_password.encode('utf-8')):
                    session['type']='user'
                    session['loggedin']=True        
                    session['id']=account["lecId"]
                    session['surname']=account["lastName"]
                    session['firstname']=account['firstName']
                    session['email']=account["email"]
                    nameOfUser=session['surname']
                    return redirect(url_for('dashboard'))
                else:
                    msg='Password is Incorrect'
            else:
                msg="Account not verified..Please check your inbox for verification mail"  
                return render_template('resendmail.html',msg=msg)
        else:
            msg="account does not exist"
    
    return render_template('login.html',msg=msg)

##--------------------------
##----verfication mail------
##--------------------------
#@app.route('/sendmail',methods=['POST','GET'])
#def sendMail():
#    pass




##---------DASHBOARD----------
@app.route('/dashboard',methods=["POST","GET"])
def dashboard():
    if g.loggedin==True and request.method=="GET":
        cur=mysql.connection.cursor()
        cur.execute("SELECT count(slotDay) FROM LAB1")
        slot=cur.fetchone()
        slots=slot['count(slotDay)']

#----For Mondays------
        cur=mysql.connection.cursor()
        cur.execute("SELECT coalesce(courseCode,'Slot Available') as 'courseCode',initials from lab1 where slotDay='Monday'")
        mondays=cur.fetchall()

#------FOR TUESDAY-------
        cur.execute("SELECT coalesce(courseCode,'Slot Available') as 'courseCode',initials from lab1 where slotDay='Tuesday'")
        tuesdays=cur.fetchall()


    #-----FOR WEDNESDAY----
        cur.execute("SELECT coalesce(courseCode,'Slot Available') as 'courseCode',initials from lab1 where slotDay='Wednesday'")
        wednesdays=cur.fetchall()

    #-------FOR THURSDAY---
        cur.execute("SELECT coalesce(courseCode,'Slot Available') as 'courseCode',initials from lab1 where slotDay='Thursday'")
        thursdays=cur.fetchall()


    #---FOR FRIDAYS----
        cur.execute("SELECT coalesce(courseCode,'Slot Available') as 'courseCode',initials from lab1 where slotDay='Friday'")
        fridays=cur.fetchall()

        cur.close()

        session["surname"]=g.lname
        nameOfUser=session["surname"]
        return render_template('dashboard.html',nameOfUser=nameOfUser,slots=slots,mondays=mondays,tuesdays=tuesdays,wednesdays=wednesdays,thursdays=thursdays,fridays=fridays)
        
    else:
        return redirect(url_for('login'))


@app.route('/lab2',methods=["POST","GET"])
def lab2_dashboard():
    if g.loggedin==True and request.method=="GET":
        cur=mysql.connection.cursor()
        cur.execute("SELECT count(slotDay) FROM LAB2")
        slot=cur.fetchone()
        slots=slot['count(slotDay)']
#----For Mondays------
        cur=mysql.connection.cursor()
        cur.execute("SELECT coalesce(courseCode,'Slot Available') as 'courseCode',initials from lab2 where slotDay='Monday'")
        mondays=cur.fetchall()

#------FOR TUESDAY-------
        cur.execute("SELECT coalesce(courseCode,'Slot Available') as 'courseCode',initials from lab2 where slotDay='Tuesday'")
        tuesdays=cur.fetchall()


    #-----FOR WEDNESDAY----
        cur.execute("SELECT coalesce(courseCode,'Slot Available') as 'courseCode',initials from lab2 where slotDay='Wednesday'")
        wednesdays=cur.fetchall()

    #-------FOR THURSDAY---
        cur.execute("SELECT coalesce(courseCode,'Slot Available') as 'courseCode',initials from lab2 where slotDay='Thursday'")
        thursdays=cur.fetchall()


    #---FOR FRIDAYS----
        cur.execute("SELECT coalesce(courseCode,'Slot Available') as 'courseCode',initials from lab2 where slotDay='Friday'")
        fridays=cur.fetchall()

        cur.close()

        session["surname"]=g.lname
        nameOfUser=session["surname"]
        return render_template('lab2.html',nameOfUser=nameOfUser,slots=slots,mondays=mondays,tuesdays=tuesdays,wednesdays=wednesdays,thursdays=thursdays,fridays=fridays)
        
    else:
        return redirect(url_for('login'))


##---------BOOK SLOT----------
@app.route('/bookslot',methods=["POST","GET"])
def bookslot():
    if not g.loggedin==True:
        return redirect(url_for('login'))
   
 
    if request.method=='POST':                          
        courseCode=request.form['courseCode']              
        time=request.form["time"]
        day=request.form['days']
                                                       
        cur=mysql.connection.cursor()
        cur.execute('SELECT firstName,lastName FROM USERS WHERE lecId=%s',[g.id])
        item=cur.fetchone()
        lastname=item['lastName']
        firstname=item['firstName']
        lname=lastname[1]
        fname=firstname[1]
        initials=lname+'.'+fname        
        cur.execute("select count(courseCode) from Lab1")
        booked=cur.fetchone()
        bookedSlots=booked['count(courseCode)']
        if bookedSlots < 50:
            cur.execute("SELECT courseCode from LAB1 WHERE slotTime=%s and slotDay=%s",[time,day])
            slot=cur.fetchone()
            if slot != 'NULL':
                cur.execute(" UPDATE LAB1 SET courseCode=%s,initials=%s where slotTime=%s and slotDay=%s",[courseCode,initials,time,day])
                mysql.connection.commit()
                flash('Slot booked successfully')
                return redirect(url_for('dashboard'))
            else:
                flash("Slot already booked, Please select another slot")
        else:
            flash("Sorry, all slots have been booked")
        return redirect(url_for('dashboard'))
    
    session["surname"]=g.lname
    nameOfUser=session['surname']
    return render_template('dashboard.html',nameOfUser=nameOfUser)
 
##---------BOOK SLOT LAB 2----------
@app.route('/bookslotlab2',methods=["POST","GET"])
def bookslotlab2():
    if not g.loggedin==True:
        return redirect(url_for('login'))
   
 
    if request.method=='POST':
        courseCode=request.form['courseCode']
        time=request.form["time"]
        day=request.form['days']
        cur=mysql.connection.cursor()
        cur.execute('SELECT firstName,lastName FROM USERS WHERE lecId=%s',[g.id])
        item=cur.fetchone()
        lastname=item['lastName']
        firstname=item['firstName']
        lname=lastname[1]
        fname=firstname[1]
        initials=lname+'.'+fname   
        cur=mysql.connection.cursor()
        cur.execute("select count(courseCode) from Lab2")
        booked=cur.fetchone()
        bookedSlots=booked['count(courseCode)']
        if bookedSlots<50:
            cur.execute("SELECT courseCode from LAB2 WHERE slotTime=%s and slotDay=%s",[time,day])
            slot=cur.fetchone()
            if slot != "NULL":
                cur.execute(" UPDATE LAB2 SET courseCode=%s,initials=%s where slotTime=%s and slotDay=%s",[courseCode,initials,time,day])
                mysql.connection.commit()
                flash('Slot booked successfully')
                return redirect(url_for('lab2_dashboard'))
            else:
                msg="Slot already booked, Please select another slot"
        else:
            msg="Sorry, all slots have been booked"
        return render_template('lab2.html',msg=msg)
    
    session["surname"]=g.lname
    nameOfUser=session['surname']
    return render_template('lab2.html',nameOfUser=nameOfUser)

#---------------------------------
#-----------Profile-------------
#---------------------------------
@app.route('/profile',methods=["POST","GET"])
def profile():
    if g.loggedin!=True:
        return redirect(url_for('login'))
    g.lname=session['surname']
    g.id=session['id']
    nameOfUser=g.lname
    cur=mysql.connection.cursor()
    cur.execute('SELECT firstName,lastName,email FROM USERS WHERE lecId=%s',[g.id])
    item=cur.fetchone()

    return render_template('profile.html',nameOfUser=nameOfUser,item=item)
    


#---------------------------------
#-----Updatee Profile Password----
#---------------------------------
@app.route('/updatepassword',methods=["POST","GET"])
def updatePassword():
        password=request.form['password'].encode('utf-8')
        hash_password=bcrypt.hashpw(password,bcrypt.gensalt())
        cur=mysql.connection.cursor()
        cur.execute("UPDATE USERS SET lecPassword=%s where lecId=%s",[hash_password,g.id])
        mysql.connection.commit()
        flash('Password Updated Successfully')
        return redirect(url_for('profile'))   


#---------------------------------
#------Forgot Password page-------
#---------------------------------
@app.route('/forgotpassword',methods=["POST",'GET'])
def forgotPassword():
    if request.method=='POST':
        email=request.form['email']
        cur=mysql.connection.cursor()
        cur.execute("SELECT * FROM  USERS WHERE EMAIL=%s",[email])
        account=cur.fetchone()
        if account:
            token = ts.dumps(email, salt='email-confirm-key')

            reset_url = url_for(
            'user_reset',
            token=token,
            _external=True)

            html = render_template('resetpasswordmail.html',reset_url=reset_url)

        # compose email
            msg=Message(recipients = [email])
            msg.subject="Reset Password"
            msg.html=html
            mail.send(msg)
            flash('A reset link has been sent to your mail')
            return redirect(url_for("home"))
        else:
            msg1="No account with this mail found"
            return render_template('forgotpassword.html',msg=msg1)
    else:
        return render_template('forgotpassword.html')

#---------------------------------
#--------Reset Password page---------
#---------------------------------
@app.route('/resetpassword/<token>',methods=["POST",'GET'])
def user_reset(token):
    try:
        email = ts.loads(token, salt="email-confirm-key", max_age=86400)
        if request.method=='GET':
            return render_template('resetpassword.html',email=email)
        
    except:
        msg='Link expired'
        return render_template('forgotpassword.html',msg=msg)

#---------------------------------
#--------Reset Password ---------
#---------------------------------
@app.route('/resetuserpassword',methods=["POST","GET"])
def newuserPassword():
        password=request.form['password'].encode('utf-8')
        email=request.form['email']
        hash_password=bcrypt.hashpw(password,bcrypt.gensalt())
        cur=mysql.connection.cursor()
        cur.execute("UPDATE USERS SET lecPassword=%s WHERE email=%s",[hash_password,email])
        mysql.connection.commit()
        flash('Password reset successful.')
        return redirect(url_for('login'))

##-----------------------------------------------------------------------------------------------------
##--------------------------------------ADMIN PAGE-----------------------------------------------------
##-----------------------------------------------------------------------------------------------------


@app.route('/admin',methods=["POST","GET"])
def adminIndex():
    return render_template('admin/index.html')

#---------------------------------
#-------------signUp--------------
#---------------------------------

@app.route('/admin/signup',methods=["POST","GET"])
def adminSignup():
    if request.method=='POST':
        username=request.form['username']
        email=request.form['email']
        password=request.form['password'].encode('utf-8')
        confirmPassword=request.form["confirmPassword"].encode('utf-8')
        hash_password=bcrypt.hashpw(password,bcrypt.gensalt())

        cur=mysql.connection.cursor()
        cur.execute("SELECT * FROM  ADMIN WHERE EMAIL=%s",[email])
        account=cur.fetchall()
        if account:
            msg="account already exist"
            return render_template('signup.html',msg=msg)
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
                msg = 'Invalid email address!'
        elif password!=confirmPassword:
            msg = 'Passwords do not match'
        else:
            cur.execute("INSERT INTO USERS(email,username,password) values (%s,%s,%s)",[email,username,hash_password])
            mysql.connection.commit()
            cur.execute("SELECT * FROM admin WHERE email= %s",[email])
            account= cur.fetchone()
            cur.close()
            session['loggedin']=True
            session['id']=account["adminId"]
            session['email']=account["email"]
            nameOfUser='admin'
            mysql.connection.commit()
#           cur.execute("SELECT * FROM users WHERE email= %s",[email])
 #           account= cur.fetchone()
 #           cur.close()
 #           session['loggedin']=True
 #           session['id']=account["lecId"]
  #          session['surname']=account["lastName"]
 #           session['email']=account["email"]
 #           nameOfUser=session['surname']

 #           return render_template('dashboard.html',nameOfUser=nameOfUser)
            
            token = ts.dumps(email, salt='email-confirm-key')

            confirm_url = url_for(
            'admin_confirm',
            token=token,
            _external=True)

            html = render_template(
            'verifymail.html',
            confirm_url=confirm_url)

        # compose email
            msg=Message(sender="mensahmolar@gmail.com",recipients = [email])
            msg.subject="Confirm your email"
            msg.html=html
            mail.send(msg)
            return redirect(url_for("adminIndex"))

    return render_template('admin/index.html',msg=msg)

        
#-----------------------
#------confirm email----
#-----------------------
@app.route('/admin/confirm/<token>')
def admin_confirm(token):
    try:
        email = ts.loads(token, salt="email-confirm-key", max_age=86400)
        cur=mysql.connection.cursor()
        cur.execute("UPDATE ADMIN SET verification='YES' WHERE EMAIL=%s",[email])
        mysql.connection.commit()
        
    except:
        msg='Link expired'
        return render_template('admin/resendmail.html',msg=msg)
    flash('Account verified.Please log in')
    return redirect(url_for('adminIndex'))

#---------------------------------
#-------------logIn--------------
#---------------------------------
@app.route('/admin/login',methods=["POST","GET"])
def adminLogin():
    if request.method=='POST':
        username=request.form['username']
        password=request.form['password'].encode('utf-8')
        cur=mysql.connection.cursor()
        cur.execute("SELECT * FROM ADMIN WHERE USERNAME=%s",[username])
        account=cur.fetchone()
        cur.close()
        if account:
            if account['verification']=='YES':
                hash_password=account['password']
                if bcrypt.checkpw(password,hash_password.encode('utf-8')):
                    session['type']='admin'
                    session['loggedin']=True        
                    session['id']=account["adminId"]
                    session['email']=account["email"]
                    session['surname']=account['username']

                    nameOfUser="admin"
                    return redirect(url_for('adminDashboard'))
                else:
                    msg='Password is Incorrect'
            else:
                msg="Account not verified. Please check your inbox for confirmation mail"
                return render_template('admin/resendmail.html',msg=msg)    
        else:
            msg="account does not exist"
    
    return render_template('admin/index.html',msg=msg)

#---------------------------------
#------dashboard lab 1-----------
#---------------------------------

@app.route('/admin/dashboard',methods=["POST","GET"])
def adminDashboard():
    if not g.type=='admin':
        return redirect(url_for('adminIndex'))
    totalSlots=50
    cur=mysql.connection.cursor()
    cur.execute("select count(courseCode) from Lab1")
    booked=cur.fetchone()
    bookedSlots=booked['count(courseCode)']
    availableSlots=totalSlots-bookedSlots
#----For Mondays------
    cur=mysql.connection.cursor()
    cur.execute("SELECT coalesce(courseCode,'Slot Available') as 'courseCode',initials from lab1 where slotDay='Monday'")
    mondays=cur.fetchall()

#------FOR TUESDAY-------
    cur.execute("SELECT coalesce(courseCode,'Slot Available') as 'courseCode',initials from lab1 where slotDay='Tuesday'")
    tuesdays=cur.fetchall()

    #-----FOR WEDNESDAY----
    cur.execute("SELECT coalesce(courseCode,'Slot Available') as 'courseCode',initials from lab1 where slotDay='Wednesday'")
    wednesdays=cur.fetchall()

    #-------FOR THURSDAY---
    cur.execute("SELECT coalesce(courseCode,'Slot Available') as 'courseCode',initials from lab1 where slotDay='Thursday'")
    thursdays=cur.fetchall()


    #---FOR FRIDAYS----
    cur.execute("SELECT coalesce(courseCode,'Slot Available') as 'courseCode',initials from lab1 where slotDay='Friday'")
    fridays=cur.fetchall()

    cur.close()
    nameOfUser='admin'
    return render_template('admin/dashboard.html',nameOfUser=nameOfUser,totalSlots=totalSlots,bookedSlots=bookedSlots,availableSlots=availableSlots,mondays=mondays,tuesdays=tuesdays,wednesdays=wednesdays,thursdays=thursdays,fridays=fridays)

#---------------------------------
#------dashboard lab 2-----------
#---------------------------------

@app.route('/admin/lab2',methods=["POST","GET"])
def adminlab2():
    if not g.type=='admin':
        return redirect(url_for('adminIndex'))
    totalSlots=50
    cur=mysql.connection.cursor()
    cur.execute("select count(courseCode) from Lab2")
    booked=cur.fetchone()
    bookedSlots=booked['count(courseCode)']
    availableSlots=totalSlots-bookedSlots
#----For Mondays------
    cur=mysql.connection.cursor()
    cur.execute("SELECT coalesce(courseCode,'Slot Available') as 'courseCode',initials from lab2 where slotDay='Monday'")
    mondays=cur.fetchall()

#------FOR TUESDAY-------
    cur.execute("SELECT coalesce(courseCode,'Slot Available') as 'courseCode',initials from lab2 where slotDay='Tuesday'")
    tuesdays=cur.fetchall()


    #-----FOR WEDNESDAY----
    cur.execute("SELECT coalesce(courseCode,'Slot Available') as 'courseCode',initials from lab2 where slotDay='Wednesday'")
    wednesdays=cur.fetchall()

    #-------FOR THURSDAY---
    cur.execute("SELECT coalesce(courseCode,'Slot Available') as 'courseCode',initials from lab2 where slotDay='Thursday'")
    thursdays=cur.fetchall()


    #---FOR FRIDAYS----
    cur.execute("SELECT coalesce(courseCode,'Slot Available') as 'courseCode',initials from lab2 where slotDay='Friday'")
    fridays=cur.fetchall()

    cur.close()

    nameOfUser='admin'
    return render_template('admin/lab2.html',nameOfUser=nameOfUser,totalSlots=totalSlots,bookedSlots=bookedSlots,availableSlots=availableSlots,mondays=mondays,tuesdays=tuesdays,wednesdays=wednesdays,thursdays=thursdays,fridays=fridays)



#---------------------------------
#--------lab1 timetable list------
#---------------------------------
@app.route('/admin/timetable1',methods=["POST","GET"])
def table1():
    cur=mysql.connection.cursor()
    cur.execute("Select * from Lab1")
    slots=cur.fetchall()
    lab1='lab1'
    tableName='Lab 1'
    nameOfUser='admin'
    return render_template('admin/timetable.html',tableName=tableName,lab1=lab1,slots=slots,nameOfUser=nameOfUser)

#---------------------------------
#--------lab2 timetable list------
#---------------------------------
@app.route('/admin/timetable2',methods=["POST","GET"])
def table2():
    cur=mysql.connection.cursor()
    cur.execute("Select * from Lab2")
    slots=cur.fetchall()
    tableName='Lab 2'
    nameOfUser='admin'
    return render_template('admin/timetable.html',tableName=tableName,slots=slots,nameOfUser=nameOfUser)

#---------------------------------
#--------EDIT Slot--------------
#---------------------------------
@app.route('/admin/editslot/<int:itemid>',methods=["POST","GET"])
def edit_slot(itemid):
    cur=mysql.connection.cursor()
    cur.execute("Select * from Lab1 where slotId=%s",[itemid])
    item=cur.fetchone()
    lab1='lab1'
    nameOfUser='admin'
    return render_template('admin/editslot.html',lab1='lab1',item=item,nameOfUser=nameOfUser)

#---------------------------------
#--------Update Slot--------------
#---------------------------------
@app.route('/admin/updateslot/<int:itemid>',methods=["POST","GET"])
def update_slot(itemid):
    if request.method=='POST':
        course=request.form['course']
        initials=request.form['initials']
        cur=mysql.connection.cursor()
        cur.execute("UPDATE Lab1 set courseCode =%s,initials=%s where slotId=%s",[course,initials,itemid])
        mysql.connection.commit()
        return redirect(url_for('table1'))

#---------------------------------
#--------EDIT lab 2 Slot--------------
#---------------------------------
@app.route('/admin/editlab2slot/<int:itemid>',methods=["POST","GET"])
def editlab2slot(itemid):
    cur=mysql.connection.cursor()
    cur.execute("Select * from Lab2 where slotId=%s",[itemid])
    item=cur.fetchone()
    return render_template('admin/editslot.html',item=item)

#---------------------------------
#--------Update Slot for lab2--------------
#---------------------------------
@app.route('/admin/updatelab2slot/<int:itemid>',methods=["POST","GET"])
def updatelab2slot(itemid):
    if request.method=='POST':
        course=request.form['course']
        initials=request.form['initials']
        cur=mysql.connection.cursor()
        cur.execute("UPDATE Lab2 set courseCode =%s,initials=%s where slotId=%s",[course,initials,itemid])
        mysql.connection.commit()
        return redirect(url_for('table2'))

#---------------------------------
#-----------Admin Profile---------
#---------------------------------
@app.route('/admin/profile',methods=["POST","GET"])
def adminProfile():
    if g.loggedin==True:
        itemid=g.id
        cur=mysql.connection.cursor()
        cur.execute('SELECT username,email FROM ADMIN WHERE adminId=%s',[itemid])
        item=cur.fetchone()
        nameOfUser='admin'
        return render_template('admin/profile.html',item=item,nameOfUser=nameOfUser,itemid=itemid)
    else:
        return redirect(url_for('adminIndex'))

    

#---------------------------------
#-----Update Profile Password----
#---------------------------------
@app.route('/admin/updatepassword',methods=["POST","GET"])
def updateAdminPassword():
    g.id=session['id']
    if request.method=="POST":
        password=request.form['password'].encode('utf-8')
        hash_password=bcrypt.hashpw(password,bcrypt.gensalt())
        cur=mysql.connection.cursor()
        cur.execute("UPDATE ADMIN SET password=%s where adminId=%s",[hash_password,g.id])
        mysql.connection.commit()
        flash('Password Updated Successfully')
        return redirect(url_for("adminProfile"))






#---------------------------------
#-------------userslist-----------
#---------------------------------

@app.route('/admin/userslist',methods=["POST","GET"])
def userslist():
    if not g.type=='admin':
        return redirect(url_for('adminIndex'))
#    cur=mysql.connection.cursor()
    cur=mysql.connection.cursor()
    cur.execute("SELECT * FROM USERS")
    users=cur.fetchall()
    tableName='Users Table'
    nameOfUser='admin'
    return render_template('admin/userslist.html',tableName=tableName,users=users,nameOfUser=nameOfUser)


#---------------------------------
#------------edit user--------------
#---------------------------------
@app.route('/admin/edituser/<int:itemid>',methods=["POST","GET"])
def editUser(itemid):
    if not g.type=='admin':
        return redirect(url_for('adminIndex'))
#        cur=mysql.connection.cursor()
    cur=mysql.connection.cursor()
    cur.execute("SELECT * FROM USERS where lecId=%s",[itemid])
    item=cur.fetchone()
    nameOfUser='admin'
    return render_template('admin/edituser.html',item=item,nameOfUser=nameOfUser) 



#---------------------------------
#------------update user----------
#---------------------------------
@app.route('/admin/updateuser/<int:itemid>',methods=["POST","GET"])
def updateUser(itemid):
    #if not g.type=='admin':
#        return redirect('/admin/index.html')
        
    if request.method=="POST":
        password=request.form['password'].encode('utf-8')
        hash_password=bcrypt.hashpw(password,bcrypt.gensalt())
        cur=mysql.connection.cursor()
        cur.execute("UPDATE USERS SET password=%s where lecId=%s",[hash_password,itemid])
        mysql.connection.commit()
        flash('Password Updated Successfully')
        return redirect(url_for('userslist'))


#---------------------------------
#------------add user----------
#---------------------------------
@app.route('/admin/adduser',methods=["POST","GET"])
def addUser():
    if request.method=="POST":
        email=request.form['email']
        lname=request.form['lname']
        fname=request.form['fname']
        password=request.form['password'].encode('utf-8')
        hash_password=bcrypt.hashpw(password,bcrypt.gensalt())
        cur=mysql.connection.cursor()
        cur.execute('INSERT INTO USERS(firstName,lastName,lecPassword,email) VALUES (%s,%s,%s,%s)',[fname,lname,hash_password,email])
        mysql.connection.commit()
        flash('User added successfully')
        return redirect(url_for('userslist')) 
    else:
        return render_template('admin/adduser.html')



#---------------------------------
#------------Start sem page-------
#---------------------------------
@app.route('/admin/startsemester',methods=["POST","GET"])
def startSemester():
    if not g.type=='admin':
        return redirect(url_for('adminIndex'))
    nameOfUser='admin'
    return render_template('admin/startsemester.html',nameOfUser=nameOfUser)

#---------------------------------
#-----------clear slots-----------
#---------------------------------
@app.route('/admin/clearslots',methods=["POST","GET"])
def clearSlots():
    cur=mysql.connection.cursor()
    cur.execute("TRUNCATE TABLE LAB1")
    cur.execute("TRUNCATE TABLE LAB2")
    mysql.connection.commit()
    
    flash('Slots cleared succesfully')
    return redirect(url_for('startSemester'))

#---------------------------------
#----------upload csv----------
#---------------------------------
@app.route('/admin/uploadlab1csv',methods=["POST","GET"])
def lab1Csv():
    # get the uploaded file
      uploaded_file = request.files['file']
      if uploaded_file.filename != '':
          # set the file path
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], uploaded_file.filename)
          # save the file
            uploaded_file.save(file_path)
          # call function to parse csv
            parseCSV(file_path)
            flash('Upload successful')
            return redirect(url_for('startSemester'))
def parseCSV(filePath): #function to work on csv
      # CVS Column Names
      col_names = ['slot_time','slot_day']
      # Use Pandas to parse the CSV file
      csvData =pandas.read_csv(filePath,names=col_names, header=None)
      # Loop through the Rows
      for i,row in csvData.iterrows():
             sql = "INSERT INTO lab1(slotTime, slotDay) VALUES (%s, %s)"
             value = (row['slot_time'],row['slot_day'])
             cur=mysql.connection.cursor()
             cur.execute(sql, value)
             sql1 = "INSERT INTO lab2(slotTime, slotDay) VALUES (%s, %s)"
             value1 = (row['slot_time'],row['slot_day'])
             cur=mysql.connection.cursor()
             cur.execute(sql1, value1)
             mysql.connection.commit()
            

#---------------------------------
#---------DOWNLOAD CSV-----------
#---------------------------------
@app.route('/admin/downloadcsv',methods=["POST","GET"])
def downloadCsv():
    path="static/files/here.csv"
    return send_file(path, attachment_filename='uploadfile.csv') 


#---------------------------------
#------Forgot Password page-------
#---------------------------------
@app.route('/admin/forgotpassword',methods=["POST",'GET'])
def adminforgotPassword():
    if request.method=='POST':
        email=request.form['email']
        cur=mysql.connection.cursor()
        cur.execute("SELECT * FROM  ADMIN WHERE EMAIL=%s",[email])
        account=cur.fetchone()
        if account:
            token = ts.dumps(email, salt='email-confirm-key')

            reset_url = url_for(
            'admin_reset',
            token=token,
            _external=True)

            html = render_template('admin/resetpasswordmail.html',reset_url=reset_url)

        # compose email
            msg=Message(recipients = [email])
            msg.subject="Reset Password"
            msg.body=html
            mail.send(msg)
            return redirect(url_for("adminIndex"))
        else:
            msg1="No account with this mail found"
            return render_template('admin/forgotpassword.html',msg=msg1)
    else:
        return render_template('admin/forgotpassword.html')

#---------------------------------
#--------Reset Password page---------
#---------------------------------
@app.route('/admin/resetpassword/<token>',methods=["POST",'GET'])
def admin_reset(token):
    try:
        email = ts.loads(token, salt="email-confirm-key", max_age=86400)
        if request.method=='GET':
            return render_template('admin/resetpassword.html',email=email)
        
    except:
        msg='Link expired'
        return render_template('admin/forgotpassword.html',msg=msg)

#---------------------------------
#--------Reset Password ---------
#---------------------------------
@app.route('/admin/resetadminpassword',methods=["POST","GET"])
def newadminPassword():
        password=request.form['password'].encode('utf-8')
        email=request.form['email']
        hash_password=bcrypt.hashpw(password,bcrypt.gensalt())
        cur=mysql.connection.cursor()
        cur.execute("UPDATE ADMIN SET password=%s WHERE email=%s",[hash_password,email])
        mysql.connection.commit()
        flash('Password reset successful.')
        return redirect(url_for('adminIndex'))


@app.errorhandler(404)
def page_not_found(e):
    if g.loggedin==True:
        session['surname']=g.lname
        nameOfUser=session['surname']
        return render_template("404.html",nameOfUser=nameOfUser)
    else:
        return render_template("404.html")
    
            

        



##---------LOGOUT----------
@app.route('/logout')
def logout():
    # Remove session data, this will log the user out
   session.pop('loggedin', None)
   session.pop('id', None)
   session.pop('email', None)
   session.pop('type', None)
   session.pop('surname', None)
   # Redirect to login page
   return redirect(request.referrer)



#----------------------------------------------------
#-----the real deal....performs this action every time any request is made
@app.before_request
def before_request():
    g.type=None
    g.loggedin= None
    g.id=None
    g.email=None
    g.lname=None
 
    if 'loggedin' in session:
        g.type=session['type']
        g.loggedin= session['loggedin']
        g.id=session['id']
        g.email=session['email']
        g.lname=session['surname']



if __name__=='__main__':
    app.run(debug=True)
