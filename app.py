import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import json
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

# Page configuration
st.set_page_config(
    page_title="Study Schedule Manager",
    page_icon="📚",
    layout="wide"
)

# Database setup
def init_db():
    conn = sqlite3.connect('study_schedule.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS schedules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_name TEXT NOT NULL,
            course_code TEXT NOT NULL,
            teacher TEXT NOT NULL,
            lesson TEXT,
            notes TEXT,
            study_date TEXT NOT NULL,
            session TEXT NOT NULL,
            color TEXT DEFAULT '#4CAF50',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# CRUD Operations
def add_schedule(course_name, course_code, teacher, lesson, notes, study_date, session, color):
    conn = sqlite3.connect('study_schedule.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO schedules (course_name, course_code, teacher, lesson, notes, study_date, session, color)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (course_name, course_code, teacher, lesson, notes, study_date, session, color))
    conn.commit()
    conn.close()

def get_all_schedules():
    conn = sqlite3.connect('study_schedule.db')
    df = pd.read_sql_query("SELECT * FROM schedules ORDER BY study_date, session", conn)
    conn.close()
    return df

def update_schedule(schedule_id, course_name, course_code, teacher, lesson, notes, study_date, session, color):
    conn = sqlite3.connect('study_schedule.db')
    c = conn.cursor()
    c.execute('''
        UPDATE schedules 
        SET course_name=?, course_code=?, teacher=?, lesson=?, notes=?, study_date=?, session=?, color=?
        WHERE id=?
    ''', (course_name, course_code, teacher, lesson, notes, study_date, session, color, schedule_id))
    conn.commit()
    conn.close()

def delete_schedule(schedule_id):
    conn = sqlite3.connect('study_schedule.db')
    c = conn.cursor()
    c.execute('DELETE FROM schedules WHERE id=?', (schedule_id,))
    conn.commit()
    conn.close()

def export_to_csv():
    df = get_all_schedules()
    return df.to_csv(index=False).encode('utf-8')

def generate_pdf():
    df = get_all_schedules()
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    
    # Title
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1f4788'),
        spaceAfter=30,
        alignment=1
    )
    title = Paragraph("Study Schedule", title_style)
    elements.append(title)
    elements.append(Spacer(1, 0.3*inch))
    
    # Table data
    data = [['Date', 'Session', 'Course', 'Code', 'Lesson', 'Teacher', 'Notes']]
    for _, row in df.iterrows():
        data.append([
            row['study_date'],
            row['session'],
            row['course_name'],
            row['course_code'],
            row['lesson'][:40] + '...' if len(str(row['lesson'])) > 40 else row['lesson'],
            row['teacher'],
            row['notes'][:40] + '...' if len(str(row['notes'])) > 40 else row['notes']
        ])
    
    # Create table
    table = Table(data, colWidths=[0.9*inch, 0.8*inch, 1.2*inch, 0.8*inch, 1.3*inch, 1*inch, 1.5*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f4788')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
    ]))
    
    elements.append(table)
    doc.build(elements)
    buffer.seek(0)
    return buffer

# Initialize database
init_db()

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        color: #1f4788;
        text-align: center;
        margin-bottom: 2rem;
    }
    .stButton>button {
        width: 100%;
    }
    .schedule-card {
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
    </style>
""", unsafe_allow_html=True)

# Header
st.markdown("<h1 class='main-header'>📚 Study Schedule Manager</h1>", unsafe_allow_html=True)

# Sidebar for adding/editing schedules
with st.sidebar:
    st.header("➕ Add New Schedule")
    
    with st.form("schedule_form", clear_on_submit=True):
        course_name = st.text_input("Course Name*", placeholder="e.g., Calculus I")
        course_code = st.text_input("Course Code*", placeholder="e.g., MATH101")
        teacher = st.text_input("Teacher*", placeholder="e.g., Dr. Smith")
        lesson = st.text_input("Lesson/Topic", placeholder="e.g., Chapter 3: Derivatives")
        notes = st.text_area("Notes", placeholder="Optional notes about the class...")
        study_date = st.date_input("Study Date*", min_value=datetime.today())
        session = st.selectbox("Session*", ["Morning", "Afternoon", "Evening"])
        color = st.color_picker("Choose Color", "#4CAF50")
        
        submitted = st.form_submit_button("Add Schedule", use_container_width=True)
        
        if submitted:
            if course_name and course_code and teacher:
                add_schedule(
                    course_name, course_code, teacher, lesson, notes,
                    study_date.strftime('%Y-%m-%d'), session, color
                )
                st.success("✅ Schedule added successfully!")
                st.rerun()
            else:
                st.error("Please fill in all required fields (*)")

# Main content tabs
tab1, tab2, tab3 = st.tabs(["📋 All Schedules", "📅 Weekly Calendar", "⚙️ Manage"])

# Tab 1: All Schedules
with tab1:
    st.subheader("All Study Schedules")
    
    df = get_all_schedules()
    
    if not df.empty:
        # Export buttons
        col1, col2, col3 = st.columns([1, 1, 4])
        with col1:
            csv = export_to_csv()
            st.download_button(
                label="📥 Export CSV",
                data=csv,
                file_name=f"study_schedule_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        with col2:
            pdf_buffer = generate_pdf()
            st.download_button(
                label="📄 Export PDF",
                data=pdf_buffer,
                file_name=f"study_schedule_{datetime.now().strftime('%Y%m%d')}.pdf",
                mime="application/pdf"
            )
        
        st.dataframe(
            df[['id', 'study_date', 'session', 'course_name', 'course_code', 'lesson', 'teacher', 'notes', 'color']],
            use_container_width=True,
            height=400
        )
    else:
        st.info("No schedules yet. Add your first schedule using the sidebar!")

# Tab 2: Weekly Calendar View
with tab2:
    st.subheader("Weekly Calendar View")
    
    # Week selector
    col1, col2 = st.columns([3, 1])
    with col1:
        selected_date = st.date_input("Select a date in the week", datetime.today())
    
    # Calculate week start (Monday)
    week_start = selected_date - timedelta(days=selected_date.weekday())
    week_dates = [week_start + timedelta(days=i) for i in range(7)]
    
    df = get_all_schedules()
    
    if not df.empty:
        # Create calendar grid
        sessions = ["Morning", "Afternoon", "Evening"]
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        
        # Display week range
        st.markdown(f"**Week: {week_dates[0].strftime('%B %d')} - {week_dates[6].strftime('%B %d, %Y')}**")
        
        # Create columns for each day
        cols = st.columns(7)
        
        for idx, (col, day, date) in enumerate(zip(cols, days, week_dates)):
            with col:
                st.markdown(f"**{day}**")
                st.markdown(f"*{date.strftime('%m/%d')}*")
                
                for session in sessions:
                    # Filter schedules for this day and session
                    day_schedules = df[
                        (df['study_date'] == date.strftime('%Y-%m-%d')) & 
                        (df['session'] == session)
                    ]
                    
                    if not day_schedules.empty:
                        for _, schedule in day_schedules.iterrows():
                            lesson_text = schedule['lesson'] if schedule['lesson'] and schedule['lesson'].strip() else ''
                            st.markdown(
                                f"""<div style='background-color: {schedule['color']}; 
                                padding: 10px; border-radius: 5px; margin: 5px 0; 
                                color: white; font-size: 0.75rem; min-height: 80px;
                                box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>
                                <b style='font-size: 0.7rem;'>{session}</b><br>
                                <b style='font-size: 0.9rem;'>{schedule['course_name']}</b><br>
                                <span style='font-size: 0.7rem;'>{schedule['course_code']}</span><br>
                                {f"<div style='font-size: 0.7rem; margin: 3px 0; font-style: italic;'>📖 {lesson_text}</div>" if lesson_text else ""}
                                <small style='font-size: 0.65rem;'>👨‍🏫 {schedule['teacher']}</small>
                                </div>""",
                                unsafe_allow_html=True
                            )
                    else:
                        st.markdown(
                            f"""<div style='background-color: #f5f5f5; 
                            padding: 10px; border-radius: 5px; margin: 5px 0; 
                            text-align: center; font-size: 0.7rem; color: #bbb;
                            min-height: 80px; display: flex; align-items: center;
                            justify-content: center; border: 1px dashed #ddd;'>
                            <span>{session}<br>Free</span>
                            </div>""",
                            unsafe_allow_html=True
                        )
    else:
        st.info("No schedules to display. Add schedules to see them in calendar view!")

# Tab 3: Manage Schedules
with tab3:
    st.subheader("Edit or Delete Schedules")
    
    df = get_all_schedules()
    
    if not df.empty:
        # Select schedule to edit/delete
        schedule_options = [f"{row['id']}: {row['course_name']} - {row['study_date']} ({row['session']})" 
                          for _, row in df.iterrows()]
        selected = st.selectbox("Select a schedule", schedule_options)
        
        if selected:
            schedule_id = int(selected.split(':')[0])
            schedule = df[df['id'] == schedule_id].iloc[0]
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("### Edit Schedule")
                with st.form("edit_form"):
                    edit_course_name = st.text_input("Course Name", value=schedule['course_name'])
                    edit_course_code = st.text_input("Course Code", value=schedule['course_code'])
                    edit_teacher = st.text_input("Teacher", value=schedule['teacher'])
                    edit_lesson = st.text_input("Lesson/Topic", value=schedule['lesson'] if schedule['lesson'] else "")
                    edit_notes = st.text_area("Notes", value=schedule['notes'])
                    edit_study_date = st.date_input("Study Date", 
                                                    value=datetime.strptime(schedule['study_date'], '%Y-%m-%d'))
                    edit_session = st.selectbox("Session", ["Morning", "Afternoon", "Evening"], 
                                               index=["Morning", "Afternoon", "Evening"].index(schedule['session']))
                    edit_color = st.color_picker("Choose Color", value=schedule['color'])
                    
                    update_btn = st.form_submit_button("💾 Update Schedule", use_container_width=True)
                    
                    if update_btn:
                        update_schedule(
                            schedule_id, edit_course_name, edit_course_code, 
                            edit_teacher, edit_lesson, edit_notes, edit_study_date.strftime('%Y-%m-%d'),
                            edit_session, edit_color
                        )
                        st.success("✅ Schedule updated!")
                        st.rerun()
            
            with col2:
                st.write("### Schedule Details")
                lesson_display = f"<p><b>Lesson:</b> {schedule['lesson']}</p>" if schedule['lesson'] and schedule['lesson'].strip() else ""
                st.markdown(f"""
                <div style='background-color: {schedule['color']}; padding: 20px; 
                border-radius: 10px; color: white;'>
                    <h3>{schedule['course_name']}</h3>
                    <p><b>Code:</b> {schedule['course_code']}</p>
                    <p><b>Teacher:</b> {schedule['teacher']}</p>
                    {lesson_display}
                    <p><b>Date:</b> {schedule['study_date']}</p>
                    <p><b>Session:</b> {schedule['session']}</p>
                    <p><b>Notes:</b> {schedule['notes']}</p>
                </div>
                """, unsafe_allow_html=True)
                
                st.write("")
                if st.button("🗑️ Delete This Schedule", type="secondary", use_container_width=True):
                    delete_schedule(schedule_id)
                    st.success("✅ Schedule deleted!")
                    st.rerun()
    else:
        st.info("No schedules to manage yet.")

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666;'>Made with ❤️ using Streamlit | "
    "Study Schedule Manager v1.0</div>",
    unsafe_allow_html=True
)