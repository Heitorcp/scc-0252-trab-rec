# Official python image version 3.10.11
FROM python:3.10-slim-bullseye

#Expose the port that Streamlit will work on - if you're hosting on GCP Cloud Run you don't need to Expose it
# EXPOSE 8501 

#setting the working environment inside the container 
WORKDIR /app

#Copy the requirements file to the container
COPY requirements.txt /app/

#Instala as dependencias ao criar a imagem 
RUN pip install -r requirements.txt 

COPY . /app

#Command to run the Streamlit app 
ENTRYPOINT ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501"]