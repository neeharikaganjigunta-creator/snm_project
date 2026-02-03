from flask import Flask,request,url_for,redirect,render_template,flash,session,send_file
from flask_session import Session
from otp import genotp
import flask_excel as excel
from stoken import endata,dndata
from cmail import send_mail
import mysql.connector
from mysql.connector import (connection)
import re
from io import BytesIO
mydb=mysql.connector.connect(user='root',host='localhost', password='admin',database='notes')
app=Flask(__name__)
excel.init_excel(app)
app.secret_key="neeha"
app.config['SESSION_TYPE']='filesystem'
Session(app)

# FOR WELCOME

@app.route("/")
def home():
    return render_template("welcome.html")

# FOR REGISTER

@app.route("/register",methods=["GET","POST"])  
def register():
    if request.method=="POST":
        username=request.form["uname"]
        useremail=request.form["uemail"]
        userpassword=request.form["password"]
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select count(*) from user where user_email=%s',[useremail])
            count_email=cursor.fetchone() #(1,) or (0,)
            cursor.close()
        except Exception as e:
            print(e)
            flash('could not verify email')
            return redirect(url_for('register'))
        else:
            if count_email[0]==0:
                server_otp=genotp()
                userdata={'username':username,'useremail':useremail,'userpassword':userpassword,'server_otp':server_otp}
                # return server_otp     # for otp
                subject="OTP for SNM_APP"
                body=f"use the given otp for user registration{server_otp}"
                send_mail(to=useremail,subject=subject,body=body)
                flash("OTP has been sent to given email")
                return redirect(url_for("otpverify",var_data=endata(data=userdata)))
            elif count_email[0]==1:
                flash('email already exist')
  
    return render_template("register.html") 

# FOR OTP

@app.route("/otpverify/<var_data>",methods=['GET','POST'])
def otpverify(var_data):
    if request.method=='POST':
        user_otp=request.form['userotp']
        print(user_otp)
        try:
            user_data=dndata(var_data) #{'username':username,'useremail':useremail,'userpassword':userpassword,'server_otp':server_otp}
            print(user_data)
        except Exception as e:
            print(e)
            flash('could not verify otp pls try again')
            return redirect(url_for('register'))
        else:
            if user_data['server_otp']==user_otp:
                cursor=mydb.cursor()
                cursor.execute('insert into user(user_name,user_email,user_password) values(%s,%s,%s)',[user_data['username'],user_data['useremail'],user_data['userpassword']])
                mydb.commit()
                flash('user details stored')

                return redirect(url_for('login'))
            else:
                flash('otp was wrong')
    return render_template('otp.html')  


@app.route('/login',methods=['GET','POST'])
def login():
    if request.method=='POST':
        login_useremail=request.form.get('uemail','').strip()
        login_password=request.form.get('password','').strip()
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select count(*) from user where user_email=%s',[login_useremail])
            count_email=cursor.fetchone() #(1,) or (0,)
            #cursor.close()
        except Exception as e:
            print(e)
            flash('could not connect to db')
            return redirect(url_for('login'))
        else:
            if count_email[0]==1:
                cursor.execute('select user_password from user where user_email=%s',[login_useremail])
                stored_password=cursor.fetchone() #(123,)
                cursor.close()
                if stored_password[0]==login_password:
                    flash('you are successfully login')
                    session['user']=login_useremail
                    return redirect(url_for('dashboard'))
                else:
                    flash('password is invalid')
                    redirect(url_for('login'))
            else:
                flash('user not found pls check')
                
    return render_template('login.html')
@app.route('/dashboard')
def dashboard():
    if session.get('user'):
        return render_template('dashboard.html')
    else:
        flash('please login')
        return redirect(url_for('login'))

@app.route('/addnotes', methods=['GET','POST'])
def addnotes():
    if session.get('user'):
        if request.method=='POST':
            title=request.form.get('title').strip()
            notesContent=request.form.get('content').strip()
            try:
                cursor=mydb.cursor(buffered=True)
                cursor.execute('select user_id from user where user_email=%s',[session.get('user')])
                user_id=cursor.fetchone()
                if user_id:
                    cursor.execute('insert into notesdata(notes_title,notes_content,user_id) values(%s,%s,%s)',[title,notesContent,user_id[0]])
                    mydb.commit()
                    cursor.close()
                else:
                    print(user_id)
                    flash('user not verified')
                    return redirect(url_for('addnotes'))
            except Exception as e:
                print(e)
                flash('could not add notes')
                return redirect(url_for('addnotes'))
            else:
                 
                flash('notes added successfully')
        return render_template('addnotes.html')
    else:
        flash('login first')
        return redirect(url_for('login'))

@app.route('/viewallnotes')
def viewallnotes():
    if session.get('user'):
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select user_id from user where user_email=%s',[session.get('user')])
            user_id=cursor.fetchone()
            if user_id:
                cursor.execute('select * from notesdata where user_id=%s',[user_id[0]])
                notesdata=cursor.fetchall() #[(1,python,pro lang)]
            else:
                flash('could not verify user')
                return redirect(url_for('dashboard'))
        except Exception as e:
            print(e)
            flash('could not fetch notes data')
            return redirect(url_for('dashboard'))
        else:
            return render_template('viewallnotes.html',notesdata=notesdata)
    else:
        flash('please login')
        return redirect(url_for('login'))

@app.route('/viewnotes/<nid>')
def viewnotes(nid):
    if session.get('user'):
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select user_id from user where user_email=%s',[session.get('user')])
            user_id=cursor.fetchone()
            if user_id:
                cursor.execute('select * from notesdata where user_id=%s and notes_id=%s',[user_id[0],nid])
                notesdata=cursor.fetchone() #(1,python,pro lang)
            else:
                flash('could not verify user')
                return redirect(url_for('dashboard'))
        except Exception as e:
            print(e)
            flash('could not fetch notes data')
            return redirect(url_for('dashboard'))
        else:
            return render_template('viewnotes.html',notesdata=notesdata)
    else:
        flash('please login')
        return redirect(url_for('login'))


@app.route('/deletenotes/<nid>')
def deletenotes(nid):
    if session.get('user'):
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select user_id from user where user_email=%s',[session.get('user')])
            user_id=cursor.fetchone()
            if user_id:
                cursor.execute('delete  from notesdata where user_id=%s and notes_id=%s',[user_id[0],nid])
                mydb.commit()
                cursor.close()
            else:
                flash('could not verify user')
                return redirect(url_for('dashboard'))
        except Exception as e:
            print(e)
            flash('could not delete notes data')
            return redirect(url_for('dashboard'))
        else:
            flash('notes deleted successfully')
            return redirect(url_for('viewallnotes'))
    else:
        flash('please login')
        return redirect(url_for('login'))

@app.route('/updatenotes/<nid>',methods=['GET','POST'])
def updatenotes(nid):
    if session.get('user'):
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select user_id from user where user_email=%s',[session.get('user')])
            user_id=cursor.fetchone()
            if user_id:
                cursor.execute('select * from notesdata where user_id=%s and notes_id=%s',[user_id[0],nid])
                notesdata=cursor.fetchone() #(1,python,pro lang)
            else:
                flash('could not verify user')
                return redirect(url_for('dashboard'))
        except Exception as e:
            print(e)
            flash('could not update notes data')
            return redirect(url_for('dashboard'))
        else:
            if request.method=='POST':
                updated_titile=request.form['title']
                updated_content=request.form['content']
                try:
                    cursor.execute('update notesdata set notes_title=%s,notes_content=%s where notes_id=%s and user_id=%s',[updated_titile,updated_content,nid,user_id[0]])
                    mydb.commit()
                    cursor.close()
                except Exception as e:
                    print(e)
                    flash('could not update notes ')
                    return redirect(url_for('updatenotes',nid=nid))
                else:
                    flash('notes updated successfully')
                    return redirect(url_for('updatenotes',nid=nid))
            return render_template('updatenotes.html',notesdata=notesdata)
        
    else:
        flash('please login first')
        return redirect(url_for('login'))

@app.route('/getexceldata')
def getexceldata():
    if session.get('user'):
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select user_id from user where user_email=%s',[session.get('user')])
            user_id=cursor.fetchone()
            if user_id:
                cursor.execute('select * from notesdata where user_id=%s',[user_id[0]])
                notesdata=cursor.fetchall() #[(1,python,pro lang)]
            else:
                flash('could not verify user')
                return redirect(url_for('dashboard'))
        except Exception as e:
            print(e)
            flash('could not fetch notes data')
            return redirect(url_for('dashboard'))
        else:
             array_data=[list(i) for i in notesdata]
             columns=['notesid','title','content','userid','time']
             array_data.insert(0,columns)
             return excel.make_response_from_array(array_data,'xlsx',filename='notesdata')
    else:
        flash('please login')
        return redirect(url_for('login'))

# For Upload File

@app.route("/uploadfile",methods=["GET","POST"])
def uploadfile():
    if session.get("user"):
        if request.method=="POST":
            fileobj=request.files["filedata"]
            filedata=fileobj.read()
            fname=fileobj.filename
            try:
                cursor=mydb.cursor(buffered=True)
                cursor.execute("select user_id from user where user_email=%s",[session.get("user")])
                user_id=cursor.fetchone()
                cursor.execute("select count(*) from file where file_name=%s",[fname])
                filecount=cursor.fetchone()
                if user_id:
                    if filecount[0]==0:
                        cursor.execute("insert into file(file_name,file_data,user_id) values(%s,%s,%s)",[fname,filedata,user_id[0]])
                        mydb.commit()
                        cursor.close()
                    else:
                        flash("File already existed")
                        return redirect(url_for("uploadfile"))
                else:
                    flash("Couldn't verify user")            
                    return redirect(url_for("uploadfile"))
            except Exception as e:
                print(e)
                flash("Couldn't upload file")
                return redirect(url_for("uploadfile"))
            else:
                flash("File Uploaded Successfully!!")        

        return render_template("uploadfile.html")
    else:
        flash("Please login to upload a file")
        return redirect(url_for("login"))    

        # For View All Files in Files

@app.route("/viewallfiles")
def viewallfiles():
    if session.get("user"):
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute("select user_id from user where user_email=%s",[session.get("user")])
            user_id=cursor.fetchone()

            if user_id:
                cursor.execute("select * from file where user_id=%s",[user_id[0]])
                filesdata=cursor.fetchall()  # used to fetch all the records and in the form of list[]
                #  i.e, [(1,"python","programming",1,"2026-1-23 16.07")] , [(2,"MySQL","declarative language",1,"2026-1-23 16.07")]

            else:
                flash("Couldn't verify user")
                return redirect(url_for("dashboard")) 

        except Exception as e:
            print(e)
            flash("Couldn't fetch fies data")
            return redirect(url_for("dashboard"))

        else:
            return render_template("viewallfiles.html",filesdata=filesdata)    
        
    else:
        flash("Please login to view all notes")
        return redirect(url_for("login"))   

# for view file in View All Files

@app.route("/viewfile/<fid>")
def viewfile(fid):
    if session.get("user"):
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute("select user_id from user where user_email=%s",[session.get("user")])
            user_id=cursor.fetchone()

            if user_id:
                cursor.execute("select * from file where user_id=%s and file_id=%s",[user_id[0],fid])
                file_data=cursor.fetchone()  # used to fetch all the records and in the form of list[]
                #  i.e, [(1,"python","programming",1,"2026-1-23 16.07")] , [(2,"MySQL","declarative language",1,"2026-1-23 16.07")]

            else:
                flash("Couldn't verify user")
                return redirect(url_for("dashboard")) 

        except Exception as e:
            print(e)
            flash("Couldn't fetch files data")
            return redirect(url_for("dashboard"))

        else:
            byte_array=BytesIO(file_data[2])
            return send_file(byte_array,download_name=file_data[1],as_attachment=False)   # as_attach=false-> just view, true-> download
        
    else:
        flash("Please login to view file")
        return redirect(url_for("login"))    

        # For Download file Viel All Files

@app.route("/downloadfile/<fid>")
def downloadfile(fid):
    if session.get("user"):
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute("select user_id from user where user_email=%s",[session.get("user")])
            user_id=cursor.fetchone()

            if user_id:
                cursor.execute("select * from file where user_id=%s and file_id=%s",[user_id[0],fid])
                file_data=cursor.fetchone()  # used to fetch all the records and in the form of list[]
                #  i.e, [(1,"python","programming",1,"2026-1-23 16.07")] , [(2,"MySQL","declarative language",1,"2026-1-23 16.07")]

            else:
                flash("Couldn't verify user")
                return redirect(url_for("dashboard")) 

        except Exception as e:
            print(e)
            flash("Couldn't fetch files data")
            return redirect(url_for("dashboard"))

        else:
            byte_array=BytesIO(file_data[2])
            return send_file(byte_array,download_name=file_data[1],as_attachment=True)   # as_attach=false-> just view, true-> download
        
    else:
        flash("Please login to view file")
        return redirect(url_for("login"))    

        # For DELETE in View All Files   # Delete

@app.route("/deletefile/<fid>")
def deletefile(fid):
    if session.get("user"):
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute("select user_id from user where user_email=%s",[session.get("user")])
            user_id=cursor.fetchone()

            if user_id:
                cursor.execute("delete from file where user_id=%s and file_id=%s",[user_id[0],fid])
                mydb.commit()
                cursor.close()

            else:
                flash("Couldn't verify user")
                return redirect(url_for("dashboard")) 

        except Exception as e:
            print(e)
            flash("Couldn't delete file data")
            return redirect(url_for("dashboard"))

        else:
            flash("File deleted successfully!!")
            return redirect(url_for("dashboard"))
        
    else:
        flash("Please login to delete file data")
        return redirect(url_for("login"))  

      # FOR SEARCH FOR NOTES DATA & FILES DATA

@app.route("/search",methods=["POST"])
def search():
    if session.get("user"):
        search_data=request.form["search_value"]
        strg=["A-Z0-9a-z"]
        pattern=re.compile(f"^{strg}",re.IGNORECASE)
        if pattern.match(search_data):
            try:
                cursor=mydb.cursor(buffered=True)
                cursor.execute("select user_id from user where user_email=%s",[session.get("user")])
                user_id=cursor.fetchone()

                if user_id:
                    cursor.execute("select * from notesdata where user_id=%s and notes_title like %s",[user_id[0],search_data+"%"])  # % is used to see the all the files name starting with that letter
                    # cursor.execute("select * from file where user_id=%s and file_name like %s",[user_id[0],search_data+"%"])
                    search_result=cursor.fetchall()  # used to fetch all the records and in the form of list[]

                else:
                    flash("Couldn't verify user")
                    return redirect(url_for("dashboard")) 

            except Exception as e:
                print(e)
                flash("Couldn't fetch notes data")
                return redirect(url_for("dashboard"))

            else:
                return render_template("viewallnotes.html",notesdata=search_result) 
        else:
            flash("Invalid search")
            return redirect(url_for("dashboard"))
    else:
        flash("Please login to search notes") 
        return redirect(url_for("login"))   

        
        # FOR LOGOUT

@app.route("/logout")
def logout():
    if session.get("user"):
        session.pop("user")
        return redirect(url_for("login"))
    else:
        flash("Please login to logout")
        return redirect(url_for("login"))     




# app.run(debug=True,use_reloader=True)
if __name__ =='__main__':
    app.run()
