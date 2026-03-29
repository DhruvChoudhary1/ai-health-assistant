import kagglehub

# Download AI Medical Chatbot dataset
chatbot_path = kagglehub.dataset_download("yousefsaeedian/ai-medical-chatbot")
print("AI Medical Chatbot dataset path:", chatbot_path)

# Download Diseases and Symptoms dataset
disease_path = kagglehub.dataset_download("dhivyeshrk/diseases-and-symptoms-dataset")
print("Diseases and Symptoms dataset path:", disease_path)