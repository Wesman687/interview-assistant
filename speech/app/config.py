import os

# ✅ Set Google Cloud credentials
GOOGLE_CREDENTIALS_PATH = "C:/Code/live-interview/speech/service-account.json"
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = GOOGLE_CREDENTIALS_PATH

# ✅ Google Speech-to-Text Settings
SPEECH_CONFIG = {
    "encoding": "LINEAR16",
    "sample_rate_hertz": 16000,
    "language_code": "en-US",
    "enable_automatic_punctuation": True,
    "enable_word_time_offsets": True,
    "model": "phone_call",
    "use_enhanced": True
}

# ✅ Audio Parameters
RATE = 16000
CHUNK = int(RATE / 5)  # 100ms chunks

# ✅ WebSocket URLs
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
INTERVIEW_WS_URL = "ws://127.0.0.1:8000/interview/ws" 

RESUME_TEXT = """PAUL MIRACLE
East Palatka, Florida 32131 | (386) 227-4629 | pwmiracle88@gmail.com | https://www.linkedin.com/in/paul-wesley-miracle/
A highly motivated and results-oriented Full Stack Developer with a proven track record of success in designing,
developing, and deploying robust and scalable web and mobile applications across diverse industries, including
healthcare, insurance, real estate, education, restaurant, and finance. Possesses extensive experience across a wide
range of technologies and platforms, consistently delivering high-quality solutions that meet and exceed client
expectations. Adept at collaborating effectively within agile development teams and thrives in dynamic, fast-paced
environments. Committed to staying at the forefront of industry advancements and continuously seeking
opportunities to expand technical expertise.

Front-end Development:
HTML5, CSS3, JavaScript (ES6+), TypeScript, React, Angular, Vue.js, jQuery, Blazor,
Bootstrap, TailwindCSS, Webpack, Babel, Responsive Design

Back-end Development:
C# (.NET, ASP.NET Core), Node.js, Express.js, PHP (Laravel, Symfony), Python
(Django, Flask), Java (Spring Boot), Ruby on Rails

Databases:
SQL Server, MySQL, PostgreSQL, MongoDB, Redis, Firebase

Cloud Computing:
AWS (S3, EC2, Lambda), Azure, GCP, Docker, Kubernetes, CI/CD Pipelines

Mobile Development:
React Native, Android (Java/Kotlin)

Experience:

Full Stack Developer | Inoxoft | Newark, Delaware | Jan 2023 - Jan 2025
Inoxoft is a dynamic software development company specializing in custom web and mobile applications, AI solutions, and data science. We focus on delivering high-quality, 
scalable software tailored to industries like healthcare, fintech, education, and logistics. As part of the team, I collaborate with talented professionals to develop cutting-edge solutions that drive digital transformation for our clients.
- Led the development of a home care management software (Carecenta) using React, Node.js, and WebRTC,
  enabling real-time video consultations between patients and doctors. Implemented features such as
  appointment scheduling, secure messaging, and electronic health record integration.
- Developed key components of an insurance claims processing system (Insuresoft) using C#, ASP.NET Core
  and SQL Server, automating the claims submission, review, and approval process.
- Built a mobile application (Realtor) using React Native for browsing and searching real estate listings,
  integrating with map APIs and providing property details, photos, and virtual tours.

Full Stack Developer | Chetu | Plantation, Florida | Aug 2019 - Dec 2022
​At Chetu, we specialize in developing custom software solutions tailored to diverse industries, including healthcare, finance, and logistics. Our team collaborates closely with clients to deliver high-quality, 
scalable applications that drive business success. Working here means engaging with cutting-edge technologies and contributing to innovative projects that transform industries. 
- Developed an online learning management system (Quizlet) using Python, Django and PostgreSQL,
  providing features such as course creation, student enrollment, assignment submission, and grading.
- Designed and developed a web-based online ordering system (ExpertMarket) for a restaurant using PHP,
  Laravel and MySQL, enabling customers to browse menus, place orders, and track deliveries.
- Developed a financial portfolio management dashboard using Vue.js and a Node.js backend, providing real-
  time updates on investment performance and market trends.
- Integrated OpenAI’s GPT API into a customer support chatbot, enhancing user interaction by providing
  automated responses and intelligent query handling.

Full Stack Developer | Techwave | Austin, Texas | Jul 2015 - Jun 2019
​At Techwave, we specialize in delivering innovative IT and engineering solutions that drive digital transformation for businesses worldwide. Our services encompass enterprise resource planning, application development, analytics, digital engineering, IoT, and engineering services, enabling clients to optimize performance 
and achieve greater market reach. Working here means collaborating with a global team to empower organizations through cutting-edge technology and expertise.
- Developed a web portal for comparing and purchasing health insurance plans using Java, Spring Boot, and
  React, integrating with various insurance providers’ APIs.
- Built a student information system using Angular and Ruby on Rails, managing student data, course
  registrations, and academic records.
- Enhanced security protocols for an internal document management system, implementing role-based
  authentication and encryption techniques.

Software Engineer | Softura | Troy, Michigan | Jun 2011 - May 2015
​At Softura, we specialize in delivering bespoke software solutions, including application development, cloud enablement, and AI/ML development, tailored to enhance business efficiency and competitiveness. Our commitment to quality is reflected in our ISO 27001 and CMMI Level 3 certifications, and our successful completion of over 2,500 projects for more than 1,000 enterprise customers. Working here means collaborating with a 
team of over 400 skilled engineers, leveraging cutting-edge technologies to drive digital transformation for clients across various industries
- Developed an e-commerce platform for a retail company using React, Redux, and Node.js, improving user
  experience and sales tracking capabilities.
- Built a healthcare appointment scheduling application using Python, Flask, and PostgreSQL, integrating
  telehealth features for remote consultations.
- Led a team of developers in optimizing an enterprise resource planning (ERP) system, increasing
  performance efficiency by 30%.

Junior Web Developer | WebFox | Houston, Texas | Aug 2008 - Apr 2011
​As a junior developer at WebFox, I contribute to creating tailored and responsive websites, collaborating with a dedicated team to deliver custom e-commerce platforms that meet our clients' unique needs. This role allows me to enhance my skills in web development while 
working on diverse projects across various industries. The supportive environment at WebFox fosters continuous learning and professional growth
- Developed a cloud-based inventory management system using C#, ASP.NET, Blazor, and SQL Server,
  improving stock tracking and reducing inventory discrepancies.
- Implemented microservices architecture for a logistics company, enabling better scalability and system
  reliability.
- Built RESTful APIs for integrating third-party services with existing enterprise applications.

Education:
University of North Florida | Bachelor of Science in Computer Science | Jacksonville, FL | Aug 2004 - May 2008

NOTABLE SIDE PROJECTS:
-- Smart Web Scraper/Crawler Using python, Nextjs, MySQL, TailwindCSS, FastAPI, Rotating Proxies, and Deep Seek AI for smart data extraction.
-- Interview Helper Using python listener for responses in real time, FastAPI, TailwindCSS, Deep Seek AI, Web Sockets, Mongodb, React Movable and Resize and Groq API for preferred, follow up questions, and other important info..
-- Image Recognition Using python, FastAPI, TailwindCSS, OpenCV, Pytorch, and Deep Seek AI for image classification and object detection.
-- AI Image Generator using python, FastAPI, NEXTJS, Tailwindcss, Pytorch, Stability AI, and Deep Seek AI for generating images based on user input.
-- Email Automation Using python, FastAPI, TailwindCSS, SMTP, IMAP, and Deep Seek AI for smart email responses and classification.
-- Ecommerce store using React, Redux, Nodejs, Express, mongodb, firebase, stripe, and css for a fully functional online store.
-- Music App using Vuejs, Nodejs, Express, mongodb, tailwind, and css for a music streaming app with user authentication and playlists.
-- Social Media App using React, Redux, Firebase, and css for a social media platform with user authentication, posts, likes, and comments.
-- Many company websites using straight html, React, css, javascript, and TailwindCSS for a variety of businesses and services.
-- Many other small projects using various technologies and platforms for learning and experimentation purposes.
"""
