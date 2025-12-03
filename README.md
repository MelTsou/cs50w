# SSEMapp 
## Server-Side Encrypted Messaging Application

SSEMapp is a compact, privacy oriented web application that offers private group messaging with server-side encryption and optional self-destructing conversations.
The signed-in users have the ability to create conversations, send and receive text messages, as well as configure a timer that automatically deletes all messages in a conversation after a predefined time delay.

## Distinctiveness and Complexity

SSEMapp is neither a Social Network nor an E-commerce Platform because in the application developed there are no public posts, profiles, timelines, likes, bids or listings.
The application is specifically focused on safe, secure, anonymous and private group communication with temporary data.  It is completely different in nature from all other CS50W Projects.
The objective of the application is an encrypted communication through messages, by designing a backend that utilizes encryption and key management as top priority, and not sharing public posts nor buying and selling products.

The main complexity exists in its algorithmic encryption. Each single message is encrypted using AES-256-GCM from the `cryptography` library. A random Data Encryption Key (DEK) is generated per-message, that's used to encrypt user's text, and then it's wrapped with a Key Encryption Key (KEK) that is loaded from an environment variable.
Only the encrypted text (ciphertext), random number used only once (nonce), additional authenticated data (aad), and the wrapped DEK are stored in the database as `BinaryField`.
Messages are never stored unencrypted. Decryption uses AAD acquired from combining conversation and sender IDs, thus by altering metadata decryption breaks.

Another important aspect of the complexity is the self-destruct technique. Conversations have an `autodestruct_at` timestamp. On each message fetch, the backend checks the value and if the time has passed, all the messages of that conversation are deleted and the timer is cleared.
The front-end displays a dropdown to set the delay (1, 3 or 5 minutes) and updates a live countdown span element by polling the server, thus it achieves to to stay in sync.

Conclusively, the project is designed as a mini single-page application written in vanilla Javascript.
All conversation and message processes use JSON endpoints, the User Interface is developed by manipulating dynamically the DOM, polling for new messages, aligning chat bubbles 
depending on the sender, polling and updating conversation list, self-destruct feature, handling validation errors from the API.
Models use UUID primary keys, Many-To-Many relationship for members, an indexed `(conversation, created_at)` pair optimized for speed and scalability and a JSON `meta` for future development.

## File Overview

- `encryptedmessenger/models.py`: `User`, `Conversation` (with `autodestruct_at`), and `Message` with all encryption fields and metadata.
- `encryptedmessenger/enc_services.py`: Encryption/decryption helpers using AES-GCM and AES key wrapping/unwrapping, loads KEK from settings/env.
- `encryptedmessenger/views.py`: Index, login, logout, and registration views.
- `encryptedmessenger/api.py`: JSON API for conversations, messages, and autodestruct configuration, including various checks and username validation.
- `encryptedmessenger/urls.py`: Routes for HTML views and API endpoints.
- `templates/encryptedmessenger/layout.html`: Base template, Bootstrap 5.3.3 and script includes.
- `templates/encryptedmessenger/index.html`: Main app (navbar, conversation list, chat, autodestruct controls).
- `templates/encryptedmessenger/login.html`, `register.html`: Authentication pages with error messages.
- `static/encryptedmessenger/main.js`: Frontend code (fetch helpers, polling, messages, alerts and autodestruct countdown).
- `static/encryptedmessenger/styles.css`: Layout, mobile responsiveness additions.
- `capstone/settings.py`: Project settings, custom user model, dotenv loading, and KEK configuration.
- `.env`: Local environment variables (`KEK` and `KEK_ID`).
- `encryptedmessenger/apps.py`: Django app configuration.
- `requirements.txt`: Django, cryptography, python-dotenv
- `manage.py` is unmodified.

## How to run the application

1. Clone the repository and change into the project directory.
2. Create and activate a virtual environment:
```bash
python -m venv newvenv
venv\Scripts\activate
```
3. Install dependencies:
```bash
pip install -r requirements.txt
```
4. Open a terminal and run the following command:
```bash
python -c "import os, binascii; print(binascii.hexlify(os.urandom(32)).decode())"
```
5. Create a `.env` file next to manage.py and set the terminal's output:
```
KMS_KEK_HEX= <64 hex chars from os.urandom(32)>
KEK_ID= kek-local-1
```
**OR:** Use the existing KEK_HEX (found in `.env` file) that I have commited.

***Note: In a real deployment, KEK management would be handled by a dedicated KMS and the .env contents would never be commited. HTTPS would be mandatory.***

6. Run migrations:
```bash
python manage.py makemigrations
python manage.py migrate
```

7. Start the development server:
```bash
python manage.py runserver
```
8. Visit http://127.0.0.1:8000/ in your browser.

## Additional information
The UI is designed with Bootstrap's grid system and classes and CSS @media. 
It fulfills the mobile-responsiveness requirement.
### Future Development
The `meta` JSON field, the `kek_id` field and the separate `enc_services.py` are there so it's easy to add seen status, KEK rotation, etc.