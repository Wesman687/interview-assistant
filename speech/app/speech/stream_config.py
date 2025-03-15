from google.cloud import speech_v1p1beta1 as speech

# 1. Define domain-specific and business terms
industry_terms = [
    "cloud computing", "microservices", "Kubernetes", "Docker", "DevOps",
    "CI/CD", "machine learning", "neural network", "REST API", "Agile"
]
business_terms = [
    "stakeholder", "return on investment", "client requirements", 
    "project timeline", "team collaboration", "budget", "Agile methodology"
]

# 2. Define common technical and behavioral interview questions
technical_questions = [
    "Can you explain the Model-View-Controller architecture?",
    "How does the event loop work in Node.js?",
    "What are the differences between REST and GraphQL?",
    "How would you optimize a database query?",
    "Describe a challenging bug you encountered.",
    "What is the difference between unit and integration testing?",
    "Explain the concept of 'state' in React.",
    "How do you handle asynchronous operations in JavaScript?",
    "What is the purpose of a Docker container?",
    "How would you deploy a web application to AWS?"
    "Can you tell me your experience using python?",
    "Can you explain how you manage states in React?",
    "How do you handle errors in JavaScript?",
    "What is the difference between SQL and NoSQL databases?",
    "How do you ensure the security of a web application?",
    "What is the purpose of a RESTful API?",
    "How do you ensure your code is scalable and maintainable?",
    "What is the difference between Git and GitHub?",
    "How do you stay updated with the latest technologies?",
    "What is your experience with cloud computing services?",
    "Can you explain the difference between Agile and Waterfall methodologies?",
    "How do you approach debugging and troubleshooting in your projects?",
    "What is your experience with CI/CD pipelines?",
    "How do you handle version control in your projects?",
    "What is your experience with microservices architecture?",
    "Can you explain the concept of 'dependency injection'?",
    "How do you handle performance optimization in web applications?",
    "What is your experience with cloud computing services?",
    "Can you explain the difference between Agile and Waterfall methodologies?",
    "How do you approach debugging and troubleshooting in your projects?",
    "What is your experience with CI/CD pipelines?",
    "How do you handle version control in your projects?",
    "What is your experience with microservices architecture?",
    "Can you explain the concept of 'dependency injection'?",
    "How do you handle performance optimization in web applications?",
]
algorithmic_questions = [
    "Can you implement a binary search algorithm?",
    "What is the time complexity of quicksort?",
    "Can you explain the difference between breadth-first search and depth-first search?",
    "How would you reverse a linked list?",
    "What are the advantages of using a hash table over an array?",
    "How would you detect a cycle in a linked list?",
    "Can you implement a LRU cache?",
    "What is memoization and how does it differ from tabulation?",
    "Can you implement the Fibonacci sequence using dynamic programming?",
    "How would you solve the knapsack problem?",
    "Explain the longest increasing subsequence problem.",
    "Can you optimize a search function for a large dataset?",
    "How would you handle a large number of concurrent API requests?",
    "How do you handle memory leaks in JavaScript applications?"
]

behavioral_questions = [
    "Tell me about a time you resolved a team conflict.",
    "Describe a situation where you missed a deadline.",
    "How do you handle multiple priorities under pressure?",
    "Give an example of showing leadership in a project.",
    "How do you respond to constructive criticism?"
]

# 3. Include keywords from the provided resume (programming languages, frameworks, etc.)
resume_keywords = [
    "React", "Node.js", "Express", "Django", "GraphQL", "PostgreSQL",
    "MongoDB", "AWS", "Docker", "Kubernetes", "Python", "JavaScript", "TypeScript", "CI/CD", "Agile",
    "Vue.js", "Angular", "REST API", "Bootstrap", "TailwindCSS", "C#", ".NET", "ASP.NET Core", "SQL Server",
    "MySQL", "Firebase", "Azure", "GCP", "Java", "Spring Boot", "Ruby on Rails", "Laravel", "Symfony",
    "React Native", "Android", "Java", "Kotlin", "HTML5", "CSS3", "jQuery", "Blazor", "Webpack", "Babel",
    "Responsive Design", "PHP", "Flask", "Redis", "Firebase", "AWS", "S3", "EC2", "Lambda", "CI/CD Pipelines",
    "microservices", "machine learning", "neural network", "DevOps", "cloud computing", "NEXT.js", "Nuxt.js"
]

# Combine all custom phrases and assign a strong boost for recognition
custom_phrases = industry_terms + business_terms + technical_questions + behavioral_questions + resume_keywords 
+ algorithmic_questions
speech_context = speech.SpeechContext(phrases=custom_phrases, boost=20.0)

# 4. Configure speaker diarization for exactly 2 speakers (Recruiter and Me)
diarization_config = speech.SpeakerDiarizationConfig(
    enable_speaker_diarization=True,
    min_speaker_count=2,
    max_speaker_count=2
)

# 5. Assemble the RecognitionConfig with clarity-focused settings
recognition_config = speech.RecognitionConfig(
    language_code="en-US",
    encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,  # assuming linear PCM audio
    sample_rate_hertz=44100,  # typical sample rate for microphone audio
    model="video",            # use an enhanced model for conversations (e.g., "video" or "phone_call")
    use_enhanced=True,        # enable enhanced model for higher accuracy
    enable_automatic_punctuation=True,  # add punctuation for sentence coherence
    speech_contexts=[speech_context],   # include our custom phrase hints with boost
    diarization_config=diarization_config  # enable speaker diarization (2 speakers)
)

# 6. Create the StreamingRecognitionConfig for the streaming transcription
streaming_config = speech.StreamingRecognitionConfig(
    config=recognition_config,
    interim_results=False,    # prioritize complete sentences over interim partial results
    single_utterance=False    # allow multiple utterances (entire interview) in one session
)
