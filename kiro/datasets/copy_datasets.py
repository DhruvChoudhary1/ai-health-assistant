import shutil
import os

# Source paths from kagglehub
src_chatbot = r'C:\Users\HP\.cache\kagglehub\datasets\yousefsaeedian\ai-medical-chatbot\versions\1\ai-medical-chatbot.csv'
src_disease = r'C:\Users\HP\.cache\kagglehub\datasets\dhivyeshrk\diseases-and-symptoms-dataset\versions\1\Final_Augmented_dataset_Diseases_and_Symptoms.csv'

dst_chatbot = r'./ai-medical-chatbot.csv'
dst_disease = r'./Final_Augmented_dataset_Diseases_and_Symptoms.csv'

shutil.copy(src_chatbot, dst_chatbot)
shutil.copy(src_disease, dst_disease)
print('Datasets copied to local datasets directory.')