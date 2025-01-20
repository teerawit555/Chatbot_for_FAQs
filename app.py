import string
import torch
import json
from sklearn.metrics.pairwise import cosine_similarity
from flask import Flask, render_template, request, jsonify
from transformers import AutoTokenizer, AutoModel, pipeline

faq = {
    # คำถามทั่วไป
    "What are your business hours?": "We are open from 9 AM to 5 PM.",
    "What time do you open?": "We are open from 9 AM to 5 PM.",
    "How much is the shipping fee?": "The shipping fee is $5.",
    "What's the delivery charge?": "The shipping fee is $5.",
    "Do you charge for shipping?": "The shipping fee is $5.",
    "What payment methods do you accept?": "We accept credit cards, PayPal, and bank transfers.",
    "Can I cancel my order?": "Yes, you can cancel your order within 24 hours of purchase.",
    "What is your return policy?": "You can return items within 30 days for a full refund.",
    "Do you ship internationally?": "Yes, we ship to most countries worldwide.",
    
    # คำทักทาย
    "Hello": "Hello! How can I assist you today?",
    "Hi": "Hi there! What can I help you with?",
    "Hey": "Hey! How can I assist you?",
    "Good morning": "Good morning! How can I help you today?",
    "Good afternoon": "Good afternoon! What can I assist you with?",
    "Good evening": "Good evening! How may I help you?",
    
    # การแสดงความขอบคุณ
    "Thank you": "You're welcome! Let me know if you have more questions.",
    "Thanks": "You're welcome! Is there anything else I can assist you with?",
    "Thanks a lot": "My pleasure! Feel free to ask anything else.",
    "Thank you so much": "You're very welcome! Let me know if you need more help.",
    
    # คำถามเกี่ยวกับสินค้า
    "Is this product available?": "Yes, the product is available. You can place your order now.",
    "Can I get a discount?": "We occasionally have discounts. Please check our website for ongoing promotions.",
    "How do I track my order?": "You can track your order using the tracking number sent to your email.",
    "What is the warranty period?": "The warranty period for this product is 1 year from the date of purchase.",
    
    # คำถามเกี่ยวกับบริการ
    "Can I speak to a human agent?": "Sure! Let me connect you to our support team.",
    "How do I contact customer support?": "You can reach our customer support team via email at support@example.com or call us at +123456789.",
    "How do I reset my password?": "Click on 'Forgot Password' on the login page and follow the instructions.",
    "Do you offer installation services?": "Yes, we offer installation services for certain products. Please contact our support team for details.",
    
    # คำถามเกี่ยวกับความปลอดภัย
    "Is my payment information secure?": "Yes, we use secure encryption to protect your payment information.",
    "Do you store my credit card details?": "No, we do not store your credit card details. Payments are processed through a secure gateway.",
    
    # คำถามอื่นๆ
    "Can I change my shipping address?": "Yes, you can change your shipping address before the order is shipped.",
    "What happens if my order is delayed?": "If your order is delayed, please contact our support team for assistance.",
    "Do you offer express shipping?": "Yes, we offer express shipping for an additional fee."
}

# Synonym mapping function
def replace_synonyms(text):
    synonyms = {
        "time": ["hours", "working hours", "opening"],
        "open": ["business", "available", "start"],
        "fee": ["cost", "charge", "price", "expense"],
        "payment": ["options", "methods", "ways", "accepted", "payment types"],
        "shipping": ["delivery", "transportation", "postage"],
        "return": ["refund", "exchange", "replacement"],
        "cancel": ["stop", "terminate", "revoke"],
        "order": ["purchase", "buy", "checkout", "track order", "order status"],
        "reset password": ["forgot password", "recover password", "change password"]
    }
    for key, values in synonyms.items():
        for value in values:
            text = text.replace(f" {value} ", f" {key} ")
    return text

# Text preprocessing
def preprocess_text_for_matching(text):
    text = text.lower()
    text = text.translate(str.maketrans("", "", string.punctuation))
    return replace_synonyms(text)

# Preprocess FAQ
faq_preprocessed = {preprocess_text_for_matching(key): value for key, value in faq.items()}

# Greeting Detection
def detect_greeting(user_message):
    greetings = ["hello", "hi", "hey", "good morning", "good afternoon", "good evening"]
    user_message_lower = user_message.lower().strip()
    if user_message_lower in greetings:
        return f"{user_message_lower.capitalize()}! How can I help you today?"
    return None

# Semantic Similarity
tokenizer = AutoTokenizer.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")
model = AutoModel.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")

def calculate_similarity(text1, text2):
    inputs1 = tokenizer(text1, return_tensors="pt", padding=True, truncation=True)
    inputs2 = tokenizer(text2, return_tensors="pt", padding=True, truncation=True)
    with torch.no_grad():
        embeddings1 = model(**inputs1).last_hidden_state.mean(dim=1)
        embeddings2 = model(**inputs2).last_hidden_state.mean(dim=1)
    similarity = cosine_similarity(embeddings1.numpy(), embeddings2.numpy())
    return similarity[0][0]

# GPT-2 Fallback
generator = pipeline("text-generation", model="distilgpt2")

def generate_generic_response(user_message):
    try:
        result = generator(user_message, max_length=50, num_return_sequences=1)
        return result[0]['generated_text']
    except Exception:
        return "I'm sorry, I couldn't process your request right now."

# Keyword Matching
def match_with_keywords(user_message):
    keywords = {
        "fee": "The shipping fee is $5.",
        "payment": "We accept credit cards, PayPal, and bank transfers.",
        "shipping": "The shipping fee is $5.",
        "open": "We are open from 9 AM to 5 PM.",
        "credit card": "We accept credit cards, PayPal, and bank transfers.",
        "cancel": "Yes, you can cancel your order within 24 hours of purchase.",
        "return": "You can return items within 30 days for a full refund.",
        "order": "You can track your order using the tracking number sent to your email.",
        "discount": "We occasionally have discounts. Please check our website for ongoing promotions.",
        "reset password": "Click on 'Forgot Password' on the login page and follow the instructions."
    }
    user_message_lower = user_message.lower()
    for keyword, response in keywords.items():
        if keyword in user_message_lower:
            return response
    return None

# Split questions in user input
def split_questions(user_message):
    separators = [',', ' and ', '&']
    questions = [user_message]
    for sep in separators:
        temp_questions = []
        for question in questions:
            if sep in question:
                temp_questions.extend(question.split(sep))
            else:
                temp_questions.append(question)
        questions = temp_questions
    return [q.strip() for q in questions if q.strip()]


# Format multiple responses
def format_multiple_responses(responses):
    formatted = "\n".join(f"- {response}" for response in responses)
    return "\n".join(responses)

# Main Matching Function
def find_best_match(user_message):
    # ตรวจจับคำทักทายก่อน
    greeting_response = detect_greeting(user_message)
    if greeting_response:
        return greeting_response

    # แยกคำถามในกรณีข้อความยาว
    user_message_parts = split_questions(user_message)
    responses = []

    for part in user_message_parts:
        part = part.strip()
        if not part:
            continue

        # Matching Keyword ก่อน
        keyword_response = match_with_keywords(part)
        if keyword_response:
            responses.append(keyword_response)
            continue

        # Matching FAQ ผ่าน Semantic Similarity
        best_match_score = -1
        best_response = "Sorry, I couldn't find an answer to your question."
        for question, answer in faq.items():
            score = calculate_similarity(preprocess_text_for_matching(part), preprocess_text_for_matching(question))
            print(f"[DEBUG] Comparing: '{part}' with '{question}' - Score: {score}")
            if score > best_match_score:
                best_match_score = score
                best_response = answer

        # Threshold สำหรับ FAQ Matching
        if best_match_score > 0.5:  # ลด Threshold
            responses.append(best_response)
        else:
            responses.append(f"I couldn't find an answer to: '{part}'")

    # รวมคำตอบทั้งหมด
    return format_multiple_responses(responses)

# Flask App
app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get('message', '').strip()
    if not user_message:
        return jsonify({"response": "Please provide a valid message."})

    response = find_best_match(user_message)
    return jsonify({"response": response})

# @app.route('/add-faq', methods=['POST'])
# def add_faq():
#     data = request.json
#     question = data.get('question', '').strip()
#     answer = data.get('answer', '').strip()

#     if not question or not answer:
#         return jsonify({"message": "Invalid input"}), 400

#     if question in faq:
#         return jsonify({"message": "Question already exists!"}), 400

#     # เพิ่มคำถาม-คำตอบใน FAQ
#     faq[question] = answer

#     # บันทึกกลับไปที่ไฟล์ JSON
#     with open("faq.json", "w") as file:
#         json.dump(faq, file, indent=4)

#     return jsonify({"message": "FAQ added successfully!"}), 200


if __name__ == '__main__':
    app.run(debug=True)
