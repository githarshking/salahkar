import os
import io
import re
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from dotenv import load_dotenv
import google.generativeai as genai
import traceback

# Import ReportLab components
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
# --- !! NEW FONT MAPPING IMPORT !! ---
from reportlab.lib.fonts import addMapping

# --- Setup ---
load_dotenv()
app = Flask(__name__)
CORS(app) 

# --- Register Hindi Font ---
# **IMPORTANT**: These files MUST be in the same directory as app.py
try:
    pdfmetrics.registerFont(TTFont('NotoSansDevanagari', 'NotoSansDevanagari-Regular.ttf'))
    pdfmetrics.registerFont(TTFont('NotoSansDevanagari-Bold', 'NotoSansDevanagari-Bold.ttf'))
    # Use Bold as a fallback for italic
    pdfmetrics.registerFont(TTFont('NotoSansDevanagari-Italic', 'NotoSansDevanagari-Bold.ttf'))
    
    # --- !! NEW FONT MAPPING !! ---
    # This tells ReportLab how the font family pieces fit together
    addMapping('NotoSansDevanagari', 0, 0, 'NotoSansDevanagari') # Normal
    addMapping('NotoSansDevanagari', 1, 0, 'NotoSansDevanagari-Bold') # Bold
    addMapping('NotoSansDevanagari', 0, 1, 'NotoSansDevanagari-Italic') # Italic
    addMapping('NotoSansDevanagari', 1, 1, 'NotoSansDevanagari-Bold') # Bold-Italic (fallback)

    print("Successfully registered and mapped Hindi fonts.")
except Exception as e:
    print(f"--- WARNING ---")
    print(f"Could not register Hindi fonts. Hindi PDF will NOT render correctly.")
    print(f"Error: {e}")
    print("Please download 'NotoSansDevanagari-Regular.ttf' and 'NotoSansDevanagari-Bold.ttf' and place them in the same folder as app.py")
    print(f"---------------")
# ---

# --- System Prompt Definitions ---
SYSTEM_PROMPT_TEXT_ENGLISH = (
    "You are an expert real estate developer, financial analyst, and business advisor. Your job is to provide a detailed, actionable report on the best use for a plot of land. "
    "Analyze the user's data provided and provide comprehensive recommendations based on your expertise in real estate development, market analysis, and business planning. "
    "Focus on the user's specific location, budget, and local needs as the primary factors for your recommendations. "
    "Your report must be professional, easy to understand, and provide 3 concrete recommendations in well-structured Markdown. "
    "Format your output clearly with Headings (#, ##), bullet points (*), and tables for comparisons."
)

SYSTEM_PROMPT_TEXT_HINDI = (
    "आप एक विशेषज्ञ रियल एस्टेट डेवलपर, वित्तीय विश्लेषक और व्यापार सलाहकार हैं। आपका काम भूमि के सर्वोत्तम उपयोग पर एक विस्तृत, कार्य योग्य रिपोर्ट प्रदान करना है। "
    "उपयोगकर्ता के दिए गए डेटा का विश्लेषण करें और रियल एस्टेट डेवलपमेंट, बाजार विश्लेषण और व्यापार योजना में अपने विशेषज्ञता के आधार पर व्यापक सिफारिशें प्रदान करें। "
    "उपयोगकर्ता के विशिष्ट स्थान, बजट और स्थानीय आवश्यकताओं को अपनी सिफारिशों के प्राथमिक कारकों के रूप में केंद्रित करें। "
    "आपकी रिपोर्ट पेशेवर, समझने में आसान होनी चाहिए और अच्छी तरह से संरचित मार्कडाउन में 3 ठोस सिफारिशें प्रदान करनी चाहिए। "
    "अपने आउटपुट को हेडिंग्स (#, ##), बुलेट पॉइंट्स (*), और तुलना के लिए तालिकाओं के साथ स्पष्ट रूप से प्रारूपित करें।"
)

# Configure the generative AI model
try:
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    model_english = genai.GenerativeModel(
        'gemini-2.5-flash-preview-09-2025',
        system_instruction=SYSTEM_PROMPT_TEXT_ENGLISH
    )
    model_hindi = genai.GenerativeModel(
        'gemini-2.5-flash-preview-09-2025',
        system_instruction=SYSTEM_PROMPT_TEXT_HINDI
    )
except KeyError:
    print("Error: GEMINI_API_KEY not found. Please set it in your .env file.")
    exit()

# --- Helper Function for PDF Generation ---

def create_report_pdf(markdown_text, name, location, language='english'):
    """
    Creates a professional PDF report from markdown text using ReportLab.
    Supports English and Hindi.
    Includes robust error handling to always return a valid PDF.
    """
    buffer = io.BytesIO()
    try:
        if not markdown_text or not markdown_text.strip():
            print("ERROR: Empty or None markdown text provided")
            raise ValueError("No markdown content provided for PDF generation")
        
        doc = SimpleDocTemplate(buffer, pagesize=A4,
                                rightMargin=inch*0.5, leftMargin=inch*0.5,
                                topMargin=inch*0.75, bottomMargin=inch*0.75)
        
        styles = getSampleStyleSheet()
        
        # --- !! FONT FIX !! ---
        # Set the base font name for all styles
        if language == 'hindi':
            try:
                pdfmetrics.getFont('NotoSansDevanagari')
                base_font_name = 'NotoSansDevanagari'
            except KeyError:
                print("ERROR: Hindi font 'NotoSansDevanagari' was requested but not found. Falling back to Helvetica.")
                base_font_name = 'Helvetica' # Fallback
        else:
            base_font_name = 'Helvetica'
        # ---
        
        # Create custom styles using the base font name
        # ReportLab will now use the MAPPING to find bold/italic versions
        custom_styles = {
            'CustomH1': ParagraphStyle(name='CustomH1', fontSize=18, spaceAfter=12, fontName=base_font_name, textColor=colors.HexColor("#2C3E50")),
            'CustomH2': ParagraphStyle(name='CustomH2', fontSize=14, spaceAfter=10, fontName=base_font_name, textColor=colors.HexColor("#16a085")),
            'CustomH3': ParagraphStyle(name='CustomH3', fontSize=12, spaceAfter=8, fontName=base_font_name, textColor=colors.HexColor("#34495e")),
            'CustomBody': ParagraphStyle(name='CustomBody', fontSize=10, spaceAfter=6, fontName=base_font_name, leading=14),
            'CustomBullet': ParagraphStyle(name='CustomBullet', fontSize=10, spaceAfter=4, fontName=base_font_name, leading=14, leftIndent=20, bulletIndent=10),
            'CustomNumber': ParagraphStyle(name='CustomNumber', fontSize=10, spaceAfter=4, fontName=base_font_name, leading=14, leftIndent=20, bulletIndent=10),
            'CustomDisclaimer': ParagraphStyle(name='CustomDisclaimer', fontSize=9, fontName=base_font_name, textColor=colors.grey, spaceBefore=12, borderPadding=10, borderColor=colors.lightgrey, borderWidth=1)
        }
        
        for style_name, style_obj in custom_styles.items():
            styles.add(style_obj)
        
        flowables = []
        
        # --- PDF Header ---
        # We manually add <b> tags for headings
        if language == 'hindi':
            flowables.append(Paragraph("<b>पेशेवर भूमि उपयोग रिपोर्ट</b>", styles['CustomH1']))
            flowables.append(Paragraph(f"<b>तैयार की गई: {name}</b>", styles['CustomH3']))
            flowables.append(Paragraph(f"<b>स्थान: {location}</b>", styles['CustomH3']))
        else:
            flowables.append(Paragraph("<b>Professional Land Use Report</b>", styles['CustomH1']))
            flowables.append(Paragraph(f"<b>Prepared for: {name}</b>", styles['CustomH3']))
            flowables.append(Paragraph(f"<b>Location: {location}</b>", styles['CustomH3']))
        flowables.append(Spacer(1, 0.25 * inch))

        # --- Parse Markdown ---
        lines = markdown_text.split('\n')
        current_table_data = []
        in_table = False
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            if not line:
                continue

            # Handle Tables
            if line.startswith('|') and line.endswith('|'):
                if not in_table:
                    in_table = True
                    current_table_data = []
                
                cells = [cell.strip() for cell in line.split('|')[1:-1]]
                
                if not all(c.strip().replace('-', '').replace(':', '').replace(' ', '') == '' for c in cells):
                    cell_paragraphs = []
                    cell_style = ParagraphStyle(name='TableBody', fontName=base_font_name, fontSize=9, leading=11)
                    for cell in cells:
                        # --- !! MARKDOWN PARSING FIX !! ---
                        cell_text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', cell)
                        cell_text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', cell_text)
                        cell_paragraphs.append(Paragraph(cell_text, cell_style))
                    current_table_data.append(cell_paragraphs)
            
            # End of table
            elif in_table and not (line.startswith('|') and line.endswith('|')):
                in_table = False
                if current_table_data and len(current_table_data) > 0:
                    try:
                        num_cols = len(current_table_data[0])
                        col_widths = [doc.width * 0.35, doc.width * 0.65] if num_cols == 2 else [doc.width / num_cols] * num_cols
                        
                        header_data = current_table_data[0]
                        header_style = ParagraphStyle(name='TableHeader', fontName=base_font_name, fontSize=10, textColor=colors.HexColor("#2c3e50"))
                        # Manually make header bold
                        styled_header = [Paragraph(f"<b>{cell.text}</b>", header_style) for cell in header_data]
                        
                        table_data = [styled_header] + current_table_data[1:]
                        table = Table(table_data, colWidths=col_widths)
                        
                        table.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#ecf0f1")),
                            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor("#bdc3c7")),
                            ('BOX', (0, 0), (-1, -1), 1, colors.black),
                            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                            ('PADDING', (0, 0), (-1, -1), 6),
                        ]))
                        flowables.append(table)
                        flowables.append(Spacer(1, 0.1 * inch))
                    except Exception as table_error:
                        print(f"Error creating table: {table_error}")
                        for row in current_table_data:
                            row_text = " | ".join([cell.text for cell in row])
                            flowables.append(Paragraph(row_text, styles['CustomBody']))
                    current_table_data = []
            
            # Handle Headings
            elif line.startswith('# '):
                flowables.append(Paragraph(f"<b>{line[2:].strip()}</b>", styles['CustomH1']))
            elif line.startswith('## '):
                flowables.append(Paragraph(f"<b>{line[3:].strip()}</b>", styles['CustomH2']))
            elif line.startswith('### '):
                flowables.append(Paragraph(f"<b>{line[4:].strip()}</b>", styles['CustomH3']))
            
            # Handle Lists
            elif line.startswith('* ') or line.startswith('- '):
                # --- !! MARKDOWN PARSING FIX !! ---
                text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', line[2:].strip())
                text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
                flowables.append(Paragraph(text, styles['CustomBullet'], bulletText='•'))
            elif re.match(r'^\d+\. ', line):
                # --- !! MARKDOWN PARSING FIX !! ---
                text = re.sub(r'^\d+\. ', '', line).strip()
                text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
                text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
                number = line.split('.')[0]
                flowables.append(Paragraph(text, styles['CustomNumber'], bulletText=f"{number}."))

            # Handle Disclaimer
            elif line.startswith('Disclaimer:') or line.startswith('अस्वीकरण:'):
                flowables.append(Paragraph(f"<i>{line}</i>", styles['CustomDisclaimer']))
                
            # Handle Body Text
            else:
                # --- !! MARKDOWN PARSING FIX !! ---
                processed_line = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', line)
                processed_line = re.sub(r'\*(.*?)\*', r'<i>\1</i>', processed_line)
                if processed_line.strip():
                    flowables.append(Paragraph(processed_line, styles['CustomBody']))

        # Add a final disclaimer if not present
        if not any('Disclaimer' in str(flowable) or 'अस्वीकरण' in str(flowable) for flowable in flowables):
            flowables.append(Spacer(1, 0.2 * inch))
            disclaimer_text = "<i>अस्वीकरण: यह रिपोर्ट केवल सूचनात्मक उद्देश्यों के लिए है। किसी भी निवेश निर्णय लेने से पहले कृपया स्थानीय जोनिंग अधिकारियों, वित्तीय सलाहकारों और कानूनी पेशेवरों से परामर्श करें।</i>" if language == 'hindi' else "<i>Disclaimer: This report is for informational purposes only. Please consult with local zoning authorities, financial advisors, and legal professionals before making any investment decisions.</i>"
            flowables.append(Paragraph(disclaimer_text, styles['CustomDisclaimer']))
        
        print("Building PDF document...")
        doc.build(flowables)
        
    except Exception as e:
        print(f"ERROR in create_report_pdf: {e}")
        traceback.print_exc()
        
        # --- !! ROBUST ERROR PDF FALLBACK !! ---
        try:
            buffer.close() 
            buffer = io.BytesIO() 
            
            doc = SimpleDocTemplate(buffer, pagesize=A4)
            styles = getSampleStyleSheet()
            
            error_style = ParagraphStyle(name='ErrorNormal', fontName='Helvetica', fontSize=10, spaceAfter=10)
            error_title_style = ParagraphStyle(name='ErrorTitle', fontName='Helvetica-Bold', fontSize=14, spaceAfter=12, textColor=colors.red)
            error_code_style = ParagraphStyle(name='ErrorCode', fontName='Courier', fontSize=9, textColor=colors.darkgrey, spaceAfter=10, leftIndent=10)

            error_flowables = [
                Paragraph("PDF Generation Failed", error_title_style),
                Paragraph("An error occurred while trying to create your PDF report. This usually means the font files are missing or the markdown from the AI was malformed.", error_style),
                Paragraph(f"Error Details:", styles['Heading2']),
                Paragraph(f"{str(e)}", error_style),
                Paragraph(f"Debug Info:", styles['Heading2']),
                Paragraph(f"Name: {name}, Location: {location}, Language: {language}", error_style),
                Paragraph(f"Full Traceback:", styles['Heading3']),
                Paragraph(traceback.format_exc().replace('\n', '<br/>\n'), error_code_style)
            ]
            
            doc.build(error_flowables)
            print("Successfully built a fallback error PDF.")
            
        except Exception as fallback_error:
            print(f"CRITICAL: Fallback error PDF creation failed: {fallback_error}")
            buffer.close()
            buffer = io.BytesIO()
            buffer.write(b"CRITICAL ERROR: Could not generate any PDF.")
            
    # --- End of function ---
    buffer.seek(0)
    return buffer

# --- API Endpoints ---

@app.route('/api/generate', methods=['POST'])
def generate_report():
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No JSON data received"}), 400

        language = data.get('language', 'english')
        model = model_hindi if language == 'hindi' else model_english
        
        # Construct the prompt (using f-string and pulling data)
        if language == 'hindi':
            user_prompt = f"""
            यह मेरी भूमि का डेटा है। कृपया एक पूरी रिपोर्ट तैयार करें।

            **भाग 1: भूमि विवरण**
            * **नाम:** {data.get('name')}
            * **स्थान:** {data.get('location')}
            * **निर्देशांक:** {data.get('latlong', 'प्रदान नहीं किया गया')}
            * **क्षेत्र प्रकार:** {data.get('areaType')}
            * **भूमि का आकार:** {data.get('landSize')}
            * **भूमि का आकृति:** {data.get('landShape')}
            * **पहुंच:** {data.get('accessibility')}
            * **दृश्यता:** {data.get('visibility')}
            * **वर्तमान स्थिति:** {data.get('landStatus')}
            * **ज्ञात जोनिंग (उपयोगकर्ता इनपुट):** {data.get('zoning', 'उपयोगकर्ता को पता नहीं')}

            **भाग 2: बाजार संदर्भ (उपयोगकर्ता की धारणा - इसे प्राथमिकता दें)**
            * **आसन्न संपत्तियां:** {data.get('neighborhood', 'निर्दिष्ट नहीं')}
            * **स्थानीय जनसांख्यिकी:** {data.get('demographics', 'निर्दिष्ट नहीं')}
            * **पहचानी गई स्थानीय आवश्यकताएं/अंतराल:** {data.get('localNeeds', 'निर्दिष्ट नहीं')}
            * **सफल निकटवर्ती व्यवसाय (प्रतिस्पर्धा):** {data.get('competition', 'निर्दिष्ट नहीं')}

            **भाग 3: उपयोगकर्ता के लक्ष्य और संसाधन**
            * **निवेश बजट:** {data.get('budget')}
            * **न्यूनतम मासिक आय लक्ष्य:** {data.get('incomeGoal')}
            * **समय की भागीदारी:** {data.get('time')}
            * **व्यक्तिगत कौशल/रुचियां:** {data.get('skills', 'निर्दिष्ट नहीं')}

            **निर्देश:**
            1.  रिपोर्ट को हेडर के साथ शुरू करें: "# पेशेवर भूमि उपयोग और वित्तीय व्यवहार्यता रिपोर्ट"
            2.  "## 1. कार्यकारी सारांश" बनाएं जिसमें सबसे अच्छी सिफारिश हो।
            3.  "## 2. शीर्ष 3 सिफारिशें" बनाएं जिसमें प्रत्येक के लिए विस्तृत विवरण हो।
            4.  प्रत्येक सिफारिश के लिए, एक मार्कडाउन तालिका शामिल करें:
                | विवरण | विस्तार |
                |---|---|
                | **व्यापार मॉडल** | (यह विचार क्यों) |
                | **अनुमानित निवेश** | (उपयोगकर्ता के बजट से संबंधित) |
                | **संभावित लाभ/आरओआई** | (उपयोगकर्ता के आय लक्ष्य से संबंधित) |
                | **पेशेवर** | (2-3 पेशेवरों की सूची) |
                | **विपक्ष** | (2-3 विपक्ष/जोखिमों की सूची) |
                | **पहले कदम** | (कार्य योग्य पहले कदम) |
            5.  "## 3. सामान्य अस्वीकरण" के साथ समाप्त करें जो बताता है कि यह सूचनात्मक है और उन्हें स्थानीय जोनिंग वकीलों और वित्तीय सलाहकारों से परामर्श करना चाहिए।
            """
        else:
            user_prompt = f"""
            Here is the data for my land. Please generate a full report.

            **Part 1: Land Details**
            * **Name:** {data.get('name')}
            * **Location:** {data.get('location')}
            * **Coordinates:** {data.get('latlong', 'Not Provided')}
            * **Area Type:** {data.get('areaType')}
            * **Land Size:** {data.get('landSize')}
            * **Land Shape:** {data.get('landShape')}
            * **Accessibility:** {data.get('accessibility')}
            * **Visibility:** {data.get('visibility')}
            * **Current Status:** {data.get('landStatus')}
            * **Known Zoning (User Input):** {data.get('zoning', 'User has no idea')}

            **Part 2: Market Context (User's Perception - PRIORITIZE THIS)**
            * **Adjacent Properties:** {data.get('neighborhood', 'Not specified')}
            * **Local Demographics:** {data.get('demographics', 'Not specified')}
            * **Identified Local Needs/Gaps:** {data.get('localNeeds', 'Not specified')}
            * **Successful Nearby Businesses (Competition):** {data.get('competition', 'Not specified')}

            **Part 3: User's Goals & Resources**
            * **Investment Budget:** {data.get('budget')}
            * **Minimum Monthly Income Goal:** {data.get('incomeGoal')}
            * **Time Involvement:** {data.get('time')}
            * **Personal Skills/Interests:** {data.get('skills', 'Not specified')}

            **Instructions:**
            1.  Start the report with a header: "# Professional Land Use & Financial Feasibility Report"
            2.  Create an "## 1. Executive Summary" with the single best recommendation.
            3.  Create "## 2. Top 3 Recommendations" with a detailed breakdown for each.
            4.  For each recommendation, include a Markdown table:
                | Detail | Breakdown |
                |---|---|
                | **Business Model** | (Why this idea) |
                | **Estimated Investment** | (Relate to user's budget) |
                | **Potential Profit/ROI** | (Relate to user's income goal) |
                | **Pros** | (List 2-3 pros) |
                | **Cons** | (List 2-3 cons/risks) |
                | **First Steps** | (Actionable first steps) |
            5.  End with "## 3. General Disclaimer" stating this is informational and they must consult local zoning lawyers and financial advisors.
            """

        response = model.generate_content(user_prompt)
        
        if response.candidates:
            report_text = response.candidates[0].content.parts[0].text
            return jsonify({"reportText": report_text})
        else:
            error_message = "AI model did not generate a response."
            if response.prompt_feedback:
                error_message += f" Reason: {response.prompt_feedback}"
            print(f"ERROR: {error_message}")
            return jsonify({"error": error_message}), 500

    except Exception as e:
        print(f"Error in /api/generate: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/download_pdf', methods=['POST'])
def download_pdf():
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No JSON data received"}), 400
            
        markdown_text = data.get('markdown_text')
        name = data.get('name', 'User')
        location = data.get('location', 'Not Specified')
        language = data.get('language', 'english')

        if not markdown_text or not isinstance(markdown_text, str):
            print(f"ERROR: Invalid or missing markdown text. Type: {type(markdown_text)}")
            return jsonify({"error": "Invalid or missing markdown_text"}), 400

        print(f"Calling create_report_pdf for {name} ({language})...")
        pdf_buffer = create_report_pdf(markdown_text, name, location, language)
        
        if not pdf_buffer:
            print("ERROR: PDF buffer is None after creation")
            return jsonify({"error": "Failed to generate PDF buffer"}), 500
            
        pdf_content = pdf_buffer.getvalue()
        if len(pdf_content) < 200: 
            print(f"WARNING: PDF size is suspiciously small: {len(pdf_content)} bytes. It might be an error PDF.")
        else:
            print(f"PDF generated successfully, size: {len(pdf_content)} bytes")
        
        filename = 'भूमि_रिपोर्ट.pdf' if language == 'hindi' else 'AI_Land_Report.pdf'
        
        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )

    except Exception as e:
        print(f"CRITICAL Error in /api/download_pdf: {e}")
        traceback.print_exc()
        return jsonify({"error": f"Failed to generate PDF: {str(e)}"}), 500

# --- Run the App ---
if __name__ == '__main__':
    app.run(debug=True)

