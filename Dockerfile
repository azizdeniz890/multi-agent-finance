# Python 3.13 image kullanalım
FROM python:3.13-slim

# Çalışma dizini oluştur
WORKDIR /app

# Kod dosyalarını kopyala
COPY . .

# Gerekli kütüphaneleri yükle
RUN pip install --no-cache-dir -r requirements.txt

# Streamlit portunu açalım
EXPOSE 8501

# Streamlit uygulamasını başlat
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
