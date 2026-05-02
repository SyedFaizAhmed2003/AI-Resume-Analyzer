import os
import io
import random
import sqlite3
import time
import datetime
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import geocoder
import socket
import platform

from pyresparser import ResumeParser
from pdfminer3.layout import LAParams
from pdfminer3.pdfpage import PDFPage
from pdfminer3.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer3.converter import TextConverter

from Courses import ds_course, web_course, android_course, ios_course, uiux_course, resume_videos, interview_videos

import nltk
nltk.download('stopwords')

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all origins for local dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_NAME = "cv.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_data (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            sec_token TEXT,
            ip_add TEXT,
            host_name TEXT,
            dev_user TEXT,
            os_name_ver TEXT,
            latlong TEXT,
            city TEXT,
            state TEXT,
            country TEXT,
            act_name TEXT,
            act_mail TEXT,
            act_mob TEXT,
            Name TEXT,
            Email_ID TEXT,
            resume_score TEXT,
            Timestamp TEXT,
            Page_no TEXT,
            Predicted_Field TEXT,
            User_level TEXT,
            Actual_skills TEXT,
            Recommended_skills TEXT,
            Recommended_courses TEXT,
            pdf_name TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_feedback (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            feed_name TEXT,
            feed_email TEXT,
            feed_score TEXT,
            comments TEXT,
            Timestamp TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

def pdf_reader(file):
    resource_manager = PDFResourceManager()
    fake_file_handle = io.StringIO()
    converter = TextConverter(resource_manager, fake_file_handle, laparams=LAParams())
    page_interpreter = PDFPageInterpreter(resource_manager, converter)
    with open(file, 'rb') as fh:
        for page in PDFPage.get_pages(fh, caching=True, check_extractable=True):
            page_interpreter.process_page(page)
        text = fake_file_handle.getvalue()

    converter.close()
    fake_file_handle.close()
    return text

def course_recommender(course_list):
    c = 0
    rec_course = []
    no_of_reco = 5
    random.shuffle(course_list)
    for c_name, c_link in course_list:
        c += 1
        rec_course.append({"name": c_name, "link": c_link})
        if c == no_of_reco:
            break
    return rec_course

os.makedirs('./Uploaded_Resumes', exist_ok=True)

@app.post("/api/analyze")
async def analyze_resume(request: Request, file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
        
    save_image_path = f'./Uploaded_Resumes/{file.filename}'
    with open(save_image_path, "wb") as f:
        f.write(await file.read())

    try:
        resume_data = ResumeParser(save_image_path).get_extracted_data()
        if not resume_data:
            return {"error": "Failed to extract data from resume."}
            
        resume_text = pdf_reader(save_image_path)
        
        # Predicting Candidate Experience Level 
        cand_level = ''
        no_of_pages = resume_data.get('no_of_pages', 0)
        if no_of_pages and no_of_pages < 1:                
            cand_level = "Fresher"
        elif any(word in resume_text for word in ['INTERNSHIP', 'INTERNSHIPS', 'Internship', 'Internships']):
            cand_level = "Intermediate"
        elif any(word in resume_text for word in ['EXPERIENCE', 'WORK EXPERIENCE', 'Experience', 'Work Experience']):
            cand_level = "Experienced"
        else:
            cand_level = "Fresher"
            
        # Skills Analyzing and Recommendation
        ds_keyword = ['tensorflow','keras','pytorch','machine learning','deep Learning','flask','streamlit']
        web_keyword = ['react', 'django', 'node jS', 'react js', 'php', 'laravel', 'magento', 'wordpress','javascript', 'angular js', 'C#', 'Asp.net', 'flask']
        android_keyword = ['android','android development','flutter','kotlin','xml','kivy']
        ios_keyword = ['ios','ios development','swift','cocoa','cocoa touch','xcode']
        uiux_keyword = ['ux','adobe xd','figma','zeplin','balsamiq','ui','prototyping','wireframes','storyframes','adobe photoshop','photoshop','editing','adobe illustrator','illustrator','adobe after effects','after effects','adobe premier pro','premier pro','adobe indesign','indesign','wireframe','solid','grasp','user research','user experience']
        n_any = ['english','communication','writing', 'microsoft office', 'leadership','customer management', 'social media']
        
        recommended_skills = []
        reco_field = ''
        rec_course = []
        
        skills = resume_data.get('skills', [])
        if skills:
            for i in skills:
                if i.lower() in ds_keyword:
                    reco_field = 'Data Science'
                    recommended_skills = ['Data Visualization','Predictive Analysis','Statistical Modeling','Data Mining','Clustering & Classification','Data Analytics','Quantitative Analysis','Web Scraping','ML Algorithms','Keras','Pytorch','Probability','Scikit-learn','Tensorflow',"Flask",'Streamlit']
                    rec_course = course_recommender(ds_course)
                    break
                elif i.lower() in web_keyword:
                    reco_field = 'Web Development'
                    recommended_skills = ['React','Django','Node JS','React JS','php','laravel','Magento','wordpress','Javascript','Angular JS','c#','Flask','SDK']
                    rec_course = course_recommender(web_course)
                    break
                elif i.lower() in android_keyword:
                    reco_field = 'Android Development'
                    recommended_skills = ['Android','Android development','Flutter','Kotlin','XML','Java','Kivy','GIT','SDK','SQLite']
                    rec_course = course_recommender(android_course)
                    break
                elif i.lower() in ios_keyword:
                    reco_field = 'IOS Development'
                    recommended_skills = ['IOS','IOS Development','Swift','Cocoa','Cocoa Touch','Xcode','Objective-C','SQLite','Plist','StoreKit',"UI-Kit",'AV Foundation','Auto-Layout']
                    rec_course = course_recommender(ios_course)
                    break
                elif i.lower() in uiux_keyword:
                    reco_field = 'UI-UX Development'
                    recommended_skills = ['UI','User Experience','Adobe XD','Figma','Zeplin','Balsamiq','Prototyping','Wireframes','Storyframes','Adobe Photoshop','Editing','Illustrator','After Effects','Premier Pro','Indesign','Wireframe','Solid','Grasp','User Research']
                    rec_course = course_recommender(uiux_course)
                    break
                elif i.lower() in n_any:
                    reco_field = 'NA'
                    recommended_skills = ['No Recommendations']
                    rec_course = []
                    break
                    
        # Resume Scorer
        resume_score = 0
        if 'Objective' in resume_text or 'Summary' in resume_text:
            resume_score += 6
        if 'Education' in resume_text or 'School' in resume_text or 'College' in resume_text:
            resume_score += 12
        if 'EXPERIENCE' in resume_text or 'Experience' in resume_text:
            resume_score += 16
        if 'INTERNSHIPS' in resume_text or 'INTERNSHIP' in resume_text or 'Internships' in resume_text or 'Internship' in resume_text:
            resume_score += 6
        if 'SKILLS' in resume_text or 'SKILL' in resume_text or 'Skills' in resume_text or 'Skill' in resume_text:
            resume_score += 7
        if 'HOBBIES' in resume_text or 'Hobbies' in resume_text:
            resume_score += 4
        if 'INTERESTS' in resume_text or 'Interests' in resume_text:
            resume_score += 5
        if 'ACHIEVEMENTS' in resume_text or 'Achievements' in resume_text:
            resume_score += 13
        if 'CERTIFICATIONS' in resume_text or 'Certifications' in resume_text or 'Certification' in resume_text:
            resume_score += 12
        if 'PROJECTS' in resume_text or 'PROJECT' in resume_text or 'Projects' in resume_text or 'Project' in resume_text:
            resume_score += 19

        # Background Data Collection
        ip_add = request.client.host
        host_name = socket.gethostname()
        try:
            dev_user = os.getlogin()
        except:
            dev_user = os.environ.get('USERNAME', 'Unknown')
        os_name_ver = platform.system() + " " + platform.release()
        
        # Geolocation
        try:
            g = geocoder.ip('me') if ip_add == "127.0.0.1" else geocoder.ip(ip_add)
            latlong = str(g.latlng)
            city = g.city or "Unknown"
            state = g.state or "Unknown"
            country = g.country or "Unknown"
        except:
            latlong, city, state, country = "Unknown", "Unknown", "Unknown", "Unknown"

        ts = time.time()
        timestamp = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d_%H:%M:%S')

        # Insert to DB
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO user_data (sec_token, ip_add, host_name, dev_user, os_name_ver, latlong, city, state, country, 
                                   act_name, act_mail, act_mob, Name, Email_ID, resume_score, Timestamp, Page_no, 
                                   Predicted_Field, User_level, Actual_skills, Recommended_skills, Recommended_courses, pdf_name)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "token", ip_add, host_name, dev_user, os_name_ver, latlong, city, state, country,
            resume_data.get('name', 'Unknown'), resume_data.get('email', 'Unknown'), resume_data.get('mobile_number', 'Unknown'), 
            resume_data.get('name', 'Unknown'), resume_data.get('email', 'Unknown'), str(resume_score), timestamp, str(no_of_pages),
            reco_field, cand_level, str(skills), str(recommended_skills), str([c['name'] for c in rec_course]), file.filename
        ))
        conn.commit()
        conn.close()

        # Tailored interview videos based on field
        field_interview_videos = {
            'Data Science': ['https://youtu.be/k2P_pHQDlp0', 'https://youtu.be/HG68Ymazo18'],
            'Web Development': ['https://youtu.be/1mHjMNZZvFo', 'https://youtu.be/e0E6-dRPcJA', 'https://youtu.be/WfdtKbAJOmE'],
            'Android Development': ['https://youtu.be/KukmClH1KoA', 'https://youtu.be/thkuu_FWFD8'],
            'IOS Development': ['https://youtu.be/7_aAicmPB3A', 'https://youtu.be/Ge0Udbws1kc'],
            'UI-UX Development': ['https://youtu.be/TZ3C_syg9Ow']
        }

        # Random videos for frontend
        res_vid = random.choice(resume_videos) if resume_videos else ""
        
        # Select tailored interview video if available, else fallback to random
        if reco_field in field_interview_videos and field_interview_videos[reco_field]:
            int_vid = random.choice(field_interview_videos[reco_field])
        else:
            int_vid = random.choice(interview_videos) if interview_videos else ""

        return {
            "success": True,
            "basic_info": {
                "name": resume_data.get('name'),
                "email": resume_data.get('email'),
                "mobile_number": resume_data.get('mobile_number'),
                "degree": resume_data.get('degree'),
                "no_of_pages": resume_data.get('no_of_pages')
            },
            "cand_level": cand_level,
            "skills": skills,
            "recommended_skills": recommended_skills,
            "reco_field": reco_field,
            "courses": rec_course,
            "resume_score": resume_score,
            "resume_video": res_vid,
            "interview_video": int_vid
        }
    except Exception as e:
        return {"error": str(e)}

class FeedbackModel(BaseModel):
    name: str
    email: str
    score: str
    comments: str

@app.post("/api/feedback")
async def submit_feedback(feedback: FeedbackModel):
    ts = time.time()
    timestamp = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d_%H:%M:%S')
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO user_feedback (feed_name, feed_email, feed_score, comments, Timestamp)
        VALUES (?, ?, ?, ?, ?)
    """, (feedback.name, feedback.email, feedback.score, feedback.comments, timestamp))
    conn.commit()
    conn.close()
    return {"success": True}

class LoginModel(BaseModel):
    username: str
    password: str

@app.post("/api/admin/login")
async def admin_login(creds: LoginModel):
    if creds.username == 'admin' and creds.password == 'admin@resume-analyzer':
        return {"success": True, "token": "admin-session-token"}
    return {"success": False, "error": "Invalid credentials"}

@app.get("/api/admin/data")
async def get_admin_data():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM user_data ORDER BY ID DESC")
    user_data = [dict(row) for row in cursor.fetchall()]
    
    cursor.execute("SELECT * FROM user_feedback ORDER BY ID DESC")
    feedback_data = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    return {
        "success": True,
        "user_data": user_data,
        "feedback_data": feedback_data
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
