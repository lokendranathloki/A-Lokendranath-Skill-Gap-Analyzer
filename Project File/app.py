from flask import Flask, request, jsonify, render_template, session, send_file
import os
import re
import json
from werkzeug.utils import secure_filename
from datetime import datetime
import io
import base64
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Try to import sklearn with error handling
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("=" * 50)
    print("WARNING: scikit-learn not installed!")
    print("Install it using: pip install scikit-learn")
    print("=" * 50)

# Try to import FPDF for PDF export
try:
    from fpdf import FPDF
    FPDF_AVAILABLE = True
except ImportError:
    FPDF_AVAILABLE = False
    print("=" * 50)
    print("WARNING: fpdf not installed!")
    print("Install it using: pip install fpdf")
    print("=" * 50)

app = Flask(__name__)
app.secret_key = 'skill-gap-analyzer-secret-key-2024'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

# Create upload folder
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Allowed extensions
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx'}

# Try to import PDF and DOCX libraries
try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    print("PyPDF2 not installed. Install with: pip install PyPDF2")

try:
    import docx
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False
    print("python-docx not installed. Install with: pip install python-docx")

# Skill database with synonyms (Expanded)
TECH_SKILLS = {
    "python": ["python", "py", "django", "flask", "fastapi"],
    "java": ["java", "spring", "hibernate", "j2ee"],
    "javascript": ["javascript", "js", "ecmascript", "node.js", "nodejs"],
    "react": ["react", "reactjs", "react.js"],
    "angular": ["angular", "angularjs", "angular.js"],
    "vue": ["vue", "vuejs", "vue.js"],
    "machine learning": ["machine learning", "ml", "deep learning", "dl", "neural networks"],
    "sql": ["sql", "mysql", "postgresql", "postgres", "database"],
    "mongodb": ["mongodb", "mongo", "nosql"],
    "aws": ["aws", "amazon web services", "ec2", "s3", "lambda"],
    "azure": ["azure", "microsoft azure", "az-"],
    "docker": ["docker", "container", "dockerfile"],
    "kubernetes": ["kubernetes", "k8s", "kube"],
    "tensorflow": ["tensorflow", "tf"],
    "pytorch": ["pytorch", "torch"],
    "git": ["git", "github", "gitlab", "version control"],
    "ci/cd": ["ci/cd", "jenkins", "circleci", "github actions"],
    "devops": ["devops", "terraform", "ansible"],
    "rest api": ["rest api", "restful", "api", "rest"],
    "graphql": ["graphql", "gql"],
    "data analysis": ["data analysis", "analytics", "business intelligence"],
    "tableau": ["tableau", "data visualization"],
    "power bi": ["power bi", "powerbi"],
    "fastapi": ["fastapi", "fast api"],
    "leadership": ["leadership", "team lead", "leading", "mentoring"],
    "communication": ["communication", "verbal", "written", "presentation"],
    "html": ["html", "html5", "css", "css3"],
    "c++": ["c++", "cpp", "c plus plus"],
    "c#": ["c#", "csharp", "dotnet"],
    "php": ["php", "laravel", "symfony"],
    "ruby": ["ruby", "rails", "ruby on rails"],
    "swift": ["swift", "ios", "apple"],
    "kotlin": ["kotlin", "android"],
    "flutter": ["flutter", "dart", "mobile"],
    "react native": ["react native", "rn", "expo"],
    "blockchain": ["blockchain", "web3", "solidity", "ethereum"],
    "ai": ["ai", "artificial intelligence", "openai", "gpt", "llm"],
    "rag": ["rag", "retrieval augmented generation", "langchain"],
    "big data": ["big data", "hadoop", "spark", "kafka"],
    "data science": ["data science", "analytics", "statistics", "r"],
    "excel": ["excel", "spreadsheet", "vba"],
    "sap": ["sap", "erp", "sap hana"],
    "salesforce": ["salesforce", "crm", "sales cloud"],
    "cybersecurity": ["cybersecurity", "security", "information security", "ethical hacking"],
    "cloud": ["cloud", "cloud computing", "iaas", "paas", "saas"],
    "pandas": ["pandas", "data manipulation", "python data"],
    "numpy": ["numpy", "numerical python", "scientific computing"]
}

SOFT_SKILLS = {
    "communication": ["communication", "verbal communication", "written communication", "presentation", "public speaking"],
    "leadership": ["leadership", "team lead", "leading", "mentoring", "coaching"],
    "teamwork": ["teamwork", "collaboration", "team player", "cooperation", "interpersonal"],
    "problem solving": ["problem solving", "analytical", "critical thinking", "troubleshooting", "diagnostic"],
    "adaptability": ["adaptability", "flexible", "agile", "resilient", "versatile"],
    "time management": ["time management", "deadline", "prioritization", "organization", "planning"],
    "project management": ["project management", "project manager", "pm", "scrum master", "agile", "waterfall"],
    "creativity": ["creativity", "innovative", "creative thinking", "design thinking"],
    "emotional intelligence": ["emotional intelligence", "eq", "empathy", "self awareness"],
    "conflict resolution": ["conflict resolution", "negotiation", "mediation", "dispute resolution"],
    "decision making": ["decision making", "judgment", "decisiveness", "critical decisions"],
    "strategic thinking": ["strategic thinking", "strategy", "long term planning", "vision"],
    "customer focus": ["customer focus", "customer service", "client relations", "customer success"],
    "results driven": ["results driven", "goal oriented", "achievement focused", "target driven"],
    "initiative": ["initiative", "self starter", "proactive", "drive"],
    "attention to detail": ["attention to detail", "detail oriented", "thorough", "meticulous"],
    "work ethic": ["work ethic", "dedication", "commitment", "professionalism"],
    "learning agility": ["learning agility", "quick learner", "fast learner", "adaptable learner"],
    "influencing": ["influencing", "persuasion", "stakeholder management", "negotiation"],
    "networking": ["networking", "relationship building", "connections", "business development"],
    "presentation": ["presentation", "public speaking", "demo", "pitching"],
    "writing": ["writing", "technical writing", "documentation", "report writing"],
    "research": ["research", "analysis", "investigation", "data gathering"],
    "mentoring": ["mentoring", "coaching", "training", "development"],
    "collaboration": ["collaboration", "cross functional", "teamwork", "coordination"],
    "innovation": ["innovation", "creative", "novel ideas", "disruptive thinking"]
}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_txt(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        with open(file_path, 'r', encoding='latin-1') as f:
            return f.read()
    except Exception as e:
        return ""

def extract_text_from_pdf(file_path):
    if not PDF_AVAILABLE:
        return "PDF support not available. Please install PyPDF2."
    try:
        text = ""
        with open(file_path, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text
    except Exception as e:
        return f"Error reading PDF: {str(e)}"

def extract_text_from_docx(file_path):
    if not DOCX_AVAILABLE:
        return "DOCX support not available. Please install python-docx."
    try:
        doc = docx.Document(file_path)
        text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        return text
    except Exception as e:
        return f"Error reading DOCX: {str(e)}"

def extract_text(file_path):
    ext = file_path.rsplit('.', 1)[1].lower()
    if ext == 'txt':
        return extract_text_from_txt(file_path)
    elif ext == 'pdf':
        return extract_text_from_pdf(file_path)
    elif ext == 'docx':
        return extract_text_from_docx(file_path)
    return ""

def extract_skills_with_synonyms(text):
    """Extract skills with synonym support and confidence scoring"""
    text_lower = text.lower()
    found_skills = {}
    
    # Extract technical skills with synonyms
    for main_skill, synonyms in TECH_SKILLS.items():
        confidence = 0
        found_variants = []
        
        for synonym in synonyms:
            if synonym in text_lower:
                # Calculate position-based confidence
                pos = text_lower.find(synonym)
                if pos > 0:
                    context = text_lower[max(0, pos-50):min(len(text_lower), pos+50)]
                    if "skill" in context or "experience" in context or "proficient" in context:
                        confidence += 20
                    if "expert" in context or "advanced" in context or "master" in context:
                        confidence += 15
                    if "basic" in context or "familiar" in context or "beginner" in context:
                        confidence -= 10
                    if "certified" in context or "certification" in context:
                        confidence += 10
                
                # Count occurrences (more mentions = higher confidence)
                count = text_lower.count(synonym)
                confidence += min(count * 5, 25)
                found_variants.append(synonym)
        
        if found_variants:
            confidence = min(confidence + 70, 100)
            found_skills[main_skill] = {
                "name": main_skill.title(),
                "type": "Technical",
                "confidence": confidence,
                "variants": found_variants
            }
    
    # Extract soft skills with synonyms
    for main_skill, synonyms in SOFT_SKILLS.items():
        confidence = 0
        found_variants = []
        
        for synonym in synonyms:
            if synonym in text_lower:
                pos = text_lower.find(synonym)
                if pos > 0:
                    context = text_lower[max(0, pos-50):min(len(text_lower), pos+50)]
                    if "skill" in context or "demonstrated" in context or "proven" in context:
                        confidence += 20
                    if "strong" in context or "excellent" in context:
                        confidence += 10
                
                count = text_lower.count(synonym)
                confidence += min(count * 5, 25)
                found_variants.append(synonym)
        
        if found_variants:
            confidence = min(confidence + 65, 100)
            found_skills[main_skill] = {
                "name": main_skill.title(),
                "type": "Soft",
                "confidence": confidence,
                "variants": found_variants
            }
    
    return list(found_skills.values())

def calculate_cosine_similarity(text1, text2):
    """Calculate semantic similarity using TF-IDF and cosine similarity"""
    if not SKLEARN_AVAILABLE:
        # Fallback to simple word overlap if sklearn not available
        words1 = set(re.findall(r'\b\w+\b', text1.lower()))
        words2 = set(re.findall(r'\b\w+\b', text2.lower()))
        if not words1 or not words2:
            return 0
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        return round((len(intersection) / len(union)) * 100, 2)
    
    if not text1 or not text2:
        return 0
    
    try:
        vectorizer = TfidfVectorizer(stop_words='english', max_features=1000)
        tfidf_matrix = vectorizer.fit_transform([text1, text2])
        similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        return round(similarity * 100, 2)
    except Exception as e:
        print(f"Error calculating similarity: {e}")
        return 0

def analyze_skill_gap(resume_skills, jd_skills):
    """Analyze gaps with exact, partial, and missing matching"""
    resume_names = [s["name"].lower() for s in resume_skills]
    
    matched = []
    partial = []
    missing = []
    
    for jd_skill in jd_skills:
        jd_name = jd_skill["name"].lower()
        found = False
        is_partial = False
        
        for resume_skill in resume_skills:
            resume_name = resume_skill["name"].lower()
            
            # Exact match
            if jd_name == resume_name:
                matched.append(jd_skill)
                found = True
                break
            # Partial match (one skill contains the other)
            elif jd_name in resume_name or resume_name in jd_name:
                is_partial = True
        
        if not found:
            if is_partial:
                partial.append(jd_skill)
            else:
                missing.append(jd_skill)
    
    total = len(jd_skills)
    matched_count = len(matched)
    partial_count = len(partial)
    missing_count = len(missing)
    
    # Weighted match: exact=100%, partial=50%
    weighted_match = ((matched_count * 100) + (partial_count * 50)) / total if total > 0 else 0
    risk_percent = 100 - weighted_match
    
    # Decision logic
    is_recommended = weighted_match >= 70 and missing_count <= 3
    
    return {
        "matched": matched,
        "partial": partial,
        "missing": missing,
        "matched_count": matched_count,
        "partial_count": partial_count,
        "missing_count": missing_count,
        "overall_match": round(weighted_match, 2),
        "risk_percent": round(risk_percent, 2),
        "is_recommended": is_recommended,
        "total_jd_skills": total
    }

def generate_recommendations(missing_skills):
    """Generate detailed upskilling recommendations"""
    recommendations = []
    
    course_recommendations = {
        "python": "Complete Python Bootcamp + Python for Data Science + Practice on LeetCode",
        "java": "Java Programming Masterclass + Oracle Certification Prep + Spring Framework",
        "javascript": "The Complete JavaScript Course + FreeCodeCamp JS Algorithms + ES6+ Tutorials",
        "react": "React - The Complete Guide + React Official Tutorial + Build 5 Projects",
        "angular": "Angular Complete Guide + Angular Official Docs + RxJS Mastery",
        "machine learning": "Machine Learning Specialization (Andrew Ng) + Kaggle Projects",
        "sql": "SQL for Data Analysis + LeetCode SQL Problems + Database Design Course",
        "aws": "AWS Certified Solutions Architect + Hands-on Labs + AWS Free Tier Projects",
        "docker": "Docker Mastery + Docker Official Tutorials + Containerization Projects",
        "kubernetes": "Certified Kubernetes Administrator + K8s Practice + Minikube Projects",
        "communication": "Effective Communication Course + Toastmasters + Public Speaking",
        "leadership": "Leadership Principles + People Management Skills + Team Building",
        "project management": "PMP Certification Prep + Agile Scrum Master Certification",
        "fastapi": "FastAPI Official Tutorial + Build REST APIs + Async Python",
        "django": "Django for Professionals + Django REST Framework + Real World Projects"
    }
    
    for skill in missing_skills[:10]:
        skill_name = skill["name"].lower()
        found = False
        
        for key, course in course_recommendations.items():
            if key in skill_name or skill_name in key:
                recommendations.append({
                    "skill": skill["name"],
                    "recommendation": course,
                    "priority": "High" if skill["type"] == "Technical" else "Medium",
                    "estimated_time": "4-6 weeks" if skill["type"] == "Technical" else "2-3 weeks"
                })
                found = True
                break
        
        if not found:
            recommendations.append({
                "skill": skill["name"],
                "recommendation": f"Comprehensive online courses and hands-on projects in {skill['name']}",
                "priority": "Medium",
                "estimated_time": "3-5 weeks"
            })
    
    return recommendations

def generate_ai_insights(resume_skills, gap_analysis):
    """Generate AI-powered insights about strengths and weaknesses"""
    high_confidence = [s for s in resume_skills if s["confidence"] >= 85]
    
    strengths = []
    weaknesses = []
    
    # Identify strengths
    for skill in high_confidence[:3]:
        if skill["type"] == "Technical":
            strengths.append(f"Strong proficiency in {skill['name']}")
        else:
            strengths.append(f"Excellent {skill['name'].lower()} skills")
    
    # Identify gaps from missing skills
    for skill in gap_analysis.get("missing", [])[:3]:
        weaknesses.append(f"Missing {skill['name']} ({skill['type']} skill)")
    
    if not strengths:
        strengths = ["Good foundation in core technologies"]
    if not weaknesses:
        weaknesses = ["Well-aligned with job requirements"]
    
    # Calculate overall assessment
    match_score = gap_analysis.get('overall_match', 0)
    if match_score >= 85:
        assessment = "Excellent fit! Candidate strongly matches all requirements."
    elif match_score >= 70:
        assessment = "Good fit. Minor skill gaps can be easily addressed."
    elif match_score >= 50:
        assessment = "Moderate fit. Significant upskilling recommended."
    else:
        assessment = "Needs substantial development in key areas."
    
    return {
        "strengths": strengths,
        "weaknesses": weaknesses,
        "assessment": assessment,
        "summary": f"Candidate matches {gap_analysis.get('overall_match', 0)}% of requirements.",
        "recommended_action": "Proceed with interview" if match_score >= 70 else "Consider upskilling"
    }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_files():
    """Upload and parse multiple resume files and JD"""
    resume_files = request.files.getlist('resumes')
    jd_file = request.files.get('jd')
    manual_jd_text = request.form.get('manual_jd_text', '')
    
    resume_texts = []
    resume_filenames = []
    all_resumes_data = []
    
    for resume in resume_files:
        if resume and resume.filename:
            filename = secure_filename(resume.filename)
            if allowed_file(filename):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{timestamp}_{filename}")
                resume.save(file_path)
                text = extract_text(file_path)
                if text.strip():
                    resume_texts.append(text)
                    resume_filenames.append(resume.filename)
                    all_resumes_data.append({
                        "filename": resume.filename,
                        "text": text
                    })
                os.remove(file_path)
    
    combined_resume_text = "\n\n--- NEXT RESUME ---\n\n".join(resume_texts) if resume_texts else ""
    
    # Process JD
    jd_text = ""
    jd_filename = ""
    
    if manual_jd_text and manual_jd_text.strip():
        jd_text = manual_jd_text.strip()
        jd_filename = "Manual Input"
    elif jd_file and jd_file.filename:
        filename = secure_filename(jd_file.filename)
        if allowed_file(filename):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{timestamp}_{filename}")
            jd_file.save(file_path)
            jd_text = extract_text(file_path)
            jd_filename = jd_file.filename
            os.remove(file_path)
    
    if not combined_resume_text:
        return jsonify({'error': 'Could not extract text from resume files'}), 400
    
    if not jd_text:
        return jsonify({'error': 'Could not extract text from job description'}), 400
    
    # Store in session
    session['all_resumes'] = all_resumes_data
    session['resume_text'] = combined_resume_text
    session['jd_text'] = jd_text
    session['resume_filenames'] = resume_filenames
    session['jd_filename'] = jd_filename
    session['resumes_count'] = len(all_resumes_data)
    
    # Clear previous analysis
    session.pop('all_resumes_skills', None)
    session.pop('jd_skills', None)
    session.pop('all_gap_analyses', None)
    
    return jsonify({
        'success': True,
        'resumes_count': len(all_resumes_data),
        'resume': {
            'filenames': resume_filenames,
            'characters': len(combined_resume_text),
            'words': len(combined_resume_text.split()),
            'preview': combined_resume_text[:1000] + '...' if len(combined_resume_text) > 1000 else combined_resume_text
        },
        'jd': {
            'filename': jd_filename,
            'characters': len(jd_text),
            'words': len(jd_text.split()),
            'preview': jd_text[:1000] + '...' if len(jd_text) > 1000 else jd_text
        }
    })

@app.route('/extract', methods=['POST'])
def extract_skills():
    """Extract skills from all resumes and JD"""
    all_resumes = session.get('all_resumes', [])
    jd_text = session.get('jd_text', '')
    
    if not all_resumes or not jd_text:
        return jsonify({'error': 'Please upload documents first'}), 400
    
    # Extract skills for each resume
    all_resumes_skills = []
    for idx, resume in enumerate(all_resumes):
        skills = extract_skills_with_synonyms(resume['text'])
        all_resumes_skills.append({
            "id": idx,
            "name": resume['filename'],
            "skills": sorted(skills, key=lambda x: x['confidence'], reverse=True)
        })
    
    # Extract JD skills
    jd_skills = extract_skills_with_synonyms(jd_text)
    jd_skills = sorted(jd_skills, key=lambda x: x['confidence'], reverse=True)
    
    # Calculate stats for combined view
    all_skills_combined = []
    for rs in all_resumes_skills:
        all_skills_combined.extend(rs['skills'])
    
    unique_skills = {}
    for skill in all_skills_combined:
        if skill['name'] not in unique_skills:
            unique_skills[skill['name']] = skill
    unique_skills_list = list(unique_skills.values())
    
    tech_count = len([s for s in unique_skills_list if s["type"] == "Technical"])
    soft_count = len([s for s in unique_skills_list if s["type"] == "Soft"])
    total_unique = len(unique_skills_list)
    avg_confidence = sum(s["confidence"] for s in all_skills_combined) / len(all_skills_combined) if all_skills_combined else 0
    
    session['all_resumes_skills'] = all_resumes_skills
    session['jd_skills'] = jd_skills
    
    return jsonify({
        'success': True,
        'all_resumes_skills': all_resumes_skills,
        'jd_skills': jd_skills,
        'stats': {
            'technical': tech_count,
            'soft': soft_count,
            'total': total_unique,
            'avg_confidence': round(avg_confidence, 2),
            'resumes_count': len(all_resumes_skills)
        }
    })

@app.route('/analyze', methods=['POST'])
def analyze_gaps():
    """Analyze skill gaps for all resumes"""
    all_resumes_skills = session.get('all_resumes_skills', [])
    jd_skills = session.get('jd_skills', [])
    all_resumes = session.get('all_resumes', [])
    jd_text = session.get('jd_text', '')
    
    if not all_resumes_skills or not jd_skills:
        return jsonify({'error': 'Please extract skills first'}), 400
    
    # Analyze gaps for each resume
    all_gap_analyses = []
    for resume_skills_data in all_resumes_skills:
        gap_analysis = analyze_skill_gap(resume_skills_data['skills'], jd_skills)
        
        # Get resume text for similarity calculation
        resume_text = ""
        for resume in all_resumes:
            if resume['filename'] == resume_skills_data['name']:
                resume_text = resume['text']
                break
        
        semantic_similarity = calculate_cosine_similarity(resume_text, jd_text)
        recommendations = generate_recommendations(gap_analysis['missing'])
        ai_insights = generate_ai_insights(resume_skills_data['skills'], gap_analysis)
        
        all_gap_analyses.append({
            "resume_id": resume_skills_data['id'],
            "resume_name": resume_skills_data['name'],
            **gap_analysis,
            'semantic_similarity': semantic_similarity,
            'recommendations': recommendations,
            'ai_insights': ai_insights
        })
    
    session['all_gap_analyses'] = all_gap_analyses
    
    return jsonify({
        'success': True,
        'analyses': all_gap_analyses
    })

@app.route('/dashboard', methods=['POST'])
def get_dashboard():
    """Generate comprehensive dashboard with multi-resume support"""
    all_gap_analyses = session.get('all_gap_analyses', [])
    all_resumes_skills = session.get('all_resumes_skills', [])
    jd_skills = session.get('jd_skills', [])
    
    if not all_gap_analyses:
        return jsonify({'error': 'Please analyze gaps first'}), 400
    
    # Get primary analysis (first resume)
    primary_analysis = all_gap_analyses[0] if all_gap_analyses else {}
    
    # Get top skills from first resume
    top_skills = []
    if all_resumes_skills:
        top_skills = sorted(all_resumes_skills[0]['skills'], key=lambda x: x['confidence'], reverse=True)[:10]
    
    # Create leaderboard
    leaderboard = []
    for analysis in all_gap_analyses:
        leaderboard.append({
            "name": analysis['resume_name'],
            "match_percent": analysis['overall_match'],
            "risk_percent": analysis['risk_percent'],
            "matched_count": analysis['matched_count'],
            "missing_count": analysis['missing_count']
        })
    leaderboard = sorted(leaderboard, key=lambda x: x['match_percent'], reverse=True)
    
    return jsonify({
        'success': True,
        'dashboard': {
            'overall_match': primary_analysis.get('overall_match', 0),
            'risk_percent': primary_analysis.get('risk_percent', 0),
            'matched_count': primary_analysis.get('matched_count', 0),
            'partial_count': primary_analysis.get('partial_count', 0),
            'missing_count': primary_analysis.get('missing_count', 0),
            'semantic_similarity': primary_analysis.get('semantic_similarity', 0),
            'is_recommended': primary_analysis.get('is_recommended', False),
            'top_skills': top_skills,
            'recommendations': primary_analysis.get('recommendations', []),
            'ai_insights': primary_analysis.get('ai_insights', {}),
            'leaderboard': leaderboard,
            'total_jd_skills': len(jd_skills),
            'total_resumes': len(all_gap_analyses)
        }
    })

@app.route('/export', methods=['POST'])
def export_report():
    """Export report as PDF for all resumes"""
    all_gap_analyses = session.get('all_gap_analyses', [])
    
    if not FPDF_AVAILABLE:
        return jsonify({'error': 'PDF generation failed. Please install fpdf using: pip install fpdf'}), 500

    # HELPER: FPDF standard fonts only support latin-1. 
    # This prevents crashes from special characters (like bullets •, smart quotes ”, dashes —)
    def clean_text(text):
        if text is None:
            return ""
        return str(text).encode('latin-1', 'replace').decode('latin-1')

    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        
        # Colors and Fonts
        pdf.set_text_color(0, 0, 0)
        
        # Header
        pdf.set_font("Arial", 'B', 18)
        pdf.cell(0, 10, txt="AI Resume Analyzer - Multi-Resume Skill Gap Report", ln=True, align='C')
        pdf.set_font("Arial", size=10)
        pdf.cell(0, 8, txt=f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True, align='C')
        pdf.cell(0, 8, txt=f"Total Resumes Analyzed: {len(all_gap_analyses)}", ln=True, align='C')
        pdf.ln(10)
        
        # Leaderboard Section
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, txt="=== RESUME LEADERBOARD ===", ln=True)
        pdf.set_font("Arial", 'B', 10)
        
        # Table Header
        pdf.cell(15, 10, "Rank", border=1, align='C')
        pdf.cell(60, 10, "Resume Name", border=1, align='C')
        pdf.cell(25, 10, "Match %", border=1, align='C')
        pdf.cell(25, 10, "Risk %", border=1, align='C')
        pdf.cell(20, 10, "Matched", border=1, align='C')
        pdf.cell(20, 10, "Missing", border=1, align='C')
        pdf.cell(25, 10, "Verdict", border=1, ln=True, align='C')
        
        pdf.set_font("Arial", size=10)
        sorted_analyses = sorted(all_gap_analyses, key=lambda x: x['overall_match'], reverse=True)
        
        for idx, analysis in enumerate(sorted_analyses, 1):
            pdf.cell(15, 10, str(idx), border=1, align='C')
            # Truncate filename if it's too long
            name = analysis['resume_name'][:25] + '...' if len(analysis['resume_name']) > 25 else analysis['resume_name']
            pdf.cell(60, 10, clean_text(name), border=1)
            pdf.cell(25, 10, f"{analysis['overall_match']}%", border=1, align='C')
            pdf.cell(25, 10, f"{analysis['risk_percent']}%", border=1, align='C')
            pdf.cell(20, 10, str(analysis['matched_count']), border=1, align='C')
            pdf.cell(20, 10, str(analysis['missing_count']), border=1, align='C')
            verdict = 'Yes' if analysis['is_recommended'] else 'No'
            pdf.cell(25, 10, verdict, border=1, ln=True, align='C')
            
        pdf.ln(15)
        
        # Detailed Analysis Section
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, txt="=== DETAILED ANALYSIS PER RESUME ===", ln=True)
        pdf.ln(5)
        
        for analysis in all_gap_analyses:
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 10, txt=clean_text(f"Resume: {analysis['resume_name']}"), ln=True)
            
            pdf.set_font("Arial", size=11)
            pdf.cell(0, 8, txt=f"Match %: {analysis['overall_match']}%    |    Risk %: {analysis['risk_percent']}%", ln=True)
            pdf.cell(0, 8, txt=f"Matched Skills: {analysis['matched_count']}    |    Missing Skills: {analysis['missing_count']}", ln=True)
            
            decision = 'RECOMMENDED' if analysis['is_recommended'] else 'NOT RECOMMENDED'
            pdf.cell(0, 8, txt=f"Decision: {decision}", ln=True)
            pdf.ln(3)
            
            # Missing Skills
            pdf.set_font("Arial", 'B', 11)
            pdf.cell(0, 8, txt="Missing Skills Details:", ln=True)
            pdf.set_font("Arial", size=10)
            missing_skills = analysis.get('missing', [])
            if missing_skills:
                for skill in missing_skills:
                    pdf.cell(10) # indent
                    pdf.cell(0, 6, txt=clean_text(f"- {skill['name']} ({skill['type']})"), ln=True)
            else:
                pdf.cell(10)
                pdf.cell(0, 6, txt="- None", ln=True)
                
            pdf.ln(3)
            
            # Recommendations
            pdf.set_font("Arial", 'B', 11)
            pdf.cell(0, 8, txt="Recommendations:", ln=True)
            pdf.set_font("Arial", size=10)
            recs = analysis.get('recommendations', [])
            if recs:
                for rec in recs[:5]:
                    pdf.cell(10) # indent
                    pdf.multi_cell(0, 6, txt=clean_text(f"- {rec['skill']}: {rec['recommendation']}"))
            else:
                pdf.cell(10)
                pdf.cell(0, 6, txt="- None required", ln=True)
                
            pdf.ln(5)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y()) # Separator line
            pdf.ln(5)
            
        # Save to memory and return
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], f"temp_report_{datetime.now().strftime('%H%M%S')}.pdf")
        pdf.output(temp_path)
        
        with open(temp_path, 'rb') as f:
            pdf_data = f.read()
        
        # Cleanup temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)
            
        return send_file(
            io.BytesIO(pdf_data),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'multi_resume_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
        )
    except Exception as e:
        print(f"Error generating PDF: {str(e)}")
        return jsonify({'error': 'Failed to generate PDF due to a server error.'}), 500

@app.route('/reset', methods=['POST'])
def reset_session():
    session.clear()
    return jsonify({'success': True})

if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("AI RESUME ANALYZER - BACKEND SERVER")
    print("=" * 60)
    print("\nServer running at: http://localhost:5000")
    print("\nMake sure 'templates' folder exists with index.html")
    print("\n" + "=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5000)
