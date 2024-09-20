# Intelligent File Management System Backend

This repository contains the backend implementation for an advanced file management system developed during the A2SV Hackathon. Our solution aims to address common file management challenges and introduce intelligent features for enhanced user experience.

## 🚀 Key Features


**AI Features** 🤖
- **Intelligent Chatbot Assistant**: Interacts with users and can read file contents
- **Natural Language Search**: Supports multiple languages and voice input
- **Automatic File Categorization**: Tags files based on content (e.g., financial, marketing, studies)
- **Automatic File Hierarchy Suggestion**: Proposes optimal file organization structures
  
**Other Features**
- **Duplicate File Detection**: Identifies and manages duplicate files
- **Local Deployment Option**: Ability to deploy the application on local infrastructure
- **Version Control Detection**: Automatically detects version information from file names

## 🛠️ Additional Features

- Automatic file translation
- Data backup capabilities
- Malicious file detection
- Advanced file search (image content, voice, etc.)
- File correction (fonts, spelling)

## 🔮 Future Enhancements

- Integration with PC file systems

## 🚀 How to run the project

We have two application setup environments

##### Source code Pre-setup
- Make sure to replicate the environment variables listed in the `.env.example` in a new file called `.env` located in the root folder, this should be done in all environment listed bellow and before starting the nxt step obviously.
- **For production only**: make sure to have a valid SSL certificate provider and a domain name to attribute in the nginx configurations.

##### Development environment
- **Local development environment**
    - Clone the repository
    - Navigate into code folder using ```cd code```
    - install the requirements by using `pip install -r requirements.txt`
    - Initialize a firestore database and storage (as the provided in the `.env.example`).
    - After this you can directly start the API by using `uvicorn main:app --reload`
- **Docker containers based environment**
    - Navigate into the dev folder located inside the deployment folder using ```cd deployment/dev```
    - Run the shell script located in the folder navigated using `sudo sh ./dev.sh`
##### Porduction environment
- Navigate into the prod folder located inside the deployment folder using ```cd deployment/prod```
- Run the shell script located in the folder navigated using `sudo sh ./prod.sh`
- Mae sure to generate a .httpasswd file to protect the documentation from annonymous access or use 'Okba' Magic splitter utility OR any data protection (public/private keys binding) logic to prevent random access token generation and usage.

##### Post setup
- Backend will be running in port `8000` with nginx as a reverse proxy.


## 🛠️ Technologies Used

- FastAPI: For building the API.
- Nginx: Webserver and reverse proxy.
- Firestore: As the database solution.
- Firebase Storage: For file storage.
- Elastic Search: For advanced search capabilities.
- LLAMA-2: For natural language processing.
- Stripe: As payment gateway.
- Docker: dockerize the app for better development experience.
- Google/Github: As OAuth access providers.

## 📞 Contact
For any inquiries or support, please contact:

Email: Ls_yekene@esi.dz
Phone: +213559047526

Email: lo_allaoua@esi.dz
Phone: +213777363236

Email: la_bengherbia@esi.dz

Email: js_zouambia@esi.dz

Email: la_akeb@esi.dz
