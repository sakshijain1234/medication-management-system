from flask import Flask,render_template, request,redirect, url_for,jsonify
import json
import pywhatkit
import pyautogui as pg
from pywhatkit.core import core, exceptions, log
import datetime
import time

app = Flask(__name__)

pg.FAILSAFE = False

core.check_connection()

@app.route("/shedule/<id>",methods=["GET","POST"])
def shedule(id):
    found=False
    data=show_shed(id)
    if data:
        found=True
    if request.method=="POST":
        button=request.form.get("rem")
        if button=="rem":
            phone=request.form.get("phone")
            add_phone(id,phone)
            msg_sent(id)
    return render_template("shedule.html",data=data,found=found,id=id)

@app.route("/home/<id>",methods=["GET","POST"])
def home(id):
    print("i am in home")
    user_data={}
    data=get_data()
    submit=request.form.get("submit")
    print("i am submit",submit)
    if "P_info" in data[id]:   #if user id old
        print("i am in patient subimission")
        user_data=data[id]["P_info"]
    else:      
        if submit=="submit_p_info" and request.method=="POST":                  #if user is new 
            name=request.form.get("P_name")
            gender=request.form.get("gender")
            age=request.form.get("age")
            user_data=put_p_info(id,name,age,gender,data)
    if submit=="submit_m_info" and request.method=="POST":
        print("i am in medicine subimission")
        name=request.form.get("m_name")
        duration=request.form.get("duration")
        time=request.form.get("m_time")
        des=request.form.get("des")
        put_m_info(id,name,duration,time,des)
    return render_template("index.html",user_data=user_data,id=id)

@app.route("/signup",methods=["GET","POST"])  #signup page
def signup():
    found=False
    if request.method=="POST":
        username=request.form.get("username")
        password=request.form.get("password")
        id=username+"+"+password
        button=request.form.get("button")
        if button=="login":
            return redirect(url_for("login"))
        else:
            if username!="" and password!="":
                data=new_user(id)
                if id in data:
                    found=True
    return render_template("signup.html",found=found)

@app.route("/",methods=["GET","POST"])   #login page 
def login():
    found=True
    if request.method=="POST":
        username=request.form.get("username")
        password=request.form.get("password")
        id=username+"+"+password
        button=request.form.get("button")
        if button=="login":
            data=get_data()
            if id in data:
                return redirect(url_for("home",id=id))
            else:
                found=False
        if button=="signup":
           return redirect(url_for("signup")) 
    return render_template("login.html",found=found)

def get_data():
    with open('patient.json', 'r') as file:
                data=json.load(file)
    return data

def new_user(id):  #new signup (create key)
    data=get_data()
    data[id]={}
    with open('patient.json', 'w') as save:
        json.dump(data,save)
    return data

def put_p_info(id,name,age,gender,data):   #insert P_info of new user
    info={
        "p_name":name,
        "age":age,
        "gender":gender
    }
    data[id]["P_info"]=info
    with open('patient.json', 'w') as save:
        json.dump(data,save)
    return data[id]["P_info"]

def put_m_info(id,m_info,duration,time,description):  #insert the new medicine
    print("wait i am enetering!!!!!!")
    data=get_data()
    info={
        "m_info":m_info,
        "duration":int(duration),
        "time":time,
        "description":description
    }
    if "M_info" in data[id]:
        data[id]["M_info"].append(info)
    else:
        data[id]["M_info"]=[]
        data[id]["M_info"].append(info)
    with open('patient.json', 'w') as save:
        json.dump(data,save)

def show_shed(id):  #return list of medicines
    data=get_data()
    if "M_info" in data[id]:
        return data[id]["M_info"]
    else:
        return 0
    
def add_phone(id,no):  #add phone number
    data=get_data()
    if "phone" not in data[id]:
        data[id]["phone"]=no
        with open('patient.json', 'w') as save:
            json.dump(data,save)

def msg_sent(id):
    m_data=get_m_info(id)
    m_data.sort(key=get_time)
    phone=get_phone(id)
    if phone:
        for i in m_data:
            if i["time"]:
                name=i['m_info']
                msg=f"Important Remainder!!!\nmedicine time: {name}"
                hour, minute = i['time'].split(":")
                # minute=int(minute)
                # hour=int(hour)
                # print(i["time"],hour,minute)
                # return 0
                sendwhatmsg(phone,msg,hour,min)

def get_m_info(id):  #get info of all medicine (list)
    data=get_data()
    m_info=data[id]["M_info"]
    return m_info

def get_phone(id):   #get phone number
    data=get_data()
    if "phone" in data[id]:
        return data[id]["phone"]
    return ""

def get_time(t):  #give the time of employee
    return t.get('time')

def sendwhatmsg(
    phone_no: str,
    message: str,
    time_hour: int,
    time_min: int,
    wait_time: int = 15,
    tab_close: bool = False,
    close_time: int = 3,
) -> None:
    """Send a WhatsApp Message at a Certain Time"""

    if not core.check_number(number=phone_no):
        raise exceptions.CountryCodeException("Country Code Missing in Phone Number!")

    if time_hour not in range(25) or time_min not in range(60):
        raise Warning("Invalid Time Format!")

    current_time = datetime.now()
    left_time = datetime.strptime(
        f"{time_hour}:{time_min}:0", "%H:%M:%S"
    ) - datetime.strptime(
        f"{current_time.tm_hour}:{current_time.tm_min}:{current_time.tm_sec}",
        "%H:%M:%S",
    )

    if left_time.seconds < wait_time:
        raise exceptions.CallTimeException(
            "Call Time must be Greater than Wait Time as WhatsApp Web takes some Time to Load!"
        )

    sleep_time = left_time.seconds - wait_time
    print(
        f"In {sleep_time} Seconds WhatsApp will open and after {wait_time} Seconds Message will be Delivered!"
    )
    time.sleep(sleep_time)
    core.send_message(message=message, receiver=phone_no, wait_time=wait_time)
    log.log_message(_time=current_time, receiver=phone_no, message=message)
    if tab_close:
        core.close_tab(wait_time=close_time)

if __name__ == '__main__':
	app.run(debug=True)