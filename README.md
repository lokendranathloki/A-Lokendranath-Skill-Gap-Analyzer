# 🚀 Skill Gap Analyzer

An AI-powered system that analyzes resumes and identifies skill gaps by comparing candidate profiles with job requirements. This project automates the hiring process by reducing manual effort and improving accuracy using NLP and semantic analysis.

---

## 📌 Project Overview

In today’s hiring process, recruiters deal with a large number of resumes. Manual screening is time-consuming and inefficient.

**Skill Gap Analyzer** helps by:
- Automatically extracting skills from resumes
- Comparing them with job requirements
- Identifying missing skills
- Generating insightful reports

---

## ⚠️ Problem Statement

- Handling large volumes of resumes is difficult  
- Manual screening consumes time  
- Hard to identify relevant skills quickly  
- No intelligent comparison system  

---

## 💡 Solution

This system uses **Natural Language Processing (NLP)** and AI to:
- Parse resumes  
- Extract technical & soft skills  
- Compare with job descriptions  
- Identify skill gaps  
- Visualize results  

---

## 🧩 Modules

### 1️⃣ Data Ingestion & Parsing
- Supports PDF, DOCX, TXT files  
- Extracts raw text  
- Removes noise (symbols, formatting)  
- Converts into structured text  

### 2️⃣ Skill Extraction (NLP)
- Uses keyword-based NLP techniques  
- Identifies:
  - Technical Skills (Python, ML, etc.)  
  - Soft Skills (Communication, Leadership)  
- Uses predefined skill database  

### 3️⃣ Skill Gap Analysis
- Compares Resume Skills with Job Description  
- Identifies:
  - Matching Skills  
  - Missing Skills  
- Calculates skill gap  

### 4️⃣ Visualization & Report Generation
- Displays charts and graphs  
- Shows skill match percentage  
- Generates downloadable reports (PDF / CSV)  

---

## 🤖 AI Concept Used

### BERT (Bidirectional Encoder Representations from Transformers)
- Uses Sentence-BERT embeddings  
- Measures semantic similarity  
- Understands context, not just keywords  
- Improves matching accuracy  

---

## ✨ Features

- 📄 Automated Resume Screening  
- ⚡ Faster Hiring Process  
- 🎯 Accurate Skill Matching  
- 📊 Visual Reports  
- 🖥️ User-Friendly Interface  

---

## 🛠️ Tech Stack

- Frontend: HTML, CSS  
- Backend: Python  
- Libraries: NLP, Sentence-BERT  
- File Handling: PyPDF, python-docx  
- Visualization: Matplotlib  

---

## 📂 Project Structure

Skill-Gap-Analyzer/  
│── app.py  
│── parser.py  
│── requirements.txt  
│── templates/  
│── static/  
│── uploads/  
│── README.md  

---

## ▶️ How to Run

1. Clone the repository  
git clone https://github.com/your-username/skill-gap-analyzer.git  

2. Navigate to the project folder  
cd skill-gap-analyzer  

3. Install dependencies  
pip install -r requirements.txt  

4. Run the application  
python app.py  

5. Open in browser  
http://127.0.0.1:5000/  

---

## 📊 Future Enhancements

- Integration with job portals  
- Advanced AI-based matching  
- Real-time resume feedback  
- Analytics dashboard  
- Multi-language support  

---

## 👨‍💻 Team

**Team C**  
- Lokendranath  
- Prathiksha 
- Divya  
- Ranganayaki  

Trainer: Sandhiya Kumari  

---

## 📜 License

This project is for educational purposes.

---

## 🙌 Acknowledgement

Thanks to our trainer and mentors for their guidance and support.
