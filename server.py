from flask import Flask, render_template, request, redirect, url_for
import smtplib
import time
import random
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

app = Flask(__name__)

@app.route('/')
def index():
    # templates klasöründeki index.html'i döndürür.
    return render_template('index.html')

@app.route('/send_emails', methods=['POST'])
def send_emails():
    """
    Formdan gelen verileri alıp toplu e-posta gönderim işlemini gerçekleştirir.
    """
    # 1. Form verilerini al
    email_user = request.form.get('email_user')
    email_password = request.form.get('email_password')
    subject = request.form.get('subject', 'KAL Liseler Arası Müzik Yarışması Sponsorluk')
    message_body = request.form.get('message_body', '')

    # 2. Dosyaları çek
    pdf_file = request.files.get('pdf_file')
    ad_file = request.files.get('ad_file')
    mail_file = request.files.get('mail_file')
    company_file = request.files.get('company_file')

    if not (email_user and email_password and pdf_file and ad_file and mail_file and company_file):
        return "Eksik bilgi veya dosya yüklemesi var!"

    # 3. Geçici klasörde veya bellek üzerinde dosyaları oku
    # Ad listesi
    names_data = ad_file.read().decode('utf-8').splitlines()
    # Mail listesi
    emails_data = mail_file.read().decode('utf-8').splitlines()
    # Şirket listesi
    companies_data = company_file.read().decode('utf-8').splitlines()

    # Uzunluk kontrolü
    if len(names_data) != len(emails_data) or len(names_data) != len(companies_data):
        return "İsim, e-posta ve şirket listeleri aynı satır sayısında olmalıdır."

    # PDF içeriğini bellek üzerinde tutalım
    pdf_content = pdf_file.read()

    # SMTP işlemi
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(email_user, email_password)
    except Exception as e:
        return f"SMTP sunucusuna bağlanırken hata oluştu: {e}"

    # Gönderim raporunu tutmak için log stringi
    send_log = []

    for index, (name, email, company) in enumerate(zip(names_data, emails_data, companies_data), start=1):
        msg = MIMEMultipart()
        msg['From'] = email_user
        msg['To'] = email
        msg['Subject'] = subject

        # Kişiselleştirilmiş mesaj
        personalized_body = message_body.format(name=name, company=company)
        msg.attach(MIMEText(personalized_body, 'plain', 'utf-8'))

        # PDF ekle
        try:
            pdf_attachment = MIMEApplication(pdf_content, _subtype='pdf')
            pdf_attachment.add_header('Content-Disposition', 'attachment', filename=pdf_file.filename)
            msg.attach(pdf_attachment)
        except Exception as e:
            send_log.append(f"{index}. {company}/{name} → {email} | PDF eklenemedi: {e}")
            continue
        
        # E-posta gönder
        try:
            server.send_message(msg)
            send_log.append(f"{index}. Gönderildi → {company}/{name} ({email})")
        except Exception as e:
            send_log.append(f"{index}. Hata → {company}/{name} ({email}): {e}")

        # Spam riskini azaltmak için rastgele bekleme
        time.sleep(random.randint(3, 6))

    server.quit()
    
    # Sonuçları döndür
    final_log = "\n".join(send_log)
    return f"""<h2>Gönderim Tamamlandı</h2>
               <pre>{final_log}</pre>
               <p><a href="{url_for('index')}">Geri Dön</a></p>"""

if __name__ == '__main__':
    # Flask sunucusunu 5000 portunda başlat
    app.run(debug=True)
