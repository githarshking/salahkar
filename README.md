# **Project: The भूमि सलाहकार (The Land Consultant)**

**The भूमि सलाहकार** is a full-stack, AI-powered web application designed to act as an expert real estate and financial consultant. It empowers landowners by providing detailed, actionable, and personalized reports on the most profitable and feasible uses for their land.

# **The application is fully bilingual (English and Hindi) to ensure accessibility for a wide range of users.**

## **Core Problem**

Many landowners possess valuable plots of land but lack the specialized knowledge to determine its best use. Hiring expensive consultants is often not feasible. This application provides instant, data-driven, and expert-level advice to answer questions like:

* "Should I build apartments, shops, or a warehouse?"
* "What business is missing in my local area?"
* "How much will it cost, and what is the potential profit?"

## **Key Features**

* **AI-Powered Analysis:** Leverages the Google Generative AI (Gemini) API to provide sophisticated, non-generic analysis.
* **Hyper-Personalized Reports:** The AI's recommendations are based *specifically* on the user's unique plot, budget, and local needs.
* **Bilingual Interface \& Output:** The entire user experience is available in both **English** and **हिंदी (Hindi)**.
* **On-Screen Report Generation:** The AI's Markdown-formatted report is instantly converted to styled HTML and displayed on the page.
* **Professional PDF Downloads:** Users can download their report as a beautifully styled, multi-page PDF document, with full support for Hindi (Devanagari) fonts.

## **Technology Stack**

* **Frontend:** HTML5, Tailwind CSS, Vanilla JavaScript (ES6+)
* **Backend:** Python, Flask, Flask-CORS
* **AI \& Data:** Google Generative AI (Gemini), ReportLab

## **Project Setup \& Installation**

Follow these steps to get the project running on your local machine.

### **1. Prerequisites**

* [Python 3.10+](https://www.python.org/downloads/)
* A [Google Gemini API Key](https://ai.google.dev/gemini-api/docs/api-key)

### **2. Clone the Repository**

git clone \[https://github.com/your-username/your-repo-name.git](https://github.com/your-username/your-repo-name.git)  
cd your-repo-name

### **3. Set Up the Backend (Python)**

**A. Create a Virtual Environment:**

### For Windows 
```http
  python -m venv venv  
```
```http
  .\\venv\\Scripts\\activate
```

### For macOS/Linux  
```http
  python3 -m venv venv  
```
```http
  source venv/bin/activate
```
B. Install Required Packages:  
 A requirements.txt file is included in this repository.  
```http
  pip install -r requirements.txt
```
C. Set Up Environment Variables:  
 Create a file named .env in the root of your project folder. 
```http
  GEMINI\_API\_KEY=your\_api\_key\_goes\_here
```
D. Downloaded Hindi Fonts:  
The PDF generation for Hindi requires two font files.

1. From [Noto Sans Devanagari on Google Fonts](https://fonts.google.com/specimen/Noto+Sans+Devanagari).
2. the "Regular 400" and "Bold 700" styles.

   * NotoSansDevanagari-Regular.ttf
   * NotoSansDevanagari-Bold.ttf

Your project folder should now look like this:

/  
├── app.py  
├── frontend.html  
├── requirements.txt  
├── .env  
├── NotoSansDevanagari-Regular.ttf  
└── NotoSansDevanagari-Bold.ttf

## **How to Run the Application**

### **1. Start the Backend Server**

 With your virtual environment active, run the Flask application:
```http
  python app.py
```
Your server will start, typically on http://127.0.0.1:5000.

### **2. Open the Frontend**

Simply **open the frontend.html file in your web browser.** You can do this by double-clicking the file.

The application is now ready to use! You can fill out the form, generate reports, and download PDFs.



