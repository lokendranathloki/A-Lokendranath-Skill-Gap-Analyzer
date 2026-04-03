from flask import Flask, request, jsonify, render_template, session, send_file
import os
import re
import numpy as np
from werkzeug.utils import secure_filename
import csv
from datetime import datetime
import io
import base64
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

app = Flask(__name__)
app.secret_key = 'skill-gap-analyzer-secret-key-2024'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Create upload folder
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Allowed extensions
ALLOWED_EXTENSIONS = {'txt'}  # Start with just txt files to avoid PDF/DOCX dependencies

# Simplified skill database
TECH_SKILLS = [
    "python", "java", "c++", "javascript", "typescript", "ruby", "go", "rust",
    "machine learning", "deep learning", "nlp", "data analysis", "statistics",
    "tensorflow", "pytorch", "keras", "scikit-learn", "pandas", "numpy",
    "sql", "mysql", "postgresql", "mongodb", "redis",
    "aws", "azure", "gcp", "docker", "kubernetes",
    "tableau", "power bi", "matplotlib", "seaborn",
    "django", "flask", "react", "angular", "vue.js",
    "git", "jenkins", "jira", "confluence"
]

SOFT_SKILLS = [
    "communication", "teamwork", "leadership", "problem solving",
    "critical thinking", "creativity", "adaptability", "time management",
    "collaboration", "presentation", "negotiation", "conflict resolution",
    "emotional intelligence", "empathy", "decision making", "mentoring"
]

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_txt(file_path):
    """Extract text from TXT file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        try:
            with open(file_path, 'r', encoding='latin-1') as f:
                return f.read()
        except Exception as e:
            print(f"Error reading file: {e}")
            return ""

def extract_text(file_path):
    """Extract text from file"""
    return extract_text_from_txt(file_path)

def extract_skills_simple(text):
    """Simple skill extraction without ML dependencies"""
    text_lower = text.lower()
    found_skills = []
    
    # Check technical skills
    for skill in TECH_SKILLS:
        if skill in text_lower:
            # Calculate simple confidence based on context
            confidence = 85
            # Check for skill section
            if "skill" in text_lower[max(0, text_lower.find(skill)-50):min(len(text_lower), text_lower.find(skill)+50)]:
                confidence += 10
            found_skills.append({
                "name": skill.title(),
                "type": "Technical Skill",
                "confidence": min(confidence, 100)
            })
    
    # Check soft skills
    for skill in SOFT_SKILLS:
        if skill in text_lower:
            confidence = 80
            found_skills.append({
                "name": skill.title(),
                "type": "Soft Skill",
                "confidence": min(confidence, 100)
            })
    
    # Remove duplicates (keep highest confidence)
    unique_skills = {}
    for skill in found_skills:
        key = skill["name"].lower()
        if key not in unique_skills or skill["confidence"] > unique_skills[key]["confidence"]:
            unique_skills[key] = skill
    
    return list(unique_skills.values())

def calculate_similarity_simple(text1, text2):
    """Simple word overlap similarity"""
    words1 = set(re.findall(r'\b\w+\b', text1.lower()))
    words2 = set(re.findall(r'\b\w+\b', text2.lower()))
    
    if not words1 or not words2:
        return 0
    
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    
    return round((len(intersection) / len(union)) * 100, 2)

def analyze_skill_gap(resume_skills, jd_skills):
    """Analyze gaps between resume and job description"""
    resume_skill_names = [s["name"].lower() for s in resume_skills]
    jd_skill_names = [s["name"].lower() for s in jd_skills]
    
    matched = []
    missing = []
    
    for jd_skill in jd_skills:
        if jd_skill["name"].lower() in resume_skill_names:
            matched.append(jd_skill)
        else:
            missing.append(jd_skill)
    
    # Calculate match percentages
    total = len(jd_skills)
    matched_count = len(matched)
    missing_count = len(missing)
    
    overall_match = (matched_count / total * 100) if total > 0 else 0
    
    return {
        "matched": matched,
        "missing": missing,
        "matched_count": matched_count,
        "missing_count": missing_count,
        "overall_match": round(overall_match, 2),
        "total_jd_skills": total
    }

def generate_recommendations(missing_skills):
    """Generate upskilling recommendations"""
    recommendations = []
    
    course_map = {
        "aws": "AWS Certified Solutions Architect",
        "azure": "Microsoft Azure Fundamentals",
        "gcp": "Google Cloud Professional",
        "docker": "Docker Mastery Course",
        "kubernetes": "Certified Kubernetes Administrator",
        "tensorflow": "TensorFlow Developer Certificate",
        "pytorch": "PyTorch for Deep Learning",
        "python": "Advanced Python Programming",
        "machine learning": "Machine Learning Specialization",
        "sql": "Advanced SQL for Data Analysis",
        "communication": "Business Communication Skills",
        "leadership": "Leadership and Management Course"
    }
    
    for skill in missing_skills[:5]:
        skill_name = skill["name"].lower()
        found = False
        
        for key, course in course_map.items():
            if key in skill_name:
                recommendations.append({
                    "skill": skill["name"],
                    "recommendation": course,
                    "priority": "High" if skill["type"] == "Technical Skill" else "Medium"
                })
                found = True
                break
        
        if not found:
            recommendations.append({
                "skill": skill["name"],
                "recommendation": f"Online courses and certifications in {skill['name']}",
                "priority": "Medium"
            })
    
    return recommendations

def create_visualizations(analysis_data):
    """Create simple visualizations"""
    visuals = {}
    
    # Bar chart for matched skills
    if analysis_data.get("matched"):
        plt.figure(figsize=(10, 6))
        skills = [s["name"] for s in analysis_data["matched"][:8]]
        confidences = [s["confidence"] for s in analysis_data["matched"][:8]]
        
        if skills:
            colors = ['#28a745'] * len(skills)
            plt.barh(skills, confidences, color=colors)
            plt.xlabel('Confidence Score (%)')
            plt.title('Top Skill Matches')
            plt.tight_layout()
            
            img = io.BytesIO()
            plt.savefig(img, format='png', dpi=100, bbox_inches='tight')
            img.seek(0)
            visuals['match_chart'] = base64.b64encode(img.getvalue()).decode()
            plt.close()
    
    # Pie chart for skill distribution
    plt.figure(figsize=(8, 8))
    labels = ['Matched', 'Missing']
    sizes = [
        analysis_data["matched_count"],
        analysis_data["missing_count"]
    ]
    colors = ['#28a745', '#dc3545']
    
    if sum(sizes) > 0:
        plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
        plt.title('Skill Distribution')
        plt.axis('equal')
        
        img = io.BytesIO()
        plt.savefig(img, format='png', dpi=100, bbox_inches='tight')
        img.seek(0)
        visuals['pie_chart'] = base64.b64encode(img.getvalue()).decode()
        plt.close()
    
    return visuals

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_files():
    """Upload and parse documents"""
    if 'resume' not in request.files or 'jd' not in request.files:
        return jsonify({'error': 'Missing files'}), 400
    
    resume = request.files['resume']
    jd = request.files['jd']
    
    if resume.filename == '' or jd.filename == '':
        return jsonify({'error': 'No files selected'}), 400
    
    # Save temporarily
    resume_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(resume.filename))
    jd_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(jd.filename))
    
    resume.save(resume_path)
    jd.save(jd_path)
    
    # Extract text
    resume_text = extract_text(resume_path)
    jd_text = extract_text(jd_path)
    
    # Clean up
    os.remove(resume_path)
    os.remove(jd_path)
    
    # Store in session
    session['resume_text'] = resume_text
    session['jd_text'] = jd_text
    session['resume_filename'] = resume.filename
    session['jd_filename'] = jd.filename
    
    return jsonify({
        'success': True,
        'resume': {
            'filename': resume.filename,
            'characters': len(resume_text),
            'words': len(resume_text.split()),
            'preview': resume_text[:500] + '...' if len(resume_text) > 500 else resume_text
        },
        'jd': {
            'filename': jd.filename,
            'characters': len(jd_text),
            'words': len(jd_text.split()),
            'preview': jd_text[:500] + '...' if len(jd_text) > 500 else jd_text
        }
    })

@app.route('/extract', methods=['POST'])
def extract_skills():
    """Extract skills from text"""
    resume_text = session.get('resume_text', '')
    jd_text = session.get('jd_text', '')
    
    if not resume_text or not jd_text:
        return jsonify({'error': 'Please upload documents first'}), 400
    
    # Extract skills
    resume_skills = extract_skills_simple(resume_text)
    jd_skills = extract_skills_simple(jd_text)
    
    # Calculate stats
    tech_skills = [s for s in resume_skills if s["type"] == "Technical Skill"]
    soft_skills = [s for s in resume_skills if s["type"] == "Soft Skill"]
    avg_confidence = sum(s["confidence"] for s in resume_skills) / len(resume_skills) if resume_skills else 0
    
    # Store in session
    session['resume_skills'] = resume_skills
    session['jd_skills'] = jd_skills
    
    return jsonify({
        'success': True,
        'resume_skills': resume_skills,
        'jd_skills': jd_skills,
        'stats': {
            'technical': len(tech_skills),
            'soft': len(soft_skills),
            'total': len(resume_skills),
            'avg_confidence': round(avg_confidence, 2)
        }
    })

@app.route('/analyze', methods=['POST'])
def analyze_gaps():
    """Analyze skill gaps"""
    resume_skills = session.get('resume_skills', [])
    jd_skills = session.get('jd_skills', [])
    resume_text = session.get('resume_text', '')
    jd_text = session.get('jd_text', '')
    
    if not resume_skills or not jd_skills:
        return jsonify({'error': 'Please extract skills first'}), 400
    
    # Analyze gaps
    gap_analysis = analyze_skill_gap(resume_skills, jd_skills)
    
    # Calculate similarity
    similarity = calculate_similarity_simple(resume_text, jd_text)
    
    # Generate recommendations
    recommendations = generate_recommendations(gap_analysis['missing'])
    
    result = {
        **gap_analysis,
        'similarity': similarity,
        'recommendations': recommendations
    }
    
    session['gap_analysis'] = result
    
    return jsonify({
        'success': True,
        'analysis': result
    })

@app.route('/dashboard', methods=['POST'])
def get_dashboard():
    """Generate dashboard"""
    gap_analysis = session.get('gap_analysis', {})
    resume_skills = session.get('resume_skills', [])
    
    if not gap_analysis:
        return jsonify({'error': 'Please analyze gaps first'}), 400
    
    # Create visualizations
    visuals = create_visualizations(gap_analysis)
    
    # Get top skills
    top_skills = sorted(resume_skills, key=lambda x: x['confidence'], reverse=True)[:6]
    
    return jsonify({
        'success': True,
        'dashboard': {
            'overall_match': gap_analysis.get('overall_match', 0),
            'matched_count': gap_analysis.get('matched_count', 0),
            'missing_count': gap_analysis.get('missing_count', 0),
            'similarity': gap_analysis.get('similarity', 0),
            'top_skills': top_skills,
            'recommendations': gap_analysis.get('recommendations', []),
            'visualizations': visuals
        }
    })

@app.route('/export', methods=['POST'])
def export_report():
    """Export report as CSV"""
    gap_analysis = session.get('gap_analysis', {})
    resume_skills = session.get('resume_skills', [])
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow(['Skill Gap Analysis Report'])
    writer.writerow(['Generated:', datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
    writer.writerow([])
    writer.writerow(['Overall Match:', f"{gap_analysis.get('overall_match', 0)}%"])
    writer.writerow(['Matched Skills:', gap_analysis.get('matched_count', 0)])
    writer.writerow(['Missing Skills:', gap_analysis.get('missing_count', 0)])
    writer.writerow([])
    
    writer.writerow(['Skill', 'Type', 'Confidence'])
    for skill in resume_skills[:20]:
        writer.writerow([skill['name'], skill['type'], f"{skill['confidence']}%"])
    writer.writerow([])
    
    writer.writerow(['Missing Skill', 'Recommendation', 'Priority'])
    for rec in gap_analysis.get('recommendations', []):
        writer.writerow([rec['skill'], rec['recommendation'], rec['priority']])
    
    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode()),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'skill_gap_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    )

@app.route('/reset', methods=['POST'])
def reset_session():
    session.clear()
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(debug=True)