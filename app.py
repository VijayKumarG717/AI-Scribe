from dotenv import load_dotenv
load_dotenv()
import os
import time
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.utils import secure_filename
import requests
import google.generativeai as genai
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(env_path)

# Also try to load from api key.txt if .env doesn't have the keys
assembly_key_found = os.getenv("ASSEMBLYAI_API_KEY") or os.getenv("ASSEMBLY_API_KEY")
if not assembly_key_found:
    # Try to load from api key.txt file
    possible_files = ['api key.txt', 'api_key.txt', 'apikey.txt', 'api-keys.txt']
    for api_file in possible_files:
        api_key_file = os.path.join(os.path.dirname(__file__), api_file)
        if os.path.exists(api_key_file):
            try:
                with open(api_key_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and ('ASSEMBLY' in line.upper() or 'ASSEMBLYAI' in line.upper()):
                            if '=' in line:
                                parts = line.split('=', 1)
                                key_name = parts[0].strip()
                                key_value = parts[1].strip().strip('"\'')  # Remove quotes if present
                                os.environ[key_name] = key_value
                                # Also set the standard variable name
                                if 'ASSEMBLY' in key_name.upper():
                                    os.environ["ASSEMBLYAI_API_KEY"] = key_value
                                break
            except Exception as e:
                print(f"Error reading {api_file}: {e}")
                continue
            if os.getenv("ASSEMBLYAI_API_KEY") or os.getenv("ASSEMBLY_API_KEY"):
                break

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'

# Ensure uploads directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Configure AssemblyAI - check multiple variable names
assembly_api_key = os.getenv("ASSEMBLYAI_API_KEY") or os.getenv("ASSEMBLY_API_KEY")

# If still not found, use default from your provided key
if not assembly_api_key:
    assembly_api_key = "29c2b594dcaf4c18ba93348005a9bc22"
    print("Warning: Using default AssemblyAI API key. Please set ASSEMBLYAI_API_KEY in .env file.")

# AssemblyAI API configuration
ASSEMBLYAI_BASE_URL = "https://api.assemblyai.com"
ASSEMBLYAI_HEADERS = {
    "authorization": assembly_api_key
}

# Configure Gemini
gemini_api_key = os.getenv("GEMINI_API_KEY")
if not gemini_api_key or gemini_api_key.strip() == "":
    raise RuntimeError(
        "GEMINI_API_KEY is not set.\n"
        "Please create your own Gemini API key in Google AI Studio and add it to the .env file as:\n"
        "GEMINI_API_KEY=your_api_key_here"
    )
else:
    gemini_api_key = gemini_api_key.strip()  # Remove any whitespace

# Validate API key format
if gemini_api_key and not gemini_api_key.startswith("AIza"):
    print(f"Warning: Gemini API key format looks incorrect. Should start with 'AIza'. Current: {gemini_api_key[:10]}...")

genai.configure(api_key=gemini_api_key)

# Try to initialize the model (skip test on startup to avoid crashes)
# The API key will be validated when it's actually used
# Using Gemini 2.5 Flash model
try:
    gemini_model = genai.GenerativeModel("gemini-2.5-flash")
except Exception as e:
    # If model name doesn't work, try alternative model names
    error_msg = str(e)
    if "not found" in error_msg.lower():
        try:
            gemini_model = genai.GenerativeModel("gemini-2.0-flash-exp")
        except:
            try:
                gemini_model = genai.GenerativeModel("gemini-2.0-flash")
            except:
                # Fallback to 1.5 flash if 2.5/2.0 is not available
                gemini_model = genai.GenerativeModel("gemini-1.5-flash")
    else:
        # If API key is invalid, model will fail when used, which is handled in format_with_gemini
        gemini_model = genai.GenerativeModel("gemini-2.5-flash")


def generate_with_timeout(prompt, generation_config, timeout_seconds=120):
    """Run Gemini generation with a manual timeout using a separate thread."""
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(
            gemini_model.generate_content,
            prompt,
            generation_config=generation_config
        )
        return future.result(timeout=timeout_seconds)

# Allowed file extensions
ALLOWED_AUDIO_EXTENSIONS = {'mp3', 'wav', 'm4a'}
ALLOWED_TEXT_EXTENSIONS = {'txt', 'docx'}


def allowed_file(filename, extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in extensions


def transcribe_audio(audio_path):
    """Transcribe audio using AssemblyAI REST API"""
    try:
        # Step 1: Upload the audio file to AssemblyAI
        upload_url = f"{ASSEMBLYAI_BASE_URL}/v2/upload"
        
        with open(audio_path, 'rb') as audio_file:
            upload_response = requests.post(
                upload_url,
                headers=ASSEMBLYAI_HEADERS,
                files={'file': audio_file}
            )
        
        if upload_response.status_code != 200:
            raise Exception(f"Upload failed: {upload_response.json()}")
        
        audio_url = upload_response.json()['upload_url']
        
        # Step 2: Submit transcription request
        transcript_url = f"{ASSEMBLYAI_BASE_URL}/v2/transcript"
        
        config = {
            "audio_url": audio_url,
            "speaker_labels": True,
            "format_text": True,
            "punctuate": True,
            "speech_model": "universal",
            "language_detection": True
        }
        
        response = requests.post(
            transcript_url,
            json=config,
            headers=ASSEMBLYAI_HEADERS
        )
        
        if response.status_code != 200:
            raise Exception(f"Transcription request failed: {response.json()}")
        
        transcript_id = response.json()['id']
        polling_endpoint = f"{ASSEMBLYAI_BASE_URL}/v2/transcript/{transcript_id}"
        
        # Step 3: Poll for completion
        while True:
            transcription_result = requests.get(
                polling_endpoint,
                headers=ASSEMBLYAI_HEADERS
            ).json()
            
            status = transcription_result['status']
            
            if status == 'completed':
                transcription_text = transcription_result.get('text', '')
                if not transcription_text:
                    raise Exception("Transcription completed but no text returned")
                return transcription_text
            
            elif status == 'error':
                error_msg = transcription_result.get('error', 'Unknown error')
                raise Exception(f"Transcription failed: {error_msg}")
            
            else:
                # Status is 'queued' or 'processing', wait and check again
                time.sleep(3)
    
    except requests.exceptions.RequestException as e:
        raise Exception(f"Network error during transcription: {str(e)}")
    except Exception as e:
        raise Exception(f"Transcription error: {str(e)}")


def format_with_gemini(text, template_type, max_retries=3):
    """Format text using Gemini according to template type with retry logic"""
    if template_type == "SOAP Note":
        prompt = f"""
You are a clinical documentation assistant. Convert the provided clinical transcript into a concise, accurate, and well-structured SOAP note.

Strict rules:
- Only use information explicitly stated in the transcript.
- Do NOT add, infer, or assume any data not mentioned.
- If a section has no data in the transcript, write: "Not mentioned."
- For Setting, determine (telemedicine / in-person) ONLY if the transcript explicitly indicates it. Otherwise write: "Not mentioned."

Output format EXACTLY as below (include the headings and bullet symbols exactly, no extra commentary):

SOAP NOTE
Patient Name:
DOB:
Clinician:
Date:
Setting: (telemedicine / in-person) — based on transcript

S – Subjective
• Chief Complaint:
• History of Present Illness:
• Review of Systems (only items mentioned):
• Past Medical History:
• Medications:
• Allergies:
• Family History:
• Social History:

O – Objective
• Exam findings from transcript
(If telehealth and no exam provided, write: "No physical exam performed; assessment based on verbal report.")
• Vitals if mentioned

A – Assessment
• List all clinician-stated assessments or inferred concerns explicitly stated in the transcript
• Do NOT generate diagnoses that were not discussed

P – Plan
• Diagnostics ordered or recommended
• Treatments/medications advised
• Work restrictions
• Safety netting / follow-up advice

Transcript:
[TRANSCRIPT]
{text}
"""
    elif template_type == "H&P Note":
        prompt = f"""
You are a clinical documentation assistant. Convert the provided transcript into a structured History & Physical (H&P) note.

Strict rules:
- Use only information explicitly stated. Do NOT guess or add details.
- If a section is missing information, write exactly: "Not mentioned."

Output format EXACTLY as below (include the headings and bullet symbols exactly, no extra commentary):

HISTORY & PHYSICAL (H&P)

Patient Name:
DOB:
Clinician:
Date:
Setting:

HISTORY
Chief Complaint:
History of Present Illness:
Past Medical History:
Past Surgical History:
Medications:
Allergies:
Family History:
Social History:
Review of Systems:
(Only list items explicitly found in the transcript.)

PHYSICAL EXAM
• If no exam data exists, write: "Not performed in transcript."

ASSESSMENT
• Summarize the clinician’s diagnostic thinking exactly as discussed.
• Do NOT generate new differentials unless mentioned.

PLAN
• Document investigations ordered or recommended
• Treatment recommendations
• Follow-up instructions
• Any disposition (e.g., clinic referral, ER recommendation)

Transcript:
[TRANSCRIPT]
{text}
"""
    else:
        prompt = f"Only restructure the following transcript per clinical best practice without adding any new content. Use 'Not mentioned.' for missing items.\n\nTranscript:\n{text}"
    
    # Configure generation with longer timeout
    generation_config = {
        "temperature": 0.1,
        "max_output_tokens": 8192,
    }
    
    # Retry logic with exponential backoff
    for attempt in range(max_retries):
        try:
            response = generate_with_timeout(
                prompt,
                generation_config,
                timeout_seconds=120
            )
            
            if hasattr(response, 'text') and response.text:
                return response.text
            else:
                raise Exception("Gemini API returned empty response")
        
        except FuturesTimeoutError:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                print(f"Timeout on attempt {attempt + 1}/{max_retries}. Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
                continue
            else:
                if len(text) > 5000:
                    raise Exception(
                        "Gemini API timeout. The content is too long. Please try with shorter text or split it into smaller sections."
                    )
                else:
                    raise Exception(
                        f"Gemini API request timed out after {max_retries} attempts. "
                        "The service may be experiencing high load. Please try again in a few moments."
                    )
                
        except Exception as e:
            error_msg = str(e)
            
            # Handle other specific errors
            if "API_KEY_INVALID" in error_msg or "API key not valid" in error_msg:
                raise Exception(
                    "Invalid Gemini API key. Please check your GEMINI_API_KEY in the .env file.\n"
                    "The API key should start with 'AIza' and be a valid Google AI Studio API key.\n"
                    f"Error details: {error_msg}"
                )
            elif "quota" in error_msg.lower() or "429" in error_msg:
                raise Exception(
                    "Gemini API quota exceeded.\n\n"
                    "What you can do:\n"
                    "- This may be a per-minute limit: wait 30–60 seconds and try again, or\n"
                    "- Use your own GEMINI_API_KEY in the .env file (recommended), or\n"
                    "- Check your usage/plan at https://ai.dev/usage and the rate limits docs.\n\n"
                    f"Raw error from API: {error_msg}"
                )
            else:
                # For other errors, retry or raise
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    print(f"Error on attempt {attempt + 1}/{max_retries}. Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                    continue
                else:
                    raise Exception(f"Gemini formatting error: {error_msg}")
    
    # Should never reach here, but just in case
    raise Exception("Gemini formatting failed after all retries")


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/process_audio', methods=['POST'])
def process_audio():
    try:
        if 'audio_file' not in request.files:
            return render_template('result.html',
                                   original_text='',
                                   formatted_output='No audio file provided',
                                   template_type=request.form.get('template_type', 'SOAP Note')), 400
        
        file = request.files['audio_file']
        template_type = request.form.get('template_type', 'SOAP Note')
        
        if file.filename == '':
            return render_template('result.html',
                                   original_text='',
                                   formatted_output='No file selected',
                                   template_type=template_type), 400
        
        if not allowed_file(file.filename, ALLOWED_AUDIO_EXTENSIONS):
            return render_template('result.html',
                                   original_text='',
                                   formatted_output='Invalid file type. Allowed: mp3, wav, m4a',
                                   template_type=template_type), 400
        
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        transcript_text = transcribe_audio(filepath)
        formatted_output = format_with_gemini(transcript_text, template_type)
        
        os.remove(filepath)
        
        return render_template('result.html',
                               original_text=transcript_text,
                               formatted_output=formatted_output,
                               template_type=template_type)
        
    except Exception as e:
        return render_template('result.html',
                               original_text='',
                               formatted_output=str(e),
                               template_type=request.form.get('template_type', 'SOAP Note')), 500


@app.route('/process_text', methods=['POST'])
def process_text():
    try:
        template_type = request.form.get('template_type', 'SOAP Note')
        text_input = request.form.get('text_input', '')
        text_file = request.files.get('text_file')
        
        if text_file and text_file.filename != '':
            if not allowed_file(text_file.filename, ALLOWED_TEXT_EXTENSIONS):
                return render_template('result.html',
                                       original_text='',
                                       formatted_output='Invalid file type. Allowed: txt, docx',
                                       template_type=template_type), 400
            
            if text_file.filename.endswith('.txt'):
                text_input = text_file.read().decode('utf-8')
            else:
                return render_template('result.html',
                                       original_text='',
                                       formatted_output='DOCX support requires python-docx. Please upload TXT file.',
                                       template_type=template_type), 400
        
        if not text_input.strip():
            return render_template('result.html',
                                   original_text='',
                                   formatted_output='No text provided',
                                   template_type=template_type), 400
        
        formatted_output = format_with_gemini(text_input, template_type)
        
        return render_template('result.html',
                               original_text=text_input,
                               formatted_output=formatted_output,
                               template_type=template_type)
        
    except Exception as e:
        return render_template('result.html',
                               original_text='',
                               formatted_output=str(e),
                               template_type=request.form.get('template_type', 'SOAP Note')), 500


@app.route('/result')
def result():
    if 'formatted_output' not in session:
        return redirect(url_for('index'))
    
    return render_template('result.html',
                         original_text=session.get('original_text', ''),
                         formatted_output=session.get('formatted_output', ''),
                         template_type=session.get('template_type', 'SOAP Note'))


@app.route('/download', methods=['POST'])
def download():
    """Generate text file for download"""
    from flask import make_response
    
    content = request.form.get('content', '')
    filename = request.form.get('filename', 'output.txt')
    
    response = make_response(content)
    response.headers['Content-Type'] = 'text/plain; charset=utf-8'
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'
    
    return response
